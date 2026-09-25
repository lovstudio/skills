#!/usr/bin/env python3
"""Deterministic client for the public dshfind plugin gateway.

Outputs JSON on stdout only, so the agent can pipe or save results directly.
All query and detail operations are public, read-only, and need no auth.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_BASE_URL = "https://api.dshfind.com"
DEFAULT_TIMEOUT = 30
MAX_PER_PAGE = 100
USER_AGENT = "dsh-search-plugin/0.1 (public read-only gateway client)"


def resolve_base_url(cli_value: str | None) -> str:
    if cli_value:
        return cli_value.rstrip("/")
    return os.environ.get("DSHFIND_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def http_get_json(url: str, timeout: int) -> Any:
    request = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        print(
            json.dumps(
                {"error": {"status": exc.code, "url": url, "detail": str(exc.reason)}},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(
            json.dumps({"error": {"url": url, "detail": str(exc)}}, ensure_ascii=False),
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        print(f"ERROR: non-JSON response from {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def emit(data: Any, pretty: bool) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2 if pretty else None))


def cmd_health(args: argparse.Namespace) -> int:
    url = f"{args.base}/healthz"
    emit(http_get_json(url, args.timeout), args.pretty)
    return 0


def cmd_suggest(args: argparse.Namespace) -> int:
    query = urllib.parse.urlencode({"q": args.keyword})
    url = f"{args.base}/v1/suggest?{query}"
    emit(http_get_json(url, args.timeout), args.pretty)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    params: dict[str, str] = {}
    if args.keyword:
        params["q"] = args.keyword
    if args.category:
        params["category"] = args.category
    if args.language:
        params["language"] = args.language
    if args.grade:
        params["grade"] = args.grade
    if args.owner:
        params["owner"] = args.owner
    if args.tag:
        params["tag"] = args.tag
    if args.min_score is not None:
        params["min_score"] = str(args.min_score)
    if args.featured:
        params["featured"] = "true"
    if args.official:
        params["official"] = "true"
    if args.page is not None:
        params["page"] = str(args.page)
    if args.per_page is not None:
        params["per_page"] = str(args.per_page)
    url = f"{args.base}/v1/plugins?{urllib.parse.urlencode(params)}"
    emit(http_get_json(url, args.timeout), args.pretty)
    return 0


def cmd_detail(args: argparse.Namespace) -> int:
    query = urllib.parse.urlencode({"snapshot_days": args.snapshot_days})
    url = f"{args.base}/v1/plugins/{args.owner}/{args.repo}?{query}"
    emit(http_get_json(url, args.timeout), args.pretty)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=None,
        help=f"Gateway base URL (default: $DSHFIND_BASE_URL or {DEFAULT_BASE_URL})",
    )
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="HTTP timeout seconds")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output")
    sub = parser.add_subparsers(dest="command", required=True)

    health = sub.add_parser("health", help="Read public service health")
    health.set_defaults(func=cmd_health)

    suggest = sub.add_parser("suggest", help="Suggest plugins by keyword")
    suggest.add_argument("keyword", help="At least two trimmed characters")
    suggest.set_defaults(func=cmd_suggest)

    search = sub.add_parser("search", help="List and filter public plugins")
    search.add_argument("keyword", nargs="?", default=None, help="Search keyword (max 64 chars)")
    search.add_argument("--category", default=None)
    search.add_argument("--language", default=None)
    search.add_argument("--grade", choices=["S", "A", "B", "C"], default=None)
    search.add_argument("--owner", default=None)
    search.add_argument("--tag", default=None)
    search.add_argument("--min-score", type=int, default=None, help="0-100")
    search.add_argument("--featured", action="store_true")
    search.add_argument("--official", action="store_true")
    search.add_argument("--page", type=int, default=None)
    search.add_argument("--per-page", "--limit", dest="per_page", type=int, default=10,
                        help=f"1-{MAX_PER_PAGE}")
    search.set_defaults(func=cmd_search)

    detail = sub.add_parser("detail", help="Get one plugin with localized detail and growth")
    detail.add_argument("owner", help="Repository owner")
    detail.add_argument("repo", help="Repository name")
    detail.add_argument("--snapshot-days", type=int, default=7, help="1-90")
    detail.set_defaults(func=cmd_detail)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.base = resolve_base_url(args.base_url)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
