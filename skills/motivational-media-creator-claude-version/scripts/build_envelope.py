#!/usr/bin/env python3
"""Build a reference envelope from rhythm profiles.

Groups motivational-rhythm-profile/v1 files by archetype and records, for each
metric, the observed minimum, median and maximum plus a band widened by a
tolerance. check_timeline.py and study_reference.py --envelope read the bands.
Standard library only.
"""
import argparse
import json
import statistics
import sys
from datetime import date
from pathlib import Path

METRICS = {
    "duration_s": ("duration_s",),
    "shots.median_s": ("shots", "median_s"),
    "shots.q4_over_q1": ("shots", "q4_over_q1"),
    "loudness.lra_lu": ("loudness", "lra_lu"),
    "arc.peak_position": ("loudness", "arc", "loudest_10s_position"),
    "arc.opening_vs_peak_lu": ("loudness", "arc", "opening_vs_peak_lu"),
    "arc.ending_vs_peak_lu": ("loudness", "arc", "ending_vs_peak_lu"),
    "arc.pre_peak_dip_lu": ("loudness", "arc", "pre_peak_dip_lu"),
    "speech.coverage": ("speech", "coverage"),
    "speech.coda_s": ("speech", "coda_s"),
    "speech.long_breaths": ("speech", "long_breaths"),
}


def dig(data, path):
    for key in path:
        if not isinstance(data, dict) or data.get(key) is None:
            return None
        data = data[key]
    return data


def band(values, tolerance):
    lo, hi = min(values), max(values)
    pad = (hi - lo) * tolerance
    return {
        "observed_min": lo,
        "median": round(statistics.median(values), 3),
        "observed_max": hi,
        "min": round(lo - pad, 3),
        "max": round(hi + pad, 3),
        "n": len(values),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("profiles", nargs="+", help="Profile JSON files from study_reference.py")
    parser.add_argument("--member", action="append", default=[], metavar="SOURCE_STEM=ARCHETYPE",
                        help="Assign a profile (file stem) to an archetype; repeatable")
    parser.add_argument("--tolerance", type=float, default=0.1,
                        help="Widen each band by this share of its observed range (default 0.1)")
    parser.add_argument("--label", default="", help="Human label for the reference set")
    parser.add_argument("--out", help="Write the envelope JSON here instead of stdout")
    args = parser.parse_args()

    members = dict(m.split("=", 1) for m in args.member)
    groups = {}
    for path in args.profiles:
        stem = Path(path).stem
        if stem not in members:
            sys.exit(f"no archetype given for {stem}; pass --member {stem}=<archetype>")
        profile = json.loads(Path(path).read_text(encoding="utf-8"))
        groups.setdefault(members[stem], []).append((stem, profile))

    envelope = {
        "schema": "motivational-rhythm-envelope/v1",
        "label": args.label,
        "built": date.today().isoformat(),
        "tolerance": args.tolerance,
        "note": "Descriptive bands from a small reference set. Outside a band is a prompt to look, not a defect.",
        "archetypes": {},
    }
    for archetype, items in sorted(groups.items()):
        bands = {}
        for key, path in METRICS.items():
            values = [v for v in (dig(p, path) for _, p in items) if v is not None]
            if values:
                bands[key] = band(values, args.tolerance)
        envelope["archetypes"][archetype] = {"members": [s for s, _ in items], "bands": bands}

    text = json.dumps(envelope, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(args.out)
    else:
        print(text)


if __name__ == "__main__":
    main()
