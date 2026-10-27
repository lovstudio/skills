#!/usr/bin/env python3
"""Measure the rhythm of a reference or finished film.

Reads one video (plus an optional VTT/SRT transcript) and writes a JSON
rhythm profile: cut pace, black intervals, loudness arc, speech coverage,
music-only breathing windows, peak position and coda length. With
--envelope it also compares the profile against a reference envelope.

Requires ffmpeg on PATH. Standard library only.
"""
import argparse
import json
import math
import re
import statistics
import subprocess
import sys
from pathlib import Path

BREATH_MIN_S = 2.0      # a speech gap at least this long counts as a breathing window
LONG_BREATH_S = 8.0     # a breathing window this long is a music-only passage
CREDIT_CUES = r"(?i)subtitles? by|amara\.org|captions? by|captioned by"


def run_ffmpeg(args):
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-nostats"] + args,
                          capture_output=True, text=True, errors="replace")
    return proc.stdout + proc.stderr


def probe_duration(video):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(video)],
                         capture_output=True, text=True)
    return float(out.stdout.strip())


def detect_cuts(video, threshold):
    log = run_ffmpeg(["-i", str(video), "-an", "-vf",
                      f"scale=256:-2,select='gt(scene,{threshold})',metadata=print:file=-",
                      "-f", "null", "-"])
    return [float(m) for m in re.findall(r"pts_time:([\d.]+)", log)]


def detect_black(video):
    log = run_ffmpeg(["-i", str(video), "-an", "-vf",
                      "scale=256:-2,blackdetect=d=0.25:pix_th=0.12:pic_th=0.88",
                      "-f", "null", "-"])
    return [{"start": float(a), "end": float(b)}
            for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", log)]


def measure_loudness(video):
    log = run_ffmpeg(["-i", str(video), "-vn", "-af",
                      "ebur128=metadata=1,ametadata=print:key=lavfi.r128.S:file=-",
                      "-f", "null", "-"])
    frames = [(float(t), float(s)) for t, s in
              re.findall(r"pts_time:([\d.]+)\s+lavfi\.r128\.S=(-?[\d.]+)", log)]
    summary = log[log.rfind("Summary:"):] if "Summary:" in log else ""
    integrated = re.search(r"I:\s*(-?[\d.]+) LUFS", summary)
    lra = re.search(r"LRA:\s*(-?[\d.]+) LU", summary)
    per_second = {}
    for t, s in frames:
        per_second.setdefault(int(t), []).append(s)
    curve = [max(v) for _, v in sorted(per_second.items())]
    return {
        "integrated_lufs": float(integrated.group(1)) if integrated else None,
        "lra_lu": float(lra.group(1)) if lra else None,
        "short_term_per_second": curve,
    }


def parse_timestamp(value):
    parts = value.replace(",", ".").split(":")
    parts = ["0"] * (3 - len(parts)) + parts
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])


def parse_transcript(path, ignore=()):
    patterns = [re.compile(CREDIT_CUES)] + [re.compile(p) for p in ignore]
    cues = []
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"\s*([\d:.,]+)\s+-->\s+([\d:.,]+)", lines[i])
        if m:
            start, end = parse_timestamp(m.group(1)), parse_timestamp(m.group(2))
            i += 1
            text = []
            while i < len(lines) and lines[i].strip():
                text.append(re.sub(r"<[^>]+>", "", lines[i]).strip())
                i += 1
            joined = " ".join(text).strip()
            if joined and not re.fullmatch(r"\[.*\]|♪+", joined) \
                    and not any(p.search(joined) for p in patterns):
                cues.append((start, end, joined))
        i += 1
    return cues


def merge_intervals(intervals):
    merged = []
    for a, b in sorted(intervals):
        if merged and a <= merged[-1][1] + 0.05:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return merged


def count_units(text):
    cjk = len(re.findall(r"[\u3400-\u9fff]", text))
    latin = len(re.findall(r"[A-Za-z0-9']+", text))
    return cjk, latin


