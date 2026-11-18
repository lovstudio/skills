#!/usr/bin/env python3
"""Turn a black-on-white line drawing into transparent single-color ink.

Darker pixels become more opaque; white becomes fully transparent. The result
is trimmed to its content so it can be positioned as a decor block on a card.

usage: lineart.py RAW.png OUT.png [--ink "#6C675E"] [--black 4.7] [--white 78] [--no-trim]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[-400:] or f"{cmd[0]} failed")
    return proc.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert a line drawing to transparent single-color ink (ImageMagick).")
    ap.add_argument("raw")
    ap.add_argument("out")
    ap.add_argument("--ink", default="#6C675E", help="ink color as #RRGGBB (default warm gray)")
    ap.add_argument("--black", type=float, default=4.7, help="level black point %% after inversion")
    ap.add_argument("--white", type=float, default=78.0, help="level white point %% after inversion")
    ap.add_argument("--no-trim", action="store_true", help="keep the original canvas instead of trimming")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    magick = shutil.which("magick")
    if not magick:
        print(json.dumps({"status": "error", "error": "ImageMagick 7 'magick' not found (brew install imagemagick)"}))
        return 1
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", args.ink):
        print(json.dumps({"status": "error", "error": "--ink must be #RRGGBB"}))
        return 1
    raw, out = Path(args.raw), Path(args.out)
    if not raw.is_file():
        print(json.dumps({"status": "error", "error": f"input not found: {raw.name}"}))
        return 1
    if out.exists() and not args.force:
        print(json.dumps({"status": "refused", "reason": "output exists; pass --force", "file": out.name}))
        return 2
    if not 0 <= args.black < args.white <= 100:
        print(json.dumps({"status": "error", "error": "need 0 <= --black < --white <= 100"}))
        return 1
    try:
        size = run([magick, "identify", "-format", "%wx%h", str(raw)]).split()[0]
        with tempfile.TemporaryDirectory(prefix="jessy-card-ink-") as tmp:
            alpha = Path(tmp) / "alpha.png"
            run([magick, str(raw), "-colorspace", "Gray", "-negate",
                 "-level", f"{args.black:g}%,{args.white:g}%", str(alpha)])
            cmd = [magick, "-size", size, f"xc:{args.ink}", str(alpha), "-alpha", "off",
                   "-compose", "CopyOpacity", "-composite"]
            if not args.no_trim:
                cmd += ["-trim", "+repage"]
            out.parent.mkdir(parents=True, exist_ok=True)
            run(cmd + [str(out)])
        result = run([magick, "identify", "-format", "%wx%h", str(out)]).split()[0]
    except (RuntimeError, OSError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1
    print(json.dumps({"status": "ok", "out": str(out), "input_size": size, "output_size": result, "ink": args.ink}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
