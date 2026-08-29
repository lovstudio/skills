#!/usr/bin/env python3
"""Verify one case in public JSON and on a public LovStudio detail page."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def canonical_fingerprint(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fetch(url: str, timeout: float) -> tuple[int, bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "lov-skill-add-case/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read(), response.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as exc:
        raise ValueError(f"HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"network error for {url}: {exc.reason}") from exc


def fetch_public_image(url: str, timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "lov-skill-add-case/0.2"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            content_type = response.headers.get_content_type()
            if not content_type.startswith("image/"):
                raise ValueError(
                    f"public case image is not image content: {content_type} for {url}"
                )
            if not body:
                raise ValueError(f"public case image is empty: {url}")
            return {
                "url": url,
                "http_status": response.status,
                "content_type": content_type,
                "bytes": len(body),
            }
    except urllib.error.HTTPError as exc:
        raise ValueError(f"HTTP {exc.code} for public case image {url}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(
            f"network error for public case image {url}: {exc.reason}"
        ) from exc


def run(args: argparse.Namespace) -> dict[str, Any]:
    cases_status, cases_body, charset = fetch(args.cases_url, args.timeout)
    try:
        cases = json.loads(cases_body.decode(charset))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"public cases response is not valid JSON: {exc}") from exc
    if not isinstance(cases, list):
        raise ValueError("public cases response must be a JSON array")
    match = next(
        (item for item in cases if isinstance(item, dict) and item.get("id") == args.case_id),
        None,
    )
    if match is None:
        raise ValueError(f"public cases JSON does not contain case id: {args.case_id}")
    actual_fingerprint = canonical_fingerprint(match)
    if actual_fingerprint != args.fingerprint:
        raise ValueError(
            f"public case fingerprint mismatch: expected {args.fingerprint}, got {actual_fingerprint}"
        )

    page_status, page_body, page_charset = fetch(args.page_url, args.timeout)
    try:
        page_text = html.unescape(page_body.decode(page_charset, errors="replace"))
    except LookupError as exc:
        raise ValueError(f"unsupported page charset: {page_charset}") from exc
    if args.marker not in page_text:
        raise ValueError(f"public detail page is missing marker: {args.marker}")
    image_values: list[str] = []
    cover = match.get("cover")
    if isinstance(cover, str) and cover.strip():
        image_values.append(cover.strip())
    gallery = match.get("gallery")
    if isinstance(gallery, list):
        image_values.extend(
            value.strip()
            for value in gallery
            if isinstance(value, str) and value.strip()
        )
    image_results: list[dict[str, Any]] = []
    for value in dict.fromkeys(image_values):
        if value.startswith("data:image/"):
            if value not in page_text:
                raise ValueError("public detail page is missing embedded case image")
            image_results.append({"url": "data:image/...", "embedded": True})
            continue
        if value.startswith("/"):
            image_url = urllib.parse.urljoin(args.page_url, value)
        else:
            image_url = urllib.parse.urljoin(args.cases_url, value)
        if value not in page_text and image_url not in page_text:
            raise ValueError(f"public detail page is missing case image: {value}")
        image_results.append(fetch_public_image(image_url, args.timeout))
    session_result: dict[str, Any] = {}
    session = match.get("session")
    if isinstance(session, dict) and session.get("access") == "paid":
        session_url = session.get("url")
        price_credits = session.get("priceCredits")
        if not isinstance(session_url, str) or not session_url.startswith(
            "https://lovstudio.ai/yoda/session/"
        ):
            raise ValueError("public case contains an invalid paid session URL")
        session_status, session_body, session_charset = fetch(
            session_url, args.timeout
        )
        session_text = html.unescape(
            session_body.decode(session_charset, errors="replace")
        )
        for session_marker in (
            "PAID CASE SESSION",
            str(match.get("title", "")),
            str(price_credits),
        ):
            if session_marker not in session_text:
                raise ValueError(
                    f"paid session page is missing marker: {session_marker}"
                )
        session_result = {
            "session_url": session_url,
            "session_http_status": session_status,
            "session_access": "paid-paywall-verified",
            "session_price_credits": price_credits,
        }

    return {
        "status": "live-verified",
        "case_id": args.case_id,
        "fingerprint": actual_fingerprint,
        "cases_url": args.cases_url,
        "cases_http_status": cases_status,
        "page_url": args.page_url,
        "page_http_status": page_status,
        "marker": args.marker,
        "images": image_results,
        **session_result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases-url", required=True)
    parser.add_argument("--page-url", required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--fingerprint", required=True)
    parser.add_argument("--marker", required=True)
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args()
    try:
        result = run(args)
    except (ValueError, OSError) as exc:
        print(f"context_id=skill-add-case-public-verify error={exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
