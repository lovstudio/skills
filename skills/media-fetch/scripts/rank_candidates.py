#!/usr/bin/env python3
"""Rank normalized Media Fetch candidates and identify genuine user choices."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


GIB = 1024**3
EDITION_SCORES = {
    "director-cut": 30,
    "extended": 26,
    "uncut": 24,
    "complete": 22,
    "restored": 18,
    "theatrical": 12,
    "original": 12,
    "regional": 5,
    "unknown": 0,
}
RESOLUTION_SCORES = {"4320p": 18, "2160p": 36, "1080p": 31, "720p": 13}
CODEC_SCORES = {"av1": 16, "hevc": 15, "h265": 15, "h264": 8, "avc": 8, "vp9": 9}


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERROR: cannot read candidate JSON {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("candidates"), list):
        raise SystemExit("ERROR: candidate document must contain a candidates array")
    return data


def infer(candidate: dict[str, Any]) -> dict[str, Any]:
    item = dict(candidate)
    name = str(item.get("name", ""))
    lower = name.lower().replace("_", ".").replace(" ", ".")
    if not item.get("resolution"):
        match = re.search(r"(?<!\d)(4320|2160|1080|720)p(?!\d)", lower)
        item["resolution"] = f"{match.group(1)}p" if match else "unknown"
    if not item.get("video_codec"):
        if re.search(r"\b(av1)\b", lower):
            item["video_codec"] = "av1"
        elif re.search(r"\b(hevc|h\.?265|x265)\b", lower):
            item["video_codec"] = "hevc"
        elif re.search(r"\b(avc|h\.?264|x264)\b", lower):
            item["video_codec"] = "h264"
        else:
            item["video_codec"] = "unknown"
    if not item.get("edition"):
        if re.search(r"director.?s?.?cut|directors.?cut", lower):
            item["edition"] = "director-cut"
        elif "extended" in lower:
            item["edition"] = "extended"
        elif re.search(r"uncut|unrated", lower):
            item["edition"] = "uncut"
        elif re.search(r"complete|完整版", lower):
            item["edition"] = "complete"
        elif re.search(r"theatrical|影院版", lower):
            item["edition"] = "theatrical"
        else:
            item["edition"] = "unknown"
    languages = set(item.get("subtitle_languages") or [])
    if re.search(r"\b(chs|zh-cn|zh-hans|中字|简中|双语)\b", lower):
        languages.add("zh-Hans")
    if re.search(r"\b(eng|english|双语)\b", lower):
        languages.add("en")
    item["subtitle_languages"] = sorted(languages)
    return item


def score_candidate(
    candidate: dict[str, Any], max_size_gib: float, requested_editions: list[str]
) -> dict[str, Any]:
    item = infer(candidate)
    score = 0.0
    strengths: list[str] = []
    warnings: list[str] = []

    edition = str(item.get("edition") or "unknown")
    edition_score = EDITION_SCORES.get(edition, 0)
    if requested_editions and edition in requested_editions:
        edition_score += max(0, 12 - requested_editions.index(edition) * 2)
        strengths.append(f"matches requested edition: {edition}")
    score += edition_score

    confidence = str(item.get("metadata_confidence") or "unknown")
    if confidence == "verified":
        score += 18
        strengths.append("verified release metadata")
    elif confidence == "release-record":
        score += 12
        strengths.append("release-record evidence")
    elif confidence == "filename":
        warnings.append("edition and stream claims rely on filename")
    else:
        score -= 4
        warnings.append("weak metadata evidence")

    resolution = str(item.get("resolution") or "unknown").lower()
    codec = str(item.get("video_codec") or "unknown").lower()
    score += RESOLUTION_SCORES.get(resolution, 0)
    score += CODEC_SCORES.get(codec, 0)
    if resolution == "2160p" and codec in {"hevc", "h265", "av1"}:
        strengths.append("efficient 2160p")
    elif resolution == "1080p" and codec in {"hevc", "h265", "av1"}:
        strengths.append("compact high-quality 1080p")

    size_bytes = int(item.get("size_bytes") or 0)
    size_gib = size_bytes / GIB if size_bytes else 0.0
    if size_bytes:
        if size_gib > max_size_gib:
            over = size_gib / max_size_gib
            score -= 55 + min(35, (over - 1) * 30)
            warnings.append(f"exceeds size cap ({size_gib:.1f} GiB > {max_size_gib:.1f} GiB)")
        elif resolution == "2160p" and size_gib < 2.5:
            score -= 20
            warnings.append("implausibly small for a typical 2160p feature")
        elif resolution == "1080p" and size_gib < 1.2:
            score -= 12
            warnings.append("very small for a typical 1080p feature")
        else:
            score += 10
            strengths.append(f"inside size cap at {size_gib:.1f} GiB")
        if "remux" in str(item.get("name", "")).lower() and size_gib > max_size_gib * 0.8:
            score -= 12
            warnings.append("large remux in balanced mode")
    else:
        score -= 10
        warnings.append("size unknown")

    subtitles = {str(value).lower() for value in item.get("subtitle_languages") or []}
    has_zh = bool(subtitles & {"zh-hans", "zh", "chs", "zh-cn"})
    has_en = bool(subtitles & {"en", "eng", "english"})
    if has_zh and has_en:
        score += 20
        strengths.append("Chinese and English subtitles advertised")
    elif has_zh or has_en:
        score += 7
        warnings.append("only one preferred subtitle language advertised")
    else:
        score -= 8
        warnings.append("preferred subtitles absent or unknown")
    if bool(item.get("subtitle_verified")):
        score += 8
        strengths.append("subtitle streams verified")

    if bool(item.get("trusted_source")):
        score += 8
        strengths.append("trusted source")
    seeders = max(0, int(item.get("seeders") or 0))
    score += min(18, math.log2(seeders + 1) * 2.4)
    if seeders >= 20:
        strengths.append(f"healthy seeder count ({seeders})")
    elif seeders == 0:
        warnings.append("no current seeders reported")

    return {
        "candidate": item,
        "score": round(score, 2),
        "strengths": strengths,
        "warnings": warnings,
    }


def choice_reasons(
    ranked: list[dict[str, Any]], cap: float, query: dict[str, Any]
) -> list[str]:
    if not ranked:
        return ["no viable candidates"]
    reasons: list[str] = []
    if bool(query.get("title_ambiguous")):
        reasons.append("multiple plausible works share the requested identity")
    if bool(query.get("edition_choice_required")):
        reasons.append("credible editions contain materially different content")
    first = ranked[0]
    candidate = first["candidate"]
    if str(candidate.get("edition") or "unknown") != "theatrical" and str(
        candidate.get("metadata_confidence") or "unknown"
    ) not in {"verified", "release-record"}:
        reasons.append("preferred edition lacks independent release evidence")
    size_gib = int(candidate.get("size_bytes") or 0) / GIB
    if size_gib > cap:
        reasons.append("top candidate exceeds the explicit size cap")
    if len(ranked) >= 2 and first["score"] - ranked[1]["score"] <= 8:
        second = ranked[1]["candidate"]
        edition_diff = candidate.get("edition") != second.get("edition")
        size_a = int(candidate.get("size_bytes") or 0)
        size_b = int(second.get("size_bytes") or 0)
        size_diff = max(size_a, size_b) / max(1, min(size_a, size_b)) if size_a and size_b else 1
        resolution_diff = candidate.get("resolution") != second.get("resolution")
        if edition_diff or resolution_diff or size_diff > 1.35:
            reasons.append("top candidates are close but trade edition, picture, or size")
    return reasons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-size-gib", type=float)
    args = parser.parse_args()

    document = load_json(args.input)
    query = document.get("query") if isinstance(document.get("query"), dict) else {}
    media_type = str(query.get("media_type") or "movie")
    default_cap = 6.0 if media_type == "episode" else 24.0
    max_size_gib = args.max_size_gib or float(query.get("max_size_gib") or default_cap)
    requested = [str(value) for value in query.get("requested_editions") or []]
    seen: set[str] = set()
    ranked: list[dict[str, Any]] = []
    for index, raw in enumerate(document["candidates"]):
        if not isinstance(raw, dict):
            continue
        item = dict(raw)
        item.setdefault("id", f"candidate-{index + 1}")
        key = str(item.get("info_hash") or item.get("uri") or item["id"]).upper()
        if key in seen:
            continue
        seen.add(key)
        ranked.append(score_candidate(item, max_size_gib, requested))
    ranked.sort(key=lambda item: item["score"], reverse=True)
    reasons = choice_reasons(ranked, max_size_gib, query)
    result = {
        "schema_version": "1.0",
        "query": query,
        "max_size_gib": max_size_gib,
        "selected_id": ranked[0]["candidate"]["id"] if ranked else None,
        "choice_required": bool(reasons),
        "reasons": reasons,
        "ranked": ranked,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected_id": result["selected_id"],
        "choice_required": result["choice_required"],
        "reasons": reasons,
        "candidates": len(ranked),
        "output": str(args.output),
    }, ensure_ascii=False, indent=2))
    return 0 if ranked else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
