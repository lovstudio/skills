#!/usr/bin/env python3
"""Fetch a public WeChat Official Account article and extract reusable assets."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
BLOCK_TAGS = {
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "li",
    "blockquote",
    "br",
    "section",
    "div",
}


class ContentBlockParser(HTMLParser):
    """Collect the raw HTML of the element with id=js_content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._capture = False
        self._depth = 0
        self.parts: List[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attrs_map = dict(attrs)
        if not self._capture and tag == "div" and attrs_map.get("id") == "js_content":
            self._capture = True
            self._depth = 1
            self.parts.append(self.get_starttag_text() or "")
            return
        if self._capture:
            self._depth += 1
            self.parts.append(self.get_starttag_text() or "")

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        if self._capture:
            self.parts.append(self.get_starttag_text() or "")

    def handle_endtag(self, tag: str) -> None:
        if not self._capture:
            return
        self.parts.append(f"</{tag}>")
        self._depth -= 1
        if self._depth <= 0:
            self._capture = False

    def handle_data(self, data: str) -> None:
        if self._capture:
            self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        if self._capture:
            self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._capture:
            self.parts.append(f"&#{name};")


class TextParser(HTMLParser):
    """Convert article HTML into readable text while preserving block boundaries."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: List[str] = []
        self._skip_stack: List[bool] = []
        self._skip = 0

    def _newline(self) -> None:
        if not self.parts or not self.parts[-1].endswith("\n"):
            self.parts.append("\n")

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attrs_map = dict(attrs)
        style = attrs_map.get("style", "")
        should_skip = tag in {"script", "style"} or any(
            token in style.lower() for token in ("display:none", "visibility:hidden", "opacity:0")
        )
        self._skip_stack.append(should_skip)
        if should_skip:
            self._skip += 1
            return
        if tag in BLOCK_TAGS and self._skip == 0:
            self._newline()

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        attrs_map = dict(attrs)
        style = attrs_map.get("style", "")
        should_skip = tag in {"script", "style"} or any(
            token in style.lower() for token in ("display:none", "visibility:hidden", "opacity:0")
        )
        if should_skip:
            return
        if tag in BLOCK_TAGS and self._skip == 0:
            self._newline()

    def handle_endtag(self, tag: str) -> None:
        if self._skip_stack:
            was_skipping = self._skip_stack.pop()
            if was_skipping:
                self._skip = max(0, self._skip - 1)
                return
        if tag in BLOCK_TAGS and self._skip == 0:
            self._newline()

    def handle_data(self, data: str) -> None:
        if self._skip == 0:
            self.parts.append(data)


def decode_js_string(value: Optional[str]) -> str:
    if value is None:
        return ""
    value = html.unescape(value)
    value = value.replace("\\'", "'").replace('\\"', '"')
    value = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), value)
    return value.strip()


def first_js_string(raw: str, key: str) -> str:
    patterns = (
        rf"var\s+{re.escape(key)}\s*=\s*htmlDecode\(\s*\"((?:\\.|[^\"])*)\"\s*\)",
        rf"var\s+{re.escape(key)}\s*=\s*\"((?:\\.|[^\"])*)\"",
        rf"var\s+{re.escape(key)}\s*=\s*'((?:\\.|[^'])*)'",
        rf'(?:window\.)?{re.escape(key)}\s*[:=]\s*"((?:\\.|[^\"])*)"',
        rf"(?:window\.)?{re.escape(key)}\s*[:=]\s*'((?:\\.|[^'])*)'",
    )
    for pattern in patterns:
        match = re.search(pattern, raw)
        if match:
            return decode_js_string(match.group(1))
    return ""


def fetch_html(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("gb18030", errors="ignore")


def extract_content_block(raw: str) -> str:
    parser = ContentBlockParser()
    try:
        parser.feed(raw)
        parser.close()
    except Exception:
        return ""
    return "".join(parser.parts)


def extract_text(block: str) -> str:
    parser = TextParser()
    try:
        parser.feed(block)
        parser.close()
    except Exception:
        return ""
    text = "".join(parser.parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_images(block: str) -> List[str]:
    urls: List[str] = []
    for pattern in (r'data-src="([^"]+)"', r'src="([^"]+)"'):
        for match in re.finditer(pattern, block):
            url = html.unescape(match.group(1))
            if url.startswith("http") and url not in urls:
                urls.append(url)
    return urls


def safe_slug(value: str) -> str:
    value = re.sub(r"[\\/:*?\"<>|\s]+", "-", value).strip("-")
    return (value or "wechat-article")[:80]


def image_extension(url: str) -> str:
    query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    fmt = (query.get("wx_fmt") or [""])[0].lower()
    if fmt not in {"png", "jpg", "jpeg", "gif", "webp"}:
        fmt = "png"
    return fmt


def download_image(url: str, destination: Path, timeout: int = 30) -> bool:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Referer": "https://mp.weixin.qq.com/",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content = response.read()
        if not content:
            return False
        destination.write_bytes(content)
        return True
    except Exception:
        return False


def build_manifest(
    url: str,
    raw: str,
    output_dir: Path,
    timeout: int,
    download: bool,
) -> Dict[str, object]:
    title = first_js_string(raw, "msg_title")
    description = first_js_string(raw, "msg_desc")
    account = first_js_string(raw, "nickname")
    publish_time = first_js_string(raw, "createTime") or first_js_string(
        raw, "oriCreateTime"
    )
    block = extract_content_block(raw)
    text = extract_text(block)
    images = extract_images(block)

    image_entries: List[Dict[str, object]] = []
    images_dir = output_dir / "images"
    if download and images:
        images_dir.mkdir(parents=True, exist_ok=True)
    for index, image_url in enumerate(images, start=1):
        ext = image_extension(image_url)
        file_name = f"{index:02d}.{ext}"
        relative = f"images/{file_name}"
        destination = images_dir / file_name
        ok = download_image(image_url, destination, timeout) if download else False
        image_entries.append(
            {
                "index": index,
                "url": image_url,
                "file": relative,
                "downloaded": ok,
            }
        )
    image_only = bool(images) and len(text) < 40
    slug = safe_slug(title or "wechat-article")
    manifest_path = output_dir / "manifest.json"
    html_path = output_dir / "article.html"
    html_path.write_text(raw, encoding="utf-8")

    manifest = {
        "schema": "wechat-article/v1",
        "source_url": url,
        "title": title,
        "description": description,
        "account": account,
        "publish_time": publish_time,
        "slug": slug,
        "image_only": image_only,
        "text_chars": len(text),
        "extracted_text": text,
        "images": image_entries,
        "files": {
            "raw_html": str(html_path.name),
            "manifest": str(manifest_path.name),
            "images_dir": "images/",
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="WeChat Official Account article URL")
    parser.add_argument("--output-dir", default=".", help="Output directory")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Only extract metadata and URLs; do not download images",
    )
    args = parser.parse_args()

    if not (
        "mp.weixin.qq.com/s/" in args.url
        or "mp.weixin.qq.com/s?" in args.url
    ):
        print("ERROR: only public mp.weixin.qq.com article URLs are supported", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        raw = fetch_html(args.url, args.timeout)
    except Exception as exc:
        print(f"ERROR: cannot fetch article: {exc}", file=sys.stderr)
        return 3
    if "js_content" not in raw:
        print(
            "ERROR: response does not contain article content; the page may require login or be unavailable",
            file=sys.stderr,
        )
        return 4

    manifest = build_manifest(
        args.url,
        raw,
        output_dir,
        args.timeout,
        not args.no_download,
    )
    summary = {
        "title": manifest["title"],
        "account": manifest["account"],
        "publish_time": manifest["publish_time"],
        "images": len(manifest["images"]),
        "image_only": manifest["image_only"],
        "text_chars": manifest["text_chars"],
        "manifest": str(output_dir / "manifest.json"),
        "raw_html": str(output_dir / "article.html"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
