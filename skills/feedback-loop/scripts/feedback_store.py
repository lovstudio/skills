#!/usr/bin/env python3
"""反馈账本 CLI：追加事件、回填结果、查看与统计反馈。"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

EVENT_SCHEMA = "feedback-event/v1"
OUTCOME_SCHEMA = "feedback-outcome/v1"
STORE_SCHEMA = "feedback-loop-store/v1"
STORE_VERSION = "0.1.0"

CHANNELS = ("explicit", "passive")
POLARITIES = ("positive", "negative", "mixed", "neutral")
KINDS = (
    "praise",
    "delight",
    "approval",
    "lukewarm",
    "dissatisfaction",
    "frustration",
    "anger",
    "correction",
    "repeat_complaint",
    "disengagement",
    "direction_change",
)
SCOPES = ("task", "skill", "reference", "root-prompt")
STATUSES = (
    "captured",
    "triaged",
    "change-proposed",
    "change-applied",
    "verified",
    "declined",
    "deferred",
)
CLOSED_STATUSES = ("verified", "declined")

REDACT_PATTERNS = (
    re.compile(r"(?i)\b(?:sk|pk|ghp|gho|ghs|xox[baprs])[-_][A-Za-z0-9_\-]{8,}"),
    re.compile(r"(?i)\b(?:password|passwd|token|secret|api[_\- ]?key)\b\s*[:=]\s*\S+"),
    re.compile(r"\b[A-Za-z0-9+/]{40,}={0,2}\b"),
)

EVIDENCE_LIMIT = 240


def resolve_store(value: Optional[str]) -> Path:
    candidate = value or os.environ.get("FEEDBACK_LOOP_HOME") or "~/.feedback-loop"
    return Path(candidate).expanduser().resolve()


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_ts(value: str) -> datetime:
    text = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_since(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    text = value.strip().lower()
    match = re.fullmatch(r"(\d+)([dhw])", text)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        hours = amount * (24 if unit == "d" else 168 if unit == "w" else 1)
        return utc_now() - timedelta(hours=hours)
    return parse_ts(value)


def redact(text: str, limit: int = EVIDENCE_LIMIT) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    for pattern in REDACT_PATTERNS:
        cleaned = pattern.sub("[redacted]", cleaned)
    if len(cleaned) > limit:
        cleaned = cleaned[: limit - 1].rstrip() + "…"
    return cleaned


def new_event_id(ts: datetime) -> str:
    stamp = ts.strftime("%Y%m%dT%H%M%S")
    return "fb-{}-{}".format(stamp, secrets.token_hex(2))


def ensure_store(store: Path) -> bool:
    store.mkdir(parents=True, exist_ok=True)
    (store / "reports").mkdir(exist_ok=True)
    config_path = store / "config.json"
    if config_path.exists():
        return False
    payload = {
        "schema": STORE_SCHEMA,
        "version": STORE_VERSION,
        "created_at": iso(utc_now()),
        "event_schema": EVENT_SCHEMA,
        "outcome_schema": OUTCOME_SCHEMA,
    }
    config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name in ("events.jsonl", "outcomes.jsonl"):
        (store / name).touch()
    return True


def append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    records: List[Dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit("账本第 {} 行不是合法 JSON：{}".format(number, exc))
        if isinstance(item, dict):
            records.append(item)
    return records


def load_events(store: Path) -> List[Dict[str, Any]]:
    return read_jsonl(store / "events.jsonl")


def load_outcomes(store: Path) -> List[Dict[str, Any]]:
    return read_jsonl(store / "outcomes.jsonl")


def latest_outcomes(outcomes: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    latest: Dict[str, Dict[str, Any]] = {}
    for item in outcomes:
        event_id = str(item.get("event_id", ""))
        if not event_id:
            continue
        current = latest.get(event_id)
        if current is None or str(item.get("ts", "")) >= str(current.get("ts", "")):
            latest[event_id] = item
    return latest


def merged_events(events: List[Dict[str, Any]], outcomes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    latest = latest_outcomes(outcomes)
    merged = []
    for event in events:
        outcome = latest.get(str(event.get("id", "")))
        view = dict(event)
        view["latest_status"] = str(outcome.get("status")) if outcome else str(event.get("status", "captured"))
        view["latest_action"] = str(outcome.get("action", "")) if outcome else ""
        view["latest_verification"] = str(outcome.get("verification", "")) if outcome else ""
        view["latest_outcome_ts"] = str(outcome.get("ts", "")) if outcome else ""
        merged.append(view)
    merged.sort(key=lambda item: str(item.get("ts", "")))
    return merged


def filter_since(events: List[Dict[str, Any]], since: Optional[datetime]) -> List[Dict[str, Any]]:
    if since is None:
        return list(events)
    kept = []
    for event in events:
        try:
            if parse_ts(str(event.get("ts", ""))) >= since:
                kept.append(event)
        except ValueError:
            continue
    return kept


def compute_stats(events: List[Dict[str, Any]], outcomes: List[Dict[str, Any]], since: Optional[datetime]) -> Dict[str, Any]:
    window = filter_since(events, since)
    merged = merged_events(window, outcomes)
    by_polarity: Dict[str, int] = {key: 0 for key in POLARITIES}
    by_kind: Dict[str, int] = {}
    by_date: Dict[str, Dict[str, int]] = {}
    ages: List[float] = []
    unresolved = []
    verified_events = []
    for item in merged:
        polarity = str(item.get("polarity", "neutral"))
        if polarity in by_polarity:
            by_polarity[polarity] += 1
        else:
            by_polarity[polarity] = by_polarity.get(polarity, 0) + 1
        kind = str(item.get("kind", "unknown"))
        by_kind[kind] = by_kind.get(kind, 0) + 1
        date_key = str(item.get("local_date", "")) or str(item.get("ts", ""))[:10]
        bucket = by_date.setdefault(date_key, {key: 0 for key in POLARITIES})
        if polarity in bucket:
            bucket[polarity] += 1
        status = str(item.get("latest_status", "captured"))
        if status not in CLOSED_STATUSES:
            try:
                age_days = (utc_now() - parse_ts(str(item.get("ts", "")))).total_seconds() / 86400.0
            except ValueError:
                age_days = 0.0
            unresolved.append(
                {
                    "id": str(item.get("id", "")),
                    "ts": str(item.get("ts", "")),
                    "local_date": str(item.get("local_date", "")),
                    "polarity": polarity,
                    "kind": kind,
                    "intensity": item.get("intensity"),
                    "evidence": str(item.get("evidence", "")),
                    "status": status,
                    "age_days": round(age_days, 2),
                }
            )
        elif status == "verified":
            verified_events.append(item)
    for item in verified_events:
        try:
            start = parse_ts(str(item.get("ts", "")))
            end = parse_ts(str(item.get("latest_outcome_ts", "")))
        except ValueError:
            continue
        ages.append(max(0.0, (end - start).total_seconds() / 86400.0))
    ages.sort()
    median_age = ages[len(ages) // 2] if ages else None
    total = len(merged)
    positive = by_polarity.get("positive", 0)
    satisfaction = (positive / total) if total else None
    return {
        "schema": "feedback-stats/v1",
        "generated_at": iso(utc_now()),
        "window_since": iso(since) if since else None,
        "total": total,
        "by_polarity": by_polarity,
        "by_kind": dict(sorted(by_kind.items(), key=lambda pair: (-pair[1], pair[0]))),
        "satisfaction_rate": satisfaction,
        "unresolved": unresolved,
        "unresolved_count": len(unresolved),
        "median_time_to_verified_days": median_age,
        "daily": [
            {"date": date, "counts": counts}
            for date, counts in sorted(by_date.items())
        ],
    }


def cmd_init(args: argparse.Namespace) -> int:
    store = resolve_store(args.store)
    created = ensure_store(store)
    print("store={}".format(store))
    print("created={}".format("true" if created else "false"))
    print("config={}".format(store / "config.json"))
    return 0


def cmd_append(args: argparse.Namespace) -> int:
    store = resolve_store(args.store)
    ensure_store(store)
    ts = parse_ts(args.ts) if args.ts else utc_now()
    event = {
        "schema": EVENT_SCHEMA,
        "id": args.id or new_event_id(ts),
        "ts": iso(ts),
        "local_date": ts.astimezone().strftime("%Y-%m-%d"),
        "host": args.host or "generic",
        "session_id": args.session_id or "",
        "cwd": args.cwd or "",
        "channel": args.channel,
        "polarity": args.polarity,
        "intensity": int(args.intensity),
        "kind": args.kind,
        "confidence": float(args.confidence),
        "evidence": redact(args.evidence),
        "scope": args.scope,
        "scope_target": args.scope_target or "",
        "status": args.status,
        "created_by": args.created_by or "lov-feedback-loop",
        "note": redact(args.note or "", limit=240),
    }
    if event["channel"] == "passive" and event["confidence"] >= 1:
        event["confidence"] = 0.8
    if not args.force:
        for existing in reversed(load_events(store)):
            if (
                existing.get("session_id") == event["session_id"]
                and existing.get("evidence") == event["evidence"]
                and existing.get("kind") == event["kind"]
            ):
                try:
                    delta = abs((parse_ts(str(existing.get("ts", ""))) - ts).total_seconds())
                except ValueError:
                    delta = 0
                if delta <= 600:
                    print(json.dumps({"ok": False, "duplicate": True, "event": existing}, ensure_ascii=False, indent=2))
                    return 0
    append_jsonl(store / "events.jsonl", event)
    print(json.dumps({"ok": True, "duplicate": False, "event": event, "store": str(store)}, ensure_ascii=False, indent=2))
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    store = resolve_store(args.store)
    ensure_store(store)
    events = load_events(store)
    if not any(str(item.get("id")) == args.event_id for item in events):
        print("ERROR: 未知事件 id：{}".format(args.event_id), file=sys.stderr)
        return 2
    ts = parse_ts(args.ts) if args.ts else utc_now()
    outcome = {
        "schema": OUTCOME_SCHEMA,
        "event_id": args.event_id,
        "ts": iso(ts),
        "status": args.status,
        "action": redact(args.action or "", limit=240),
        "artifacts": args.artifact or [],
        "verification": redact(args.verification or "", limit=240),
        "actor": args.actor,
        "note": redact(args.note or "", limit=240),
    }
    append_jsonl(store / "outcomes.jsonl", outcome)
    print(json.dumps({"ok": True, "outcome": outcome, "store": str(store)}, ensure_ascii=False, indent=2))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    store = resolve_store(args.store)
    merged = merged_events(load_events(store), load_outcomes(store))
    if args.since:
        merged = filter_since(merged, parse_since(args.since))
    if args.polarity:
        merged = [item for item in merged if item.get("polarity") == args.polarity]
    if args.status:
        merged = [item for item in merged if item.get("latest_status") == args.status]
    if args.limit:
        merged = merged[-args.limit :]
    if args.json:
        print(json.dumps({"ok": True, "count": len(merged), "events": merged}, ensure_ascii=False, indent=2))
        return 0
    if not merged:
        print("（窗口内没有反馈事件）")
        return 0
    for item in merged:
        print(
            "{}  {:<9} {:<10} i{}  {:<18} {}".format(
                item.get("local_date", ""),
                item.get("polarity", ""),
                item.get("kind", ""),
                item.get("intensity", "-"),
                item.get("latest_status", ""),
                item.get("evidence", ""),
            )
        )
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    store = resolve_store(args.store)
    stats = compute_stats(load_events(store), load_outcomes(store), parse_since(args.since))
    if args.json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return 0
    print("窗口起点：{}".format(stats["window_since"] or "全部"))
    print("事件总数：{}".format(stats["total"]))
    print("极性分布：{}".format(json.dumps(stats["by_polarity"], ensure_ascii=False)))
    rate = stats["satisfaction_rate"]
    print("满意率：{}".format("n/a" if rate is None else "{:.0%}".format(rate)))
    print("未闭环：{}".format(stats["unresolved_count"]))
    median = stats["median_time_to_verified_days"]
    print("修复时长中位数：{}".format("n/a" if median is None else "{:.2f} 天".format(median)))
    if stats["by_kind"]:
        print("类型分布：{}".format(json.dumps(stats["by_kind"], ensure_ascii=False)))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    store = resolve_store(args.store)
    problems: List[str] = []
    events = load_events(store)
    outcomes = load_outcomes(store)
    required_event = ("schema", "id", "ts", "host", "session_id", "channel", "polarity", "intensity", "kind", "confidence", "evidence", "scope", "status")
    required_outcome = ("schema", "event_id", "ts", "status", "actor")
    seen = set()
    for index, event in enumerate(events, start=1):
        for key in required_event:
            if key not in event or event.get(key) in ("", None):
                problems.append("events[{}] 缺少字段 {}".format(index, key))
        if event.get("schema") != EVENT_SCHEMA:
            problems.append("events[{}] schema 不是 {}".format(index, EVENT_SCHEMA))
        event_id = str(event.get("id", ""))
        if event_id in seen:
            problems.append("事件 id 重复：{}".format(event_id))
        seen.add(event_id)
        if event.get("polarity") not in POLARITIES:
            problems.append("events[{}] polarity 非法：{}".format(index, event.get("polarity")))
        if event.get("channel") not in CHANNELS:
            problems.append("events[{}] channel 非法：{}".format(index, event.get("channel")))
        if not isinstance(event.get("intensity"), int) or not 1 <= int(event.get("intensity")) <= 5:
            problems.append("events[{}] intensity 必须是 1-5 整数".format(index))
        if event.get("kind") not in KINDS:
            problems.append("events[{}] kind 非法：{}".format(index, event.get("kind")))
        if event.get("scope") not in SCOPES:
            problems.append("events[{}] scope 非法：{}".format(index, event.get("scope")))
        if event.get("status") not in STATUSES:
            problems.append("events[{}] status 非法：{}".format(index, event.get("status")))
        try:
            if len(str(event.get("evidence", ""))) > EVIDENCE_LIMIT:
                problems.append("events[{}] evidence 超过 {} 字符".format(index, EVIDENCE_LIMIT))
        except TypeError:
            problems.append("events[{}] evidence 类型错误".format(index))
    for index, outcome in enumerate(outcomes, start=1):
        for key in required_outcome:
            if key not in outcome or outcome.get(key) in ("", None):
                problems.append("outcomes[{}] 缺少字段 {}".format(index, key))
        if outcome.get("schema") != OUTCOME_SCHEMA:
            problems.append("outcomes[{}] schema 不是 {}".format(index, OUTCOME_SCHEMA))
        if str(outcome.get("event_id", "")) not in seen:
            problems.append("outcomes[{}] 指向不存在的事件：{}".format(index, outcome.get("event_id")))
        if outcome.get("status") not in STATUSES:
            problems.append("outcomes[{}] status 非法：{}".format(index, outcome.get("status")))
    print("store={}".format(store))
    print("events={} outcomes={}".format(len(events), len(outcomes)))
    if problems:
        print("FAILED: {} 个问题".format(len(problems)))
        for problem in problems:
            print("- {}".format(problem))
        return 1
    print("PASSED: 账本结构有效")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", dest="store_global", help="账本目录，默认 ~/.feedback-loop 或 FEEDBACK_LOOP_HOME")
    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init", help="初始化账本目录")
    init_parser.add_argument("--store", dest="store_sub", default=None, help="账本目录（也可写在子命令之前）")
    init_parser.set_defaults(func=cmd_init)

    append_parser = sub.add_parser("append", help="追加一条反馈事件")
    append_parser.add_argument("--store", dest="store_sub", default=None, help="账本目录（也可写在子命令之前）")
    append_parser.add_argument("--channel", required=True, choices=CHANNELS)
    append_parser.add_argument("--polarity", required=True, choices=POLARITIES)
    append_parser.add_argument("--intensity", required=True, type=int, choices=range(1, 6))
    append_parser.add_argument("--kind", required=True, choices=KINDS)
    append_parser.add_argument("--confidence", type=float, default=0.9)
    append_parser.add_argument("--evidence", required=True)
    append_parser.add_argument("--host", default="generic")
    append_parser.add_argument("--session-id", default="")
    append_parser.add_argument("--cwd", default="")
    append_parser.add_argument("--scope", default="task", choices=SCOPES)
    append_parser.add_argument("--scope-target", default="")
    append_parser.add_argument("--status", default="captured", choices=STATUSES)
    append_parser.add_argument("--created-by", default="lov-feedback-loop")
    append_parser.add_argument("--note", default="")
    append_parser.add_argument("--ts", default="")
    append_parser.add_argument("--id", default="")
    append_parser.add_argument("--force", action="store_true", help="跳过 10 分钟去重检查")
    append_parser.set_defaults(func=cmd_append)

    update_parser = sub.add_parser("update", help="为事件追加一条结果")
    update_parser.add_argument("--store", dest="store_sub", default=None, help="账本目录（也可写在子命令之前）")
    update_parser.add_argument("--event-id", required=True)
    update_parser.add_argument("--status", required=True, choices=STATUSES)
    update_parser.add_argument("--action", default="")
    update_parser.add_argument("--artifact", action="append", default=[])
    update_parser.add_argument("--verification", default="")
    update_parser.add_argument("--actor", default="agent", choices=("agent", "user"))
    update_parser.add_argument("--note", default="")
    update_parser.add_argument("--ts", default="")
    update_parser.set_defaults(func=cmd_update)

    list_parser = sub.add_parser("list", help="查看合并后的反馈事件")
    list_parser.add_argument("--store", dest="store_sub", default=None, help="账本目录（也可写在子命令之前）")
    list_parser.add_argument("--since", default="")
    list_parser.add_argument("--polarity", default="", choices=("",) + POLARITIES)
    list_parser.add_argument("--status", default="", choices=("",) + STATUSES)
    list_parser.add_argument("--limit", type=int, default=0)
    list_parser.add_argument("--json", action="store_true")
    list_parser.set_defaults(func=cmd_list)

    stats_parser = sub.add_parser("stats", help="统计满意度趋势与未闭环清单")
    stats_parser.add_argument("--store", dest="store_sub", default=None, help="账本目录（也可写在子命令之前）")
    stats_parser.add_argument("--since", default="")
    stats_parser.add_argument("--json", action="store_true")
    stats_parser.set_defaults(func=cmd_stats)

    verify_parser = sub.add_parser("verify", help="校验账本结构")
    verify_parser.add_argument("--store", dest="store_sub", default=None, help="账本目录（也可写在子命令之前）")
    verify_parser.set_defaults(func=cmd_verify)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.store = getattr(args, "store_sub", None) or args.store_global
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
