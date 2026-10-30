#!/usr/bin/env python3
"""Synthesize a stand-in narration take for an animatic or an aligner test (Doubao Seed-TTS 2.0).

usage: tts.py work/script.json --out recording/tts-take.wav [--speaker ID] [--rate 25] [--gap 0.22]
              [--lead 3.0] [--simulate-retakes L03,L07] [--ledger ledger/costs.jsonl] [--dry-run]

The animatic lets the author judge pacing, shots and packaging before recording; it is never the film.
--simulate-retakes inserts, before each listed line, a broken first attempt (its first ~45% plus a
filler) so align.py's "last good take" choice can be regression-tested; the ground truth goes to
<out>.json. --lead adds silence where the author would hold the cover pose.
Per-line audio is cached by text+speaker+rate under <out dir>/tts/. Needs VOICENGINE_API_KEY (env only,
never printed); every request is one line in the ledger (characters; the provider bills per character).
"""
import argparse
import base64
import datetime
import hashlib
import json
import os
import subprocess
import tempfile
import urllib.request
import uuid
from pathlib import Path

URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
SR = 48000


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
    spoken = sum(len(j[2]) for j in jobs if j[0] == "take")
    take_time = sum(x["to"] - x["from"] for x in truth if x["kind"] == "take")
    print(json.dumps({"out": str(out), "seconds": round(t + 1.0, 2), "requests": len(need), "chars_billed": chars,
                      "chars_per_second": round(spoken / take_time, 2) if take_time else None}, ensure_ascii=False))


if __name__ == "__main__":
    main()
