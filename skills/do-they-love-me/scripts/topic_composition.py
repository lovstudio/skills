#!/usr/bin/env python3
"""Aggregate topic labels into per-side shares and a weekly trend."""

import argparse
import json
from collections import Counter, defaultdict
from datetime import date

ORDER = ("work", "love", "life", "other")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--labels", required=True, help="labels.jsonl")
    ap.add_argument("--out", required=True, help="composition JSON")
    ap.add_argument("--weeks-start", default="", help="week 0 start date (defaults to first label day)")
    ap.add_argument("--weeks", type=int, default=8, help="how many week buckets to emit")
    ap.add_argument("--accuracy", default="", help="semantic_label report JSON, copied into the output")
    args = ap.parse_args()

    rows = [
        json.loads(line)
        for line in open(args.labels, encoding="utf-8")
        if line.strip()
    ]
    if not rows:
        raise SystemExit("no labels found")

    per_side = defaultdict(Counter)
    for row in rows:
        per_side[row["s"]][row["label"]] += 1

    start = date.fromisoformat(args.weeks_start) if args.weeks_start else date.fromisoformat(
        min(r["d"] for r in rows)
    )
    weekly = defaultdict(Counter)
    love_by_week = defaultdict(Counter)
    for row in rows:
        w = (date.fromisoformat(row["d"]) - start).days // 7
        weekly[w][row["label"]] += 1
        if row["label"] == "love":
            love_by_week[w][row["s"]] += 1

    def shares(counter):
        n = sum(counter.values())
        return {k: round(counter[k] / n * 100, 1) for k in ORDER} if n else {k: 0.0 for k in ORDER}

    data = {
        "labels_total": len(rows),
        "sides": {
            side: {
                "n": sum(per_side[side].values()),
                "pct": shares(per_side[side]),
                "count": {k: per_side[side][k] for k in ORDER},
            }
            for side in ("other", "me")
        },
        "weeks": [
            {
                "w": w,
                "n": sum(weekly[w].values()),
                "pct": shares(weekly[w]),
                "love_other": love_by_week[w]["other"],
                "love_me": love_by_week[w]["me"],
            }
            for w in range(args.weeks)
            if weekly.get(w)
        ],
    }
    if args.accuracy:
        data["accuracy"] = json.loads(open(args.accuracy, encoding="utf-8").read())

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"sides": {k: v["pct"] for k, v in data["sides"].items()}},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
