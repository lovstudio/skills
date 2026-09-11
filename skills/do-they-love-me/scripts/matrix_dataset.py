#!/usr/bin/env python3
"""Turn the chat export into the calendar-matrix dataset used by the card.

One record per calendar day: how many messages each side sent, the day's first
and last time, one short verbatim line from the partner, and the components of
the (explicitly defined) activity index.
"""

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

AFFECTION = re.compile(
    r"想你|喜欢|爱你|亲亲|么么|抱抱|宝贝|亲爱的|晚安|早安|陪你|开心|哈哈|辛苦|照顾好|到家"
)
PRIVATE = re.compile(r"\d{5,}|电话|地址|姓名|身份证|http")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--messages", required=True)
    ap.add_argument("--me", required=True)
    ap.add_argument("--other", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tz-offset", type=float, default=8.0)
    args = ap.parse_args()

    tz = timezone(timedelta(hours=args.tz_offset))
    rows = []
    with open(args.messages, encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if "timestamp" not in row:
                continue
            who = row.get("senderUsername")
            side = "me" if who == args.me else ("other" if who == args.other else "system")
            if side == "system":
                continue
            row["side"] = side
            row["dt"] = datetime.fromisoformat(row["timestamp"]).astimezone(tz)
            row["day"] = row["dt"].date().isoformat()
            rows.append(row)
    rows.sort(key=lambda r: r["dt"])
    if not rows:
        raise SystemExit("no messages for that pair; check --me / --other")

    by_day = defaultdict(list)
    for row in rows:
        by_day[row["day"]].append(row)

    start, end = rows[0]["dt"].date(), rows[-1]["dt"].date()
    days = []
    cursor = start
    while cursor <= end:
        key = cursor.isoformat()
        day_rows = by_day.get(key, [])
        mine = [r for r in day_rows if r["side"] == "me"]
        hers = [r for r in day_rows if r["side"] == "other"]
        gaps = fast = 0
        for prev, cur in zip(day_rows, day_rows[1:]):
            if prev["side"] != cur["side"]:
                delta = (cur["dt"] - prev["dt"]).total_seconds() / 60
                if delta <= 24 * 60:
                    gaps += 1
                    fast += delta <= 5
        quote = ""
        candidates = [
            (r.get("text") or "").strip()
            for r in hers
            if r["messageType"] in ("text", "quote")
        ]
        candidates = [
            t for t in candidates if t and not t.startswith("[") and not PRIVATE.search(t)
        ]
        if candidates:
            quote = max(candidates, key=len).replace("\n", " ")[:16]
        days.append(
            {
                "d": key,
                "wd": cursor.weekday(),
                "other": len(hers),
                "me": len(mine),
                "n": len(day_rows),
                "aff": sum(1 for r in day_rows if AFFECTION.search(r.get("text") or "")),
                "rich": sum(
                    1
                    for r in day_rows
                    if r["messageType"] in ("voice", "image", "video", "emoji", "pat")
                ),
                "late_share": (
                    sum(1 for r in day_rows if r["dt"].hour >= 23 or r["dt"].hour < 3)
                    / len(day_rows)
                    if day_rows
                    else 0.0
                ),
                "fast_share": (fast / gaps) if gaps else 0.0,
                "first": day_rows[0]["dt"].strftime("%H:%M") if day_rows else "",
                "last": day_rows[-1]["dt"].strftime("%H:%M") if day_rows else "",
                "quote": quote,
            }
        )
        cursor += timedelta(days=1)

    # activity index: volume enters on a log scale so one loud day cannot dominate;
    # the other four components are countable ratios. Weights are fixed and printed
    # on the card so the number is reproducible rather than mystical.
    weights = {"n": 0.30, "aff": 0.20, "rich": 0.15, "late_share": 0.15, "fast_share": 0.20}
    components = {
        "n": [math.log1p(d["n"]) for d in days],
        "aff": [math.log1p(d["aff"]) for d in days],
        "rich": [math.log1p(d["rich"]) for d in days],
        "late_share": [d["late_share"] for d in days],
        "fast_share": [d["fast_share"] for d in days],
    }

    def norm(values):
        lo, hi = min(values), max(values)
        return [0.0] * len(values) if hi == lo else [(v - lo) / (hi - lo) for v in values]

    scaled = {k: norm(v) for k, v in components.items()}
    for i, day in enumerate(days):
        day["idx"] = round(100 * sum(weights[k] * scaled[k][i] for k in weights))

    hours = Counter(r["dt"].hour for r in rows)
    out = {
        "range": {"start": start.isoformat(), "end": end.isoformat()},
        "totals": {
            "other": sum(d["other"] for d in days),
            "me": sum(d["me"] for d in days),
            "active_days": sum(1 for d in days if d["n"]),
            "max_day": max(d["n"] for d in days),
            "max_other": max(d["other"] for d in days),
            "max_me": max(d["me"] for d in days),
        },
        "index_weights": weights,
        "hours": {str(h): hours.get(h, 0) for h in range(24)},
        "days": days,
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(json.dumps(out["totals"], ensure_ascii=False))


if __name__ == "__main__":
    main()
