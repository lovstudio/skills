#!/usr/bin/env python3
"""Align the author's one-take recording to script.json: pick the last good take of every line, trim pauses.

usage: align.py work/script.json recording/take.mov --out work/takes.json
                [--model turbo|large-v3|<hf repo or dir>] [--max-gap 0.32] [--min-score 0.6] [--asr-cache work/asr]

The author reads the whole script in one take and simply re-reads a line after a slip (teleprompter
checklist). This script:
1. transcribes with mlx-whisper (word timestamps; prompt = the script's own nouns), cached per file+model;
2. scores every transcript window against every line (difflib ratio on normalized simplified chars);
3. chooses one window per line by monotonic dynamic programming, preferring the later of two good takes
   (a re-read follows the slip), and flags lines below --min-score as `low` or not found as `missing`;
4. moves each in/out point to the nearest quiet frame of the audio envelope (ASR word edges drift), and
   cuts silences longer than --max-gap inside a take down to that gap (the jump-cut rhythm of the genre).
Output takes.json: per line `spans` in source seconds, `score`, `status`, `heard` (ASR text of the take)
and `chars` (normalized char → source time) for caption timing; plus `discarded` re-read windows.
Run with the persistent venv Python that has mlx-whisper (and opencc for traditional → simplified).
"""
import argparse
import difflib
import hashlib
import json
import re
import subprocess
from pathlib import Path

import numpy as np

MODELS = {"turbo": "mlx-community/whisper-large-v3-turbo", "large-v3": "mlx-community/whisper-large-v3-mlx"}
PUNCT = re.compile(r"[\s，。！？、：；“”‘’（）《》【】,.!?:;\"'()\[\]<>…—\-~·]")
try:
    import opencc
    _T2S = opencc.OpenCC("t2s")
except Exception:  # opencc is optional; Whisper with a simplified prompt mostly answers in simplified
    _T2S = None


def norm(text: str) -> str:
    t = _T2S.convert(text) if _T2S else text
    t = t.translate({ord(c): ord(c) - 0xFEE0 for c in "０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"})
    return PUNCT.sub("", t).lower()


def transcribe(media: Path, model: str, prompt: str, cache_dir: Path):
    st = media.stat()
    key = hashlib.sha1(f"{media.resolve()}|{st.st_size}|{st.st_mtime}|{model}|{prompt}".encode()).hexdigest()[:12]
    cache = cache_dir / f"{media.stem}.{key}.words.json"
    if cache.exists():
        return json.loads(cache.read_text())
    import mlx_whisper
    r = mlx_whisper.transcribe(str(media), path_or_hf_repo=MODELS.get(model, model), language="zh",
                               word_timestamps=True, initial_prompt=prompt, condition_on_previous_text=False)
    words = [{"w": w["word"], "s": round(w["start"], 3), "e": round(w["end"], 3)}
             for seg in r["segments"] for w in seg.get("words", [])]
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(words, ensure_ascii=False))
    return words


def char_times(words):
    """Spread each word's time evenly over its normalized characters."""
    chars, starts = [], []
    for w in words:
        n = norm(w["w"])
        if not n:
            continue
        starts.append(len(chars))
        d = (w["e"] - w["s"]) / len(n)
        for k, c in enumerate(n):
            chars.append((c, w["s"] + d * k, w["s"] + d * (k + 1)))
    return chars, starts


