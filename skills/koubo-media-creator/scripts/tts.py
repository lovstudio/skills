#!/usr/bin/env python3
"""Synthesize a stand-in narration take for an animatic or an aligner test (Doubao Seed-TTS 2.0).

usage: tts.py work/script.json --out recording/tts-take.wav [--speaker ID] [--rate 25] [--gap 0.22]
              [--lead 3.0] [--simulate-retakes L03,L07] [--ledger ledger/costs.jsonl] [--dry-run]

The animatic lets the author judge pacing, shots and packaging before recording; it is never the film.
--simulate-retakes inserts, before each listed line, a broken first attempt (its first ~45% plus a
filler) so align.py's "last good take" choice can be regression-tested; the ground truth goes to
<out>.json. --lead adds silence where the author would hold the cover pose.
The same truth is also written as <out>.words.json, the `[{w, s, e}]` input of `align.py --words`: one
entry per phrase (split at punctuation) inside the line's known window, each break snapped to a pause near
where the phrase weights put it, so an animatic is aligned without any ASR (every line scores 1.00, cuts
land on the real line edges).
Per-line audio is cached by text+speaker+rate under <out dir>/tts/; a rerun with the same arguments costs
nothing and rebuilds the take and both JSON files. Needs VOICENGINE_API_KEY (env only, never printed);
every request is one line in the ledger (characters; the provider bills per character).
"""
import argparse
import array
import base64
import datetime
import hashlib
import json
import math
import operator
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import uuid
from pathlib import Path

URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
SR = 48000
HOP = 0.01
PHRASE = re.compile(r"[，。！？、：；,.!?:;…]+")


def synth(text, speaker, rate):
    body = json.dumps({"user": {"uid": "talking-head"}, "req_params": {
        "text": text, "speaker": speaker,
        "audio_params": {"format": "mp3", "sample_rate": 24000, "speech_rate": rate}}}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "X-Api-Key": os.environ["VOICENGINE_API_KEY"], "X-Api-Resource-Id": "seed-tts-2.0",
        "X-Api-Request-Id": str(uuid.uuid4()), "Content-Type": "application/json"})
    raw = urllib.request.urlopen(req, timeout=120).read().decode()
    audio = b""
    for line in raw.splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if d.get("code") not in (0, 20000000, None):
            raise RuntimeError(line[:200])
        if d.get("data"):
            audio += base64.b64decode(d["data"])
    if not audio:
        raise RuntimeError("empty audio: " + raw[:200])
    return audio


def to_pcm(mp3: bytes) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".mp3") as f:
        f.write(mp3)
        f.flush()
        return subprocess.check_output(["ffmpeg", "-v", "error", "-i", f.name, "-af",
                                        "silenceremove=start_periods=1:start_threshold=-45dB:stop_periods=-1:stop_threshold=-45dB:stop_duration=0.15",
                                        "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"])


def envelope_db(media: Path):
    """10 ms RMS envelope (dBFS) of the take at 16 kHz, the same envelope align.py cuts on
    (at 48 kHz the fricatives' high band changes which of the short TTS pauses read as quiet)."""
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(media), "-ac", "1", "-ar", "16000",
                                   "-f", "f32le", "-"])
    x = array.array("f", raw)
    if sys.byteorder == "big":
        x.byteswap()
    n = int(16000 * HOP)
    return [20 * math.log10(math.sqrt(sum(map(operator.mul, f, f)) / n) + 1e-9)
            for f in (x[i:i + n] for i in range(0, len(x) - n + 1, n))]


def percentile(v, q):
    s = sorted(v)
    k = (len(s) - 1) * q / 100
    f = int(k)
    return s[f] + (s[min(f + 1, len(s) - 1)] - s[f]) * (k - f)


def quiet_runs(db, lo, hi, thr, min_len=6):
    runs, start = [], None
    for i in range(lo, hi):
        if db[i] < thr:
            if start is None:
                start = i
        elif start is not None:
            if i - start >= min_len:
                runs.append((start, i))
            start = None
    return runs


def weight(phrase):
    """Speaking weight of a phrase: a CJK character 1, a Latin letter or digit 0.5."""
    return sum(0.5 if ord(c) < 256 else 1.0 for c in phrase if not c.isspace()) or 1.0


