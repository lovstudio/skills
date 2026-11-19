#!/usr/bin/env python3
"""Collect suanli.cn Open API evidence from the vendor's public Apifox share.

The share publishes one OpenAPI fragment per operation inside each ``api-*.md``
page. This script lists them through the share's ``llms.txt``, extracts every
fragment verbatim, redacts credential-looking example values, and writes one
JSON evidence file for the cli2anything++ suanli adapter. It never sends
credentials and only performs anonymous GET requests against public pages.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

DEFAULT_SHARE_ID = "6aa360d3-d8f2-471e-b841-3a35c33a7b7c"
SHARE_ORIGIN = "https://s.apifox.cn"
DOCS_ORIGIN = "https://docs.suanli.cn"
DOC_PAGES = [
    "api-key/overview",
    "api-key/rsa",
    "llm/quickstart",
    "llm/status-codes",
    "llm/api-key",
    "job-batch/best-practices/api-job",
    "serverless/best-practices/api-autoscaling",
    "serverless/best-practices/task-api-multi-container",
    "distributed-training/overview",
    "distributed-training/tasks",
]
USER_AGENT = "cli2anything-docs-reader"
ENTRY = re.compile(r"^- (?P<folder>.+?) \[(?P<title>[^\]]+)\]\((?P<url>https://s\.apifox\.cn/[^)]+/(?P<id>api-\d+)\.md)\)", re.M)
YAML_BLOCK = re.compile(r"```yaml\n(.*?)\n```", re.S)
# 凭据类请求头的示例值一律清空，形如密钥的字符串一律替换，证据文件里不留任何凭据。
CREDENTIAL_NAMES = {"token", "sign_str", "authorization", "cookie", "x-api-key"}
TOKEN_LIKE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-\d{14}", re.I)


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def read_source(url: str, offline_dir: Path | None, name: str) -> bytes:
    if offline_dir:
        return (offline_dir / name).read_bytes()
    return fetch(url)


def redact(node, counter: list[int]):
    if isinstance(node, dict):
        is_credential_param = str(node.get("name", "")).lower() in CREDENTIAL_NAMES and node.get("in") == "header"
        out = {}
        for key, value in node.items():
            if is_credential_param and key in ("example", "examples", "default") and value not in (None, ""):
                counter[0] += 1
                out[key] = "" if key != "examples" else []
                continue
            out[key] = redact(value, counter)
        return out
    if isinstance(node, list):
        return [redact(item, counter) for item in node]
    if isinstance(node, str) and TOKEN_LIKE.search(node):
        counter[0] += 1
        return TOKEN_LIKE.sub("<redacted>", node)
    return node


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, help="Evidence JSON path to write")
    parser.add_argument("--docs-out", help="Optional JSON path for docs.suanli.cn page hashes")
    parser.add_argument("--share-id", default=DEFAULT_SHARE_ID)
    parser.add_argument("--offline-dir", type=Path, help="Directory holding llms.txt and api-*.md downloaded earlier")
    parser.add_argument("--delay", type=float, default=0.3, help="Seconds between page requests")
    args = parser.parse_args()

    try:
        import yaml  # type: ignore
    except ImportError:
        print("ERROR: PyYAML is required (pip install pyyaml).", file=sys.stderr)
        return 2

    share_url = f"{SHARE_ORIGIN}/{args.share_id}"
    llms = read_source(f"{share_url}/llms.txt", args.offline_dir, "llms.txt")
    entries = [m.groupdict() for m in ENTRY.finditer(llms.decode("utf-8"))]
    if not entries:
        print("ERROR: no api-*.md entries found in llms.txt", file=sys.stderr)
        return 1

    counter = [0]
    docs = []
    for entry in entries:
        raw = read_source(entry["url"], args.offline_dir, f"{entry['id']}.md")
        match = YAML_BLOCK.search(raw.decode("utf-8"))
        if not match:
            print(f"ERROR: {entry['url']} has no OpenAPI Specification block", file=sys.stderr)
            return 1
        fragment = redact(yaml.safe_load(match.group(1)), counter)
        docs.append({
            "apifoxId": entry["id"],
            "title": entry["title"],
            "folder": entry["folder"].replace(" > ", "/"),
            "url": entry["url"],
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "fragment": fragment,
        })
        if not args.offline_dir:
            time.sleep(args.delay)

    evidence = {
        "schema": "suanli-apifox-fragments/v1",
        "shareUrl": share_url,
        "llmsTxt": {"url": f"{share_url}/llms.txt", "sha256": hashlib.sha256(llms).hexdigest()},
        "fetchedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "redaction": {
            "count": counter[0],
            "rule": "header 凭据参数（token、sign_str 等）的示例值清空；任何形如 API 密钥的字符串替换为 <redacted>。",
        },
        "docs": docs,
    }
    Path(args.out).write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out}: {len(docs)} Apifox pages, {counter[0]} redactions")

    if args.docs_out:
        pages = []
        for page in DOC_PAGES:
            url = f"{DOCS_ORIGIN}/{page}.md"
            raw = read_source(url, args.offline_dir, page.replace("/", "_") + ".md")
            title = re.search(r'^title: "(.*)"$', raw.decode("utf-8"), re.M)
            pages.append({"url": f"{DOCS_ORIGIN}/{page}", "markdown": url, "title": title.group(1) if title else page, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
            if not args.offline_dir:
                time.sleep(args.delay)
        Path(args.docs_out).write_text(json.dumps(pages, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.docs_out}: {len(pages)} docs pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