def speech_metrics(cues, duration):
    if not cues:
        return None
    spans = merge_intervals([(a, min(b, duration)) for a, b, _ in cues])
    covered = sum(b - a for a, b in spans)
    cjk = latin = 0
    for _, _, t in cues:
        c, l = count_units(t)
        cjk += c
        latin += l
    boundaries = [0.0] + [x for s in spans for x in s] + [duration]
    gaps = []
    for k in range(0, len(boundaries), 2):
        a, b = boundaries[k], boundaries[k + 1]
        if b - a >= BREATH_MIN_S:
            gaps.append({"start": round(a, 2), "end": round(b, 2), "length": round(b - a, 2)})
    rate = {}
    if latin:
        rate["words_per_minute"] = round(latin / covered * 60, 1)
    if cjk:
        rate["chars_per_minute"] = round(cjk / covered * 60, 1)
    return {
        "coverage": round(covered / duration, 3),
        "first_speech_s": round(spans[0][0], 2),
        "last_speech_end_s": round(spans[-1][1], 2),
        "coda_s": round(duration - spans[-1][1], 2),
        "rate_in_speech": rate,
        "breathing_windows": gaps,
        "long_breaths": sum(1 for g in gaps if g["length"] >= LONG_BREATH_S),
    }


def quantile(values, q):
    ordered = sorted(values)
    if not ordered:
        return None
    pos = (len(ordered) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def shot_metrics(cuts, duration):
    edges = [0.0] + [c for c in cuts if 0.2 < c < duration - 0.2] + [duration]
    shots = [b - a for a, b in zip(edges, edges[1:]) if b - a > 0.04]
    quarters = []
    for q in range(4):
        lo, hi = duration * q / 4, duration * (q + 1) / 4
        n = sum(1 for c in cuts if lo <= c < hi)
        quarters.append(round((hi - lo) / (n + 1), 2))
    return {
        "count": len(shots),
        "median_s": round(statistics.median(shots), 2),
        "mean_s": round(statistics.mean(shots), 2),
        "p10_s": round(quantile(shots, 0.1), 2),
        "p90_s": round(quantile(shots, 0.9), 2),
        "avg_shot_by_quarter_s": quarters,
        "q4_over_q1": round(quarters[3] / quarters[0], 2) if quarters[0] else None,
    }


def loudness_arc(curve):
    usable = [x if x > -70 else -70.0 for x in curve]
    n = len(usable)
    if n < 20:
        return None
    deciles = []
    for d in range(10):
        part = usable[n * d // 10: n * (d + 1) // 10]
        deciles.append(round(sum(part) / len(part), 1))
    window = 10
    best_i, best_v = 0, -999.0
    for i in range(0, n - window):
        v = sum(usable[i:i + window]) / window
        if v > best_v:
            best_i, best_v = i, v
    peak_decile = min(9, (best_i + window // 2) * 10 // n)
    dip = 0.0
    for i in range(2, peak_decile + 1):
        dip = max(dip, max(deciles[1:i]) - deciles[i])
    return {
        "short_term_mean_by_decile": deciles,
        "loudest_10s_start_s": best_i,
        "loudest_10s_position": round((best_i + window / 2) / n, 3),
        "loudest_10s_lufs": round(best_v, 1),
        "opening_vs_peak_lu": round(deciles[0] - best_v, 1),
        "ending_vs_peak_lu": round(deciles[-1] - best_v, 1),
        "pre_peak_dip_lu": round(dip, 1),
    }


def peak_to_breath_s(arc, speech):
    """Seconds between the loudest 10 s window and the nearest long music-only window."""
    if not arc or not speech:
        return None
    a, b = arc["loudest_10s_start_s"], arc["loudest_10s_start_s"] + 10
    best = None
    for g in speech["breathing_windows"]:
        if g["length"] < LONG_BREATH_S:
            continue
        gap = max(0.0, g["start"] - b, a - g["end"])
        best = gap if best is None else min(best, gap)
    return None if best is None else round(best, 2)


def build_profile(video, transcript, threshold, ignore=()):
    duration = probe_duration(video)
    cuts = detect_cuts(video, threshold)
    black = detect_black(video)
    loud = measure_loudness(video)
    cues = parse_transcript(transcript, ignore) if transcript else []
    arc = loudness_arc(loud["short_term_per_second"])
    speech = speech_metrics(cues, duration)
    profile = {
        "schema": "motivational-rhythm-profile/v1",
        "source": Path(video).name,
        "duration_s": round(duration, 2),
        "scene_threshold": threshold,
        "shots": shot_metrics(cuts, duration),
        "cuts_s": [round(c, 2) for c in cuts],
        "black_intervals": [{k: round(v, 2) for k, v in b.items()} for b in black],
        "loudness": {
            "integrated_lufs": loud["integrated_lufs"],
            "lra_lu": loud["lra_lu"],
            "arc": arc,
            "peak_to_long_breath_s": peak_to_breath_s(arc, speech),
            "short_term_per_second": [round(x, 1) for x in loud["short_term_per_second"]],
        },
        "speech": speech,
        "limits": [
            "Hard cuts only; dissolves and whip transitions are under-counted.",
            "Black intervals include fades and black text cards; inspect frames to tell them apart.",
            "Speech metrics depend on transcript timing, not word alignment.",
        ],
    }
    if not cues:
        profile["limits"].append("No transcript supplied; speech and breathing metrics unavailable.")
    return profile


def metric_paths(profile):
    arc = (profile.get("loudness") or {}).get("arc") or {}
    speech = profile.get("speech") or {}
    shots = profile.get("shots") or {}
    return {
        "duration_s": profile.get("duration_s"),
        "shots.median_s": shots.get("median_s"),
        "shots.q4_over_q1": shots.get("q4_over_q1"),
        "loudness.lra_lu": (profile.get("loudness") or {}).get("lra_lu"),
        "arc.peak_position": arc.get("loudest_10s_position"),
        "arc.opening_vs_peak_lu": arc.get("opening_vs_peak_lu"),
        "arc.ending_vs_peak_lu": arc.get("ending_vs_peak_lu"),
        "arc.pre_peak_dip_lu": arc.get("pre_peak_dip_lu"),
        "speech.coverage": speech.get("coverage"),
        "speech.coda_s": speech.get("coda_s"),
        "speech.long_breaths": speech.get("long_breaths"),
    }


def compare(profile, envelope, archetype):
    bands = envelope["archetypes"][archetype]["bands"]
    rows = []
    for key, value in metric_paths(profile).items():
        band = bands.get(key)
        if band is None or value is None:
            continue
        lo, hi = band["min"], band["max"]
        status = "inside" if lo <= value <= hi else "outside"
        rows.append({"metric": key, "value": value, "band": [lo, hi], "status": status})
    return {"archetype": archetype, "rows": rows,
            "outside": [r["metric"] for r in rows if r["status"] == "outside"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("video", help="Video file to measure")
    parser.add_argument("--transcript", help="VTT or SRT with timed speech cues")
    parser.add_argument("--ignore-cue", action="append", default=[],
                        help="Regex for non-speech cues such as subtitle credits; repeatable")
    parser.add_argument("--scene-threshold", type=float, default=0.28,
                        help="ffmpeg scene score for a hard cut (default 0.28)")
    parser.add_argument("--envelope", help="Reference envelope JSON to compare against")
    parser.add_argument("--archetype", default="single-arc",
                        help="Archetype key inside the envelope (default single-arc)")
    parser.add_argument("--out", help="Write the profile JSON here instead of stdout")
    args = parser.parse_args()

    if not Path(args.video).is_file():
        sys.exit(f"video not found: {args.video}")
    profile = build_profile(args.video, args.transcript, args.scene_threshold, args.ignore_cue)
    if args.envelope:
        envelope = json.loads(Path(args.envelope).read_text(encoding="utf-8"))
        if args.archetype not in envelope.get("archetypes", {}):
            sys.exit(f"archetype not in envelope: {args.archetype}")
        profile["comparison"] = compare(profile, envelope, args.archetype)
    text = json.dumps(profile, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(args.out)
    else:
        print(text)


if __name__ == "__main__":
    main()
