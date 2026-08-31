#!/usr/bin/env python3
"""Discover and recover public X/Twitter post evidence without account login."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import html
import json
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable


USER_AGENT = "lov-search-twitter/0.1 (+local evidence recovery)"
STATUS_URL_RE = re.compile(
    r"https?://(?:www\.)?(?:x|twitter)\.com/([A-Za-z0-9_]{1,15})/(?:status|statuses)/(\d+)",
    re.IGNORECASE,
)
STATUS_PATH_RE = re.compile(r"/(?:status|statuses)/(\d+)")
SHORT_URL_RE = re.compile(r"https?://t\.co/[A-Za-z0-9]+")
JSON_TEXT_RE = re.compile(r'"(?:full_text|text)"\s*:\s*("(?:[^"\\]|\\.)*")')
TWEET_DIV_RE = re.compile(
    r'<div[^>]+data-testid=["\']tweetText["\'][^>]*>(.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")
URL_RE = re.compile(r"https?://\S+")


class MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.values: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "meta":
            return
        data = {key.lower(): value for key, value in attrs if value is not None}
        key = data.get("property") or data.get("name")
        content = data.get("content")
        if key and content:
            self.values[key.lower()] = html.unescape(content)


@dataclass(frozen=True)
class Capture:
    timestamp: str
    original: str
    archive_url: str
    metadata: dict[str, Any]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def request_bytes(
    url: str,
    *,
    timeout: float,
    headers: dict[str, str] | None = None,
) -> bytes:
    merged = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if headers:
        merged.update(headers)
    request = urllib.request.Request(url, headers=merged)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def safe_request_json(url: str, timeout: float) -> tuple[Any | None, str | None]:
    try:
        return json.loads(request_bytes(url, timeout=timeout).decode("utf-8")), None
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError, socket.timeout, json.JSONDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def canonical_url(handle: str, status_id: str) -> str:
    return f"https://x.com/{handle}/status/{status_id}"


def discover_references(text: str) -> dict[str, Any]:
    posts: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for match in STATUS_URL_RE.finditer(text):
        handle, status_id = match.groups()
        key = (handle.lower(), status_id)
        if key in seen:
            continue
        seen.add(key)
        posts.append(
            {
                "handle": handle,
                "status_id": status_id,
                "url": canonical_url(handle, status_id),
                "observed_url": match.group(0).rstrip(".,;:)]"),
            }
        )
    return {
        "type": "candidate_inventory",
        "generated_at": now_iso(),
        "posts": posts,
        "short_urls": list(dict.fromkeys(SHORT_URL_RE.findall(text))),
        "coverage_note": "Candidates extracted from supplied text; this is not a complete account inventory.",
    }


def parse_post_text(body: bytes) -> tuple[str | None, str | None]:
    page = body.decode("utf-8", errors="replace")
    parser = MetaParser()
    try:
        parser.feed(page)
    except Exception:
        pass
    for key in ("og:description", "twitter:description"):
        value = parser.values.get(key)
        if value and value.strip():
            return value.strip(), f"meta:{key}"
    for match in JSON_TEXT_RE.finditer(page):
        try:
            value = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(value, str) and value.strip():
            return value.strip(), "embedded-json"
    match = TWEET_DIV_RE.search(page)
    if match:
        value = html.unescape(TAG_RE.sub("", match.group(1))).strip()
        if value:
            return value, "tweetText-html"
    return None, None


def fetch_fx(handle: str, status_id: str, timeout: float) -> dict[str, Any]:
    endpoint = f"https://api.fxtwitter.com/{urllib.parse.quote(handle)}/status/{status_id}"
    payload, error = safe_request_json(endpoint, timeout)
    tweet = payload.get("tweet") if isinstance(payload, dict) else None
    author = tweet.get("author") if isinstance(tweet, dict) else None
    ok = isinstance(tweet, dict) and bool(tweet.get("text"))
    return {
        "provider": "FxTwitter",
        "endpoint": endpoint,
        "ok": ok,
        "text": tweet.get("text") if isinstance(tweet, dict) else None,
        "created_at": tweet.get("created_at") if isinstance(tweet, dict) else None,
        "author": author.get("screen_name") if isinstance(author, dict) else None,
        "error": None
        if ok
        else error or (payload.get("message") if isinstance(payload, dict) else None),
    }


def fetch_vx(handle: str, status_id: str, timeout: float) -> dict[str, Any]:
    endpoint = f"https://api.vxtwitter.com/{urllib.parse.quote(handle)}/status/{status_id}"
    payload, error = safe_request_json(endpoint, timeout)
    return {
        "provider": "VXTwitter",
        "endpoint": endpoint,
        "ok": isinstance(payload, dict) and bool(payload.get("text")),
        "text": payload.get("text") if isinstance(payload, dict) else None,
        "created_at": payload.get("date") if isinstance(payload, dict) else None,
        "author": payload.get("user_screen_name") if isinstance(payload, dict) else None,
        "error": error,
    }


def fetch_live(handle: str, status_id: str, timeout: float) -> list[dict[str, Any]]:
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = (
            pool.submit(fetch_fx, handle, status_id, timeout),
            pool.submit(fetch_vx, handle, status_id, timeout),
        )
        return [future.result() for future in futures]


def cdx_query(pattern: str, timeout: float) -> list[list[str]]:
    params = urllib.parse.urlencode(
        {
            "url": pattern,
            "output": "json",
            "filter": "statuscode:200",
            "fl": "timestamp,original,mimetype,statuscode,digest",
            "collapse": "digest",
        }
    )
    data, _ = safe_request_json(f"https://web.archive.org/cdx/search/cdx?{params}", timeout)
    if not isinstance(data, list) or len(data) < 2:
        return []
    return [row for row in data[1:] if isinstance(row, list) and len(row) >= 5]


def capture_from_row(row: list[str]) -> Capture | None:
    timestamp, original, mimetype, statuscode, digest = row[:5]
    if not STATUS_PATH_RE.search(original):
        return None
    return Capture(
        timestamp=timestamp,
        original=original,
        archive_url=f"https://web.archive.org/web/{timestamp}id_/{original}",
        metadata={"mimetype": mimetype, "statuscode": statuscode, "digest": digest},
    )


def wayback_captures(handle: str, status_id: str, timeout: float) -> list[Capture]:
    captures: list[Capture] = []
    for domain in ("x.com", "twitter.com", "www.twitter.com"):
        for row in cdx_query(f"{domain}/{handle}/status/{status_id}", timeout):
            capture = capture_from_row(row)
            if capture:
                captures.append(capture)
    return captures


def recover_wayback(captures: Iterable[Capture], timeout: float) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for capture in captures:
        try:
            body = request_bytes(capture.archive_url, timeout=timeout)
            text, extractor = parse_post_text(body)
            results.append(
                {
                    "provider": "Internet Archive",
                    "endpoint": capture.archive_url,
                    "ok": bool(text),
                    "text": text,
                    "extractor": extractor,
                    "timestamp": capture.timestamp,
                    "metadata": capture.metadata,
                    "error": None if text else "capture contains no recoverable post text",
                }
            )
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            results.append(
                {
                    "provider": "Internet Archive",
                    "endpoint": capture.archive_url,
                    "ok": False,
                    "text": None,
                    "timestamp": capture.timestamp,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
    return results


def common_crawl_indices(timeout: float, count: int) -> list[str]:
    data, _ = safe_request_json("https://index.commoncrawl.org/collinfo.json", timeout)
    if not isinstance(data, list):
        return []
    return [item["id"] for item in data[:count] if isinstance(item, dict) and item.get("id")]


def common_crawl_records(url: str, timeout: float, count: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index in common_crawl_indices(timeout, count):
        params = urllib.parse.urlencode({"url": url, "output": "json", "filter": "status:200"})
        endpoint = f"https://index.commoncrawl.org/{index}-index?{params}"
        try:
            lines = request_bytes(endpoint, timeout=timeout).decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, socket.timeout):
            continue
        for line in lines.splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict) and record.get("filename"):
                record["index"] = index
                records.append(record)
    return records


def common_crawl_body(record: dict[str, Any], timeout: float) -> bytes:
    offset, length = int(record["offset"]), int(record["length"])
    endpoint = f"https://data.commoncrawl.org/{record['filename']}"
    compressed = request_bytes(
        endpoint,
        timeout=timeout,
        headers={"Range": f"bytes={offset}-{offset + length - 1}"},
    )
    decoded = gzip.decompress(compressed)
    parts = decoded.split(b"\r\n\r\n", 2)
    return parts[2] if len(parts) == 3 else decoded


def recover_common_crawl(
    handle: str, status_id: str, timeout: float, index_count: int
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for domain in ("https://x.com", "https://twitter.com"):
        original = f"{domain}/{handle}/status/{status_id}"
        for record in common_crawl_records(original, timeout, index_count):
            try:
                text, extractor = parse_post_text(common_crawl_body(record, timeout))
                results.append(
                    {
                        "provider": "Common Crawl",
                        "endpoint": original,
                        "ok": bool(text),
                        "text": text,
                        "extractor": extractor,
                        "timestamp": record.get("timestamp"),
                        "index": record.get("index"),
                        "warc": record.get("filename"),
                        "error": None if text else "WARC contains no recoverable post text",
                    }
                )
            except (OSError, urllib.error.URLError, TimeoutError, socket.timeout) as exc:
                results.append(
                    {
                        "provider": "Common Crawl",
                        "endpoint": original,
                        "ok": False,
                        "text": None,
                        "index": record.get("index"),
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
    return results


def normalize_for_compare(value: str) -> str:
    return " ".join(URL_RE.sub("<URL>", value).split())


def select_text(results: list[dict[str, Any]]) -> tuple[str | None, str, list[str]]:
    successful = [item for item in results if item.get("ok") and item.get("text")]
    variants = list(dict.fromkeys(str(item["text"]) for item in successful))
    if not successful:
        return None, "unrecovered", variants
    groups: dict[str, list[str]] = {}
    for item in successful:
        value = str(item["text"])
        groups.setdefault(normalize_for_compare(value), []).append(value)
    _, best_values = max(groups.items(), key=lambda pair: (len(pair[1]), len(pair[0])))
    selected = max(best_values, key=len)
    if len(groups) > 1:
        return selected, "conflict", variants
    confidence = "two-renderer-match" if len(best_values) >= 2 else "single-source"
    return selected, confidence, variants


def recover_status(
    handle: str,
    status_id: str,
    timeout: float,
    use_common_crawl: bool,
    cc_indices: int,
) -> dict[str, Any]:
    live = fetch_live(handle, status_id, timeout)
    archive: list[dict[str, Any]] = []
    if not any(item.get("ok") for item in live):
        archive.extend(recover_wayback(wayback_captures(handle, status_id, timeout), timeout))
        if use_common_crawl:
            archive.extend(recover_common_crawl(handle, status_id, timeout, cc_indices))
    text, confidence, variants = select_text(live + archive)
    live_ok = any(item.get("ok") for item in live)
    archive_ok = any(item.get("ok") for item in archive)
    provenance = "live_original" if live_ok else "archived_original" if archive_ok else "unrecovered"
    return {
        "type": "post_evidence",
        "handle": handle,
        "status_id": status_id,
        "url": canonical_url(handle, status_id),
        "retrieved_at": now_iso(),
        "status": "recovered" if text else "not_recovered",
        "provenance": provenance,
        "confidence": confidence,
        "verbatim_text": text,
        "text_variants": variants,
        "live_sources": live,
        "archive_sources": archive,
    }


def read_status_ids(values: list[str], ids_file: str | None) -> list[str]:
    collected = list(values)
    if ids_file:
        collected.extend(Path(ids_file).read_text(encoding="utf-8").splitlines())
    return list(dict.fromkeys(value.strip() for value in collected if value.strip().isdigit()))


def screenshot_evidence(args: argparse.Namespace) -> dict[str, Any]:
    image = Path(args.image).expanduser().resolve()
    payload = image.read_bytes()
    ocr_text = Path(args.ocr_file).read_text(encoding="utf-8") if args.ocr_file else None
    return {
        "type": "image_evidence",
        "provenance": args.kind,
        "confidence": "partial" if args.truncated else "single-source",
        "source_url": args.source_url,
        "retrieved_at": now_iso(),
        "image_path": str(image),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "parent_sha256": args.parent_sha256,
        "ocr_text": ocr_text,
        "ocr_is_derived": bool(ocr_text),
        "notes": args.notes,
    }


def write_json(data: Any, pretty: bool) -> None:
    if pretty:
        json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    elif isinstance(data, list):
        for item in data:
            print(json.dumps(item, ensure_ascii=False))
    else:
        print(json.dumps(data, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover", help="extract X status URLs and t.co links from text")
    discover.add_argument("--input", required=True, help="UTF-8 text or HTML file")
    discover.add_argument("--pretty", action="store_true")

    recover = subparsers.add_parser("recover", help="recover known public status IDs")
    recover.add_argument("handle", help="X/Twitter handle without @")
    recover.add_argument("status_id", nargs="*")
    recover.add_argument("--ids-file")
    recover.add_argument("--common-crawl", action="store_true")
    recover.add_argument("--cc-indices", type=int, default=12)
    recover.add_argument("--timeout", type=float, default=20.0)
    recover.add_argument("--pretty", action="store_true")

    evidence = subparsers.add_parser("evidence", help="register screenshot or image evidence")
    evidence.add_argument("image")
    evidence.add_argument(
        "--kind",
        required=True,
        choices=("embedded_card", "screenshot_copy", "media_quote", "media_paraphrase"),
    )
    evidence.add_argument("--source-url", required=True)
    evidence.add_argument("--ocr-file")
    evidence.add_argument("--parent-sha256")
    evidence.add_argument("--truncated", action="store_true")
    evidence.add_argument("--notes", default="")
    evidence.add_argument("--pretty", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "discover":
        data = discover_references(Path(args.input).read_text(encoding="utf-8", errors="replace"))
        write_json(data, args.pretty)
        return 0
    if args.command == "evidence":
        write_json(screenshot_evidence(args), args.pretty)
        return 0
    status_ids = read_status_ids(args.status_id, args.ids_file)
    if not status_ids:
        print("No numeric status IDs supplied.", file=sys.stderr)
        return 2
    results = [
        recover_status(
            args.handle.lstrip("@"),
            status_id,
            args.timeout,
            args.common_crawl,
            args.cc_indices,
        )
        for status_id in status_ids
    ]
    write_json(results, args.pretty)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
