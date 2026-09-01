#!/usr/bin/env python3
"""Create and verify a WeChat Official Account draft through uni-api.

Secrets are resolved from lov-env-management and are never accepted as CLI
arguments, printed, or written into the receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from publication_artifacts import ArtifactContractError, validate_cover_composition_receipt
from editorial_components import EditorialComponentError, validate_editorial_components
from preflight_article import _benchmark_reproducibility_errors, _body_hero_errors


DEFAULT_GATEWAY_BASE = "https://api.lovstudio.ai/wechat/official-account"
DEFAULT_ENV_MANAGER_CANDIDATES = (
    Path.home() / "lovstudio/coding/skills/env-management-skill/scripts/env_manager.py",
    Path.home() / ".agents/skills/lov-env-management/scripts/env_manager.py",
)
USER_AGENT = "LovStudio-WeChat-Gateway-Publisher/1.0"
WECHAT_VISIBLE_TEXT_LIMIT = 20_000
WECHAT_HTML_BYTE_LIMIT = 1_000_000


class GatewayPublishError(RuntimeError):
    def __init__(self, stage: str, message: str, *, status: int | None = None):
        super().__init__(message)
        self.stage = stage
        self.status = status


@dataclass(frozen=True)
class BodyImage:
    placeholder: str
    path: Path
    alt: str


@dataclass(frozen=True)
class ManagedSecrets:
    app_secret: str
    gateway_api_key: str


LOVPEN_IMAGE_SRC_RE = re.compile(
    r"(<img\b[^>]*?(?<![-:\w])src\s*=\s*)([\"'])(.*?)\2",
    re.IGNORECASE | re.DOTALL,
)
LOVPEN_FIDELITY_KEYS = (
    "inlineStyleAttributes",
    "classAttributes",
    "spanTags",
    "tableTags",
    "imageTags",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_wechat_content_size(content_html: str) -> tuple[int, int]:
    from bs4 import BeautifulSoup

    visible_text_chars = len(BeautifulSoup(content_html, "html.parser").get_text("", strip=True))
    html_bytes = len(content_html.encode("utf-8"))
    if visible_text_chars >= WECHAT_VISIBLE_TEXT_LIMIT:
        raise GatewayPublishError(
            "preflight",
            f"渲染后的可见正文为 {visible_text_chars} 字符，需少于 {WECHAT_VISIBLE_TEXT_LIMIT:,} 字符。",
        )
    if html_bytes >= WECHAT_HTML_BYTE_LIMIT:
        raise GatewayPublishError(
            "preflight",
            f"上传后的正文 HTML 为 {html_bytes} UTF-8 字节，需小于 {WECHAT_HTML_BYTE_LIMIT:,} 字节。",
        )
    return visible_text_chars, html_bytes


def parse_frontmatter(markdown: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^\s*---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$", markdown)
    if not match:
        return {}, markdown
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key.strip()] = value
    return values, match.group(2)


def render_inline(value: str) -> str:
    escaped = html.escape(value.strip(), quote=False)
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        lambda match: f'<a href="{html.escape(match.group(2), quote=True)}">{match.group(1)}</a>',
        escaped,
    )
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    return escaped


def _table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_table_separator(line: str) -> bool:
    cells = _table_cells(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def render_compact_markdown(markdown_path: Path) -> tuple[str, list[BodyImage], dict[str, str]]:
    raw = markdown_path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(raw)
    lines = body.splitlines()
    blocks: list[str] = ["<section>"]
    images: list[BodyImage] = []
    index = 0

    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            index += 1
            continue

        image_match = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if image_match:
            placeholder = f"__LOV_WECHAT_IMAGE_{len(images):03d}__"
            image_path = Path(image_match.group(2))
            if not image_path.is_absolute():
                image_path = (markdown_path.parent / image_path).resolve()
            images.append(BodyImage(placeholder, image_path, image_match.group(1)))
            blocks.append(f'<img src="{placeholder}" width="100%">')
            index += 1
            continue

        heading_match = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading_match:
            level = len(heading_match.group(1))
            text = render_inline(heading_match.group(2))
            if level == 1:
                index += 1
                continue
            if level in (2, 3):
                blocks.append(f'<h2 style="margin-top:28px">{text}</h2>')
            else:
                blocks.append(f"<h3>{text}</h3>")
            index += 1
            continue

        if stripped.startswith(">"):
            quote_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(render_inline(lines[index].strip()[1:].strip()))
                index += 1
            blocks.append(
                f'<blockquote>{"<br>".join(quote_lines)}</blockquote>'
            )
            continue

        if stripped.startswith("|") and index + 1 < len(lines) and _is_table_separator(lines[index + 1]):
            rows = [_table_cells(stripped)]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(_table_cells(lines[index]))
                index += 1
            header = rows[0]
            blocks.append("<table>")
            blocks.append("<thead><tr>" + "".join(f"<th>{render_inline(cell)}</th>" for cell in header) + "</tr></thead><tbody>")
            for row in rows[1:]:
                blocks.append("<tr>" + "".join(f"<td>{render_inline(cell)}</td>" for cell in row) + "</tr>")
            blocks.append("</tbody></table>")
            continue

        if re.match(r"^[-*]\s+", stripped):
            items: list[str] = []
            while index < len(lines):
                item_match = re.match(r"^[-*]\s+(.+)$", lines[index].strip())
                if not item_match:
                    break
                items.append(render_inline(item_match.group(1)))
                index += 1
            blocks.append("<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>")
            continue

        if stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**"):
            caption = render_inline(stripped[1:-1])
            blocks.append(f"<small><em>{caption}</em></small><br>")
            index += 1
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < len(lines) and lines[index].strip():
            candidate = lines[index].strip()
            if (
                re.match(r"^(#{1,4})\s+", candidate)
                or candidate.startswith(">")
                or candidate.startswith("|")
                or re.match(r"^[-*]\s+", candidate)
                or re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", candidate)
            ):
                break
            paragraph_lines.append(candidate)
            index += 1
        blocks.append(f'<p>{render_inline(" ".join(paragraph_lines))}</p>')

    blocks.append("</section>")
    return "".join(blocks), images, frontmatter


def lovpen_fidelity_metrics(content_html: str) -> dict[str, int]:
    try:
        from bs4 import BeautifulSoup
    except ImportError as error:
        raise GatewayPublishError(
            "lovpen_validation",
            "缺少 beautifulsoup4，无法验证 Lovpen 微信 HTML 的结构保真度。",
        ) from error

    soup = BeautifulSoup(content_html, "html.parser")
    tags = soup.find_all(True)
    return {
        "inlineStyleAttributes": sum(1 for tag in tags if tag.has_attr("style")),
        "classAttributes": sum(1 for tag in tags if tag.has_attr("class")),
        "spanTags": len(soup.find_all("span")),
        "tableTags": len(soup.find_all("table")),
        "imageTags": len(soup.find_all("img")),
    }


def lovpen_fidelity_fingerprint(content_html: str) -> str:
    normalized = LOVPEN_IMAGE_SRC_RE.sub(
        lambda match: f'{match.group(1)}{match.group(2)}__LOV_IMAGE_SRC__{match.group(2)}',
        content_html,
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _resolve_lovpen_image_path(source: str, markdown_path: Path) -> Path:
    decoded_source = html.unescape(source).strip()
    if not decoded_source:
        raise GatewayPublishError("lovpen_validation", "Lovpen 微信正文中存在空的图片 src。")
    if decoded_source.startswith("//"):
        raise GatewayPublishError(
            "lovpen_validation",
            f"Lovpen 微信正文包含远程图片，必须先保存为本地 JPG/PNG：{decoded_source}",
        )

    parsed = urllib.parse.urlparse(decoded_source)
    if parsed.scheme == "file":
        image_path = Path(urllib.parse.unquote(parsed.path))
    elif parsed.scheme:
        raise GatewayPublishError(
            "lovpen_validation",
            f"Lovpen 微信正文包含非本地图片，必须先保存为本地 JPG/PNG：{decoded_source}",
        )
    else:
        image_path = Path(urllib.parse.unquote(parsed.path))
        if not image_path.is_absolute():
            image_path = markdown_path.parent / image_path
    return image_path.expanduser().resolve()


def render_lovpen_wechat_html(
    lovpen_html_path: Path,
    markdown_path: Path,
) -> tuple[str, list[BodyImage], str, dict[str, int], str]:
    try:
        from bs4 import BeautifulSoup
    except ImportError as error:
        raise GatewayPublishError(
            "lovpen_validation",
            "缺少 beautifulsoup4，无法验证 Lovpen 微信 HTML。",
        ) from error

    lovpen_html_path = lovpen_html_path.expanduser().resolve()
    if not lovpen_html_path.is_file():
        raise GatewayPublishError("lovpen_validation", f"Lovpen 微信 HTML 不存在：{lovpen_html_path}")
    lovpen_source = lovpen_html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(lovpen_source, "html.parser")
    roots = soup.select("section.lovpen-renderer")
    if len(roots) != 1 or roots[0].parent is not soup or soup.find() is not roots[0]:
        raise GatewayPublishError(
            "lovpen_validation",
            "Lovpen HTML 不是唯一的微信复制态 section.lovpen-renderer；请使用 lovpen-cli render --format wechat 重新生成。",
        )
    disallowed_style = next(
        (
            style
            for style in soup.find_all("style")
            if style.find_parent("mp-common-videosnap") is None
        ),
        None,
    )
    if disallowed_style or soup.find("script") or soup.find("link", rel=lambda value: value and "stylesheet" in value):
        raise GatewayPublishError(
            "lovpen_validation",
            "Lovpen 微信 HTML 含正文级外部样式或脚本；仅允许原生视频号组件 Shadow DOM 内的隔离样式。",
        )

    metrics = lovpen_fidelity_metrics(lovpen_source)
    fingerprint = lovpen_fidelity_fingerprint(lovpen_source)
    if metrics["inlineStyleAttributes"] == 0:
        raise GatewayPublishError(
            "lovpen_validation",
            "Lovpen 微信 HTML 没有内联样式；请使用 --format wechat 重新生成。",
        )

    matched_sources: list[str] = []
    images: list[BodyImage] = []

    def replace_image_src(match: re.Match[str]) -> str:
        source = match.group(3)
        matched_sources.append(source)
        placeholder = f"__LOV_WECHAT_IMAGE_{len(images):03d}__"
        image_path = _resolve_lovpen_image_path(source, markdown_path)
        images.append(BodyImage(placeholder, image_path, ""))
        return f"{match.group(1)}{match.group(2)}{placeholder}{match.group(2)}"

    content_html = LOVPEN_IMAGE_SRC_RE.sub(replace_image_src, lovpen_source)
    if len(matched_sources) != metrics["imageTags"]:
        raise GatewayPublishError(
            "lovpen_validation",
            "Lovpen 微信正文中存在缺少 src 或无法安全识别 src 的图片。",
        )
    projected_metrics = lovpen_fidelity_metrics(content_html)
    if projected_metrics != metrics or lovpen_fidelity_fingerprint(content_html) != fingerprint:
        raise GatewayPublishError(
            "lovpen_validation",
            "替换 Lovpen 本地图片占位符时结构或样式发生变化。",
        )
    return content_html, images, "lovpen-wechat-copy", metrics, fingerprint


def verify_lovpen_fidelity(
    content_html: str,
    expected_metrics: dict[str, int],
    expected_fingerprint: str,
) -> dict[str, int]:
    actual = lovpen_fidelity_metrics(content_html)
    actual_fingerprint = lovpen_fidelity_fingerprint(content_html)
    if (
        any(actual[key] != expected_metrics[key] for key in LOVPEN_FIDELITY_KEYS)
        or actual_fingerprint != expected_fingerprint
    ):
        raise GatewayPublishError(
            "lovpen_fidelity",
            "上传图片 URL 后 Lovpen HTML 的非图片内容发生变化："
            f"expectedMetrics={expected_metrics}, actualMetrics={actual}, "
            f"expectedFingerprint={expected_fingerprint}, actualFingerprint={actual_fingerprint}",
        )
    return actual


def _css_properties(style: str | None) -> dict[str, str]:
    properties: dict[str, str] = {}
    for declaration in (style or "").split(";"):
        if ":" not in declaration:
            continue
        name, value = declaration.split(":", 1)
        properties[name.strip().lower()] = " ".join(value.split()).lower()
    return properties


def _normalized_visible_text(content_html: str) -> str:
    from bs4 import BeautifulSoup

    text = BeautifulSoup(content_html, "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", "", text)


def _unwrap_only_removed_anchors(source_soup: Any, remote_soup: Any) -> int:
    """Mirror WeChat unwrapping only the anchors absent from remote HTML."""
    source_tags = source_soup.find_all(True)
    remote_tags = remote_soup.find_all(True)
    removed: list[Any] = []
    source_index = 0
    remote_index = 0

    while source_index < len(source_tags) and remote_index < len(remote_tags):
        source_tag = source_tags[source_index]
        remote_tag = remote_tags[remote_index]
        if source_tag.name == remote_tag.name:
            source_index += 1
            remote_index += 1
            continue
        if source_tag.name == "a":
            removed.append(source_tag)
            source_index += 1
            continue
        return 0

    while source_index < len(source_tags) and source_tags[source_index].name == "a":
        removed.append(source_tags[source_index])
        source_index += 1
    if source_index != len(source_tags) or remote_index != len(remote_tags):
        return 0

    for anchor in removed:
        anchor.unwrap()
    return len(removed)


def _normalize_native_video_components(source_soup: Any, remote_soup: Any) -> int:
    """Validate Channels identity, then ignore WeChat-owned shadow markup."""
    source_videos = source_soup.find_all("mp-common-videosnap")
    remote_videos = remote_soup.find_all("mp-common-videosnap")
    if len(source_videos) != len(remote_videos):
        raise GatewayPublishError(
            "draft_get",
            "微信远端正文的视频号组件数量与提交内容不一致。",
        )

    identity_attributes = (
        "data-id",
        "data-nonceid",
        "data-username",
        "data-pluginname",
        "data-type",
    )
    for index, (source_video, remote_video) in enumerate(zip(source_videos, remote_videos)):
        changed = [
            name
            for name in identity_attributes
            if source_video.get(name) != remote_video.get(name)
        ]
        if changed:
            raise GatewayPublishError(
                "draft_get",
                f"微信远端正文第 {index + 1} 个视频号组件身份字段不一致：{changed}",
            )
        source_video.clear()
        remote_video.clear()
    return len(source_videos)


def audit_remote_lovpen_fidelity(
    submitted_html: str,
    remote_html: str,
) -> dict[str, Any]:
    from bs4 import BeautifulSoup

    source_soup = BeautifulSoup(submitted_html, "html.parser")
    remote_soup = BeautifulSoup(remote_html, "html.parser")
    normalized_native_videos = _normalize_native_video_components(source_soup, remote_soup)
    removed_anchors = 0
    source_tags = source_soup.find_all(True)
    remote_tags = remote_soup.find_all(True)

    if [tag.name for tag in source_tags] != [tag.name for tag in remote_tags]:
        removed_anchors = _unwrap_only_removed_anchors(source_soup, remote_soup)
        source_tags = source_soup.find_all(True)

    source_names = [tag.name for tag in source_tags]
    remote_names = [tag.name for tag in remote_tags]
    if source_names != remote_names:
        raise GatewayPublishError(
            "draft_get",
            "微信远端正文的标签序列与提交内容不一致，且不能仅由平台移除外链标签解释。",
        )
    if _normalized_visible_text(str(source_soup)) != _normalized_visible_text(str(remote_soup)):
        raise GatewayPublishError("draft_get", "微信远端正文的可见文字与提交内容不一致。")

    removed_properties: Counter[str] = Counter()
    unexpected_changes: list[dict[str, Any]] = []
    for index, (source_tag, remote_tag) in enumerate(zip(source_tags, remote_tags)):
        if source_tag.get("class", []) != remote_tag.get("class", []):
            unexpected_changes.append(
                {
                    "index": index,
                    "tag": source_tag.name,
                    "change": "class",
                }
            )
            continue
        source_style = _css_properties(source_tag.get("style"))
        remote_style = _css_properties(remote_tag.get("style"))
        removed = set(source_style) - set(remote_style)
        added = set(remote_style) - set(source_style)
        changed = {
            name
            for name in set(source_style) & set(remote_style)
            if source_style[name] != remote_style[name]
        }
        removed_properties.update(removed)
        unexpected_removed = removed - {"position"}
        if unexpected_removed or added or changed:
            unexpected_changes.append(
                {
                    "index": index,
                    "tag": source_tag.name,
                    "removed": sorted(unexpected_removed),
                    "added": sorted(added),
                    "changed": sorted(changed),
                }
            )
    if unexpected_changes:
        raise GatewayPublishError(
            "draft_get",
            f"微信远端正文出现未允许的版式变化：{unexpected_changes[:5]}",
        )

    return {
        "remoteFidelityVerified": True,
        "remoteContentBytes": len(remote_html.encode("utf-8")),
        "remoteFidelityMetrics": lovpen_fidelity_metrics(remote_html),
        "remoteWechatSanitization": {
            "removedTags": {"a": removed_anchors} if removed_anchors else {},
            "removedStyleProperties": dict(sorted(removed_properties.items())),
            "normalizedNativeVideoComponents": normalized_native_videos,
            "preservedNodeCountAfterAnchorUnwrap": len(remote_tags),
            "preservedTagSequence": True,
            "preservedClasses": True,
            "preservedRemainingCssProperties": True,
            "preservedVisibleTextIgnoringWhitespace": True,
        },
    }


def resolve_env_manager_path(explicit: str | None) -> Path:
    candidates = [Path(explicit).expanduser()] if explicit else []
    candidates.extend(DEFAULT_ENV_MANAGER_CANDIDATES)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise GatewayPublishError(
        "credentials",
        "找不到 lov-env-management；请通过 --env-manager-script 指定 env_manager.py。",
    )


def resolve_managed_secrets(
    *, env_manager_script: Path, wechat_secret_locator: str, gateway_key_locator: str
) -> ManagedSecrets:
    spec = importlib.util.spec_from_file_location("lov_env_manager_runtime", env_manager_script)
    if spec is None or spec.loader is None:
        raise GatewayPublishError("credentials", "无法加载 lov-env-management。")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    store = module.Store(module.default_home(), 14)
    registry = store.load()

    def read(locator: str) -> str:
        _, _, record = store.get_record(registry, locator)
        return store.read_secret(locator, record)

    return ManagedSecrets(
        app_secret=read(wechat_secret_locator),
        gateway_api_key=read(gateway_key_locator),
    )


def build_multipart(
    fields: Iterable[tuple[str, str]], files: Iterable[tuple[str, Path, str]]
) -> tuple[bytes, str]:
    boundary = "----lovstudio-" + uuid.uuid4().hex
    chunks: list[bytes] = []
    for name, value in fields:
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )
    for name, file_path, content_type in files:
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                (
                    f'Content-Disposition: form-data; name="{name}"; '
                    f'filename="{file_path.name}"\r\n'
                ).encode("utf-8"),
                f"Content-Type: {content_type}\r\n\r\n".encode(),
                file_path.read_bytes(),
                b"\r\n",
            ]
        )
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


class WechatGatewayClient:
    def __init__(self, base_url: str, app_id: str, secrets: ManagedSecrets):
        self.base_url = base_url.rstrip("/")
        self.app_id = app_id
        self.secrets = secrets

    def _request_json(
        self,
        path: str,
        *,
        stage: str,
        body: bytes,
        content_type: str,
        timeout: int = 60,
    ) -> dict[str, Any]:
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            method="POST",
            headers={
                "Content-Type": content_type,
                "User-Agent": USER_AGENT,
                "X-API-Key": self.secrets.gateway_api_key,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as error:
            try:
                payload = json.loads(error.read().decode("utf-8", "replace"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                payload = {}
            detail = payload.get("detail") if isinstance(payload, dict) else None
            if not isinstance(detail, str):
                detail = f"网关返回 HTTP {error.code}。"
            raise GatewayPublishError(stage, detail, status=error.code) from None
        except (OSError, TimeoutError) as error:
            raise GatewayPublishError(stage, f"连接微信网关失败：{type(error).__name__}") from None
        if not isinstance(payload, dict):
            raise GatewayPublishError(stage, "微信网关响应格式异常。")
        return payload

    def upload_body_image(self, image: BodyImage) -> str:
        if not image.path.is_file():
            raise GatewayPublishError("upload_body_image", f"正文图片不存在：{image.path}")
        content_type = mimetypes.guess_type(image.path.name)[0] or "image/jpeg"
        if content_type not in {"image/jpeg", "image/png"}:
            raise GatewayPublishError(
                "upload_body_image", f"正文图片格式不受支持：{image.path.name} ({content_type})"
            )
        size = image.path.stat().st_size
        if size >= 1024 * 1024:
            raise GatewayPublishError(
                "upload_body_image", f"正文图片必须小于 1 MiB：{image.path.name} ({size} bytes)"
            )
        body, content_type_header = build_multipart(
            [("app_id", self.app_id), ("app_secret", self.secrets.app_secret)],
            [("image", image.path, content_type)],
        )
        payload = self._request_json(
            "/material/upload-body-image",
            stage="upload_body_image",
            body=body,
            content_type=content_type_header,
        )
        image_url = payload.get("url")
        if not isinstance(image_url, str) or not image_url.startswith("https://"):
            raise GatewayPublishError("upload_body_image", "微信网关未返回 HTTPS 正文图片地址。")
        return image_url

    def add_draft(
        self,
        *,
        title: str,
        author: str,
        digest: str,
        content_html: str,
        content_source_url: str,
        cover: Path,
        need_open_comment: int,
        only_fans_can_comment: int,
    ) -> str:
        if not cover.is_file():
            raise GatewayPublishError("draft_add", f"封面不存在：{cover}")
        cover_type = mimetypes.guess_type(cover.name)[0] or "image/jpeg"
        body, content_type_header = build_multipart(
            [
                ("app_id", self.app_id),
                ("app_secret", self.secrets.app_secret),
                ("title", title),
                ("author", author),
                ("digest", digest),
                ("content_html", content_html),
                ("content_source_url", content_source_url),
                ("show_cover_pic", "0"),
                ("need_open_comment", str(need_open_comment)),
                ("only_fans_can_comment", str(only_fans_can_comment)),
            ],
            [("cover", cover, cover_type)],
        )
        payload = self._request_json(
            "/draft/add",
            stage="draft_add",
            body=body,
            content_type=content_type_header,
            timeout=120,
        )
        media_id = payload.get("media_id")
        if not isinstance(media_id, str) or not media_id:
            raise GatewayPublishError("draft_add", "微信网关未返回 media_id。")
        return media_id

    def get_draft(self, media_id: str) -> dict[str, Any]:
        body = json.dumps(
            {"app_id": self.app_id, "app_secret": self.secrets.app_secret, "media_id": media_id},
            ensure_ascii=False,
        ).encode("utf-8")
        return self._request_json(
            "/draft/get",
            stage="draft_get",
            body=body,
            content_type="application/json",
        )


def upload_body_image_with_retry(
    client: WechatGatewayClient, image: BodyImage, *, attempts: int = 3
) -> str:
    for attempt in range(attempts):
        try:
            return client.upload_body_image(image)
        except GatewayPublishError as error:
            retryable = error.status is None or error.status == 429 or error.status >= 500
            if not retryable or attempt + 1 >= attempts:
                raise
            time.sleep(0.5 * (2**attempt))
    raise GatewayPublishError("upload_body_image", "正文图片上传重试异常结束。")


def update_receipt(
    receipt_path: Path,
    *,
    state: str,
    media_id: str | None,
    detail: dict[str, Any],
    verification_pending: bool | None = None,
) -> None:
    receipt: dict[str, Any] = {}
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt.update(
        {
            "schemaVersion": 1,
            "platform": "wechat_official_account",
            "action": "create_draft",
            "state": state,
            "transport": "uni-api-gateway",
            "mediaId": media_id,
            "verificationPending": (
                state != "draft_created"
                if verification_pending is None
                else verification_pending
            ),
            "checkedAt": utc_now(),
        }
    )
    technical = receipt.get("technicalDetail")
    if not isinstance(technical, dict):
        technical = {}
    technical.update(detail)
    for stale_key in ("apiErrorCode", "whitelistIp"):
        technical.pop(stale_key, None)
    receipt["technicalDetail"] = technical
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path)
    parser.add_argument("--app-id", required=True)
    parser.add_argument("--wechat-secret-locator", required=True)
    parser.add_argument("--gateway-key-locator", required=True)
    parser.add_argument("--gateway-base", default=DEFAULT_GATEWAY_BASE)
    parser.add_argument("--env-manager-script")
    parser.add_argument(
        "--lovpen-html",
        "--lovpen-wechat-html",
        dest="lovpen_html",
        type=Path,
        help="由 lovpen-cli render --format wechat 生成的微信复制态 HTML；仅替换图片 URL，不重建样式。",
    )
    parser.add_argument(
        "--allow-compact-markdown",
        action="store_true",
        help="仅用于诊断旧链路；允许跳过 lovpen-cli 微信复制态产物。",
    )
    parser.add_argument("--title")
    parser.add_argument("--author")
    parser.add_argument("--digest")
    parser.add_argument("--source-url")
    parser.add_argument("--cover", type=Path)
    parser.add_argument(
        "--brand-profile",
        type=Path,
        help="包含永久品牌尾注与当前活动状态的公众号品牌 Profile。",
    )
    parser.add_argument(
        "--cover-composition-receipt",
        type=Path,
        help="由 lov-wechat-branding-cover-composition 生成的 cover-composition.json。",
    )
    parser.add_argument(
        "--allow-unverified-cover",
        action="store_true",
        help="仅用于诊断旧链路；允许跳过品牌封面合成收据。",
    )
    parser.add_argument(
        "--allow-unverified-body-hero",
        action="store_true",
        help="仅用于诊断旧链路；允许跳过正文第一块 4:3 首图验收。",
    )
    parser.add_argument("--need-open-comment", type=int, choices=(0, 1), default=1)
    parser.add_argument("--only-fans-can-comment", type=int, choices=(0, 1), default=0)
    parser.add_argument("--upload-workers", type=int, default=4)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    markdown_path = args.markdown.expanduser().resolve()
    if not markdown_path.is_file():
        raise GatewayPublishError("input", f"Markdown 文件不存在：{markdown_path}")
    raw_markdown = markdown_path.read_text(encoding="utf-8")
    publication_components: dict[str, Any] = {"publicationComponentsVerified": False}
    if args.brand_profile:
        try:
            publication_components = validate_editorial_components(
                markdown_path,
                raw_markdown,
                args.brand_profile,
            )
        except EditorialComponentError as error:
            raise GatewayPublishError("editorial_components", str(error)) from None
    frontmatter, _ = parse_frontmatter(raw_markdown)
    title = (args.title or frontmatter.get("title") or "").strip()
    author = (args.author or frontmatter.get("author") or "").strip()
    digest = (
        args.digest
        or frontmatter.get("digest")
        or frontmatter.get("summary")
        or frontmatter.get("description")
        or ""
    ).strip()
    source_url = (
        args.source_url
        or frontmatter.get("sourceUrl")
        or frontmatter.get("contentSourceUrl")
        or frontmatter.get("content_source_url")
        or ""
    ).strip()
    raw_cover = args.cover or Path(frontmatter.get("cover") or "")
    cover = raw_cover if raw_cover.is_absolute() else (markdown_path.parent / raw_cover).resolve()

    if not title:
        raise GatewayPublishError("input", "文章标题为空。")
    if len(title) > 32:
        raise GatewayPublishError("input", f"文章标题超过 32 个字符：{len(title)}")
    if len(author) > 16:
        raise GatewayPublishError("input", f"作者超过 16 个字符：{len(author)}")
    if len(digest) > 120:
        raise GatewayPublishError("input", f"摘要超过 120 个字符：{len(digest)}")
    benchmark_errors = _benchmark_reproducibility_errors(raw_markdown, title)
    if benchmark_errors:
        raise GatewayPublishError("content_quality", "；".join(benchmark_errors))

    cover_evidence: dict[str, Any] = {"coverCompositionVerified": False}
    if args.cover_composition_receipt:
        try:
            cover_evidence = validate_cover_composition_receipt(
                args.cover_composition_receipt,
                cover,
            )
        except ArtifactContractError as error:
            raise GatewayPublishError("cover_validation", str(error)) from None
    elif not args.allow_unverified_cover:
        raise GatewayPublishError(
            "cover_validation",
            "常规草稿创建必须提供 --cover-composition-receipt；"
            "先用 lov-wechat-branding-cover-composition 生成最终分享封面。",
        )

    lovpen_metrics: dict[str, int] | None = None
    lovpen_fingerprint: str | None = None
    if args.lovpen_html:
        content_html, images, layout, lovpen_metrics, lovpen_fingerprint = render_lovpen_wechat_html(
            args.lovpen_html,
            markdown_path,
        )
    else:
        if not args.allow_compact_markdown:
            raise GatewayPublishError(
                "lovpen_validation",
                "常规草稿创建必须提供 --lovpen-wechat-html；"
                "先用 lovpen-cli render --format wechat 生成微信复制态 HTML。",
            )
        content_html, images, _ = render_compact_markdown(markdown_path)
        layout = "compact-markdown-diagnostic"
    body_hero_evidence: dict[str, Any] = {"bodyHeroVerified": False}
    if not args.allow_unverified_body_hero:
        body_hero_errors, body_hero = _body_hero_errors(markdown_path, raw_markdown, cover)
        if body_hero_errors:
            raise GatewayPublishError("body_hero", "；".join(body_hero_errors))
        body_hero_evidence = {"bodyHeroVerified": True, "bodyHero": body_hero}
    missing = [str(image.path) for image in images if not image.path.is_file()]
    if missing:
        raise GatewayPublishError("input", f"正文图片不存在，共 {len(missing)} 张。")

    base_result = {
        "title": title,
        "author": author,
        "digestLength": len(digest),
        "sourceUrl": source_url,
        "inlineImages": len(images),
        "layout": layout,
        "compactHtmlCharsBeforeUpload": len(content_html),
        "cover": str(cover),
        **cover_evidence,
        **body_hero_evidence,
        **publication_components,
    }
    if args.lovpen_html:
        lovpen_artifact = args.lovpen_html.expanduser().resolve()
        base_result.update(
            {
                "lovpenArtifact": str(lovpen_artifact),
                "lovpenArtifactBytes": lovpen_artifact.stat().st_size,
                "lovpenArtifactSha256": hashlib.sha256(lovpen_artifact.read_bytes()).hexdigest(),
                "lovpenFidelityVerified": True,
                "lovpenFidelityMetrics": lovpen_metrics,
                "lovpenFidelitySha256": lovpen_fingerprint,
            }
        )
    if args.dry_run:
        print(json.dumps({"status": "prepared", **base_result}, ensure_ascii=False, indent=2))
        return 0

    env_manager_script = resolve_env_manager_path(args.env_manager_script)
    secrets = resolve_managed_secrets(
        env_manager_script=env_manager_script,
        wechat_secret_locator=args.wechat_secret_locator,
        gateway_key_locator=args.gateway_key_locator,
    )
    client = WechatGatewayClient(args.gateway_base, args.app_id, secrets)

    uploaded_urls: dict[str, str] = {}
    workers = max(1, min(args.upload_workers, 6))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(upload_body_image_with_retry, client, image): image for image in images
        }
        for future in as_completed(futures):
            image = futures[future]
            uploaded_urls[image.placeholder] = future.result()

    for placeholder, image_url in uploaded_urls.items():
        content_html = content_html.replace(placeholder, image_url)
    unresolved = [image.placeholder for image in images if image.placeholder in content_html]
    if unresolved:
        raise GatewayPublishError("upload_body_image", f"仍有 {len(unresolved)} 张正文图片未被替换。")
    if lovpen_metrics is not None and lovpen_fingerprint is not None:
        verify_lovpen_fidelity(content_html, lovpen_metrics, lovpen_fingerprint)
    visible_text_chars, content_html_bytes = validate_wechat_content_size(content_html)

    media_id = client.add_draft(
        title=title,
        author=author,
        digest=digest,
        content_html=content_html,
        content_source_url=source_url,
        cover=cover,
        need_open_comment=args.need_open_comment,
        only_fans_can_comment=args.only_fans_can_comment,
    )
    if args.receipt:
        update_receipt(
            args.receipt.expanduser().resolve(),
            state="draft_created",
            media_id=media_id,
            verification_pending=True,
            detail={
                "transport": "uni-api-gateway",
                "gatewayBase": args.gateway_base,
                "wechatCredentialLocator": args.wechat_secret_locator,
                "gatewayKeyLocator": args.gateway_key_locator,
                "inlineImages": len(images),
                "layout": layout,
                "lovpenArtifact": base_result.get("lovpenArtifact"),
                "lovpenArtifactBytes": base_result.get("lovpenArtifactBytes"),
                "lovpenArtifactSha256": base_result.get("lovpenArtifactSha256"),
                "coverCompositionVerified": base_result.get("coverCompositionVerified"),
                "coverCompositionReceipt": base_result.get("coverCompositionReceipt"),
                "blocker": "草稿已创建，等待远端回读验收。",
            },
        )
    try:
        readback = client.get_draft(media_id)
    except GatewayPublishError as error:
        if args.receipt:
            update_receipt(
                args.receipt.expanduser().resolve(),
                state="draft_created",
                media_id=media_id,
                verification_pending=True,
                detail={"blocker": str(error), "verificationStage": error.stage},
            )
        raise
    verified = (
        readback.get("media_id") == media_id
        and readback.get("title") == title
        and readback.get("image_count") == len(images)
        and bool(readback.get("thumb_media_id"))
    )
    if not verified:
        error = GatewayPublishError("draft_get", "草稿已创建，但远端回读未通过完整性校验。")
        if args.receipt:
            update_receipt(
                args.receipt.expanduser().resolve(),
                state="draft_created",
                media_id=media_id,
                verification_pending=True,
                detail={"blocker": str(error), "verificationStage": error.stage},
            )
        raise error

    remote_lovpen_audit: dict[str, Any] = {}
    if lovpen_metrics is not None:
        remote_content = readback.get("content")
        if not isinstance(remote_content, str) or not remote_content:
            raise GatewayPublishError("draft_get", "草稿已创建，但远端回读没有返回 Lovpen 正文。")
        try:
            remote_lovpen_audit = audit_remote_lovpen_fidelity(content_html, remote_content)
        except GatewayPublishError as error:
            if args.receipt:
                update_receipt(
                    args.receipt.expanduser().resolve(),
                    state="draft_created",
                    media_id=media_id,
                    verification_pending=True,
                    detail={"blocker": str(error), "verificationStage": error.stage},
                )
            raise

    result = {
        "status": "draft_created",
        "mediaId": media_id,
        "transport": "uni-api-gateway",
        **base_result,
        "contentChars": readback.get("content_length"),
        "submittedVisibleTextChars": visible_text_chars,
        "submittedHtmlBytes": content_html_bytes,
        "readbackImages": readback.get("image_count"),
        "updateTime": readback.get("update_time"),
        "contentFingerprint": "sha256:"
        + hashlib.sha256(content_html.encode("utf-8")).hexdigest()[:12],
        **remote_lovpen_audit,
    }
    if args.receipt:
        update_receipt(
            args.receipt.expanduser().resolve(),
            state="draft_created",
            media_id=media_id,
            verification_pending=False,
            detail={
                "transport": "uni-api-gateway",
                "gatewayBase": args.gateway_base,
                "wechatCredentialLocator": args.wechat_secret_locator,
                "gatewayKeyLocator": args.gateway_key_locator,
                "inlineImages": len(images),
                "layout": layout,
                "lovpenArtifact": base_result.get("lovpenArtifact"),
                "lovpenArtifactBytes": base_result.get("lovpenArtifactBytes"),
                "lovpenArtifactSha256": base_result.get("lovpenArtifactSha256"),
                "lovpenFidelityVerified": base_result.get("lovpenFidelityVerified"),
                "lovpenFidelityMetrics": base_result.get("lovpenFidelityMetrics"),
                "lovpenFidelitySha256": base_result.get("lovpenFidelitySha256"),
                "coverCompositionVerified": base_result.get("coverCompositionVerified"),
                "coverCompositionReceipt": base_result.get("coverCompositionReceipt"),
                "coverCompositionSchema": base_result.get("coverCompositionSchema"),
                "coverArtifactSha256": base_result.get("coverArtifactSha256"),
                "coverLogoSha256": base_result.get("coverLogoSha256"),
                "coverLogoVariant": base_result.get("coverLogoVariant"),
                "remoteImageCount": readback.get("image_count"),
                "remoteContentChars": readback.get("content_length"),
                "remoteUpdateTime": readback.get("update_time"),
                **remote_lovpen_audit,
                "blocker": None,
            },
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GatewayPublishError as error:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "stage": error.stage,
                    "httpStatus": error.status,
                    "message": str(error),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        raise SystemExit(1)
