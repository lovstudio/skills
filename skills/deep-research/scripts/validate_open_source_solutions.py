#!/usr/bin/env python3
"""Validate the open-source solution registry and its shareable report section."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List


REQUIRED_FIELDS = {
    "name",
    "canonical_url",
    "forge",
    "description",
    "license",
    "last_activity_at",
    "retrieved_at",
    "implementation_mechanism",
    "evidence_url",
    "verification_status",
    "fit",
    "risks",
}
VERIFICATION_STATUSES = {
    "code_verified",
    "release_verified",
    "documentation_only",
    "unverified",
}
FIT_VALUES = {"reuse", "reference", "human_in_the_loop", "research_only", "reject"}
SECTION_RE = re.compile(r"^##\s+Open-Source Solutions Landscape\s*$", re.MULTILINE)


def load_rows(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValueError(f"line {line_number}: invalid JSON: {error}") from error
        if not isinstance(row, dict):
            raise ValueError(f"line {line_number}: expected a JSON object")
        row["_line"] = line_number
        rows.append(row)
    return rows


def validate_no_results(row: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for field in ("attempted_forges", "queries", "retrieved_at", "reason"):
        if not row.get(field):
            errors.append(f"line {row['_line']}: no-results record missing {field}")
    if len(row.get("attempted_forges", [])) < 1:
        errors.append(f"line {row['_line']}: attempted_forges must not be empty")
    return errors


def validate_solution(row: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    missing = sorted(field for field in REQUIRED_FIELDS if row.get(field) in (None, ""))
    if missing:
        errors.append(f"line {row['_line']}: missing fields: {', '.join(missing)}")
    if not str(row.get("canonical_url", "")).startswith("https://"):
        errors.append(f"line {row['_line']}: canonical_url must use https")
    if not str(row.get("evidence_url", "")).startswith("https://"):
        errors.append(f"line {row['_line']}: evidence_url must use https")
    if row.get("verification_status") not in VERIFICATION_STATUSES:
        errors.append(f"line {row['_line']}: invalid verification_status")
    if row.get("fit") not in FIT_VALUES:
        errors.append(f"line {row['_line']}: invalid fit")
    if not isinstance(row.get("risks"), list):
        errors.append(f"line {row['_line']}: risks must be a JSON array")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    errors: List[str] = []
    warnings: List[str] = []
    if not args.artifact.exists():
        errors.append(f"artifact not found: {args.artifact}")
        rows: List[Dict[str, Any]] = []
    else:
        try:
            rows = load_rows(args.artifact)
        except ValueError as error:
            rows = []
            errors.append(str(error))

    if not rows and not errors:
        errors.append("artifact contains no records")

    urls = set()
    no_result_rows = [row for row in rows if row.get("status") == "no_qualifying_repositories"]
    if no_result_rows:
        if len(rows) != 1:
            errors.append("no-results record cannot be mixed with solution records")
        errors.extend(validate_no_results(no_result_rows[0]))
    else:
        for row in rows:
            errors.extend(validate_solution(row))
            url = row.get("canonical_url")
            if url in urls:
                errors.append(f"line {row['_line']}: duplicate canonical_url: {url}")
            urls.add(url)

    if args.report:
        if not args.report.exists():
            errors.append(f"report not found: {args.report}")
        else:
            report = args.report.read_text(encoding="utf-8")
            if not SECTION_RE.search(report):
                errors.append("report missing '## Open-Source Solutions Landscape'")
            for url in sorted(urls):
                if url not in report:
                    warnings.append(f"canonical repository not linked in report: {url}")

    if args.strict and warnings:
        errors.extend(warnings)

    payload = {
        "status": "pass" if not errors else "fail",
        "records": len(rows),
        "solutions": len(urls),
        "no_qualifying_repositories": bool(no_result_rows),
        "warnings": warnings,
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
