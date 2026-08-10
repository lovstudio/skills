#!/usr/bin/env python3
"""Search enabled qBittorrent plugins and emit normalized Media Fetch candidates."""

from __future__ import annotations

import argparse
import base64
import http.cookiejar
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class QBitClient:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        payload = self.request(
            "/api/v2/auth/login", {"username": username, "password": password}, raw=True
        )
        if payload.strip() not in {"", "Ok."}:
            raise RuntimeError(f"qBittorrent login failed: {payload[:120]}")

    def request(
        self, path: str, data: dict[str, Any] | None = None, raw: bool = False
    ) -> Any:
        encoded = None
        if data is not None:
            encoded = urllib.parse.urlencode(data).encode("utf-8")
        request = urllib.request.Request(self.base_url + path, data=encoded)
        request.add_header("Referer", self.base_url)
        try:
            with self.opener.open(request, timeout=20) as response:
                text = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"qBittorrent HTTP {exc.code} for {path}: {detail[:300]}") from exc
        if raw:
            return text
        return json.loads(text) if text else {}


def info_hash(uri: str) -> str | None:
    match = re.search(r"(?:[?&]xt=urn:btih:)([A-Za-z0-9]+)", uri, re.I)
    if not match:
        return None
    value = match.group(1)
    if re.fullmatch(r"[0-9A-Fa-f]{40}", value):
        return value.upper()
    if re.fullmatch(r"[A-Z2-7]{32}", value.upper()):
        return base64.b32decode(value.upper()).hex().upper()
    return value.upper()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--plugins", default="all")
    parser.add_argument("--category", default="all")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--title")
    parser.add_argument("--year", type=int)
    parser.add_argument("--media-type", default="movie")
    parser.add_argument(
        "--results-json",
        type=Path,
        help="Normalize a saved qBittorrent search response without connecting",
    )
    args = parser.parse_args()

    if args.results_json:
        payload = json.loads(args.results_json.read_text(encoding="utf-8"))
        search_id = None
        status = "Fixture"
    else:
        base_url = os.environ.get("QBITTORRENT_URL", "http://127.0.0.1:8080")
        username = os.environ.get("QBITTORRENT_USERNAME", "admin")
        password = os.environ.get("QBITTORRENT_PASSWORD", "")
        if not password:
            raise SystemExit("ERROR: QBITTORRENT_PASSWORD is required")
        client = QBitClient(base_url, username, password)
        started = client.request(
            "/api/v2/search/start",
            {"pattern": args.query, "plugins": args.plugins, "category": args.category},
        )
        search_id = int(started.get("id"))
        deadline = time.monotonic() + max(5, args.timeout)
        status = "Running"
        try:
            while time.monotonic() < deadline:
                statuses = client.request(f"/api/v2/search/status?id={search_id}")
                row = statuses[0] if isinstance(statuses, list) and statuses else {}
                status = str(row.get("status") or "")
                if status.lower() not in {"running", "queued"}:
                    break
                time.sleep(2)
            client.request("/api/v2/search/stop", {"id": search_id}, raw=True)
            payload = client.request(
                f"/api/v2/search/results?id={search_id}&limit={max(1, args.limit)}&offset=0"
            )
        finally:
            try:
                client.request("/api/v2/search/delete", {"id": search_id}, raw=True)
            except RuntimeError:
                pass

    observed = datetime.now(timezone.utc).isoformat()
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(payload.get("results") or []):
        if not isinstance(row, dict):
            continue
        uri = str(row.get("fileUrl") or row.get("file_url") or "")
        if not uri:
            continue
        hash_value = info_hash(uri)
        key = hash_value or uri
        if key in seen:
            continue
        seen.add(key)
        uri_without_query = uri.split("?", 1)[0].lower()
        if uri.lower().startswith("magnet:"):
            transport_inputs = ["magnet"]
        elif uri_without_query.endswith(".torrent") and uri.lower().startswith(("http://", "https://")):
            transport_inputs = ["torrent-url"]
        elif uri_without_query.endswith(".torrent"):
            transport_inputs = ["torrent-file"]
        else:
            transport_inputs = ["url"]
        seeders = int(row.get("nbSeeders") or row.get("seeders") or 0)
        leechers = int(row.get("nbLeechers") or row.get("leechers") or 0)
        candidates.append(
            {
                "id": f"qbt-{index + 1}",
                "name": str(row.get("fileName") or row.get("file_name") or key),
                "uri": uri,
                "info_hash": hash_value,
                "transport_inputs": transport_inputs,
                "source": str(row.get("siteUrl") or row.get("site_url") or "qBittorrent plugin"),
                "source_url": str(row.get("descrLink") or row.get("descr_link") or ""),
                "observed_at": observed,
                "size_bytes": int(row.get("fileSize") or row.get("file_size") or 0),
                "seeders": seeders,
                "leechers": leechers,
                "source_health": {
                    "advertised_seeders": seeders,
                    "advertised_leechers": leechers,
                    "observed_peers": None,
                    "observed_at": observed,
                    "sustained_speed_bytes_per_second": None,
                    "metadata_ready": False,
                },
                "metadata_confidence": "filename",
                "trusted_source": False,
            }
        )
    document = {
        "schema_version": "1.0",
        "query": {
            "title": args.title or args.query,
            "year": args.year,
            "media_type": args.media_type,
            "requested_editions": [],
        },
        "search": {"pattern": args.query, "plugins": args.plugins, "status": status},
        "edition_facts": [],
        "candidates": candidates,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"search_id": search_id, "status": status, "candidates": len(candidates), "output": str(args.output)}, ensure_ascii=False, indent=2))
    return 0 if candidates else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
