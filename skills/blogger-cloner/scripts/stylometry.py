#!/usr/bin/env python3
"""Chinese-aware stylometry for blogger style packs.

Standalone (stdlib only). Used by cloner.py and copied verbatim into packaged
creator writing Skills, so it must not import anything from this repository.

  stylometry.py metrics ARTICLE.md [--title T]
  stylometry.py audit --pack PACK_DIR --draft DRAFT.md [--title T] [--allow-identity]
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

METRICS_SCHEMA = "blogger-cloner-metrics/v1"
AUDIT_SCHEMA = "blogger-cloner-audit/v1"

HAN = "㐀-䶿一-鿿豈-﫿"
HAN_RE = re.compile(f"[{HAN}]")
HAN_RUN_RE = re.compile(f"[{HAN}]+")
UNIT_RE = re.compile(f"[{HAN}]|[A-Za-z0-9]+")
LATIN_RE = re.compile(r"[A-Za-z][A-Za-z0-9.+#'-]*")
DIGIT_RE = re.compile(r"\d+(?:[.,]\d+)*%?")
ZW_RE = re.compile("[​-‏⁠﻿]")
IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*|__(.+?)__")
TAG_RE = re.compile(r"<[^>]+>")
SENT_END = re.compile(r"((?:[。！？!?…]|\.{3,})+[”’」』）)\"']*)")
NON_KEY_RE = re.compile(f"[^{HAN}A-Za-z0-9]+")

PUNCT = {
    "comma": "，,",
    "period": "。",
    "exclaim": "！!",
    "question": "？?",
    "ellipsis": "…",
    "dots": "。。",
    "dash": "—",
    "colon": "：",
    "semicolon": "；",
    "enum": "、",
    "quote": "“”‘’「」『』",
    "paren": "（）",
    "book": "《》",
    "tilde": "~～",
}
MARKERS = [
    "但是", "不过", "所以", "因为", "其实", "然后", "而且", "甚至", "毕竟", "当然",
    "真的", "就是", "确实", "居然", "竟然", "非常", "特别", "超级", "太", "最",
    "我觉得", "我认为", "我想", "说实话", "说真的", "说白了", "本质上", "简单来说",
    "换句话说", "比如", "首先", "其次", "最后", "总之", "核心", "关键", "问题是",
]
# Metrics compared against the training band. Length-scaled counts stay out.
FIT_KEYS = [
    "para_units_median", "para_units_p90", "one_sentence_para_ratio", "short_para_ratio",
    "sent_units_median", "sent_units_p90", "short_sent_ratio", "long_sent_ratio",
    "question_sent_ratio", "exclaim_sent_ratio",
    "punct_comma_per1k", "punct_period_per1k", "punct_exclaim_per1k", "punct_question_per1k",
    "punct_ellipsis_per1k", "punct_dots_per1k", "punct_dash_per1k", "punct_colon_per1k", "punct_quote_per1k",
    "pron_wo_per1k", "pron_women_per1k", "pron_ni_per1k", "pron_dajia_per1k",
    "latin_per1k", "digit_per1k", "bold_per1k", "images_per1k", "headings_per1k",
    "list_block_ratio", "units_total", "title_units",
]
SHINGLE_K = 12
DIGEST_BYTES = 6


# ---------------------------------------------------------------- parsing

def strip_front_matter(md: str) -> tuple[dict, str]:
    md = md.replace("\r\n", "\n")
    if not md.startswith("---\n"):
        return {}, md
    end = md.find("\n---", 4)
    if end == -1:
        return {}, md
    meta = {}
    for line in md[4:end].split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"').strip("'")
    rest = md[end + 4:]
    return meta, rest[1:] if rest.startswith("\n") else rest


def strip_inline(s: str) -> str:
    s = IMG_RE.sub("", s)
    s = LINK_RE.sub(r"\1", s)
    s = re.sub(r"\*\*|__", "", s)
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = TAG_RE.sub("", s)
    s = html.unescape(s)
    s = ZW_RE.sub("", s).replace("\xa0", " ").replace("　", " ")
    return re.sub(r"[ \t]+", " ", s).strip()


def parse_markdown(md: str) -> list[dict]:
    """One non-empty line is one block; WeChat exports put each paragraph on its own line."""
    _, md = strip_front_matter(md)
    blocks: list[dict] = []
    in_code = False
    code: list[str] = []
    for raw in md.split("\n"):
        line = raw.rstrip()
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                blocks.append({"i": len(blocks), "kind": "code", "level": 0,
                               "text": "\n".join(code), "images": 0, "bold": 0, "bold_line": False})
                code = []
            in_code = not in_code
            continue
        if in_code:
            code.append(line)
            continue
        if not stripped:
            continue
        images = len(IMG_RE.findall(stripped))
        bold = len(BOLD_RE.findall(stripped))
        kind, level, body = "p", 0, stripped
        heading = re.match(r"(#{1,6})\s+(.*)", stripped)
        if heading:
            kind, level, body = "heading", len(heading.group(1)), heading.group(2)
        elif re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            kind, body = "hr", ""
        elif stripped.startswith(">"):
            kind, body = "quote", stripped.lstrip(">").strip()
        elif re.match(r"([-*+]|\d+[.)、])\s+", stripped):
            kind, body = "list", re.sub(r"^([-*+]|\d+[.)、])\s+", "", stripped)
        text = strip_inline(body)
        if kind == "p" and not text and images:
            kind = "image"
        if not text and kind not in ("image", "hr"):
            continue
        bold_line = bool(kind == "p" and text and re.fullmatch(r"\s*(\*\*|__).+(\*\*|__)\s*", body))
        blocks.append({"i": len(blocks), "kind": kind, "level": level, "text": text,
                       "images": images, "bold": bold, "bold_line": bold_line})
    return blocks


def units(s: str) -> int:
    return len(UNIT_RE.findall(s))


def split_sentences(text: str) -> list[str]:
    sentences, buf = [], ""
    for part in SENT_END.split(text):
        if not part:
            continue
        buf += part
        if SENT_END.fullmatch(part):
            if units(buf):
                sentences.append(buf.strip())
            buf = ""
    if units(buf):
        sentences.append(buf.strip())
    return sentences


def match_key(s: str) -> str:
    """Whitespace- and punctuation-free form used for quote matching and shingles."""
    return NON_KEY_RE.sub("", s).lower()


def key_hash(key: str) -> str:
    """Distributed packs match sign-off blocks by hash so they do not carry the creator's contact lines."""
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def key_with_map(s: str) -> tuple[str, list[int]]:
    chars, index = [], []
    for i, ch in enumerate(s):
        if NON_KEY_RE.fullmatch(ch):
            continue
        chars.append(ch.lower())
        index.append(i)
    return "".join(chars), index


