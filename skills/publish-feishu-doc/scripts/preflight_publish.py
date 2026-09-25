#!/usr/bin/env python3
"""Preflight Markdown before publishing it to a Feishu Wiki document."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


LINK_ACCESS = {
    "closed": {"link_share_entity": "closed"},
    "tenant_readable": {"link_share_entity": "tenant_readable"},
    "tenant_editable": {"link_share_entity": "tenant_editable"},
    "anyone_readable": {"external_access": True, "link_share_entity": "anyone_readable"},
    "anyone_editable": {"external_access": True, "link_share_entity": "anyone_editable"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Markdown and emit a Feishu publication preflight receipt.")
    parser.add_argument("source", type=Path, help="Markdown source file")
    parser.add_argument("--title", help="Online document title; defaults to the first H1")
    parser.add_argument("--wiki-target", help="Target space name, ID, URL, or parent token")
    parser.add_argument("--link-access", choices=sorted(LINK_ACCESS), default="closed")
    parser.add_argument("--emit-prepared", action="store_true", help="Write prepared Markdown to stdout instead of a JSON receipt")
    return parser.parse_args()


def first_h1(text: str) -> tuple[str | None, int | None]:
    for index, line in enumerate(text.splitlines()):
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip(), index
    return None, None


def prepare(text: str, title: str, h1: str | None, h1_index: int | None) -> tuple[str, str]:
    if h1 is None or h1_index is None:
        return f"# {title}\n\n{text.lstrip()}", "inserted"
    if h1.strip() == title.strip():
        return text, "preserved"
    lines = text.splitlines()
    lines[h1_index] = f"# {title}"
    return "\n".join(lines).rstrip() + "\n", "replaced"


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    warnings: list[str] = []
    source = args.source.expanduser()
    if not source.is_file():
        print(json.dumps({"ok": False, "errors": ["source_not_found"]}, ensure_ascii=False))
        return 2
    if source.suffix.lower() not in {".md", ".markdown"}:
        errors.append("source_must_be_markdown")

    text = source.read_text(encoding="utf-8")
    if not text.strip():
        errors.append("source_is_empty")

    h1, h1_index = first_h1(text)
    title = (args.title or h1 or source.stem).strip()
    if not title:
        errors.append("title_is_empty")
    if len(title) > 255:
        errors.append("title_exceeds_255_characters")

    prepared, title_heading_action = prepare(text, title, h1, h1_index)
    if "/Users/" in text or re.search(r"(?m)^/home/[^/]+/", text):
        warnings.append("source_contains_private_absolute_path")

    if args.emit_prepared:
        if errors:
            print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False), file=sys.stderr)
            return 2
        sys.stdout.write(prepared)
        return 0

    headings = re.findall(r"(?m)^#{1,6}\s+.+$", prepared)
    tables = re.findall(r"(?m)^\|(?:[^\n]*\|)+\s*$", prepared)
    links = re.findall(r"(?<!!)\[[^\]]+\]\((https?://[^)]+)\)", prepared)
    blockquotes = re.findall(r"(?m)^>\s+.+$", prepared)

    result = {
        "ok": not errors,
        "state": "prepared" if not errors else "preflight_failed",
        "source": {"name": source.name, "sha256": sha256(text), "bytes": len(text.encode("utf-8"))},
        "prepared": {
            "sha256": sha256(prepared),
            "title": title,
            "title_heading_action": title_heading_action,
            "heading_count": len(headings),
            "table_row_count": len(tables),
            "link_count": len(links),
            "blockquote_count": len(blockquotes),
        },
        "target": {"wiki": args.wiki_target, "link_access": args.link_access, "permission_patch": LINK_ACCESS[args.link_access]},
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
