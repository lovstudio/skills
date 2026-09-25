#!/usr/bin/env python3
"""Render a Markdown table through Mable and return a hosted PNG URL."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_API_BASE = "https://api.lovstudio.ai"
DEFAULT_PROFILE = Path.home() / ".lovstudio" / "skills" / "profile.json"
MODEL_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class Table2ImageError(RuntimeError):
    pass


def read_profile_api_base(profile_path: Path) -> str | None:
    if not profile_path.is_file():
        return None
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        value = (
            profile.get("skills", {})
            .get("lov-table2image", {})
            .get("records", {})
            .get("api_base")
        )
    except (OSError, json.JSONDecodeError, AttributeError):
        return None
    return value.strip() if isinstance(value, str) and value.strip() else None


def resolve_api_base(explicit: str | None, profile_path: Path) -> str:
    value = (
        explicit
        or os.environ.get("MABLE_API_BASE")
        or read_profile_api_base(profile_path)
        or DEFAULT_API_BASE
    )
    value = value.strip().rstrip("/")
    if not re.match(r"^https?://", value, re.IGNORECASE):
        raise Table2ImageError("API 根地址必须以 http:// 或 https:// 开头")
    return value


def read_markdown(input_path: str | None, inline: str | None) -> str:
    if inline is not None:
        text = inline
    elif input_path in (None, "-"):
        text = sys.stdin.read()
    else:
        try:
            text = Path(input_path).expanduser().read_text(encoding="utf-8")
        except OSError as exc:
            raise Table2ImageError(f"无法读取 Markdown 表格：{exc}") from exc
    text = text.strip()
    if not text:
        raise Table2ImageError("Markdown 表格不能为空")
    if len(text) > 30_000:
        raise Table2ImageError("Markdown 表格不能超过 30000 字符")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 3 or not re.match(
        r"^\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?$", lines[1]
    ):
        raise Table2ImageError("输入必须包含表头、分隔行和至少一行数据")
    return text


def read_layout(value: str | None) -> dict[str, Any] | None:
    if value is None:
        return None
    candidate = Path(value).expanduser()
    try:
        raw = candidate.read_text(encoding="utf-8") if candidate.is_file() else value
        parsed = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise Table2ImageError(f"无法解析布局 JSON：{exc}") from exc
    if not isinstance(parsed, dict):
        raise Table2ImageError("布局 JSON 顶层必须是 object")
    return parsed


def request_json(
    url: str,
    payload: dict[str, Any],
    timeout: float,
    token: str,
) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "lov-table2image/0.1.1",
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        detail = exc.read(800).decode("utf-8", errors="replace")
        raise Table2ImageError(f"Mable API HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise Table2ImageError(f"无法连接 Mable API：{exc.reason}") from exc
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Table2ImageError("Mable API 返回了无效 JSON") from exc
    if not isinstance(result, dict):
        raise Table2ImageError("Mable API 响应顶层不是 object")
    required = (
        "image_url",
        "format",
        "width",
        "height",
        "layout_width",
        "model",
        "credits_spent",
        "credits_remaining",
    )
    missing = [key for key in required if key not in result]
    if missing:
        raise Table2ImageError("Mable API 响应缺少字段：" + ", ".join(missing))
    if result.get("format") != "png" or not isinstance(result.get("image_url"), str):
        raise Table2ImageError("Mable API 未返回有效 PNG 地址")
    return result


def download_png(url: str, output: Path, timeout: float) -> int:
    request = Request(
        url,
        headers={"Accept": "image/png", "User-Agent": "lov-table2image/0.1.1"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get_content_type()
            data = response.read()
    except HTTPError as exc:
        detail = exc.read(800).decode("utf-8", errors="replace")
        raise Table2ImageError(f"下载图片 HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise Table2ImageError(f"无法下载图片：{exc.reason}") from exc
    if content_type != "image/png" or not data.startswith(PNG_SIGNATURE):
        raise Table2ImageError("图片响应不是有效 PNG")
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as temporary:
        temporary.write(data)
        temporary_path = Path(temporary.name)
    temporary_path.replace(output)
    return len(data)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="Markdown file; use - or omit for stdin")
    parser.add_argument("--markdown", help="Inline Markdown table")
    parser.add_argument("--model", help="11-character Mable layout model")
    parser.add_argument("--layout-json", help="Layout JSON file or inline JSON object")
    parser.add_argument("--caption", help="Caption text; pass an empty string to hide")
    parser.add_argument("--pixel-ratio", type=int, choices=(1, 2), default=2)
    parser.add_argument("--api-base", help="Mable API base URL")
    parser.add_argument(
        "--token",
        help="LovStudio Access Token or sk_live_ API Key; defaults to MABLE_API_TOKEN",
    )
    parser.add_argument("--profile", type=Path, help="Shared user-profile JSON path")
    parser.add_argument("--output", type=Path, help="Download the returned PNG here")
    parser.add_argument("--timeout", type=float, default=30.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.markdown is not None and args.input is not None:
        parser.error("input 与 --markdown 只能提供一个")
    if args.model and args.layout_json:
        parser.error("--model 与 --layout-json 只能提供一个")
    if args.model and not MODEL_RE.fullmatch(args.model):
        parser.error("--model 必须是 11 位 URL-safe 字符")
    if args.timeout <= 0:
        parser.error("--timeout 必须大于 0")

    try:
        profile_path = args.profile or Path(
            os.environ.get("SKILL_PROFILE_PATH", str(DEFAULT_PROFILE))
        ).expanduser()
        api_base = resolve_api_base(args.api_base, profile_path)
        token = (args.token or os.environ.get("MABLE_API_TOKEN") or "").strip()
        if not token:
            raise Table2ImageError(
                "缺少 LovStudio 凭据；请设置 MABLE_API_TOKEN，或传入 --token"
            )
        payload: dict[str, Any] = {
            "markdown": read_markdown(args.input, args.markdown),
            "pixel_ratio": args.pixel_ratio,
        }
        if args.model:
            payload["model"] = args.model
        layout = read_layout(args.layout_json)
        if layout is not None:
            payload["layout"] = layout
        if args.caption is not None:
            payload["caption"] = args.caption

        result = request_json(
            f"{api_base}/mable/images",
            payload,
            args.timeout,
            token,
        )
        if args.output:
            output = args.output.expanduser().resolve()
            result["bytes"] = download_png(result["image_url"], output, args.timeout)
            result["output_path"] = str(output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Table2ImageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