TEXT_KINDS = ("p", "list", "quote", "heading")


def text_blocks(blocks: list[dict]) -> list[dict]:
    return [b for b in blocks if b["kind"] in TEXT_KINDS and b["text"]]


# ---------------------------------------------------------------- metrics

def quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return float(ordered[lo])
    return float(ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo))


def per1k(count: float, total: int) -> float:
    return round(count * 1000.0 / total, 3) if total else 0.0


def doc_metrics(md: str, title: str = "", skip_keys: set[str] | None = None) -> dict:
    """skip_keys: match_key() of repeated sign-off blocks, measured as brand slots instead."""
    meta, _ = strip_front_matter(md)
    title = title or meta.get("title", "")
    blocks = parse_markdown(md)
    if skip_keys:
        blocks = [b for b in blocks if not (b["text"] and (match_key(b["text"]) in skip_keys
                                                           or key_hash(match_key(b["text"])) in skip_keys))]
    tblocks = text_blocks(blocks)
    body = "\n".join(b["text"] for b in tblocks)
    total = units(body)
    paras = [b for b in tblocks if b["kind"] in ("p", "list", "quote")]
    para_units = [units(b["text"]) for b in paras]
    sentences = []
    one_sentence = 0
    for b in paras:
        ss = split_sentences(b["text"])
        sentences.extend(ss)
        if len(ss) == 1:
            one_sentence += 1
    sent_units = [units(s) for s in sentences] or [0]
    n_sent = max(len(sentences), 1)
    m: dict = {
        "units_total": total,
        "han_ratio": round(len(HAN_RE.findall(body)) / total, 3) if total else 0.0,
        "blocks": len(blocks),
        "paragraphs": len(paras),
        "para_units_median": quantile(para_units, 0.5),
        "para_units_p90": quantile(para_units, 0.9),
        "one_sentence_para_ratio": round(one_sentence / len(paras), 3) if paras else 0.0,
        "short_para_ratio": round(sum(1 for u in para_units if u <= 20) / len(paras), 3) if paras else 0.0,
        "sentences": len(sentences),
        "sent_units_median": quantile(sent_units, 0.5),
        "sent_units_p10": quantile(sent_units, 0.1),
        "sent_units_p90": quantile(sent_units, 0.9),
        "short_sent_ratio": round(sum(1 for u in sent_units if u <= 8) / n_sent, 3),
        "long_sent_ratio": round(sum(1 for u in sent_units if u >= 35) / n_sent, 3),
        "question_sent_ratio": round(sum(1 for s in sentences if re.search(r"[？?]", s[-3:])) / n_sent, 3),
        "exclaim_sent_ratio": round(sum(1 for s in sentences if re.search(r"[！!]", s[-3:])) / n_sent, 3),
    }
    for name, chars in PUNCT.items():
        if name == "dash":
            count = len(re.findall(r"—+", body))
        elif name == "ellipsis":
            count = len(re.findall(r"…+|\.{3,}", body))
        elif name == "dots":
            count = len(re.findall(r"。{2,}", body))
        else:
            count = sum(body.count(c) for c in chars)
        m[f"punct_{name}_per1k"] = per1k(count, total)
    wo, women = body.count("我"), body.count("我们")
    ni, nimen = body.count("你"), body.count("你们")
    m.update({
        "pron_wo_per1k": per1k(wo - women, total),
        "pron_women_per1k": per1k(women, total),
        "pron_ni_per1k": per1k(ni - nimen + body.count("您"), total),
        "pron_nimen_per1k": per1k(nimen, total),
        "pron_dajia_per1k": per1k(body.count("大家"), total),
        "pron_za_per1k": per1k(body.count("咱"), total),
        "latin_per1k": per1k(len(LATIN_RE.findall(body)), total),
        "digit_per1k": per1k(len(DIGIT_RE.findall(body)), total),
        "headings": sum(1 for b in blocks if b["kind"] == "heading"),
        "bold_lines": sum(1 for b in blocks if b["bold_line"]),
        "images": sum(b["images"] for b in blocks),
        "list_blocks": sum(1 for b in blocks if b["kind"] == "list"),
        "quote_blocks": sum(1 for b in blocks if b["kind"] == "quote"),
        "code_blocks": sum(1 for b in blocks if b["kind"] == "code"),
    })
    m["headings_per1k"] = per1k(m["headings"] + m["bold_lines"], total)
    m["bold_per1k"] = per1k(sum(b["bold"] for b in blocks), total)
    m["images_per1k"] = per1k(m["images"], total)
    m["list_block_ratio"] = round(m["list_blocks"] / len(paras), 3) if paras else 0.0
    m["markers_per1k"] = {k: per1k(body.count(k), total) for k in MARKERS}
    first = paras[0]["text"] if paras else ""
    last = paras[-1]["text"] if paras else ""
    first_sents = split_sentences(first)
    m.update({
        "title_units": units(title),
        "title_end": title[-1:] if title and not UNIT_RE.fullmatch(title[-1:]) else "",
        "title_has_digit": bool(re.search(r"\d", title)),
        "title_has_latin": bool(re.search(r"[A-Za-z]", title)),
        "title_has_question": bool(re.search(r"[？?]", title)),
        "title_has_exclaim": bool(re.search(r"[！!]", title)),
        "title_has_comma": bool(re.search(r"[，,]", title)),
        "title_has_colon_or_bar": bool(re.search(r"[：:｜|]", title)),
        "starts_with_image": bool(blocks and blocks[0]["kind"] == "image"),
        "first_para_units": units(first),
        "first_para_is_question": bool(first_sents and re.search(r"[？?]", first_sents[0][-3:])),
        "first_para_has_wo": "我" in first,
        "last_para_units": units(last),
        "last_para_addresses_reader": bool(re.search(r"你|大家|各位", last)),
        "last_para_end": last[-1:] if last and not UNIT_RE.fullmatch(last[-1:]) else "",
    })
    return m


