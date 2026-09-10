#!/usr/bin/env python3
"""Search Xiaohongshu notes with xiaohongshu-cli and filter note titles locally.

The script assumes the operator has installed ``xiaohongshu-cli`` and completed
login. It does not store or read cookies itself; the CLI owns authentication.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.1.0"


def cli_environment() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("LANG", "en_US.UTF-8")
    env.setdefault("LC_ALL", "en_US.UTF-8")
    env.setdefault("LC_CTYPE", "en_US.UTF-8")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("OUTPUT", "json")
    return env


def as_int(value: Any) -> int:
    try:
        return int(str(value or "0").replace(",", "").strip() or "0")
    except ValueError:
        return 0


def text_value(value: Any) -> str:
    return str(value or "").strip()


def title_of(item: dict[str, Any]) -> str:
    note_card = item.get("note_card") if isinstance(item.get("note_card"), dict) else {}
    return text_value(note_card.get("display_title") or note_card.get("title"))


def author_of(item: dict[str, Any]) -> str:
    note_card = item.get("note_card") if isinstance(item.get("note_card"), dict) else {}
    user = note_card.get("user") if isinstance(note_card.get("user"), dict) else {}
    return text_value(user.get("nickname") or user.get("nick_name"))


def note_url(item: dict[str, Any]) -> str:
    note_id = text_value(item.get("id"))
    token = text_value(item.get("xsec_token"))
    if not note_id:
        return ""
    if not token:
        return f"https://www.xiaohongshu.com/explore/{note_id}"
    return f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={token}"


def publish_label(item: dict[str, Any]) -> str:
    note_card = item.get("note_card") if isinstance(item.get("note_card"), dict) else {}
    tags = note_card.get("corner_tag_info")
    if not isinstance(tags, list):
        return ""
    for tag in tags:
        if isinstance(tag, dict) and text_value(tag.get("type")) == "publish_time":
            return text_value(tag.get("text"))
    if tags and isinstance(tags[0], dict):
        return text_value(tags[0].get("text"))
    return ""


def transform_item(item: dict[str, Any]) -> dict[str, Any]:
    note_card = item.get("note_card") if isinstance(item.get("note_card"), dict) else {}
    interact = note_card.get("interact_info") if isinstance(note_card.get("interact_info"), dict) else {}
    return {
        "id": text_value(item.get("id")),
        "title": title_of(item),
        "author": author_of(item),
        "published_at": publish_label(item),
        "likes": as_int(interact.get("liked_count")),
        "comments": as_int(interact.get("comment_count")),
        "collects": as_int(interact.get("collected_count")),
        "shares": as_int(interact.get("shared_count")),
        "url": note_url(item),
    }


def run_search(
    xhs_bin: str,
    query: str,
    sort: str,
    note_type: str,
    page: int,
    timeout: int,
) -> tuple[list[dict[str, Any]], bool]:
    command = [
        xhs_bin,
        "search",
        query,
        "--json",
        "--sort",
        sort,
        "--type",
        note_type,
        "--page",
        str(page),
    ]
    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=cli_environment(),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"xhs search timed out after {timeout}s: {query!r}") from exc
    if process.returncode != 0:
        detail = text_value(process.stderr or process.stdout)
        raise RuntimeError(f"xhs search failed ({process.returncode}): {detail}")
    try:
        payload = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"xhs search returned invalid JSON: {exc}") from exc
    if not payload.get("ok"):
        error = payload.get("error") if isinstance(payload.get("error"), dict) else {}
        message = text_value(error.get("message")) or "xhs search returned ok=false"
        raise RuntimeError(message)
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    items = data.get("items")
    return (items if isinstance(items, list) else []), bool(data.get("has_more"))


def search(
    xhs_bin: str,
    query: str,
    must_contain: list[str],
    pages: int,
    sort: str,
    note_type: str,
    limit: int,
    timeout: int,
) -> dict[str, Any]:
    if pages < 1:
        raise ValueError("pages must be at least 1")
    all_items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    fetched = 0
    has_more = False

    for page in range(1, pages + 1):
        batch, has_more = run_search(xhs_bin, query, sort, note_type, page, timeout)
        fetched += len(batch)
        for item in batch:
            if not isinstance(item, dict):
                continue
            item_id = text_value(item.get("id"))
            if item_id and item_id in seen_ids:
                continue
            if item_id:
                seen_ids.add(item_id)
            all_items.append(item)
        if not has_more:
            break

    filtered = []
    for item in all_items:
        title = title_of(item)
        if all(term in title for term in must_contain):
            filtered.append(transform_item(item))
    if limit > 0:
        filtered = filtered[:limit]

    return {
        "schema_version": "1",
        "ok": True,
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "sort": sort,
            "type": note_type,
            "pages_requested": pages,
            "items_fetched": fetched,
            "title_terms": must_contain,
            "matches": len(filtered),
        },
        "items": filtered,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("query", help="Xiaohongshu search keyword")
    parser.add_argument(
        "--xhs-bin",
        default="xhs",
        help="Path to the xiaohongshu-cli executable (default: xhs on PATH)",
    )
    parser.add_argument(
        "--must-contain",
        action="append",
        default=[],
        metavar="TEXT",
        help="Require this text in the note title; repeat for every required term",
    )
    parser.add_argument("--pages", type=int, default=1, help="Maximum pages to fetch")
    parser.add_argument(
        "--sort",
        choices=("general", "popular", "latest"),
        default="general",
        help="Search sorting mode",
    )
    parser.add_argument(
        "--type",
        choices=("all", "video", "image"),
        default="all",
        help="Search note type",
    )
    parser.add_argument("--limit", type=int, default=0, help="Limit matched rows after filtering")
    parser.add_argument("--timeout", type=int, default=120, help="Per-request timeout in seconds")
    parser.add_argument("--output", type=Path, help="Write the result JSON to this file")
    return parser


def resolve_xhs(candidate: str) -> str | None:
    located = shutil.which(candidate)
    if located:
        return located
    path = Path(candidate).expanduser()
    if path.is_file():
        return str(path)
    return None


def main() -> int:
    args = build_parser().parse_args()
    xhs_bin = resolve_xhs(args.xhs_bin)
    if not xhs_bin:
        print(
            "xiaohongshu-cli not found. Install it with: "
            "uv tool install xiaohongshu-cli",
            file=sys.stderr,
        )
        return 2
    try:
        result = search(
            xhs_bin,
            args.query,
            [term for term in args.must_contain if term],
            args.pages,
            args.sort,
            args.type,
            args.limit,
            args.timeout,
        )
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = args.output.expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
        print(
            json.dumps(
                {
                    "ok": True,
                    "saved": str(output),
                    "matches": len(result["items"]),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
