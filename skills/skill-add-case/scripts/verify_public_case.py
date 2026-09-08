#!/usr/bin/env python3
"""Verify one case in public JSON and on a public LovStudio detail page."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any
from html.parser import HTMLParser


class PublicPage(HTMLParser):
    """Inspect actual case elements without matching Next's serialized payloads."""
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.case_depth: int | None = None
        self.words: list[str] = []
        self.headings: list[str] = []
        self.images: list[str] = []
        self.links: list[str] = []
        self.all_links: list[str] = []
        self.videos: list[str] = []
        self.has_case = False
        self.has_transcript = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag not in self.VOID:
            self.stack.append(tag)
        if values.get("data-testid") == "skill-case-details":
            self.case_depth = len(self.stack)
            self.has_case = True
        if tag == "section" and values.get("aria-label") == "会话记录":
            self.has_transcript = True
        if tag == "a" and values.get("href"):
            self.all_links.append(values["href"])
        if self.case_depth is not None:
            if tag == "video" and values.get("src"):
                self.videos.append(values["src"])
            if tag == "img" and values.get("src"):
                self.images.append(values["src"])
            if tag == "a" and values.get("href"):
                self.links.append(values["href"])

    def handle_endtag(self, tag):
        if tag in self.stack:
            index = len(self.stack) - 1 - self.stack[::-1].index(tag)
            del self.stack[index:]
            if self.case_depth is not None and len(self.stack) < self.case_depth:
                self.case_depth = None

    def handle_data(self, data):
        if any(tag in self.stack for tag in ("script", "style", "template")):
            return
        self.words.append(data)
        if self.case_depth is not None and any(tag in self.stack for tag in ("h1", "h2", "h3")):
            self.headings.append(data)

    @property
    def text(self):
        return " ".join(self.words)


def canonical_fingerprint(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fetch(url: str, timeout: float) -> tuple[int, bytes, str]:
    headers = {"User-Agent": "Mozilla/5.0 LovStudioCaseVerifier", "Accept-Language": "zh-CN,zh;q=0.9"}
    if urllib.parse.urlsplit(url).hostname == "lovstudio.ai":
        headers["Cookie"] = "locale=zh-CN"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read(), response.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as exc:
        raise ValueError(f"HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"network error for {url}: {exc.reason}") from exc


def fetch_public_image(url: str, timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 LovStudioCaseVerifier"})
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
        page_text = page_body.decode(page_charset, errors="replace")
    except LookupError as exc:
        raise ValueError(f"unsupported page charset: {page_charset}") from exc
    if args.marker not in PublicPage(page_text).text:
        raise ValueError(f"public detail page is missing marker: {args.marker}")
    case_page_status, case_page_body, case_page_charset = fetch(
        args.case_page_url, args.timeout
    )
    case_page_text = case_page_body.decode(case_page_charset, errors="replace")
    case_page = PublicPage(case_page_text)
    if not case_page.has_case or args.marker not in case_page.text:
        raise ValueError("public case page is missing rendered case content")
    for case_page_marker in ("input", "prompt", "output"):
        if not re.search(rf"\b{case_page_marker}\b", " ".join(case_page.headings), re.I):
            raise ValueError(
                f"public case page is missing marker: {case_page_marker}"
            )
    relation_results = []
    skill_ids = match.get("skillIds", [])
    for skill_id in skill_ids:
        if not isinstance(skill_id, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill_id):
            raise ValueError("public case contains an invalid related Skill ID")
        skill_path = f"/skills/{skill_id}"
        if not any(urllib.parse.urlsplit(link).path == skill_path for link in case_page.links):
            raise ValueError(f"case page is missing related Skill link: {skill_id}")
        skill_url = urllib.parse.urljoin(args.case_page_url, skill_path)
        status, body, charset = fetch(skill_url, args.timeout)
        skill_page = PublicPage(body.decode(charset, errors="replace"))
        if args.marker not in skill_page.text or not any(urllib.parse.urlsplit(link).path == f"/cases/{args.case_id}" for link in skill_page.all_links):
            raise ValueError(f"related Skill page does not link this canonical case: {skill_id}")
        relation_results.append({"skill_id": skill_id, "url": skill_url, "http_status": status})
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
            if value not in case_page.images:
                raise ValueError("public detail page is missing embedded case image")
            image_results.append({"url": "data:image/...", "embedded": True})
            continue
        root = args.cases_url.rsplit("/cases/cases.json", 1)[0] + "/"
        image_url = urllib.parse.urljoin(args.page_url if value.startswith("/") else root, value)
        rendered = None
        for src in case_page.images:
            absolute = urllib.parse.urljoin(args.case_page_url, src)
            parsed = urllib.parse.urlsplit(absolute)
            query = urllib.parse.parse_qs(parsed.query)
            original = query.get("url", [absolute])[0] if parsed.path == "/_next/image" else absolute
            asset_path = query.get("path", [""])[0]
            if original == image_url or (parsed.path == "/api/skill-asset" and not urllib.parse.urlsplit(value).scheme and asset_path == value):
                rendered = absolute
                break
        if rendered is None:
            raise ValueError(f"public case page is missing case image: {value}")
        image_results.append(fetch_public_image(rendered, args.timeout))
    video_result = None
    if match.get("video"):
        if match["video"] not in case_page.videos:
            raise ValueError("public case page is missing the final video")
        video_status, video_body, _ = fetch(match["video"], args.timeout)
        if len(video_body) < 12 or video_body[4:8] != b"ftyp":
            raise ValueError("public case video is not a readable MP4")
        video_result = {"url": match["video"], "http_status": video_status, "bytes": len(video_body)}
    session_result: dict[str, Any] = {}
    session = match.get("session")
    if isinstance(session, dict) and session.get("url") not in case_page.links:
        raise ValueError("public case page is missing the Session link")
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
        session_text = PublicPage(session_body.decode(session_charset, errors="replace")).text
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
    elif isinstance(session, dict) and session.get("access") == "public":
        session_url = session.get("url", "")
        if not re.fullmatch(r"https://lovstudio\.ai/yoda/session/yss_[A-Za-z0-9_-]{43}(?:\?detail=(?:concise|full))?", session_url):
            raise ValueError("public case contains an invalid public Session URL")
        status, body, charset = fetch(session_url, args.timeout)
        public_session = PublicPage(body.decode(charset, errors="replace"))
        if not public_session.has_transcript or "PAID CASE SESSION" in public_session.text:
            raise ValueError("public Session has no transcript section or exposes a paid paywall")
        session_result = {"session_url": session_url, "session_http_status": status, "session_access": "public-page-checked"}

    return {
        "status": "live-verified",
        "case_id": args.case_id,
        "fingerprint": actual_fingerprint,
        "cases_url": args.cases_url,
        "cases_http_status": cases_status,
        "page_url": args.page_url,
        "page_http_status": page_status,
        "case_page_url": args.case_page_url,
        "case_page_http_status": case_page_status,
        "marker": args.marker,
        "images": image_results,
        "video": video_result,
        "related_skills": relation_results,
        **session_result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases-url", required=True)
    parser.add_argument("--page-url", required=True)
    parser.add_argument("--case-page-url", required=True)
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
