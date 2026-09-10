#!/usr/bin/env python3
"""Collect Xiaohongshu note bodies for a source-backed research report.

The script reuses ``xhs_search.py`` for discovery, then reads each selected
note through ``xhs read --json`` and exports a normalized evidence corpus.
It never stores or prints cookie values.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from xhs_search import (
    cli_environment,
    resolve_xhs,
    search,
    text_value,
)


def extract_xsec_token(url: str) -> str:
    """Return the xsec token embedded in a note URL, if present."""
    parsed = urlparse(url)
    values = parse_qs(parsed.query).get("xsec_token", [])
    return text_value(values[0]) if values else ""


def read_note(xhs_bin: str, note_id: str, xsec_token: str, timeout: int) -> dict[str, Any]:
    """Read one note and return its raw JSON envelope."""
    command = [xhs_bin, "read", note_id, "--json"]
    if xsec_token:
        command.extend(["--xsec-token", xsec_token])
    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=cli_environment(),
        timeout=timeout,
    )
    if process.returncode != 0:
        detail = text_value(process.stderr or process.stdout)
        raise RuntimeError(f"xhs read failed ({process.returncode}): {detail}")
    payload = json.loads(process.stdout)
    if not payload.get("ok"):
        error = payload.get("error") if isinstance(payload.get("error"), dict) else {}
        raise RuntimeError(text_value(error.get("message")) or "xhs read returned ok=false")
    return payload


def note_card_of(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract the first note card from ``xhs read`` output."""
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    items = data.get("items") if isinstance(data.get("items"), list) else []
    if not items or not isinstance(items[0], dict):
        raise RuntimeError("xhs read returned no note_card")
    card = items[0].get("note_card")
    if not isinstance(card, dict):
        raise RuntimeError("xhs read returned no note_card")
    return card


def collect(
    xhs_bin: str,
    query: str,
    must_contain: list[str],
    pages: int,
    sort: str,
    note_type: str,
    max_notes: int,
    timeout: int,
    delay: float,
) -> dict[str, Any]:
    """Discover notes and collect their source bodies."""
    discovery = search(
        xhs_bin=xhs_bin,
        query=query,
        must_contain=must_contain,
        pages=pages,
        sort=sort,
        note_type=note_type,
        limit=0,
        timeout=timeout,
    )
    rows = discovery.get("items") if isinstance(discovery.get("items"), list) else []
    selected = rows[:max_notes] if max_notes > 0 else rows
    notes: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for index, row in enumerate(selected, start=1):
        if not isinstance(row, dict):
            continue
        note_id = text_value(row.get("id"))
        if not note_id:
            continue
        try:
            payload = read_note(xhs_bin, note_id, extract_xsec_token(text_value(row.get("url"))), timeout)
            card = note_card_of(payload)
            user = card.get("user") if isinstance(card.get("user"), dict) else {}
            notes.append(
                {
                    "id": note_id,
                    "title": text_value(card.get("title") or row.get("title")),
                    "author": text_value(user.get("nickname") or row.get("author")),
                    "desc": text_value(card.get("desc") or card.get("description")),
                    "published_at": text_value(row.get("published_at")),
                    "likes": row.get("likes", 0),
                    "comments": row.get("comments", 0),
                    "collects": row.get("collects", 0),
                    "shares": row.get("shares", 0),
                    "url": text_value(row.get("url")),
                }
            )
        except Exception as exc:  # keep the corpus partial and auditable
            errors.append({"id": note_id, "error": f"{type(exc).__name__}: {exc}"})
        if index < len(selected):
            time.sleep(max(0.0, delay))

    return {
        "schema_version": "1",
        "ok": True,
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "sort": sort,
            "type": note_type,
            "pages_requested": pages,
            "items_fetched": discovery.get("meta", {}).get("items_fetched", 0),
            "matches": discovery.get("meta", {}).get("matches", 0),
            "notes_requested": len(selected),
            "notes_collected": len(notes),
            "errors": errors,
        },
        "notes": notes,
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
    parser.add_argument("--pages", type=int, default=2, help="Maximum discovery pages")
    parser.add_argument(
        "--sort",
        choices=("general", "popular", "latest"),
        default="popular",
        help="Discovery ordering",
    )
    parser.add_argument(
        "--type",
        choices=("all", "video", "image"),
        default="all",
        help="Note type",
    )
    parser.add_argument("--max-notes", type=int, default=12, help="Maximum note bodies to read")
    parser.add_argument("--delay", type=float, default=1.8, help="Delay between note reads in seconds")
    parser.add_argument("--timeout", type=int, default=90, help="Per-request timeout in seconds")
    parser.add_argument("--output", type=Path, help="Write the evidence corpus JSON to this file")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.pages < 1:
        print("ERROR: pages must be at least 1", file=sys.stderr)
        return 2
    if args.max_notes < 0:
        print("ERROR: max-notes must be 0 or greater", file=sys.stderr)
        return 2
    xhs_bin = resolve_xhs(args.xhs_bin)
    if not xhs_bin:
        print(
            "xiaohongshu-cli not found. Install it with: "
            "uv tool install xiaohongshu-cli",
            file=sys.stderr,
        )
        return 2
    try:
        result = collect(
            xhs_bin=xhs_bin,
            query=args.query,
            must_contain=[term for term in args.must_contain if term],
            pages=args.pages,
            sort=args.sort,
            note_type=args.type,
            max_notes=args.max_notes,
            timeout=args.timeout,
            delay=args.delay,
        )
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
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
                    "matches": result["meta"]["matches"],
                    "notes_collected": result["meta"]["notes_collected"],
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