def truth_words(db, truth):
    """Phrase-level `[{w, s, e}]` inside each known line window.

    Each break is expected where the phrase weights put it and snaps to the quiet run (≥ 60 ms) whose
    centre lies within max(0.3 s, 12% of the line) of that point, scored length × (1 − distance/window);
    with none in reach it stays at the expected point, and it never lands before the previous break.
    The line's longest pauses are not its breaks: Seed-TTS often pauses longer before or after a Latin
    word, or on a stressed word, than at a comma (sometimes 30 ms there).
    """
    # the take is padded with digital silence between lines; keep it out of the noise floor
    thr = percentile([v for v in db if v > -120], 20) + 6
    words = []
    for t in truth:
        phrases = [p for p in PHRASE.split(t["text"]) if p.strip()]
        lo, hi = int(t["from"] / HOP), int(t["to"] / HOP)
        runs = quiet_runs(db, lo + 5, hi - 5, thr) if len(phrases) > 1 else []
        wts = [weight(p) for p in phrases]
        span = t["to"] - t["from"]
        win = max(0.3, 0.12 * span)
        bounds, acc, prev = [], 0.0, t["from"]
        for w in wts[:-1]:
            acc += w
            exp = t["from"] + span * acc / sum(wts)
            dist = {r: abs((r[0] + r[1]) / 2 * HOP - exp) for r in runs if r[0] * HOP >= prev}
            near = [r for r in dist if dist[r] <= win]
            if near:
                r = max(near, key=lambda r: (r[1] - r[0]) * (1 - dist[r] / win))
                q = (r[0] * HOP, r[1] * HOP)
            else:
                q = (max(exp, prev), max(exp, prev))
            bounds.append(q)
            prev = q[1]
        s = t["from"]
        for p, (q0, q1) in zip(phrases, bounds + [(t["to"], t["to"])]):
            words.append({"w": p, "s": round(s, 3), "e": round(q0, 3)})
            s = q1
    return words


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("script")
    ap.add_argument("--out", required=True)
    ap.add_argument("--speaker", default="zh_male_jieshuoxiaoming_uranus_bigtts")
    ap.add_argument("--rate", type=int, default=25, help="Seed-TTS speech_rate (-50..100)")
    ap.add_argument("--gap", type=float, default=0.22)
    ap.add_argument("--lead", type=float, default=3.0)
    ap.add_argument("--simulate-retakes", default="")
    ap.add_argument("--ledger")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    s = json.loads(Path(a.script).read_text())
    out = Path(a.out)
    cache = out.parent / "tts"
    cache.mkdir(parents=True, exist_ok=True)
    retakes = {x.strip() for x in a.simulate_retakes.split(",") if x.strip()}

    jobs = []  # (kind, line id, text)
    for ln in s["lines"]:
        if ln["id"] in retakes:
            t = ln["text"]
            jobs.append(("slip", ln["id"], t[: max(3, int(len(t) * 0.45))] + "……呃，重来。"))
        jobs.append(("take", ln["id"], ln["text"]))

    def key(text):
        return hashlib.sha1(f"{a.speaker}|{a.rate}|{text}".encode()).hexdigest()[:12]

    need = [j for j in jobs if not (cache / f"{key(j[2])}.pcm").exists()]
    chars = sum(len(j[2]) for j in need)
    if a.dry_run:
        print(json.dumps({"requests": len(need), "chars": chars, "cached": len(jobs) - len(need)}, ensure_ascii=False))
        return
    if need and not os.environ.get("VOICENGINE_API_KEY"):
        raise SystemExit(f"{len(need)} requests need VOICENGINE_API_KEY")
    for kind, lid, text in need:
        ok = False
        try:
            (cache / f"{key(text)}.pcm").write_bytes(to_pcm(synth(text, a.speaker, a.rate)))
            ok = True
        finally:
            if a.ledger:
                Path(a.ledger).parent.mkdir(parents=True, exist_ok=True)
                with open(a.ledger, "a") as f:
                    f.write(json.dumps({"time": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                                        "service": "volcengine", "model": "seed-tts-2.0", "item": f"{lid}:{kind}",
                                        "qty": len(text), "unit": "chars", "cost_cny": None, "ok": ok},
                                       ensure_ascii=False) + "\n")

    pcm, truth, t = bytearray(b"\0\0" * int(SR * a.lead)), [], a.lead
    for kind, lid, text in jobs:
        clip = (cache / f"{key(text)}.pcm").read_bytes()
        d = len(clip) / 2 / SR
        truth.append({"id": lid, "kind": kind, "from": round(t, 3), "to": round(t + d, 3), "text": text})
        pcm += clip + b"\0\0" * int(SR * a.gap)
        t += d + a.gap
    pcm += b"\0\0" * int(SR * 1.0)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", str(out)],
                   input=bytes(pcm), check=True)
    out.with_suffix(".json").write_text(json.dumps({"speaker": a.speaker, "rate": a.rate, "lead": a.lead, "takes": truth},
                                                   ensure_ascii=False, indent=1))
    words = truth_words(envelope_db(out), truth)
    words_path = out.with_suffix(".words.json")
    words_path.write_text(json.dumps(words, ensure_ascii=False, indent=0))
    spoken = sum(len(j[2]) for j in jobs if j[0] == "take")
    take_time = sum(x["to"] - x["from"] for x in truth if x["kind"] == "take")
    print(json.dumps({"out": str(out), "words": str(words_path), "phrases": len(words), "seconds": round(t + 1.0, 2),
                      "requests": len(need), "chars_billed": chars,
                      "chars_per_second": round(spoken / take_time, 2) if take_time else None}, ensure_ascii=False))


if __name__ == "__main__":
    main()
