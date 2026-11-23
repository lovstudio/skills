#!/usr/bin/env python3
"""Compare a rebuilt render with the original master during a handover acceptance run (needs ffmpeg and ffprobe).

  python3 media_compare.py <original> <rebuilt> [--json out.json] [--min-psnr 40]

Checks duration and streams, decodes both audio tracks and compares their MD5 (bit-identical sound), and computes the
PSNR of every video frame: identical frames, the minimum, the mean and the five worst frames. A re-encode of the same
render rarely matches byte for byte (multi-threaded encoders, GPU and WebGL renderers), so the verdict is "visually
identical" when every frame is at or above --min-psnr dB and the durations match; anything lower names the frames
to look at. Exit 0 when the verdict passes, 1 otherwise."""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def probe(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate,sample_rate,channels",
                          "-of", "json", str(p)], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def audio_md5(p):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-map", "0:a:0?", "-f", "md5", "-"], capture_output=True, text=True)
    m = re.search(r"MD5=([0-9a-f]{32})", r.stdout)
    return m.group(1) if m else None


def psnr(a, b):
    with tempfile.TemporaryDirectory() as d:
        log = Path(d) / "psnr.log"
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(a), "-i", str(b), "-lavfi", f"[0:v][1:v]psnr=stats_file={log}", "-f", "null", "-"],
                       check=True)
        vals = []
        for line in log.read_text().splitlines():
            m = re.search(r"n:(\d+).*psnr_avg:(\S+)", line)
            if m:
                vals.append((int(m.group(1)), float("inf") if m.group(2) == "inf" else float(m.group(2))))
    return vals


def main():
    ap = argparse.ArgumentParser(description="Compare a rebuilt render with the original master.")
    ap.add_argument("original")
    ap.add_argument("rebuilt")
    ap.add_argument("--json", help="write the result here")
    ap.add_argument("--min-psnr", type=float, default=40.0, help="lowest per-frame PSNR (dB) still counted identical to the eye")
    ap.add_argument("--no-video", action="store_true", help="skip the per-frame comparison (sound only)")
    args = ap.parse_args()

    pa, pb = probe(args.original), probe(args.rebuilt)
    da, db = float(pa["format"]["duration"]), float(pb["format"]["duration"])
    res = {"duration": [da, db], "duration_match": abs(da - db) < 0.05,
           "streams": [[s.get("codec_type") for s in pa["streams"]], [s.get("codec_type") for s in pb["streams"]]]}
    ma, mb = audio_md5(args.original), audio_md5(args.rebuilt)
    res["audio_md5"] = [ma, mb]
    res["audio_identical"] = ma is not None and ma == mb
    ok = res["duration_match"] and (res["audio_identical"] or (ma is None and mb is None))
    if not args.no_video and any(s.get("codec_type") == "video" for s in pa["streams"]):
        vals = psnr(args.original, args.rebuilt)
        finite = [v for _, v in vals if v != float("inf")]
        res["frames"] = len(vals)
        res["identical_frames"] = len(vals) - len(finite)
        res["min_psnr"] = min(finite) if finite else None
        res["mean_psnr"] = round(sum(finite) / len(finite), 2) if finite else None
        res["worst_frames"] = sorted(vals, key=lambda x: x[1])[:5]
        ok = ok and (not finite or min(finite) >= args.min_psnr)
    res["verdict"] = "pass" if ok else "check"
    if args.json:
        Path(args.json).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"duration {da:.3f}s vs {db:.3f}s ({'match' if res['duration_match'] else 'DIFFER'})")
    print(f"audio {'bit-identical' if res['audio_identical'] else 'DIFFERENT or missing'} ({ma} / {mb})")
    if "frames" in res:
        print(f"video {res['frames']} frames, {res['identical_frames']} identical, min PSNR {res['min_psnr']}, mean {res['mean_psnr']} dB; worst {res['worst_frames']}")
    print(f"verdict: {res['verdict']}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
