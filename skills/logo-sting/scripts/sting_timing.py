#!/usr/bin/env python3
"""Timing JSON (logo-sting-timing/v1) for the logo sting: the frames that the picture and the sound both hit.

  python3 sting_timing.py --spec spec.json --out timing.json                      # 30 fps, 100 bpm
  python3 sting_timing.py --mark-count 3 --fps 25 --bpm 120 --out timing.json
  python3 sting_timing.py --spec spec.json --beats 0,18,36,54,72,90,108,126 --dur 144 --out timing.json

Beat k sits at round(k * fps * 60 / bpm), or is taken from --beats (a host score's own grid, frames local to the
sting start; beat 0 is frame 0). With N mark strokes (len(spec.mark)): hits are beats 1..N, bar is beat N+1, pulses
are the next three beats, dur is beat N+5 (or --dur). cut = dur - round(4 fps / 30) is the hard cut to black,
gate = bar - round(3 fps / 30) the suck-out. All values are integer frames; rounding is half up.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

SCHEMA = "logo-sting-timing/v1"


class TimingError(Exception):
    pass


def rnd(x):
    return int(math.floor(x + 0.5))


def frames30(k, fps):
    """A span of k frames at 30 fps, expressed in frames at fps."""
    return rnd(k * fps / 30)


def timing(n, fps, bpm=100.0, beats=None, dur=None):
    if n < 1:
        raise TimingError("the mark needs at least one stroke")
    if fps <= 0 or bpm <= 0:
        raise TimingError("--fps and --bpm must be positive")
    if beats is None:
        grid = [rnd(k * fps * 60.0 / bpm) for k in range(n + 6)]
        beat = rnd(fps * 60.0 / bpm)
    else:
        grid = list(beats)
        if not grid or grid[0] != 0:
            raise TimingError("--beats must start with 0: beat 0 is the sting's first frame (the downbeat it starts on)")
        if any(b <= a for a, b in zip(grid, grid[1:])):
            raise TimingError(f"--beats must be strictly increasing, got {grid}")
        need = n + 2 if dur is not None else n + 6
        if len(grid) < need:
            raise TimingError(f"--beats needs at least {need} beats for {n} strokes"
                              + ("" if dur is not None else " (or pass --dur for the end)") + f", got {len(grid)}")
        used = grid[: n + 6]
        diffs = sorted(b - a for a, b in zip(used, used[1:]))
        beat = rnd((diffs[(len(diffs) - 1) // 2] + diffs[len(diffs) // 2]) / 2)
    hits = grid[1: n + 1]
    bar = grid[n + 1]
    end = dur if dur is not None else grid[n + 5]
    cut = end - frames30(4, fps)
    gate = bar - frames30(3, fps)
    pulses = [p for p in grid[n + 2: n + 5] if p < cut]
    if hits[0] < 1:
        raise TimingError("the first stroke must land after frame 0")
    if gate - hits[-1] <= frames30(3, fps):
        raise TimingError(f"the beats are too fast: the suck-out (frame {gate}) must come more than "
                          f"{frames30(3, fps)} frames after the last stroke (frame {hits[-1]}); lower --bpm")
    if cut <= bar:
        raise TimingError(f"dur {end} leaves no hold after the bar (frame {bar}): the cut to black falls on frame {cut}")
    return {"schema": SCHEMA, "fps": int(fps) if fps == int(fps) else fps, "beat": beat, "hits": hits, "bar": bar,
            "pulses": pulses, "dur": end, "cut": cut, "gate": gate}


def dumps(obj):
    text = json.dumps(obj, indent=2)
    return re.sub(r"\[\s+([-0-9.,\s]+?)\s+\]", lambda m: "[" + ", ".join(x.strip() for x in m.group(1).split(",")) + "]", text)


def main():
    ap = argparse.ArgumentParser(description="Timing JSON (logo-sting-timing/v1) for the logo sting.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--spec", help="logo spec JSON: the stroke count N is len(spec.mark)")
    src.add_argument("--mark-count", type=int, help="the stroke count N, without a spec")
    ap.add_argument("--fps", type=float, default=30, help="frames per second (default 30)")
    ap.add_argument("--bpm", type=float, default=100, help="tempo of the default beat grid (default 100)")
    ap.add_argument("--beats", help="beat frames from the host score, local to the sting start: 0,18,36,...")
    ap.add_argument("--dur", type=int, help="sting length in frames (default: beat N+5)")
    ap.add_argument("--out", help="timing JSON to write (default: stdout)")
    args = ap.parse_args()
    try:
        if args.spec:
            spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
            if spec.get("schema") != "logo-sting-spec/v1" or not spec.get("mark"):
                raise TimingError(f"{args.spec} is not a logo-sting-spec/v1 file with a mark")
            n = len(spec["mark"])
        else:
            n = args.mark_count
        beats = None
        if args.beats:
            try:
                beats = [int(b) for b in args.beats.replace(" ", "").split(",") if b]
            except ValueError:
                raise TimingError(f"--beats must be integer frames separated by commas, got {args.beats!r}")
        t = timing(n, args.fps, args.bpm, beats, args.dur)
    except TimingError as e:
        print(f"sting_timing: error: {e}", file=sys.stderr)
        return 2
    text = dumps(t) + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    grid = "--beats" if beats else f"{args.bpm:g} bpm"
    print(f"sting_timing: {n} strokes, {t['fps']} fps, {grid}: hits {t['hits']}, bar {t['bar']}, pulses {t['pulses']}, "
          f"gate {t['gate']}, cut {t['cut']}, dur {t['dur']} ({t['dur'] / t['fps']:.3f} s)"
          + (f"\n  wrote {args.out}" if args.out else ""), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
