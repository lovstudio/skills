#!/usr/bin/env python3
"""Validate the decision-guide contract for comparison and selection reports."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SECTION_RE = re.compile(
    r"^##\s+(?:Decision Guide|Selection Flow|选型决策图|选型流程图|决策流程图)\s*$",
    re.MULTILINE | re.IGNORECASE,
)
OUTCOME_RE = re.compile(
    r"^###\s+(?:Outcome Map|Decision Outcomes|选择结果|决策结果)\s*$",
    re.MULTILINE | re.IGNORECASE,
)
VISUAL_RE = re.compile(
    r"<svg\b|data-decision-guide|```mermaid\s+.*?(?:flowchart|graph)\b|(?:→|-->|\+--)",
    re.DOTALL | re.IGNORECASE,
)
TERMINAL_RE = re.compile(
    r"(?:推荐|选择|停止|拒绝|前置条件|fallback|recommend|reject|stop|prerequisite)",
    re.IGNORECASE,
)


def section_body(report: str) -> str:
    match = SECTION_RE.search(report)
    if not match:
        return ""
    remaining = report[match.end():]
    next_section = re.search(r"^##\s+", remaining, re.MULTILINE)
    return remaining if not next_section else remaining[: next_section.start()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    errors = []
    warnings = []
    if not args.report.exists():
        errors.append(f"report not found: {args.report}")
        report = ""
    else:
        report = args.report.read_text(encoding="utf-8")

    body = section_body(report)
    if not body:
        errors.append("report missing a Decision Guide section")
    else:
        if not VISUAL_RE.search(body):
            errors.append("Decision Guide missing a branching visual")
        if not OUTCOME_RE.search(body):
            errors.append("Decision Guide missing an Outcome Map textual fallback")
        terminals = TERMINAL_RE.findall(body)
        if len(terminals) < 3:
            warnings.append("Decision Guide has fewer than three explicit terminal outcome markers")

    if args.strict and warnings:
        errors.extend(warnings)

    print(json.dumps({
        "status": "pass" if not errors else "fail",
        "warnings": warnings,
        "errors": errors,
    }, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
