#!/usr/bin/env python3
"""Small deterministic SDK surface used by the bundled dashboard selftest."""

import json
import sys


def main() -> int:
    payload = json.load(sys.stdin)
    result = {
        "artifact": "demo.pdf",
        "paper": payload.get("paper", "A4"),
        "tocDepth": int(payload.get("tocDepth", 3)),
        "searchable": bool(payload.get("searchable", True)),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

