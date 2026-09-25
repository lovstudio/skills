#!/usr/bin/env python3
"""Verify that a WeChat article state changed only as planned."""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


MISSING = object()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    if isinstance(value, dict):
        for key in sorted(value):
            child = f"{prefix}.{key}" if prefix else key
            result.update(flatten(value[key], child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            child = f"{prefix}.{index}" if prefix else str(index)
            result.update(flatten(item, child))
    else:
        result[prefix] = value
    return result


def parse_expected(raw: str) -> tuple[str, Any]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError("expectation must use PATH=JSON_VALUE")
    path, encoded = raw.split("=", 1)
    if not path:
        raise argparse.ArgumentTypeError("expectation path is empty")
    try:
        value = json.loads(encoded)
    except json.JSONDecodeError:
        value = encoded
    return path, value


def is_allowed(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def verify(before: Any, after: Any, allow: list[str], expect: list[tuple[str, Any]]) -> list[str]:
    errors: list[str] = []
    before_flat = flatten(before)
    after_flat = flatten(after)
    for path in sorted(set(before_flat) | set(after_flat)):
        old = before_flat.get(path, MISSING)
        new = after_flat.get(path, MISSING)
        if old != new and not is_allowed(path, allow):
            errors.append(f"unexpected change at {path}: {old!r} -> {new!r}")
    for path, wanted in expect:
        actual = after_flat.get(path, MISSING)
        if actual is MISSING:
            errors.append(f"expected path is missing: {path}")
        elif actual != wanted:
            errors.append(f"expectation failed at {path}: {actual!r} != {wanted!r}")
    return errors


def self_test() -> int:
    before = {
        "metadata": {"title": "A", "digest": "D"},
        "body": {"word_count": 10},
        "blocks": {},
    }
    after = {
        "metadata": {"title": "A", "digest": "D"},
        "body": {"word_count": 14},
        "blocks": {"toc": {"count": 1}},
    }
    errors = verify(
        before,
        after,
        ["body.word_count", "blocks.toc*"],
        [("blocks.toc.count", 1)],
    )
    if errors:
        print("SELF-TEST FAILED")
        print("\n".join(errors))
        return 1
    invalid = dict(after)
    invalid["metadata"] = {"title": "Changed", "digest": "D"}
    if not verify(before, invalid, ["body.word_count", "blocks.toc*"], []):
        print("SELF-TEST FAILED: unexpected metadata mutation was not detected")
        return 1
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "before.json").write_text(json.dumps(before), encoding="utf-8")
        (root / "after.json").write_text(json.dumps(after), encoding="utf-8")
        if load_json(root / "before.json") != before or load_json(root / "after.json") != after:
            print("SELF-TEST FAILED: JSON round trip")
            return 1
    print("SELF-TEST PASSED")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", nargs="?", type=Path)
    parser.add_argument("after", nargs="?", type=Path)
    parser.add_argument("--allow", action="append", default=[])
    parser.add_argument("--expect", action="append", type=parse_expected, default=[])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.before is None or args.after is None:
        parser.error("before and after JSON files are required")
    errors = verify(load_json(args.before), load_json(args.after), args.allow, args.expect)
    if errors:
        print(f"FAILED: {len(errors)} issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASSED: article state matches the mutation plan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
