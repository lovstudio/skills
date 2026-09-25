#!/usr/bin/env python3
"""Publish a generated development blog post to Supabase `blog_posts`.

The script is intentionally dependency-free. It uses PostgREST directly so the
skill can run anywhere Python 3.8+ is available.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_SOURCE_KIND = "dev-skill"
DEFAULT_AUTHOR = "Mark"
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(\s*<?([^\s)>]+)>?(?:\s+[^)]*)?\)")
HTML_IMAGE_RE = re.compile(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"']", re.IGNORECASE)


def load_env_file(path: Optional[Path]) -> None:
    if not path:
        return
    if not path.exists():
        raise SystemExit(f"Env file not found: {path}")

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def env_first(*names: str) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def split_tags(value: str) -> list[str]:
    return [t.strip() for t in re.split(r"[,，]", value) if t.strip()]


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"['’]", "", value)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    if value:
        return value[:96].strip("-")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"post-{stamp}"


def first_paragraph(markdown: str, limit: int = 180) -> str:
    lines: list[str] = []
    in_code = False

    for raw in markdown.splitlines():
        line = raw.strip()
        if line.startswith("```") or line.startswith("~~~"):
            in_code = not in_code
            continue
        if in_code or not line:
            if lines:
                break
            continue
        if line.startswith("#") or line.startswith(">") or line.startswith("!["):
            continue
        if re.match(r"^[-*]\s+", line):
            continue
        lines.append(line)

    text = re.sub(r"\s+", " ", " ".join(lines)).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def read_content(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"Input file not found: {path}")
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        raise SystemExit(f"Input file is empty: {path}")
    return content


def inline_image_sources(markdown: str) -> List[str]:
    sources = MARKDOWN_IMAGE_RE.findall(markdown)
    sources.extend(HTML_IMAGE_RE.findall(markdown))
    return [source.strip() for source in sources if source.strip()]


def validate_inline_images(markdown: str, require_inline_image: bool, published: bool) -> None:
    sources = inline_image_sources(markdown)
    if require_inline_image and not sources:
        raise SystemExit(
            "--require-inline-image was set, but the post body has no Markdown or HTML image. "
            "Upload the selected visual assets and embed their public URLs before publishing."
        )

    if not published:
        return

    non_public = [
        source
        for source in sources
        if not source.lower().startswith(("https://", "http://"))
    ]
    if non_public:
        joined = ", ".join(non_public)
        raise SystemExit(
            "Published posts must use public HTTP(S) URLs for inline images. "
            f"Replace these local or relative sources first: {joined}"
        )


def build_payload(args: argparse.Namespace, content: str) -> Dict[str, Any]:
    title = args.title.strip()
    if not title:
        raise SystemExit("--title is required")
    cover = args.cover.strip()
    if not args.draft and not cover:
        raise SystemExit("--cover is required for published posts. Generate and upload a cover, or pass --draft.")
    validate_inline_images(content, args.require_inline_image, published=not args.draft)

    slug = args.slug.strip() if args.slug else slugify(title)
    excerpt = args.excerpt.strip() if args.excerpt else first_paragraph(content)
    tags = split_tags(args.tags) if args.tags else ["dev", "skill-publisher"]
    published_at = args.published_at or dt.datetime.now(dt.timezone.utc).isoformat()
    source_path = args.source_path or f"dev-blog:{slug}"

    return {
        "slug": slug,
        "title": title,
        "excerpt": excerpt,
        "content_mdx": content,
        "cover": cover or None,
        "tags": tags,
        "author": args.author,
        "published_at": published_at,
        "is_visible": not args.draft,
        "show_in_index": not args.hide_from_index,
        "source_kind": args.source_kind,
        "source_path": source_path,
        "research_artifacts": {
            "generated_by": "lov-dev-blog",
            "schema": 1,
        },
    }


def postgrest_upsert(supabase_url: str, service_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    base = supabase_url.rstrip("/")
    url = f"{base}/rest/v1/blog_posts?on_conflict=slug"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=representation",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            raw = res.read().decode("utf-8")
            data = json.loads(raw) if raw else []
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Supabase upsert failed: HTTP {exc.code}\n{detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Supabase upsert failed: {exc}") from exc

    if isinstance(data, list) and data:
        return data[0]
    if isinstance(data, dict):
        return data
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish a Markdown/MDX blog post to Supabase blog_posts.")
    parser.add_argument("--input", required=True, help="Markdown/MDX file containing the final post body.")
    parser.add_argument("--title", required=True, help="Blog post title.")
    parser.add_argument("--slug", default="", help="URL slug. Defaults to a slug generated from --title.")
    parser.add_argument("--excerpt", default="", help="Short summary. Defaults to the first paragraph.")
    parser.add_argument("--tags", default="dev,skill-publisher", help="Comma-separated tags.")
    parser.add_argument("--author", default=DEFAULT_AUTHOR, help="Author name.")
    parser.add_argument("--cover", default="", help="Public cover image URL. Required unless --draft is set.")
    parser.add_argument(
        "--require-inline-image",
        action="store_true",
        help="Fail when the post body has no inline image. Use when the source-material inventory includes visuals.",
    )
    parser.add_argument("--published-at", default="", help="ISO timestamp. Defaults to now.")
    parser.add_argument("--source-kind", default=DEFAULT_SOURCE_KIND, help="Source kind stored in blog_posts.source_kind.")
    parser.add_argument("--source-path", default="", help="Stable source key. Defaults to dev-blog:<slug>.")
    parser.add_argument("--draft", action="store_true", help="Set is_visible=false.")
    parser.add_argument("--hide-from-index", action="store_true", help="Set show_in_index=false.")
    parser.add_argument("--env-file", default="", help="Optional .env file to load before publishing.")
    parser.add_argument("--dry-run", action="store_true", help="Print the payload and skip network writes.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    env_path = Path(args.env_file).expanduser().resolve() if args.env_file else None
    load_env_file(env_path)

    content = read_content(input_path)
    payload = build_payload(args, content)

    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    supabase_url = env_first("NEXT_PUBLIC_SUPABASE_URL", "SUPABASE_URL", "VITE_SUPABASE_URL")
    service_key = env_first("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SERVICE_KEY")
    if not supabase_url or not service_key:
        raise SystemExit(
            "Missing Supabase credentials. Set NEXT_PUBLIC_SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY, or pass --env-file."
        )

    row = postgrest_upsert(supabase_url, service_key, payload)
    slug = row.get("slug", payload["slug"])
    print(json.dumps({"ok": True, "slug": slug, "href": f"/blog/{slug}"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
