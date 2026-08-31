#!/usr/bin/env python3
"""Build the deterministic text and metadata portion of a WeChat article package."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = "lovstudio/wechat-article-package/v2"
OPENING_IMAGE = "![文章首图](cover/article-opening-4x3.jpg)"
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_source(raw: str) -> dict[str, str]:
    parts = [part.strip() for part in raw.split("|", 3)]
    parts += [""] * (4 - len(parts))
    title, url, version, supports = parts
    if not title or not url:
        raise argparse.ArgumentTypeError("source must be TITLE|URL|VERSION|SUPPORTS")
    if url.startswith(("/Users/", "C:\\Users\\")):
        raise argparse.ArgumentTypeError("private absolute paths are not allowed in public sources")
    return {"title": title, "url": url, "version": version, "supports": supports}


def inject_opening_image(markdown: str) -> str:
    if "cover/article-opening-4x3." in markdown:
        return markdown.rstrip() + "\n"
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        if re.match(r"^#\s+\S", line):
            lines[index + 1:index + 1] = ["", OPENING_IMAGE, ""]
            return "\n".join(lines).rstrip() + "\n"
    raise ValueError("article must contain one H1 before it can be packaged")


def _markdown_target(raw: str) -> str:
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        return value[1:value.index(">")].strip()
    quoted = re.match(r"(.+?)\s+(['\"]).*\2\s*$", value)
    return (quoted.group(1) if quoted else value).strip()


def copy_local_article_images(markdown: str, article_path: Path, output: Path) -> list[str]:
    copied: list[str] = []
    for match in MARKDOWN_IMAGE_RE.finditer(markdown):
        target = _markdown_target(match.group(1))
        if target.startswith(("http://", "https://", "data:", "//")):
            continue
        relative = Path(target)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"article image must use a portable relative path: {target}")
        if target.startswith("cover/article-opening-4x3."):
            continue
        source = (article_path.parent / relative).resolve()
        if not source.is_file():
            raise ValueError(f"article image not found: {target}")
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied.append(relative.as_posix())
    return sorted(set(copied))


def build_sources_markdown(items: list[dict[str, str]]) -> str:
    lines = ["# Sources", ""]
    if not items:
        lines.extend(["本文没有需要公开列出的外部来源。", ""])
        return "\n".join(lines)
    for item in items:
        lines.append(f"## {item['title']}")
        lines.append("")
        lines.append(f"- URL：{item['url']}")
        if item["version"]:
            lines.append(f"- 版本或检查日期：{item['version']}")
        if item["supports"]:
            lines.append(f"- 支持：{item['supports']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--article", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--excerpt", required=True)
    parser.add_argument("--author", default="")
    parser.add_argument("--language", default="zh-CN")
    parser.add_argument("--brand-name", required=True)
    parser.add_argument("--brand-site", default="")
    parser.add_argument("--publication-name", default="")
    parser.add_argument("--read-original-url", default="")
    parser.add_argument("--source", action="append", default=[], type=parse_source)
    args = parser.parse_args()

    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.slug):
        parser.error("slug must be lowercase ASCII kebab-case")
    if len(args.title) > 32:
        parser.error("title must be at most 32 Unicode characters")
    if len(args.excerpt) > 120:
        parser.error("excerpt must be at most 120 Unicode characters")
    if not args.article.is_file():
        parser.error(f"article not found: {args.article}")

    article_text = inject_opening_image(args.article.read_text(encoding="utf-8"))
    output = args.output.resolve()
    (output / "cover").mkdir(parents=True, exist_ok=True)
    copied_images = copy_local_article_images(article_text, args.article.resolve(), output)
    (output / "article.md").write_text(article_text, encoding="utf-8")
    (output / "sources.md").write_text(build_sources_markdown(args.source), encoding="utf-8")

    created_at = now_iso()
    manifest = {
        "schema": SCHEMA,
        "title": args.title,
        "slug": args.slug,
        "excerpt": args.excerpt,
        "author": args.author,
        "language": args.language,
        "status": "pending_validation",
        "article_path": "article.md",
        "opening_image_path": "cover/article-opening-4x3.jpg",
        "wide_cover_path": "cover/wechat-cover-wide.jpg",
        "read_original_url": args.read_original_url,
        "source_items": args.source,
        "body_image_paths": copied_images,
        "brand": {
            "name": args.brand_name,
            "logo_source": "profile:brand.logo",
            "site": args.brand_site,
        },
        "products": [],
        "publication": {
            "name": args.publication_name or args.brand_name,
            "logo_source": "profile:skills.lov-article-creator.records.cover_logo_path",
            "logo_variant": "horizontal-lockup",
            "logo_color": "white",
            "status": "pending_validation",
            "remote_id": "",
            "public_url": "",
        },
        "created_at": created_at,
    }
    (output / "article-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"package": str(output), "status": "pending_validation"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
