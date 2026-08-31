#!/usr/bin/env python3
"""Audit source fidelity and required blocks in a WeChat repost edition."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup


def normalized_text(value: str) -> str:
    return " ".join(value.split())


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def image_url(image: Any) -> str:
    return str(image.get("src") or image.get("data-src") or "")


def inspect_html(
    *,
    html: str,
    source_text: str,
    source_account: str,
    source_url: str,
    required_blocks: list[str],
    expected_source_images: int | None,
    label: str,
) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    source_blocks = [
        node
        for node in soup.find_all(attrs={"data-source-account": source_account})
        if node.get("data-repost-source") == "true"
    ]
    if not source_blocks:
        source_blocks = soup.find_all(attrs={"data-source-account": source_account})

    errors: list[str] = []
    if len(source_blocks) != 1:
        errors.append(f"{label}: expected one source block, observed {len(source_blocks)}")
        source_block = None
    else:
        source_block = source_blocks[0]

    observed_text = ""
    source_images: list[Any] = []
    if source_block is not None:
        observed_text = normalized_text(source_block.get_text(" ", strip=True))
        source_images = source_block.find_all("img")
        if observed_text != source_text:
            errors.append(f"{label}: source visible text differs")
        if expected_source_images is not None and len(source_images) != expected_source_images:
            errors.append(
                f"{label}: expected {expected_source_images} source images, "
                f"observed {len(source_images)}"
            )
        if any(not image_url(image) for image in source_images):
            errors.append(f"{label}: one or more source images have no src or data-src")

    url_visible = source_url in normalized_text(soup.get_text(" ", strip=True))
    url_linked = any((anchor.get("href") or "").startswith(source_url) for anchor in soup.find_all("a"))
    if not (url_visible or url_linked):
        errors.append(f"{label}: source URL is neither visible nor linked")

    block_counts: dict[str, int] = {}
    for selector in required_blocks:
        count = len(soup.select(selector))
        block_counts[selector] = count
        if count != 1:
            errors.append(f"{label}: selector {selector!r} expected once, observed {count}")

    return {
        "label": label,
        "valid": not errors,
        "errors": errors,
        "sourceBlockCount": len(source_blocks),
        "sourceVisibleTextSha256": sha256_text(observed_text),
        "sourceVisibleTextChars": len(observed_text),
        "sourceImageCount": len(source_images),
        "sourceUrlVisibleOrLinked": url_visible or url_linked,
        "requiredBlockCounts": block_counts,
        "totalImageCount": len(soup.find_all("img")),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-text", type=Path, required=True)
    parser.add_argument("--edition-html", type=Path, required=True)
    parser.add_argument("--remote-html", type=Path)
    parser.add_argument("--source-account", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--required-block", action="append", default=[])
    parser.add_argument("--expected-source-images", type=int)
    parser.add_argument("--copyright-mode", choices=("reprint",), default="reprint")
    parser.add_argument("--receipt", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source_text = normalized_text(args.source_text.read_text(encoding="utf-8"))
    local = inspect_html(
        html=args.edition_html.read_text(encoding="utf-8"),
        source_text=source_text,
        source_account=args.source_account,
        source_url=args.source_url,
        required_blocks=args.required_block,
        expected_source_images=args.expected_source_images,
        label="local",
    )
    remote = None
    if args.remote_html:
        remote = inspect_html(
            html=args.remote_html.read_text(encoding="utf-8"),
            source_text=source_text,
            source_account=args.source_account,
            source_url=args.source_url,
            required_blocks=args.required_block,
            expected_source_images=args.expected_source_images,
            label="remote",
        )

    valid = local["valid"] and (remote is None or remote["valid"])
    result = {
        "schema": "lov-repost-wechat-article/audit-v1",
        "valid": valid,
        "state": "draft_readback_verified" if remote is not None and valid else "prepared" if valid else "failed",
        "copyrightMode": args.copyright_mode,
        "sourceAccount": args.source_account,
        "sourceUrl": args.source_url,
        "expectedSourceVisibleTextSha256": sha256_text(source_text),
        "local": local,
        "remote": remote,
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
