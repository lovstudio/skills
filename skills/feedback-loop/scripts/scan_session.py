#!/usr/bin/env python3
"""从宿主会话 JSONL 中提取用户消息，供情绪雷达判定。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SKIP_PREFIXES = (
    "<app-context",
    "<environment_context",
    "<permissions",
    "<skills_instructions",
    "<user_instructions",
    "<system",
    "<tool",
)

INJECTED_MARKERS = (
    "# agents.md instructions",
    "# claude.md instructions",
    "instructions for /root",
    "<instructions>",
)


def text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content") or ""
                if isinstance(text, str) and text:
                    parts.append(text)
        return "\n".join(parts)
    if isinstance(content, dict):
        text = content.get("text") or content.get("content") or ""
        return text if isinstance(text, str) else ""
    return ""


def extract(line: str) -> Optional[Dict[str, Any]]:
    try:
        item = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(item, dict):
        return None
    kind = item.get("type")
    ts = str(item.get("timestamp", "") or item.get("ts", "") or "")
    # Codex rollout format
    if kind == "response_item":
        payload = item.get("payload")
        if isinstance(payload, dict) and payload.get("type") == "message" and payload.get("role") == "user":
            return {"ts": ts, "text": text_from_content(payload.get("content"))}
        return None
    # Claude Code transcript format
    if kind == "user":
        message = item.get("message")
        if isinstance(message, dict):
            return {"ts": ts, "text": text_from_content(message.get("content"))}
        return {"ts": ts, "text": text_from_content(item.get("content"))}
    # OpenClaw and generic formats
    if kind in ("human", "user_message", "message"):
        if item.get("role") in (None, "user", "human"):
            return {"ts": ts, "text": text_from_content(item.get("content") or item.get("text"))}
    return None


def clean(text: str, limit: int) -> str:
    collapsed = re.sub(r"\s+", " ", text or "").strip()
    lowered = collapsed.lower()
    for prefix in SKIP_PREFIXES:
        if lowered.startswith(prefix):
            return ""
    head = lowered[:240]
    if any(marker in head for marker in INJECTED_MARKERS):
        return ""
    if len(collapsed) > limit:
        collapsed = collapsed[: max(1, limit - 1)].rstrip() + "…"
    return collapsed


def collect(path: Path, last: int, limit: int) -> List[Dict[str, Any]]:
    messages: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        found = extract(line)
        if not found:
            continue
        text = clean(found.get("text", ""), limit)
        if not text:
            continue
        messages.append({"ts": found.get("ts", ""), "text": text})
    if last > 0:
        messages = messages[-last:]
    for index, message in enumerate(messages, start=1):
        message["index"] = index
    return messages


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", action="append", required=True, help="会话 JSONL 路径，可重复")
    parser.add_argument("--last", type=int, default=40, help="每个文件保留最近多少条用户消息")
    parser.add_argument("--max-chars", type=int, default=400, help="单条消息截断长度")
    parser.add_argument("--json", action="store_true", help="输出 JSON（默认输出带序号的纯文本）")
    args = parser.parse_args(argv)

    payload = []
    for raw in args.file:
        path = Path(raw).expanduser()
        if not path.is_file():
            print("ERROR: 找不到会话文件：{}".format(path), file=sys.stderr)
            return 1
        messages = collect(path, args.last, args.max_chars)
        payload.append({"file": str(path), "count": len(messages), "messages": messages})

    if args.json:
        print(json.dumps({"schema": "feedback-scan/v1", "files": payload}, ensure_ascii=False, indent=2))
        return 0
    for entry in payload:
        print("file={} messages={}".format(entry["file"], entry["count"]))
        for message in entry["messages"]:
            print("[{}] {} {}".format(message["index"], message.get("ts", ""), message["text"]))
        print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
