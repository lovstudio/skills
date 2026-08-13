#!/usr/bin/env python3
"""Create and maintain an append-only mainland website filing ledger."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


HEADING = "## 每日巡检记录"
HEADER = "| 时间 | 权威来源 | 阶段 | 状态 | 域名状态 | 用户动作 | 证据与备注 |"
SEPARATOR = "| --- | --- | --- | --- | --- | --- | --- |"
REQUIRED_HEADINGS = ("## 备案对象", "## 权威入口", "## 阶段门", HEADING)
STAGES = ("readiness", "icp", "cutover", "public-security", "security-assessment", "monitor")


class RecordError(ValueError):
    """Raised when a ledger cannot be safely read or updated."""


@dataclass(frozen=True)
class Observation:
    time: str
    authority: str
    stage: str
    status: str
    domain_status: str
    action: str
    evidence: str


def clean_cell(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).replace("|", "\\|")


def parse_time(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RecordError("--time must be ISO 8601, for example 2026-08-14T10:00:00+08:00") from exc
    if parsed.tzinfo is None:
        raise RecordError("--time must include a timezone offset")
    return value


def render_record(subject: str, service: str, domain: str, provider: str, timezone: str) -> str:
    return f"""---
title: {clean_cell(service)} 网站备案巡检记录
status: active
timezone: {clean_cell(timezone)}
---

# {clean_cell(service)} 网站备案巡检记录

## 备案对象

| 字段 | 值 |
| --- | --- |
| 主办者 | {clean_cell(subject)} |
| 服务 | {clean_cell(service)} |
| 域名 | {clean_cell(domain)} |
| 接入商 | {clean_cell(provider)} |

## 权威入口

- 工信部备案管理系统：https://beian.miit.gov.cn/
- 全国互联网安全管理服务平台：https://beian.mps.gov.cn/
- 接入商订单：运行时填写不含会话令牌的 URL

## 阶段门

- ICP：未核验
- 域名上线：未核验
- 公安联网备案：未核验
- 安全评估：待判断

{HEADING}

{HEADER}
{SEPARATOR}
"""


def validate_record(text: str) -> list[str]:
    issues = [f"missing heading: {heading}" for heading in REQUIRED_HEADINGS if heading not in text]
    if HEADER not in text:
        issues.append("missing canonical inspection table header")
    if SEPARATOR not in text:
        issues.append("missing canonical inspection table separator")
    return issues


def split_cells(line: str) -> list[str]:
    raw = line.strip().strip("|")
    cells = re.split(r"(?<!\\)\|", raw)
    return [cell.strip().replace("\\|", "|") for cell in cells]


def last_observation(text: str) -> Optional[Observation]:
    marker = text.find(HEADING)
    if marker < 0:
        raise RecordError(f"record is missing {HEADING}")
    rows = []
    for line in text[marker:].splitlines():
        if not line.startswith("|") or line in (HEADER, SEPARATOR):
            continue
        cells = split_cells(line)
        if len(cells) == 7:
            rows.append(Observation(cells[0], cells[1], cells[2], cells[3], cells[4], cells[5], cells[6]))
    return rows[-1] if rows else None


def changed(previous: Optional[Observation], current: Observation) -> bool:
    if previous is None:
        return True
    return any(
        getattr(previous, field) != getattr(current, field)
        for field in ("authority", "stage", "status", "domain_status", "action")
    )


def read_valid(path: Path) -> str:
    if not path.is_file():
        raise RecordError(f"record does not exist: {path}")
    text = path.read_text(encoding="utf-8")
    issues = validate_record(text)
    if issues:
        raise RecordError("; ".join(issues))
    return text


def observation_from_args(args: argparse.Namespace) -> Observation:
    return Observation(
        time=parse_time(args.time),
        authority=clean_cell(args.authority),
        stage=args.stage,
        status=clean_cell(args.status),
        domain_status=clean_cell(args.domain_status),
        action=clean_cell(args.action),
        evidence=clean_cell(args.evidence),
    )


def result_payload(path: Path, previous: Optional[Observation], current: Optional[Observation]) -> dict:
    return {
        "path": str(path),
        "previous": asdict(previous) if previous else None,
        "current": asdict(current) if current else None,
        "changed": changed(previous, current) if current else None,
        "needs_user_action": bool(current and current.status == "blocked-user-action"),
    }


def command_init(args: argparse.Namespace) -> int:
    path = args.path.expanduser().resolve()
    if path.exists():
        raise RecordError(f"refusing to overwrite existing record: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_record(args.subject, args.service, args.domain, args.provider, args.timezone), encoding="utf-8")
    print(json.dumps({"created": str(path)}, ensure_ascii=False))
    return 0


def command_check(args: argparse.Namespace) -> int:
    path = args.path.expanduser().resolve()
    text = read_valid(path)
    print(json.dumps({"valid": True, "path": str(path), "last": asdict(last_observation(text)) if last_observation(text) else None}, ensure_ascii=False))
    return 0


def command_compare(args: argparse.Namespace) -> int:
    path = args.path.expanduser().resolve()
    previous = last_observation(read_valid(path))
    current = observation_from_args(args)
    print(json.dumps(result_payload(path, previous, current), ensure_ascii=False))
    return 0


def command_append(args: argparse.Namespace) -> int:
    path = args.path.expanduser().resolve()
    text = read_valid(path)
    previous = last_observation(text)
    current = observation_from_args(args)
    if previous and previous.time == current.time:
        raise RecordError(f"an observation already exists for timestamp {current.time}")
    row = "| " + " | ".join(clean_cell(value) for value in asdict(current).values()) + " |\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(row)
    print(json.dumps(result_payload(path, previous, current), ensure_ascii=False))
    return 0


def add_observation_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--time", required=True)
    parser.add_argument("--authority", required=True)
    parser.add_argument("--stage", required=True, choices=STAGES)
    parser.add_argument("--status", required=True)
    parser.add_argument("--domain-status", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--evidence", required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create a new filing ledger")
    init_parser.add_argument("--path", required=True, type=Path)
    init_parser.add_argument("--subject", required=True)
    init_parser.add_argument("--service", required=True)
    init_parser.add_argument("--domain", required=True)
    init_parser.add_argument("--provider", required=True)
    init_parser.add_argument("--timezone", default="Asia/Shanghai")
    init_parser.set_defaults(handler=command_init)

    check_parser = subparsers.add_parser("check", help="validate a filing ledger")
    check_parser.add_argument("--path", required=True, type=Path)
    check_parser.set_defaults(handler=command_check)

    compare_parser = subparsers.add_parser("compare", help="compare without writing")
    compare_parser.add_argument("--path", required=True, type=Path)
    add_observation_arguments(compare_parser)
    compare_parser.set_defaults(handler=command_compare)

    append_parser = subparsers.add_parser("append", help="append one observation")
    append_parser.add_argument("--path", required=True, type=Path)
    add_observation_arguments(append_parser)
    append_parser.set_defaults(handler=command_append)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except RecordError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
