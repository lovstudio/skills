#!/usr/bin/env python3
"""The shared media end of every video Skill: one command to build the brand outro, one to put its sound in a mix.

usage:
  media_end.py make --out work/sting [--fps 30] [--beats 0,18,...] [--dur N] [--profile PATH]
  media_end.py mix  --mix in.m4a|wav --sting work/sting/sting.wav --at-frame N --fps 30 --out out.m4a|wav
                    [--gain 0.40] [--target -16] [--tp -3.0] [--lufs-tol 0.5]

`make` reads the shared Profile record `preferences.video_outro` (official SVG, its sha256, accent/hot/final colours,
fps, bpm, intro, sting gain, true-peak ceiling), refuses an SVG whose sha256 differs from the record, then runs
logo_spec.py, sting_timing.py and sting_audio.py into --out and writes outro.json: the frame count, fps, intro and mix
settings a host needs. --fps overrides the record when the host film runs at another rate; --beats/--dur follow the
host's music grid (see sting_timing.py). Same inputs give byte-identical spec.json, timing.json and sting.wav.

`mix` sums sting.wav sample-exact at --at-frame (round(frame / fps * 48000) samples) into a finished mix at --gain,
limits, sets one static gain so the whole film meets --target LUFS-I, encodes (.m4a = AAC 256k, .wav = PCM 24-bit),
re-measures the encoded file and lowers the limiter until the true peak is at or below --tp. Fade or stop the music
at the outro start before calling it (no music under the outro); hosts with their own pre-master mixer may sum the
sting there instead and only use `make`. Exit 1 when the encoded file misses the loudness or peak target.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROFILE = Path(os.environ.get("LOVSTUDIO_PROFILE", Path.home() / ".lovstudio/skills/profile.json"))
SR = 48000


def expand(p):
    return Path(os.path.expandvars(os.path.expanduser(str(p))))


def load_outro(profile):
    try:
        data = json.loads(Path(profile).read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"media_end: no profile at {profile}; record preferences.video_outro first (see SKILL.md)")
    rec = (data.get("preferences") or {}).get("video_outro")
    if not isinstance(rec, dict) or not rec.get("svg"):
        sys.exit("media_end: preferences.video_outro is missing or has no svg; record it first (see SKILL.md)")
    return rec


def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"media_end: {Path(args[1]).name} failed\n{r.stderr or r.stdout}")
    return r.stdout


def cmd_make(a):
    rec = load_outro(a.profile)
    svg = expand(rec["svg"])
    if not svg.is_file():
        sys.exit(f"media_end: official SVG not found: {svg}")
    sha = hashlib.sha256(svg.read_bytes()).hexdigest()
    if rec.get("svg_sha256") and sha != rec["svg_sha256"]:
        sys.exit(f"media_end: {svg.name} sha256 {sha} differs from the recorded {rec['svg_sha256']}; "
                 "use the official file or update the record with the author")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    fps = a.fps or int(rec.get("fps", 30))
    spec = [sys.executable, str(HERE / "logo_spec.py"), "--svg", str(svg), "--out", str(out / "spec.json"),
            "--preview", str(out / "spec-preview.svg")]
    for k in ("accent", "hot", "final"):
        if rec.get(k):
            spec += [f"--{k}", rec[k]]
    run(spec)
    timing = [sys.executable, str(HERE / "sting_timing.py"), "--spec", str(out / "spec.json"), "--fps", str(fps),
              "--out", str(out / "timing.json")]
    if a.beats:
        timing += ["--beats", a.beats]
        if a.dur:
            timing += ["--dur", str(a.dur)]
    else:
        timing += ["--bpm", str(rec.get("bpm", 100))]
    run(timing)
    run([sys.executable, str(HERE / "sting_audio.py"), "--timing", str(out / "timing.json"), "--out", str(out / "sting.wav")])
    t = json.loads((out / "timing.json").read_text())
    info = {
        "schema": "media-end/v1", "style": rec.get("style", "lov-logo-sting"), "brand": rec.get("brand"),
        "svg": str(svg), "svg_sha256": sha, "fps": t["fps"], "frames": t["dur"], "seconds": round(t["dur"] / t["fps"], 3),
        "intro": rec.get("intro", "black"), "sting_gain": rec.get("sting_gain", 0.40),
        "true_peak_ceiling_dbtp": rec.get("true_peak_ceiling_dbtp", -3.0),
        "files": {"spec": "spec.json", "timing": "timing.json", "sting": "sting.wav", "preview": "spec-preview.svg"},
    }
    (out / "outro.json").write_text(json.dumps(info, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(info, ensure_ascii=False))


def measure(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    tail = r.stderr[r.stderr.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", tail)
    tp = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", tail)
    return (float(i.group(1)) if i else None), (float(tp.group(1)) if tp and tp.group(1) != "-inf" else -99.0)


def cmd_mix(a):
    import numpy as np  # only the mix step needs numpy

    def decode(p):
        raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"])
        return np.frombuffer(raw, dtype="<f4").reshape(-1, 2).astype(np.float64)

    mix, sting = decode(a.mix), decode(a.sting)
    at = int(round(a.at_frame / a.fps * SR))
    end = at + len(sting)
    if end > len(mix):
        mix = np.concatenate([mix, np.zeros((end - len(mix), 2))])
    mix[at:end] += a.gain * sting
    out = Path(a.out)
    with tempfile.TemporaryDirectory() as tmp:
        summed = Path(tmp) / "summed.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f64le", "-ar", str(SR), "-ac", "2", "-i", "-",
                        "-c:a", "pcm_f32le", str(summed)], input=mix.astype("<f8").tobytes(), check=True)
        i0, _ = measure(summed)
        gain_db = a.target - i0
        limit_db = a.tp - 0.5
        codec = ["-c:a", "aac", "-b:a", "256k"] if out.suffix.lower() in (".m4a", ".aac", ".mp4") else ["-c:a", "pcm_s24le"]
        for _ in range(6):
            lim = 10 ** (limit_db / 20)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(summed), "-af",
                            f"volume={gain_db:.3f}dB,alimiter=limit={lim:.5f}:level=disabled:attack=1:release=50",
                            "-ar", str(SR), *codec, str(out)], check=True)
            i1, tp1 = measure(out)
            if tp1 <= a.tp:
                break
            limit_db -= (tp1 - a.tp) + 0.2
    ok = i1 is not None and abs(i1 - a.target) <= a.lufs_tol and tp1 <= a.tp
    print(json.dumps({"out": str(out), "at_frame": a.at_frame, "at_seconds": round(at / SR, 3), "sting_gain": a.gain,
                      "lufs_i": i1, "true_peak_dbtp": tp1, "limiter_dbfs": round(limit_db, 2), "ok": ok}, ensure_ascii=False))
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make", help="build spec.json, timing.json, sting.wav and outro.json from preferences.video_outro")
    m.add_argument("--out", required=True)
    m.add_argument("--fps", type=int, help="host film fps (default: the record, else 30)")
    m.add_argument("--beats", help="host music beat grid in local frames, first = 0 (see sting_timing.py)")
    m.add_argument("--dur", type=int, help="total frames when --beats is given")
    m.add_argument("--profile", default=str(PROFILE))
    x = sub.add_parser("mix", help="sum sting.wav into a finished mix at a frame and re-master")
    x.add_argument("--mix", required=True)
    x.add_argument("--sting", required=True)
    x.add_argument("--at-frame", type=int, required=True)
    x.add_argument("--fps", type=float, required=True)
    x.add_argument("--out", required=True)
    x.add_argument("--gain", type=float, default=0.40)
    x.add_argument("--target", type=float, default=-16.0)
    x.add_argument("--tp", type=float, default=-3.0)
    x.add_argument("--lufs-tol", type=float, default=0.5)
    a = ap.parse_args()
    cmd_make(a) if a.cmd == "make" else cmd_mix(a)


if __name__ == "__main__":
    main()
