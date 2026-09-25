#!/usr/bin/env python3
"""Validate a WeChat experience parity case JSON contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


CASE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
STATUSES = {"observed", "modeled", "implemented", "verified"}

REQUIRED_LISTS = {
    "evidence": (
        "official_reference",
        "product_observation",
        "raw_record",
        "implementation",
    ),
    "semantic_contract": (
        "storage_types",
        "participants",
        "identity_fields",
        "raw_invariants",
        "downstream_consumers",
    ),
    "experience_contract": (
        "required",
        "forbidden",
        "responsive",
        "accessibility",
        "error_and_debug",
    ),
    "verification": (
        "parser_checks",
        "consumer_checks",
        "visual_checks",
        "runtime_checks",
        "quality_commands",
        "integration_checks",
    ),
}

REQUIRED_TEXT = {
    "semantic_contract": ("canonical_type", "content_source"),
}


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def nonempty_text_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(nonempty_text(item) for item in value)
    )


def validate_case(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root must be a JSON object"]

    if data.get("schema_version") != "1":
        errors.append("schema_version must be the string '1'")

    case_id = data.get("case_id")
    if not nonempty_text(case_id) or not CASE_ID_RE.fullmatch(case_id):
        errors.append("case_id must use lowercase kebab-case")

    for field in ("surface", "platform"):
        if not nonempty_text(data.get(field)):
            errors.append(f"{field} must be a non-empty string")

    status = data.get("status")
    if status not in STATUSES:
        errors.append("status must be observed, modeled, implemented, or verified")

    for section, fields in REQUIRED_LISTS.items():
        block = data.get(section)
        if not isinstance(block, dict):
            errors.append(f"{section} must be an object")
            continue
        for field in fields:
            if not nonempty_text_list(block.get(field)):
                errors.append(f"{section}.{field} must be a non-empty string list")

    for section, fields in REQUIRED_TEXT.items():
        block = data.get(section)
        if not isinstance(block, dict):
            continue
        for field in fields:
            if not nonempty_text(block.get(field)):
                errors.append(f"{section}.{field} must be a non-empty string")

    verification = data.get("verification")
    if isinstance(verification, dict) and status == "verified":
        runtime_checks = verification.get("runtime_checks")
        if not nonempty_text_list(runtime_checks):
            errors.append("verified cases require at least one runtime check")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Parity case JSON file")
    args = parser.parse_args()

    path = args.path.expanduser().resolve()
    if not path.is_file():
        print(f"ERROR: file does not exist: {path}", file=sys.stderr)
        return 2

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: could not read valid UTF-8 JSON: {exc}", file=sys.stderr)
        return 2

    errors = validate_case(data)
    if errors:
        print(f"FAILED: {len(errors)} issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"PASSED: parity case validation ({path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
