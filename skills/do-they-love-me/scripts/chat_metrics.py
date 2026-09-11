#!/usr/bin/env python3
"""Quantify one 1:1 chat export: volume, reciprocity, rhythm, and rich media.

Input is the JSONL produced by the WeChat query handoff (each row carries
`timestamp`, `senderUsername`, `messageType`, `text`). Nothing here reads a
database directly, and nothing writes user text anywhere except the output JSON
you ask for.
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

KEYWORDS = {
    "想你": r"想你|想你了|好想你",
    "喜欢你": r"喜欢你|好喜欢|很喜欢你",
    "亲密称呼": r"宝贝|亲爱的|么么|亲亲|抱抱",
    "晚安": r"晚安",
    "见面": r"见面|约|哪天见|什么时候见|回来",
}


def load(path, me, other, tz):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if "timestamp" not in row:
                continue
            who = row.get("senderUsername")
            if who == me:
                side = "me"
            elif who == other:
                side = "other"
            else:
                side = "system"
            row["side"] = side
            row["dt"] = datetime.fromisoformat(row["timestamp"]).astimezone(tz)
            row["day"] = row["dt"].date().isoformat()
            rows.append(row)
    rows.sort(key=lambda r: r["dt"])
    return rows


def gap_stats(gaps):
    if not gaps:
        return {}
    gaps = sorted(gaps)
    mid = gaps[len(gaps) // 2]
    return {
        "n": len(gaps),
        "median_min": round(mid, 1),
        "under_5min_pct": round(100 * sum(1 for g in gaps if g <= 5) / len(gaps), 1),
        "over_6h": sum(1 for g in gaps if g > 360),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--messages", required=True, help="messages.jsonl from the query handoff")
    ap.add_argument("--me", required=True, help="username of the account owner")
    ap.add_argument("--other", required=True, help="username of the conversation partner")
    ap.add_argument("--out", required=True, help="metrics JSON output path")
    ap.add_argument("--tz-offset", type=float, default=8.0, help="local timezone offset in hours")
    args = ap.parse_args()

    tz = timezone(timedelta(hours=args.tz_offset))
    all_rows = load(args.messages, args.me, args.other, tz)
    people = [r for r in all_rows if r["side"] in ("me", "other")]
    if not people:
        raise SystemExit("no messages for that pair; check --me / --other")

    first, last = people[0]["dt"], people[-1]["dt"]
    days = sorted({r["day"] for r in people})
    metrics = {
        "span": {
            "start": first.isoformat(),
            "end": last.isoformat(),
            "calendar_days": (last.date() - first.date()).days + 1,
            "active_days": len(days),
            "silent_days": [
                (first.date() + timedelta(days=i)).isoformat()
                for i in range((last.date() - first.date()).days + 1)
                if (first.date() + timedelta(days=i)).isoformat() not in set(days)
            ],
        },
        "counts": dict(Counter(r["side"] for r in people)),
        "type_mix": {
            side: dict(Counter(r["messageType"] for r in people if r["side"] == side))
            for side in ("me", "other")
        },
    }

    day_first, day_last = {}, {}
    for r in people:
        day_first.setdefault(r["day"], r)
        day_last[r["day"]] = r
    metrics["day_openers"] = dict(Counter(r["side"] for r in day_first.values()))
    metrics["day_closers"] = dict(Counter(r["side"] for r in day_last.values()))

    # a reply gap is the distance from one side's message to the other side's next one
    gaps = defaultdict(list)
    prev = None
    for r in people:
        if prev and prev["side"] != r["side"]:
            delta = (r["dt"] - prev["dt"]).total_seconds() / 60
            if delta <= 24 * 60:
                gaps[r["side"]].append(delta)
        prev = r
    metrics["reply_gap"] = {side: gap_stats(gaps[side]) for side in ("me", "other")}

    hours = Counter(r["dt"].hour for r in people)
    late = [r for r in people if r["dt"].hour >= 23 or r["dt"].hour < 4]
    metrics["hour_hist"] = {str(h): hours.get(h, 0) for h in range(24)}
    metrics["late_night"] = {
        "n": len(late),
        "by_side": dict(Counter(r["side"] for r in late)),
        "after_midnight": sum(1 for r in late if r["dt"].hour < 4),
        "after_midnight_by_side": dict(
            Counter(r["side"] for r in late if r["dt"].hour < 4)
        ),
    }

    streaks, run, prev_day = [], 1, None
    for day in sorted({datetime.fromisoformat(d).date() for d in days}):
        if prev_day and (day - prev_day).days == 1:
            run += 1
        else:
            run = 1
        streaks.append(run)
        prev_day = day
    metrics["streak"] = {"longest": max(streaks), "active_days": len(days)}

    start = first.date()
    weekly = defaultdict(Counter)
    for r in people:
        w = (r["dt"].date() - start).days // 7
        weekly[w][r["side"]] += 1
    metrics["weekly"] = {str(w): dict(counter) for w, counter in sorted(weekly.items())}

    metrics["keywords"] = {}
    for label, pattern in KEYWORDS.items():
        rx = re.compile(pattern)
        hits = [r for r in people if rx.search(r.get("text") or "")]
        metrics["keywords"][label] = {
            "total": len(hits),
            "by_side": dict(Counter(r["side"] for r in hits)),
            "samples": [
                {"side": r["side"], "day": r["day"], "text": (r.get("text") or "")[:40]}
                for r in hits[:5]
            ],
        }

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, ensure_ascii=False, indent=1)

    print(json.dumps(
        {
            "span": metrics["span"]["calendar_days"],
            "active_days": metrics["span"]["active_days"],
            "counts": metrics["counts"],
            "reply_gap": metrics["reply_gap"],
            "late_night": metrics["late_night"]["by_side"],
            "day_openers": metrics["day_openers"],
            "day_closers": metrics["day_closers"],
            "streak": metrics["streak"],
        },
        ensure_ascii=False,
        indent=1,
    ))


if __name__ == "__main__":
    main()
