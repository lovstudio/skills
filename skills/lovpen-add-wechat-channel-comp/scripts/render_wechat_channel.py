#!/usr/bin/env python3
"""Normalize one WeChat Channels component and render it as Lovpen Markdown or HTML."""

import argparse
import hashlib
import html
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse


SCHEMA = "lovpen/wechat-channel-component/v1"
DIRECTIVE_PREFIX = "::wechat-channels{"
DEFAULT_MARKER = "<!-- lovpen-wechat-channel -->"
FIELDS = (
    "id",
    "nonce-id",
    "username",
    "nickname",
    "description",
    "cover",
    "avatar",
    "width",
    "height",
)

WECHAT_CHANNEL_SHADOW_STYLE = (
    ':host{all:initial;display:block!important;width:100%!important;max-width:100%!important;'
    'margin:22px auto!important;text-align:center;-webkit-text-size-adjust:100%}'
    '*{box-sizing:border-box}.wx-root{display:flex;width:100%;justify-content:center;'
    'font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue",Arial,sans-serif}'
    '.wxw_wechannel_card{position:relative;display:block;max-width:100%;margin:0 auto;padding:6px 14px;'
    'overflow:hidden;border-radius:18px;background:#fff;box-shadow:0 2px 12px rgba(0,0,0,.08);text-align:left}'
    '.wxw_wechannel_card_horizontal{padding:6px}'
    '.wxw_wechannel_card_bd{position:relative;overflow:hidden;border-radius:13px;background:#f1f1f1}'
    '.wxw_wechannel_video_context{position:relative;width:100%;overflow:hidden;background-position:center;'
    'background-size:cover;background-repeat:no-repeat}'
    '.weui-play-btn_primary{position:absolute;left:50%;top:50%;width:58px;height:58px;'
    'transform:translate(-50%,-50%);border:2px solid rgba(255,255,255,.96);border-radius:50%;'
    'background:rgba(0,0,0,.16);box-shadow:0 1px 8px rgba(0,0,0,.18)}'
    '.weui-play-btn_primary:after{content:"";position:absolute;left:22px;top:17px;width:0;height:0;'
    'border-top:11px solid transparent;border-bottom:11px solid transparent;border-left:17px solid #fff}'
    '.wxw_wechannel_card_ft{position:absolute;left:0;right:0;bottom:0;display:flex;align-items:flex-end;'
    'height:78px;padding:34px 15px 12px;color:#fff;background:linear-gradient(180deg,transparent,rgba(0,0,0,.62))}'
    '.wxw_wechannel_profile{display:flex;min-width:0;align-items:center}'
    '.wxw_wechannel_logo{position:relative;display:inline-block;flex:0 0 22px;width:22px;height:18px;margin-right:8px}'
    '.wxw_wechannel_logo:before,.wxw_wechannel_logo:after{content:"";position:absolute;top:2px;width:8px;'
    'height:13px;border:2px solid #fa9d3b;border-radius:50%}'
    '.wxw_wechannel_logo:before{left:2px;transform:rotate(18deg)}'
    '.wxw_wechannel_logo:after{right:2px;transform:rotate(-18deg)}'
    '.wxw_wechannel_nickname{min-width:0;overflow:hidden;color:#fff;font-size:16px;font-weight:600;'
    'line-height:20px;text-overflow:ellipsis;text-shadow:0 1px 3px rgba(0,0,0,.45);white-space:nowrap}'
    '.wxw_wechannel_msg_web{display:none}'
)


class ComponentError(ValueError):
    """A stable user-input or materialization error."""


@dataclass(frozen=True)
class ChannelComponent:
    component_id: str
    nonce_id: str
    username: str
    nickname: str
    description: str
    cover: str
    avatar: str
    width: int
    height: int