def envelope(media: Path, hop=0.01):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(media), "-vn", "-ac", "1", "-ar", "16000",
                                   "-f", "f32le", "-"])
    a = np.frombuffer(raw, np.float32)
    n = int(16000 * hop)
    frames = a[: len(a) // n * n].reshape(-1, n)
    db = 20 * np.log10(np.sqrt((frames ** 2).mean(1)) + 1e-9)
    floor = float(np.percentile(db, 8))
    return db, floor, hop


def candidates(line: str, T: str, starts, min_score: float, keep=6):
    m = len(line)
    if m == 0:
        return []
    lens = sorted({max(1, int(m * f)) for f in (0.75, 0.85, 0.95, 1.0, 1.1, 1.2, 1.3)})
    found = []
    sm = difflib.SequenceMatcher(autojunk=False)
    sm.set_seq2(line)
    for j in starts:
        best = None
        for L in lens:
            seg = T[j:j + L]
            if len(seg) < m * 0.6:
                break
            sm.set_seq1(seg)
            if sm.real_quick_ratio() < min_score or sm.quick_ratio() < min_score:
                continue
            r = sm.ratio()
            if r >= min_score and (best is None or r > best[2]):
                best = (j, j + L, r)
        if best:
            found.append(best)
    found.sort(key=lambda c: -c[2])
    picked = []
    for c in found:  # non-maximum suppression: distinct takes only
        if all(c[1] <= p[0] or c[0] >= p[1] for p in picked):
            picked.append(c)
        if len(picked) == keep:
            break
    return sorted(picked)


def trim_window(line, T, a, b):
    """Shrink a window to its first and last matched character."""
    blocks = [bl for bl in difflib.SequenceMatcher(None, T[a:b], line, autojunk=False).get_matching_blocks() if bl.size]
    if not blocks:
        return a, b
    return a + blocks[0].a, a + blocks[-1].a + blocks[-1].size


def choose(lines_n, cands, later_bonus=0.06):
    """Monotonic DP over candidate takes; a later good take beats an earlier one (re-read after a slip)."""
    n = len(lines_n)
    # state per line: list of (total, prev_index, cand) ; cand None = line skipped
    layers = []
    prev = [(0.0, None, None, -1)]  # (score, back, cand, end_char)
    for i in range(n):
        cur = []
        opts = [None] + list(enumerate(cands[i]))
        for opt in opts:
            best = None
            for pi, (ps, _, _, pend) in enumerate(prev):
                if opt is None:
                    sc, end = ps, pend
                else:
                    k, (a, b, r) = opt
                    if a < pend - 1:
                        continue
                    sc, end = ps + r + later_bonus * k, b
                if best is None or sc > best[0]:
                    best = (sc, pi, None if opt is None else opt[1], end)
            if best:
                cur.append(best)
        layers.append(cur)
        prev = cur
    # backtrack
    idx = max(range(len(prev)), key=lambda k: prev[k][0])
    chosen = [None] * n
    for i in range(n - 1, -1, -1):
        sc, back, cand, _ = layers[i][idx]
        chosen[i] = cand
        idx = back
    return chosen


def quiet(db, floor, hop, t, direction, limit, margin=7.0):
    """First frame quieter than floor+margin searching from t in direction (−1/+1) within limit seconds."""
    i = int(t / hop)
    for k in range(int(limit / hop)):
        j = i + direction * k
        if j < 0 or j >= len(db):
            break
        if db[j] < floor + margin:
            return j * hop
    return None


def longest_gap(db, floor, hop, t0, t1, margin=7.0, min_len=0.06):
    """Longest silent run inside [t0, t1] (the pause between a slip and its re-read, or between lines)."""
    i0, i1 = max(0, int(t0 / hop)), min(len(db), int(t1 / hop))
    best, k = None, i0
    while k < i1:
        if db[k] < floor + margin:
            r = k
            while r < i1 and db[r] < floor + margin:
                r += 1
            if (r - k) * hop >= min_len and (best is None or r - k > best[1] - best[0]):
                best = (k, r)
            k = r
        else:
            k += 1
    return None if best is None else (best[0] * hop, best[1] * hop)


def inner_spans(db, floor, hop, t0, t1, max_gap, margin=7.0, keep=0.12):
    """Split [t0, t1] where the voice is silent longer than max_gap, keeping `keep` seconds on each side."""
    i0, i1 = int(t0 / hop), int(t1 / hop)
    silent = db[i0:i1] < floor + margin
    spans, start, k = [], t0, 0
    while k < len(silent):
        if silent[k]:
            r = k
            while r < len(silent) and silent[r]:
                r += 1
            gs, ge = t0 + k * hop, t0 + r * hop
            if ge - gs > max_gap and gs > t0 + 0.05 and ge < t1 - 0.05:
                spans.append([round(start, 3), round(gs + keep, 3)])
                start = ge - keep
            k = r
        else:
            k += 1
    spans.append([round(start, 3), round(t1, 3)])
    return [s for s in spans if s[1] - s[0] > 0.08]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("script")
    ap.add_argument("recording")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="turbo")
    ap.add_argument("--max-gap", type=float, default=0.32)
    ap.add_argument("--min-score", type=float, default=0.6)
    ap.add_argument("--asr-cache", help="cache directory (default: <out dir>/asr)")
    ap.add_argument("--words", help="word timestamps from another ASR (JSON list of {w, s, e} in seconds); skips Whisper")
    a = ap.parse_args()

    s = json.loads(Path(a.script).read_text())
    rec = Path(a.recording)
    out = Path(a.out)
    nouns = sorted({w for ln in s["lines"] for w in ln.get("emphasis") or [] if re.search(r"[A-Za-z]", w)})
    prompt = "以下是普通话口播，简体中文。" + ("专有名词：" + "、".join(nouns) + "。" if nouns else "")
    if a.words:
        words = json.loads(Path(a.words).read_text())
    else:
        words = transcribe(rec, a.model, prompt, Path(a.asr_cache) if a.asr_cache else out.parent / "asr")
    chars, starts = char_times(words)
    T = "".join(c for c, _, _ in chars)
    lines_n = [norm(ln["text"]) for ln in s["lines"]]
    cands = [candidates(ln, T, starts, a.min_score * 0.85) for ln in lines_n]
    chosen = choose(lines_n, cands)
    db, floor, hop = envelope(rec)
    dur = len(db) * hop

    result, discarded, prev_out = [], [], 0.0
    for i, ln in enumerate(s["lines"]):
        c = chosen[i]
        for other in cands[i]:
            if c is None or other[:2] != c[:2]:
                discarded.append({"id": ln["id"], "from": round(chars[other[0]][1], 2),
                                  "to": round(chars[min(other[1], len(chars)) - 1][2], 2), "score": round(other[2], 2)})
        if c is None:
            result.append({"id": ln["id"], "status": "missing", "score": 0, "spans": [], "heard": "", "chars": []})
            continue
        a0, b0 = trim_window(lines_n[i], T, c[0], c[1])
        # ASR word edges drift by a few hundred ms: cut inside the longest pause between whatever was said
        # before this take (a slip, the previous line) and its first word, and likewise after its last word
        before = chars[a0 - 1][2] if a0 > 0 else 0.0
        g = longest_gap(db, floor, hop, max(prev_out, before - 0.3), chars[a0][1] + 0.5)
        if g:
            t_in = max(prev_out, g[1] - 0.06)
        else:
            t_in = max(prev_out, chars[a0][1] - 0.05)
            q = quiet(db, floor, hop, t_in, -1, 0.22)
            if q is not None and q >= prev_out:
                t_in = q
        after = chars[b0][1] if b0 < len(chars) else dur
        g = longest_gap(db, floor, hop, chars[b0 - 1][2] - 0.3, min(dur, after + 0.3))
        if g:
            t_out = min(dur, g[0] + 0.08)
        else:
            t_out = min(dur, chars[b0 - 1][2] + 0.08)
            q = quiet(db, floor, hop, t_out, +1, 0.35)
            t_out = min(dur, (q + 0.05) if q is not None else t_out + 0.1)
        spans = inner_spans(db, floor, hop, t_in, t_out, a.max_gap)
        prev_out = t_out
        result.append({"id": ln["id"], "status": "ok" if c[2] >= a.min_score else "low", "score": round(c[2], 3),
                       "spans": spans, "heard": T[a0:b0],
                       "chars": [[ch, round(t0, 3), round(t1, 3)] for ch, t0, t1 in chars[a0:b0]]})

    kept = sum(sp[1] - sp[0] for r in result for sp in r["spans"])
    report = {"schema": "talking-head-takes/v1", "recording": str(rec), "asr": a.words or a.model, "source_seconds": round(dur, 2),
              "kept_seconds": round(kept, 2), "noise_floor_db": round(floor, 1), "max_gap": a.max_gap,
              "lines": result, "discarded": discarded,
              "review": [r["id"] for r in result if r["status"] != "ok"]}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1))
    for r in result:
        span = f"{r['spans'][0][0]:7.2f}-{r['spans'][-1][1]:7.2f}" if r["spans"] else "      —       "
        print(f"{r['id']:>5} {r['status']:<7} {r['score']:.2f} {span} {len(r['spans'])}段  {r['heard'][:30]}")
    print(f"kept {kept:.1f}s of {dur:.1f}s; discarded takes {len(discarded)}; review {report['review'] or 'none'}")


if __name__ == "__main__":
    main()
