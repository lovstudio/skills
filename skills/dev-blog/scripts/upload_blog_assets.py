#!/usr/bin/env python3
"""Upload inline blog images to Skill Publisher's public Supabase storage bucket."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from publish_blog_post import env_first, load_env_file


DEFAULT_BUCKET = "app-assets"
DEFAULT_PREFIX = "blog-images"
ALLOWED_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
CONTENT_TYPES = {
    ".gif": "image/gif",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
}


def validate_slug(value: str) -> str:
    slug = value.strip().lower()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise SystemExit("--slug must be lowercase ASCII kebab-case")
    return slug


def normalize_filename(path: Path, index: int) -> str:
    suffix = path.suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        allowed = ", ".join(sorted(ALLOWED_SUFFIXES))
        raise SystemExit(f"Unsupported image type for {path}: {suffix or '(none)'}. Allowed: {allowed}")

    stem = path.stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "-", stem)
    stem = re.sub(r"-{2,}", "-", stem).strip("-")
    if not stem:
        stem = f"asset-{index:02d}"
    return f"{stem}{suffix}"


def content_type_for(path: Path) -> str:
    return CONTENT_TYPES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def build_records(
    paths: List[Path],
    base_url: str,
    bucket: str,
    prefix: str,
    slug: str,
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    seen_names = set()

    for index, path in enumerate(paths, start=1):
        if not path.is_file():
            raise SystemExit(f"Asset file not found: {path}")
        filename = normalize_filename(path, index)
        if filename in seen_names:
            raise SystemExit(
                f"Multiple inputs normalize to the same storage filename: {filename}. "
                "Rename the local files before uploading."
            )
        seen_names.add(filename)

        object_path = f"{prefix.strip('/')}/{slug}/{filename}"
        public_url = (
            f"{base_url.rstrip('/')}/storage/v1/object/public/"
            f"{urllib.parse.quote(bucket, safe='')}/{urllib.parse.quote(object_path, safe='/')}"
        )
        body = path.read_bytes()
        records.append(
            {
                "input": str(path),
                "filename": filename,
                "object_path": object_path,
                "public_url": public_url,
                "content_type": content_type_for(path),
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
            }
        )

    return records


def upload_record(
    record: Dict[str, Any],
    supabase_url: str,
    service_key: str,
    bucket: str,
) -> None:
    object_path = urllib.parse.quote(record["object_path"], safe="/")
    bucket_path = urllib.parse.quote(bucket, safe="")
    url = f"{supabase_url.rstrip('/')}/storage/v1/object/{bucket_path}/{object_path}"
    body = Path(record["input"]).read_bytes()
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": record["content_type"],
            "x-upsert": "true",
            "cache-control": "public, max-age=31536000, immutable",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(
            f"Storage upload failed for {record['object_path']}: HTTP {exc.code}\n{detail}"
        ) from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Storage upload failed for {record['object_path']}: {exc}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload one or more inline blog images to Skill Publisher's public Supabase storage."
    )
    parser.add_argument("--slug", required=True, help="Blog slug in lowercase ASCII kebab-case.")
    parser.add_argument(
        "--input",
        action="append",
        required=True,
        help="Image file to upload. Repeat this option for multiple files.",
    )
    parser.add_argument("--bucket", default=DEFAULT_BUCKET, help="Public Supabase storage bucket.")
    parser.add_argument("--prefix", default=DEFAULT_PREFIX, help="Object-path prefix inside the bucket.")
    parser.add_argument("--env-file", default="", help="Optional .env file containing Supabase credentials.")
    parser.add_argument("--dry-run", action="store_true", help="Print the upload manifest without writing.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env_path: Optional[Path] = Path(args.env_file).expanduser().resolve() if args.env_file else None
    load_env_file(env_path)

    supabase_url = env_first("NEXT_PUBLIC_SUPABASE_URL", "SUPABASE_URL", "VITE_SUPABASE_URL")
    if not supabase_url:
        raise SystemExit(
            "Missing Supabase URL. Set NEXT_PUBLIC_SUPABASE_URL, SUPABASE_URL, "
            "or VITE_SUPABASE_URL, or pass --env-file."
        )

    slug = validate_slug(args.slug)
    paths = [Path(value).expanduser().resolve() for value in args.input]
    records = build_records(paths, supabase_url, args.bucket, args.prefix, slug)

    if not args.dry_run:
        service_key = env_first("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SERVICE_KEY")
        if not service_key:
            raise SystemExit(
                "Missing Supabase service key. Set SUPABASE_SERVICE_ROLE_KEY "
                "or SUPABASE_SERVICE_KEY, or pass --env-file."
            )
        for record in records:
            upload_record(record, supabase_url, service_key, args.bucket)

    print(
        json.dumps(
            {
                "ok": True,
                "dry_run": args.dry_run,
                "bucket": args.bucket,
                "assets": records,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