class ChannelsDomParser(HTMLParser):
    def __init__(self) -> None:
        HTMLParser.__init__(self, convert_charrefs=True)
        self.components: List[Dict[str, str]] = []

    def handle_starttag(
        self, tag: str, attrs: List[Tuple[str, Optional[str]]]
    ) -> None:
        if tag.lower() != "mp-common-videosnap":
            return
        parsed: Dict[str, str] = {}
        for name, value in attrs:
            key = name.lower()
            if key in parsed:
                raise ComponentError("视频号 DOM 含重复属性：{}".format(key))
            parsed[key] = value or ""
        self.components.append(parsed)


def _parse_http_url(field: str, value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ComponentError("{} 必须是有效的 HTTP URL".format(field))
    return value


def _positive_integer(field: str, value: str) -> int:
    if not re.fullmatch(r"[0-9]+", value or ""):
        raise ComponentError("{} 必须是正整数".format(field))
    number = int(value)
    if number <= 0:
        raise ComponentError("{} 必须是正整数".format(field))
    return number


def _normalize(values: Dict[str, str]) -> ChannelComponent:
    missing = [field for field in FIELDS if field not in values]
    unknown = sorted(set(values) - set(FIELDS))
    if missing:
        raise ComponentError("缺少视频号字段：{}".format(", ".join(missing)))
    if unknown:
        raise ComponentError("不支持的视频号字段：{}".format(", ".join(unknown)))
    for field in ("id", "nonce-id", "username", "nickname"):
        if not values[field].strip():
            raise ComponentError("{} 不能为空".format(field))
    return ChannelComponent(
        component_id=values["id"],
        nonce_id=values["nonce-id"],
        username=values["username"],
        nickname=values["nickname"],
        description=values["description"],
        cover=_parse_http_url("cover", values["cover"]),
        avatar=_parse_http_url("avatar", values["avatar"]),
        width=_positive_integer("width", values["width"]),
        height=_positive_integer("height", values["height"]),
    )


def parse_dom(source: str) -> ChannelComponent:
    parser = ChannelsDomParser()
    try:
        parser.feed(source)
        parser.close()
    except ComponentError:
        raise
    except Exception as exc:
        raise ComponentError("无法解析视频号 DOM：{}".format(exc))
    if len(parser.components) != 1:
        raise ComponentError(
            "输入必须且只能包含一个 mp-common-videosnap，实际为 {} 个".format(
                len(parser.components)
            )
        )
    attrs = parser.components[0]
    return _normalize(
        {
            "id": attrs.get("data-id", ""),
            "nonce-id": attrs.get("data-nonceid", ""),
            "username": attrs.get("data-username", ""),
            "nickname": attrs.get("data-nickname", ""),
            "description": attrs.get("data-desc", ""),
            "cover": attrs.get("data-url", ""),
            "avatar": attrs.get("data-headimgurl", ""),
            "width": attrs.get("data-width", ""),
            "height": attrs.get("data-height", ""),
        }
    )


def _decode_escape(character: str) -> str:
    return {"n": "\n", "r": "\r", "t": "\t"}.get(character, character)


def _parse_directive_attributes(source: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    index = 0
    while index < len(source):
        while index < len(source) and source[index].isspace():
            index += 1
        if index >= len(source):
            break
        name_match = re.match(r"[A-Za-z][A-Za-z0-9-]*", source[index:])
        if not name_match:
            raise ComponentError("视频号 DSL 属性名无效")
        name = name_match.group(0).lower()
        index += len(name_match.group(0))
        while index < len(source) and source[index].isspace():
            index += 1
        if index >= len(source) or source[index] != "=":
            raise ComponentError("视频号 DSL 属性 {} 缺少 =".format(name))
        index += 1
        while index < len(source) and source[index].isspace():
            index += 1
        if index >= len(source) or source[index] != '"':
            raise ComponentError("视频号 DSL 属性 {} 必须使用双引号".format(name))
        index += 1
        characters: List[str] = []
        closed = False
        while index < len(source):
            character = source[index]
            index += 1
            if character == "\\":
                if index >= len(source):
                    raise ComponentError("视频号 DSL 以不完整转义结尾")
                characters.append(_decode_escape(source[index]))
                index += 1
                continue
            if character == '"':
                closed = True
                break
            characters.append(character)
        if not closed:
            raise ComponentError("视频号 DSL 属性 {} 缺少结束引号".format(name))
        if name in values:
            raise ComponentError("视频号 DSL 属性 {} 重复".format(name))
        values[name] = "".join(characters)
    return values


def parse_dsl(source: str) -> ChannelComponent:
    value = source.strip()
    if not value.startswith(DIRECTIVE_PREFIX) or not value.endswith("}"):
        raise ComponentError("输入不是完整的 ::wechat-channels DSL")
    attributes = value[len(DIRECTIVE_PREFIX) : -1]
    return _normalize(_parse_directive_attributes(attributes))


def parse_component(source: str, declared_kind: str) -> Tuple[ChannelComponent, str]:
    if declared_kind == "dom":
        return parse_dom(source), "dom"
    if declared_kind == "dsl":
        return parse_dsl(source), "dsl"
    if re.search(r"<mp-common-videosnap\b", source, re.IGNORECASE):
        return parse_dom(source), "dom"
    if source.strip().startswith(DIRECTIVE_PREFIX):
        return parse_dsl(source), "dsl"
    raise ComponentError("无法识别输入；请提供 mp-common-videosnap DOM 或 ::wechat-channels DSL")


def _escape_dsl(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", "\\r")
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )


def render_markdown(component: ChannelComponent) -> str:
    values = {
        "id": component.component_id,
        "nonce-id": component.nonce_id,
        "username": component.username,
        "nickname": component.nickname,
        "description": component.description,
        "cover": component.cover,
        "avatar": component.avatar,
        "width": str(component.width),
        "height": str(component.height),
    }
    attributes = " ".join(
        '{}="{}"'.format(field, _escape_dsl(values[field])) for field in FIELDS
    )
    return "{}{}{}".format(DIRECTIVE_PREFIX, attributes, "}")


def render_html(component: ChannelComponent) -> str:
    attr = lambda value: html.escape(value, quote=True)
    is_horizontal = component.width > component.height
    card_width = 360 if is_horizontal else 282
    card_inset = 6 if is_horizontal else 14
    cover_height = max(1, (card_width - card_inset * 2) * component.height // component.width)
    orientation = " wxw_wechannel_card_horizontal" if is_horizontal else ""
    cover_style = 'background-image: url({}); height: {}px'.format(
        json.dumps(component.cover, ensure_ascii=False), cover_height
    )
    return (
        '<mp-common-videosnap class="js_uneditable custom_select_card channels_iframe '
        'videosnap_video_iframe" data-pluginname="mpvideosnap" data-url="{}" '
        'data-headimgurl="{}" data-username="{}" data-nickname="{}" data-desc="{}" '
        'data-nonceid="{}" data-width="{}" data-height="{}" data-type="video" '
        'data-id="{}" draggable="true">'
        '<template shadowrootmode="open"><style>{}</style><div class="wx-root common-web" '
        'data-weui-theme="light"><div role="option" tabindex="0" '
        'class="wxw_wechannel_card appmsg_card_channel appmsg_card_context '
        'js_wechannel_video_card wx_tap_card wx_card_root common-web{}" style="width: {}px">'
        '<div class="wxw_wechannel_card_bd"><div class="wxw_wechannel_video_context" '
        'style="{}"><i class="weui-play-btn_primary"></i></div>'
        '<div class="wxw_wechannel_card_ft weui-flex"><div class="wxw_wechannel_profile '
        'weui-flex"><div class="wxw_wechannel_logo"></div><div '
        'class="wxw_wechannel_nickname js_wx_tap_highlight">{}</div></div></div></div>'
        '<div class="wxw_wechannel_msg_web js_wechannel_msg"><div '
        'class="wxw_wechannel_msg_inner js_wechannel_msg_text"></div></div>'
        '</div></div></template></mp-common-videosnap>'
    ).format(
        attr(component.cover),
        attr(component.avatar),
        attr(component.username),
        attr(component.nickname),
        attr(component.description),
        attr(component.nonce_id),
        component.width,
        component.height,
        attr(component.component_id),
        WECHAT_CHANNEL_SHADOW_STYLE,
        orientation,
        card_width,
        attr(cover_style),
        html.escape(component.nickname),
    )


def _read_input(args: argparse.Namespace) -> Tuple[str, str]:
    selected = sum(value is not None for value in (args.input, args.dom, args.dsl))
    if selected > 1:
        raise ComponentError("--input、--dom、--dsl 只能使用一个")
    if args.dom is not None:
        return args.dom, "dom"
    if args.dsl is not None:
        return args.dsl, "dsl"
    if args.input and args.input != "-":
        path = Path(args.input).expanduser()
        if not path.is_file():
            raise ComponentError("输入文件不存在：{}".format(path))
        return path.read_text(encoding="utf-8"), "auto"
    return sys.stdin.read(), "auto"


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    target_mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".{}-".format(path.name), suffix=".tmp", dir=str(path.parent)
    )
    try:
        os.fchmod(descriptor, target_mode)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, str(path))
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def materialize(path_value: str, artifact: str, marker: str, output_format: str) -> Path:
    path = Path(path_value).expanduser()
    expected_suffixes = (".md", ".markdown") if output_format == "md" else (".html", ".htm")
    if path.suffix.lower() not in expected_suffixes:
        raise ComponentError("{} 输出必须写入 {} 文件".format(output_format, " 或 ".join(expected_suffixes)))
    if path.exists():
        if not path.is_file():
            raise ComponentError("输出目标不是普通文件：{}".format(path))
        with path.open("r", encoding="utf-8", newline="") as handle:
            original = handle.read()
        marker_count = original.count(marker)
        if marker_count != 1:
            raise ComponentError(
                "现有输出文件必须且只能包含一个标记 {!r}，实际为 {} 个".format(
                    marker, marker_count
                )
            )
        content = original.replace(marker, artifact, 1)
    else:
        content = artifact + "\n"
    _atomic_write(path, content)
    return path.resolve()


def _context_id(message: str) -> str:
    digest = hashlib.sha256(message.encode("utf-8")).hexdigest()[:12]
    return "wechat-channel-{}".format(digest)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render one WeChat Channels DOM or Lovpen DSL into Markdown or HTML."
    )
    parser.add_argument("--input", help="UTF-8 DOM/DSL file, or - for stdin")
    parser.add_argument("--dom", help="Raw mp-common-videosnap DOM text")
    parser.add_argument("--dsl", help="Raw ::wechat-channels DSL text")
    parser.add_argument("--format", choices=("md", "html"), default="md")
    parser.add_argument("--output", help="New output or existing marked .md/.html file")
    parser.add_argument("--marker", default=DEFAULT_MARKER)
    parser.add_argument("--json", action="store_true", help="Return a machine-readable result")
    return parser


def run(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        source, declared_kind = _read_input(args)
        component, input_kind = parse_component(source, declared_kind)
        artifact = render_markdown(component) if args.format == "md" else render_html(component)
        output = materialize(args.output, artifact, args.marker, args.format) if args.output else None
        digest = hashlib.sha256(artifact.encode("utf-8")).hexdigest()
        payload = {
            "schema": SCHEMA,
            "ok": True,
            "input_kind": input_kind,
            "format": args.format,
            "bytes": len(artifact.encode("utf-8")),
            "sha256": digest,
            "component_id": component.component_id,
            "output": str(output) if output else None,
            "written": output is not None,
        }
        if not output:
            payload["content"] = artifact
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        elif output:
            print(str(output))
        else:
            print(artifact)
        return 0
    except (ComponentError, OSError, UnicodeError) as exc:
        message = str(exc)
        context_id = _context_id(message)
        if getattr(args, "json", False):
            print(
                json.dumps(
                    {"schema": SCHEMA, "ok": False, "context_id": context_id, "error": message},
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
        else:
            print("ERROR [{}]: {}".format(context_id, message), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run())