def summarize(values: list) -> dict:
    if values and isinstance(values[0], bool):
        return {"n": len(values), "share": round(sum(1 for v in values if v) / len(values), 3)}
    if values and isinstance(values[0], (int, float)):
        nums = [float(v) for v in values]
        return {"n": len(nums), "min": min(nums), "p10": round(quantile(nums, 0.1), 3),
                "p25": round(quantile(nums, 0.25), 3), "median": round(quantile(nums, 0.5), 3),
                "p75": round(quantile(nums, 0.75), 3), "p90": round(quantile(nums, 0.9), 3),
                "max": max(nums)}
    counts = Counter(str(v) for v in values)
    return {"n": len(values), "counts": dict(counts.most_common())}


def distributions(per_doc: dict[str, dict]) -> dict:
    docs = list(per_doc.values())
    if not docs:
        return {}
    out: dict = {}
    for key in docs[0]:
        if key == "markers_per1k":
            out[key] = {mk: summarize([d[key][mk] for d in docs]) for mk in docs[0][key]}
        else:
            out[key] = summarize([d[key] for d in docs])
    return out


# ---------------------------------------------------------------- corpus-level signals

def han_runs(texts: list[str]) -> list[str]:
    runs = []
    for t in texts:
        runs.extend(HAN_RUN_RE.findall(t))
    return runs


