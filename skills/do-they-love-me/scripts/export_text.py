#!/usr/bin/env python3
"""Keep only the messages that carry human text, for semantic labelling."""

import argparse
import json

SKIP_PREFIX = ("[", "<", "http")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--messages", required=True)
    ap.add_argument("--me", required=True)
    ap.add_argument("--other", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-chars", type=int, default=120)
    args = ap.parse_args()

    rows, previous = [], ""
    with open(args.messages, encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if "timestamp" not in row:
                continue
            who = row.get("senderUsername")
            side = "me" if who == args.me else ("other" if who == args.other else "system")
            if side == "system":
                continue
            text = (row.get("text") or "").strip()
            raw = " ".join(text.split())[:60] if text else f'[{row.get("messageType")}]'
            if not text or text.startswith(SKIP_PREFIX):
                previous = raw
                continue
            text = " ".join(text.split())[: args.max_chars]
            if len(text) < 2:
                previous = raw
                continue
            rows.append(
                {
                    "i": len(rows),
                    "s": side,
                    "d": row["timestamp"][:10],
                    "p": previous,
                    "t": text,
                }
            )
            previous = text[:60]

    with open(args.out, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({
        "rows": len(rows),
        "me": sum(1 for r in rows if r["s"] == "me"),
        "other": sum(1 for r in rows if r["s"] == "other"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