def ngram_counts(runs: list[str], n: int) -> Counter:
    c: Counter = Counter()
    for r in runs:
        for i in range(len(r) - n + 1):
            c[r[i:i + n]] += 1
    return c


def signature_ngrams(train_docs: dict[str, list[str]], baseline_docs: list[list[str]] | None,
                     n_min: int = 2, n_max: int = 6, top: int = 60) -> dict:
    """Phrases recurring across many training articles; ranked against a baseline when given."""
    n_docs = len(train_docs)
    min_df = max(2, math.ceil(0.3 * n_docs))
    doc_runs = {sid: han_runs(texts) for sid, texts in train_docs.items()}
    total_units = sum(units("".join(t)) for t in train_docs.values()) or 1
    tf: Counter = Counter()
    df: Counter = Counter()
    per_doc_counts: dict[str, Counter] = {}
    for sid, runs in doc_runs.items():
        doc_counter: Counter = Counter()
        for n in range(n_min, n_max + 1):
            doc_counter.update(ngram_counts(runs, n))
        per_doc_counts[sid] = doc_counter
        tf.update(doc_counter)
        df.update(doc_counter.keys())
    candidates = [g for g, d in df.items() if d >= min_df and tf[g] >= 3]
    base_tf: Counter = Counter()
    base_units = 0
    if baseline_docs:
        cand = set(candidates)
        lengths = sorted({len(g) for g in cand})
        for texts in baseline_docs:
            base_units += units("".join(texts))
            for r in han_runs(texts):
                for n in lengths:
                    for i in range(len(r) - n + 1):
                        g = r[i:i + n]
                        if g in cand:
                            base_tf[g] += 1
    rows = []
    for g in candidates:
        rate = tf[g] * 1000.0 / total_units
        row = {"gram": g, "df": df[g], "tf": tf[g], "rate_per1k": round(rate, 3)}
        if baseline_docs and base_units:
            base_rate = (base_tf[g] + 0.5) * 1000.0 / base_units
            row["baseline_rate_per1k"] = round(base_tf[g] * 1000.0 / base_units, 3)
            row["ratio"] = round(rate / base_rate, 2)
        doc_rates = []
        for sid, texts in train_docs.items():
            u = units("".join(texts)) or 1
            doc_rates.append(per_doc_counts[sid][g] * 1000.0 / u)
        row["doc_rate_p90"] = round(quantile(doc_rates, 0.9), 3)
        row["doc_rate_max"] = round(max(doc_rates), 3)
        rows.append(row)

    def closed(sorted_rows: list[dict]) -> list[dict]:
        kept: list[dict] = []
        for row in sorted(sorted_rows, key=lambda r: -len(r["gram"])):
            if any(row["gram"] in k["gram"] and k["tf"] >= 0.8 * row["tf"] for k in kept):
                continue
            kept.append(row)
        return kept

    def shifted(a: str, b: str) -> bool:
        k = min(len(a), len(b)) - 1
        return k >= 2 and (a[-k:] == b[:k] or b[-k:] == a[:k])

    def pick(ranked: list[dict]) -> list[dict]:
        # A repeated long phrase yields a family of one-character-shifted n-grams; keep one per family.
        kept: list[dict] = []
        for row in ranked:
            if any(shifted(row["gram"], k["gram"]) and abs(row["tf"] - k["tf"]) <= 0.25 * max(row["tf"], k["tf"])
                   for k in kept):
                continue
            kept.append(row)
            if len(kept) >= top:
                break
        return kept

    frequent = pick(sorted(closed([r for r in rows if len(r["gram"]) >= 3]),
                           key=lambda r: (-r["df"], -r["tf"])))
    result = {"n_docs": n_docs, "min_df": min_df, "frequent": frequent}
    if baseline_docs:
        distinctive = pick(sorted(closed([r for r in rows if r.get("ratio", 0) >= 3]),
                                  key=lambda r: (-r["ratio"] * math.log(1 + r["df"]), -r["tf"])))
        result["distinctive"] = distinctive
        result["baseline_docs"] = len(baseline_docs)
    return result


def boilerplate(train_blocks: dict[str, list[dict]], head: int = 3, tail: int = 6) -> list[dict]:
    """Blocks repeated at the start or end of many articles: sign-offs, CTAs, column intros."""
    n_docs = len(train_blocks)
    seen: dict[tuple[str, str], dict] = {}
    for sid, blocks in train_blocks.items():
        tb = text_blocks(blocks)
        positions = [("head", b) for b in tb[:head]] + [("tail", b) for b in tb[-tail:]]
        local = set()
        for pos, b in positions:
            k = match_key(b["text"])
            if len(k) < 4 or (pos, k) in local:
                continue
            local.add((pos, k))
            item = seen.setdefault((pos, k), {"position": pos, "text": b["text"][:160], "key": k, "samples": []})
            item["samples"].append(sid)
    out = []
    for item in seen.values():
        df = len(item["samples"])
        if df >= 2 and df >= 0.2 * n_docs:
            out.append({**item, "df": df})
    return sorted(out, key=lambda r: (-r["df"], r["position"]))


def shingles(texts: list[str], k: int = SHINGLE_K) -> set[bytes]:
    out: set[bytes] = set()
    for t in texts:
        key = match_key(t)
        for i in range(len(key) - k + 1):
            out.add(hashlib.sha1(key[i:i + k].encode("utf-8")).digest()[:DIGEST_BYTES])
    return out


def encode_shingles(digests: set[bytes]) -> dict:
    blob = b"".join(sorted(digests))
    return {"schema": "blogger-cloner-shingles/v1", "k": SHINGLE_K, "digest_bytes": DIGEST_BYTES,
            "count": len(digests), "digests": base64.b64encode(blob).decode("ascii")}


def decode_shingles(doc: dict) -> set[bytes]:
    blob = base64.b64decode(doc["digests"])
    size = doc["digest_bytes"]
    return {blob[i:i + size] for i in range(0, len(blob), size)}


# ---------------------------------------------------------------- audit

def band_fit(metrics: dict, dist: dict) -> dict:
    checked, inside, out = 0, 0, []
    for key in FIT_KEYS:
        d = dist.get(key)
        if not d or "p10" not in d or d.get("n", 0) < 3:
            continue
        value = metrics.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        checked += 1
        lo, hi = d["p10"], d["p90"]
        tol = 1e-9 if hi > lo else max(0.05 * abs(hi), 1e-9)
        if lo - tol <= value <= hi + tol:
            inside += 1
        else:
            out.append({"metric": key, "value": value, "p10": lo, "median": d["median"], "p90": hi,
                        "direction": "below" if value < lo else "above"})
    return {"checked": checked, "in_band": inside,
            "ratio": round(inside / checked, 3) if checked else None, "out_of_band": out}


def overlap_runs(md: str, corpus: set[bytes], k: int, min_run: int) -> dict:
    runs = []
    longest = 0
    for b in text_blocks(parse_markdown(md)):
        key = match_key(b["text"])
        hits = [i for i in range(len(key) - k + 1)
                if hashlib.sha1(key[i:i + k].encode("utf-8")).digest()[:DIGEST_BYTES] in corpus]
        start = prev = None
        for i in hits + [None]:
            if i is not None and prev is not None and i == prev + 1:
                prev = i
                continue
            if start is not None:
                length = prev - start + k
                longest = max(longest, length)
                if length >= min_run:
                    runs.append({"block": b["i"], "chars": length, "text": key[start:prev + k]})
            start = prev = i
    return {"k": k, "min_run": min_run, "longest": longest, "runs": runs}


def audit(pack: Path, draft: Path, title: str = "", allow_identity: bool = False, min_run: int = 20) -> dict:
    metrics_doc = json.loads((pack / "metrics.train.json").read_text(encoding="utf-8"))
    shingle_doc = json.loads((pack / "corpus-shingles.json").read_text(encoding="utf-8"))
    brand = json.loads((pack / "brand.json").read_text(encoding="utf-8"))
    md = draft.read_text(encoding="utf-8")
    skip = {r.get("key") or r.get("key_sha1") for r in metrics_doc.get("boilerplate", [])} - {None}
    m = doc_metrics(md, title, skip)
    fit = band_fit(m, metrics_doc["distributions"])
    overlap = overlap_runs(md, decode_shingles(shingle_doc), shingle_doc["k"], min_run)
    body = "\n".join(b["text"] for b in text_blocks(parse_markdown(md)))
    lowered = (title + "\n" + body).lower()
    identity_hits = sorted({t for t in brand.get("identity_tokens", []) if t and t.lower() in lowered})
    total = units(body) or 1
    overuse = []
    sig = metrics_doc.get("signature_ngrams", {})
    for row in (sig.get("distinctive") or sig.get("frequent") or [])[:40]:
        count = body.count(row["gram"])
        rate = count * 1000.0 / total
        ceiling = max(row["doc_rate_max"], row["doc_rate_p90"]) * 1.5
        if count >= 3 and rate > ceiling:
            overuse.append({"gram": row["gram"], "count": count, "rate_per1k": round(rate, 3),
                            "train_doc_rate_max": row["doc_rate_max"]})
    problems, warnings = [], []
    if overlap["runs"]:
        problems.append(f"{len(overlap['runs'])} passage(s) of {min_run}+ characters match the source corpus")
    if identity_hits and not allow_identity:
        problems.append("draft names the cloned creator or their brand: " + ", ".join(identity_hits))
    if fit["ratio"] is not None and fit["ratio"] < 0.6:
        warnings.append(f"only {fit['in_band']}/{fit['checked']} style metrics inside the training P10-P90 band")
    if overuse:
        warnings.append("signature phrases above the densest training article: "
                        + ", ".join(o["gram"] for o in overuse))
    status = "fail" if problems else ("warn" if warnings else "pass")
    return {"schema": AUDIT_SCHEMA, "draft": str(draft), "status": status, "problems": problems,
            "warnings": warnings, "band_fit": fit, "overlap": overlap, "identity_hits": identity_hits,
            "overuse": overuse, "metrics": m,
            "note": "Band fit compares surface metrics with the training range; it is not a quality or authorship score."}


# ---------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_m = sub.add_parser("metrics", help="print surface metrics for one Markdown article")
    p_m.add_argument("article", type=Path)
    p_m.add_argument("--title", default="")
    p_a = sub.add_parser("audit", help="check a draft against a frozen style pack")
    p_a.add_argument("--pack", type=Path, required=True)
    p_a.add_argument("--draft", type=Path, required=True)
    p_a.add_argument("--title", default="")
    p_a.add_argument("--min-run", type=int, default=20)
    p_a.add_argument("--allow-identity", action="store_true",
                     help="only for analysis notes that must name the creator")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "metrics":
            result = {"ok": True, "schema": METRICS_SCHEMA,
                      "metrics": doc_metrics(args.article.read_text(encoding="utf-8"), args.title)}
            code = 0
        else:
            for name in ("metrics.train.json", "corpus-shingles.json", "brand.json"):
                if not (args.pack / name).is_file():
                    raise FileNotFoundError(f"style pack is missing {name}: {args.pack}")
            report = audit(args.pack, args.draft, args.title, args.allow_identity, args.min_run)
            result = {"ok": report["status"] != "fail", **report}
            code = 0 if report["status"] != "fail" else 2
    except (OSError, ValueError, KeyError) as exc:
        result, code = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}, 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
