#!/usr/bin/env python3
"""Resolve one media URL, download it quickly, and emit a verifiable JSON report."""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Optional


VERSION = "0.1.0"
MEDIACRAWLER_REPOSITORY = "https://github.com/NanmiCoder/MediaCrawler.git"
MEDIACRAWLER_COMMIT = "5665a271ef15e0ec82b1f48a951b66760e054db9"
DEFAULT_CACHE_ROOT = Path.home() / ".cache" / "lov-media-crawler"
KEYCHAIN_SERVICE = "lov-media-crawler-yuanbao"
COOKIE_ENV = "LOV_MEDIA_CRAWLER_YUANBAO_COOKIE"
PUBLIC_WORKER_URL = "https://sph.litao.workers.dev/api/fetch_video_profile"
YUANBAO_PARSE_URL = "https://yuanbao.tencent.com/api/weixin/get_parse_result"
WECHAT_FEED_URL = "https://channels.weixin.qq.com/finder-preview/api/feed/get_feed_info"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
)
DIRECT_SUFFIXES = {
    ".mp4",
    ".mov",
    ".m4v",
    ".webm",
    ".mkv",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
}

PLATFORM_HOSTS = (
    (("xiaohongshu.com", "xhslink.com"), "xhs", "Xiaohongshu"),
    (("douyin.com", "iesdouyin.com"), "dy", "Douyin"),
    (("kuaishou.com", "gifshow.com"), "ks", "Kuaishou"),
    (("bilibili.com", "b23.tv"), "bili", "Bilibili"),
    (("weibo.com", "weibo.cn"), "wb", "Weibo"),
    (("tieba.baidu.com",), "tieba", "Baidu Tieba"),
    (("zhihu.com",), "zhihu", "Zhihu"),
)


class JobError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        next_action: str = "",
        *,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.next_action = next_action
        self.metadata = metadata or {}


def context_id() -> str:
    return f"mc_{uuid.uuid4().hex[:12]}"


def eprint(message: str, quiet: bool = False) -> None:
    if not quiet:
        print(message, file=sys.stderr, flush=True)


def write_json(path: Optional[Path], value: dict[str, Any]) -> None:
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def output_result(result: dict[str, Any], json_only: bool) -> None:
    if json_only:
        print(json.dumps(result, ensure_ascii=False))
        return
    if result.get("status") == "verified":
        print(f"完成：{result.get('output_path')}")
        print(
            f"{result.get('bytes', 0)} bytes · {result.get('elapsed_seconds', 0):.2f}s · "
            f"{result.get('average_mbps', 0):.2f} Mbps · {result.get('platform')}"
        )
    elif result.get("status") in {"ready", "passed", "resolved"}:
        label = result.get("path") or result.get("platform") or result.get("status")
        print(f"完成：{label}")
        print(f"context_id={result.get('context_id')}")
    else:
        print(f"未完成：{result.get('message', result.get('status'))}")
        if result.get("next_action"):
            print(f"下一步：{result['next_action']}")
        print(f"context_id={result.get('context_id')}")


def normalize_url(value: str) -> str:
    match = re.search(r"https?://[^\s<>]+", value.strip())
    if not match:
        raise JobError("invalid_url", "输入中没有可用的 HTTP(S) 链接。")
    return match.group(0).rstrip(".,，。)]}>'\"")


def url_kind(url: str) -> tuple[str, str]:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    path = parsed.path.lower()
    if host.endswith("weixin.qq.com") and "/sph/" in path:
        return "wechat", "WeChat Channels"
    if host.endswith("channels.weixin.qq.com"):
        return "wechat", "WeChat Channels"
    if Path(path).suffix in DIRECT_SUFFIXES:
        return "direct", "Direct media"
    for hosts, platform_id, label in PLATFORM_HOSTS:
        if any(host == item or host.endswith(f".{item}") for item in hosts):
            return platform_id, label
    return "unknown", "Unknown"


def safe_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def request_json(
    url: str,
    *,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: int = 30,
) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST")
    for key, value in headers.items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise JobError(
            "resolver_failed", f"解析接口返回 HTTP {exc.code}。"
        ) from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise JobError("resolver_failed", f"解析接口不可用：{type(exc).__name__}") from exc


def generate_rid() -> str:
    return f"{int(time.time()):x}-{random.randrange(16**8):08x}"


def wechat_short_id(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    match = re.search(r"/sph/([A-Za-z0-9_-]+)", parsed.path)
    if match:
        return match.group(1)
    query = urllib.parse.parse_qs(parsed.query)
    return query.get("id", [""])[0]


def feed_headers(referer: str) -> dict[str, str]:
    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Content-Type": "application/json",
        "Origin": "https://channels.weixin.qq.com",
        "Referer": referer,
        "User-Agent": USER_AGENT,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }


def normalize_feed_data(result: dict[str, Any]) -> dict[str, Any]:
    current: Any = result
    for _ in range(4):
        if not isinstance(current, dict):
            break
        if "feedInfo" in current or "authorInfo" in current:
            return current
        if isinstance(current.get("data"), dict):
            current = current["data"]
            continue
        break
    return {}


def public_wechat_probe(url: str) -> dict[str, Any]:
    short_id = wechat_short_id(url)
    if not short_id:
        return {}
    api_url = (
        f"{WECHAT_FEED_URL}?_rid={generate_rid()}"
        "&_pageUrl=https:%2F%2Fchannels.weixin.qq.com%2Ffinder-preview%2Fpages%2Fsph"
    )
    referer = f"https://channels.weixin.qq.com/finder-preview/pages/sph?id={short_id}"
    result = request_json(
        api_url,
        payload={"baseReq": {"generalToken": ""}, "shortUri": short_id},
        headers=feed_headers(referer),
    )
    return normalize_feed_data(result)


def read_keychain_cookie() -> str:
    if sys.platform != "darwin" or not shutil.which("security"):
        return ""
    command = [
        "security",
        "find-generic-password",
        "-s",
        KEYCHAIN_SERVICE,
        "-a",
        getpass.getuser(),
        "-w",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return completed.stdout.strip() if completed.returncode == 0 else ""


def resolve_cookie() -> str:
    return os.environ.get(COOKIE_ENV, "").strip() or read_keychain_cookie()


def yuanbao_headers(cookie: str) -> dict[str, str]:
    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "content-type": "application/json",
        "cookie": cookie,
        "origin": "https://yuanbao.tencent.com",
        "referer": "https://yuanbao.tencent.com/",
        "user-agent": USER_AGENT,
        "x-language": "zh-CN",
        "x-platform": "mac",
        "x-requested-with": "XMLHttpRequest",
        "x-source": "web",
    }


def resolve_wechat_direct(url: str, cookie: str) -> dict[str, Any]:
    parsed = request_json(
        YUANBAO_PARSE_URL,
        payload={"type": "video_channel_url", "url": url, "scene": 1},
        headers=yuanbao_headers(cookie),
    )
    parse_data = parsed.get("data") if isinstance(parsed.get("data"), dict) else {}
    if not parse_data.get("wx_export_id"):
        raise JobError(
            "authorization_failed",
            "本机元宝授权未能解析该视频号链接，登录态可能已过期。",
            "python3 scripts/authorize_yuanbao.py --test-url URL",
        )
    playable = urllib.parse.urlparse(str(parse_data.get("playable_url", "")))
    query = urllib.parse.parse_qs(playable.query)
    token = query.get("token", [""])[0]
    export_id = query.get("eid", [str(parse_data.get("wx_export_id", ""))])[0]
    api_url = (
        f"{WECHAT_FEED_URL}?_rid={generate_rid()}"
        "&_pageUrl=https:%2F%2Fchannels.weixin.qq.com%2Ffinder-preview%2Fpages%2Ffeed"
    )
    referer = (
        "https://channels.weixin.qq.com/finder-preview/pages/feed"
        f"?entry_card_type=48&comment_scene=39&appid=0&token={urllib.parse.quote(token)}"
        f"&entry_scene=0&eid={urllib.parse.quote(export_id)}"
    )
    result = request_json(
        api_url,
        payload={"baseReq": {"generalToken": token}, "exportId": export_id},
        headers=feed_headers(referer),
    )
    data = normalize_feed_data(result)
    if not data:
        raise JobError("resolver_failed", "微信视频号接口未返回可识别的数据。")
    return data


def resolve_wechat_worker(url: str, worker_url: str) -> dict[str, Any]:
    result = request_json(
        worker_url,
        payload={"url": url},
        headers={
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
        timeout=60,
    )
    data = normalize_feed_data(result)
    if not data:
        raise JobError("resolver_failed", "视频号解析服务没有返回媒体信息。")
    return data


def feed_metadata(data: dict[str, Any]) -> dict[str, Any]:
    feed = data.get("feedInfo") if isinstance(data.get("feedInfo"), dict) else {}
    author = data.get("authorInfo") if isinstance(data.get("authorInfo"), dict) else {}
    description = str(feed.get("description", "")).strip()
    return {
        "title": description.splitlines()[0][:120] if description else "视频号视频",
        "description": description,
        "author": str(author.get("nickname", "")),
        "cover_url": safe_url(str(feed.get("coverUrl", ""))),
        "created_at": feed.get("createtime", 0),
        "likes": feed.get("likeCountFmt", ""),
        "comments": feed.get("commentCountFmt", ""),
    }


def feed_video_url(data: dict[str, Any]) -> str:
    feed = data.get("feedInfo") if isinstance(data.get("feedInfo"), dict) else {}
    for candidate in (
        (feed.get("h264VideoInfo") or {}).get("videoUrl", "")
        if isinstance(feed.get("h264VideoInfo"), dict)
        else "",
        feed.get("videoUrl", ""),
        (feed.get("h265VideoInfo") or {}).get("videoUrl", "")
        if isinstance(feed.get("h265VideoInfo"), dict)
        else "",
        feed.get("originVideoUrl", ""),
    ):
        if isinstance(candidate, str) and candidate.startswith(("http://", "https://")):
            return candidate
    return ""


def resolve_wechat(
    url: str,
    *,
    worker_url: str,
    allow_public_resolver: bool,
) -> tuple[str, dict[str, Any], str]:
    cookie = resolve_cookie()
    if cookie:
        data = resolve_wechat_direct(url, cookie)
        media_url = feed_video_url(data)
        if not media_url:
            raise JobError(
                "resolver_failed",
                "授权解析成功，但响应中没有视频流。",
                "重新授权后重试；如果内容是图文，请检查返回的元数据。",
                metadata=feed_metadata(data),
            )
        return media_url, feed_metadata(data), "yuanbao_direct"
    if worker_url or allow_public_resolver:
        selected = worker_url or PUBLIC_WORKER_URL
        data = resolve_wechat_worker(url, selected)
        media_url = feed_video_url(data)
        if not media_url:
            raise JobError(
                "resolver_failed",
                "解析服务返回了元数据，但没有视频流。",
                metadata=feed_metadata(data),
            )
        return media_url, feed_metadata(data), "custom_worker" if worker_url else "public_worker"
    metadata: dict[str, Any] = {}
    try:
        metadata = feed_metadata(public_wechat_probe(url))
    except JobError:
        pass
    raise JobError(
        "authorization_required",
        "公开视频预览不暴露视频流；需要一次本机元宝授权。",
        f"python3 scripts/authorize_yuanbao.py --test-url '{url}'",
        metadata=metadata,
    )


def safe_filename(value: str, fallback: str = "media") -> str:
    normalized = re.sub(r"[<>:\"/\\|?*\x00-\x1f#]+", " ", value)
    normalized = re.sub(r"\s+", " ", normalized).strip(" .")
    return (normalized[:96] or fallback).strip()


def destination_path(output_dir: Path, title: str, media_url: str) -> Path:
    suffix = Path(urllib.parse.urlparse(media_url).path).suffix.lower()
    if suffix not in DIRECT_SUFFIXES or suffix == ".m3u8":
        suffix = ".mp4"
    return output_dir / f"{safe_filename(title)}{suffix}"


def verify_media(
    path: Path, expected_bytes: int = 0, *, run_ffprobe: bool = True
) -> dict[str, Any]:
    if not path.is_file():
        return {"ok": False, "reason": "file_missing"}
    size = path.stat().st_size
    if size < 16:
        return {"ok": False, "reason": "file_too_small", "bytes": size}
    if expected_bytes and size != expected_bytes:
        return {
            "ok": False,
            "reason": "content_length_mismatch",
            "bytes": size,
            "expected_bytes": expected_bytes,
        }
    with path.open("rb") as handle:
        header = handle.read(16)
    container = "unknown"
    if len(header) >= 8 and header[4:8] == b"ftyp":
        container = "iso-bmff"
    elif header.startswith(b"\x1a\x45\xdf\xa3"):
        container = "matroska-webm"
    elif header.startswith(b"ID3") or header[:1] == b"\x47":
        container = "stream"
    elif header.startswith(b"\x89PNG\r\n\x1a\n"):
        container = "png"
    elif header.startswith(b"\xff\xd8\xff"):
        container = "jpeg"
    elif header.startswith((b"GIF87a", b"GIF89a")):
        container = "gif"
    elif header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        container = "webp"
    elif header.lstrip().startswith((b"<", b"{", b"[")):
        return {"ok": False, "reason": "non_media_response", "bytes": size}

    result: dict[str, Any] = {"ok": container != "unknown", "container": container, "bytes": size}
    ffprobe = shutil.which("ffprobe") if run_ffprobe else None
    if ffprobe and container not in {"png", "jpeg", "gif", "webp"}:
        command = [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration,format_name:stream=index,codec_type,codec_name,width,height",
            "-of",
            "json",
            str(path),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode == 0:
            try:
                probe = json.loads(completed.stdout)
                streams = probe.get("streams", [])
                result["ffprobe"] = probe
                result["ok"] = bool(streams) and any(
                    item.get("codec_type") in {"video", "audio"} for item in streams
                )
            except json.JSONDecodeError:
                result["ffprobe_error"] = "invalid_json"
        else:
            result["ok"] = False
            result["ffprobe_error"] = completed.stderr.strip()[-500:]
    return result


def head_size(url: str, headers: dict[str, str]) -> int:
    request = urllib.request.Request(url, method="HEAD", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return int(response.headers.get("Content-Length", "0") or 0)
    except Exception:
        return 0


def run_downloader(
    media_url: str,
    target: Path,
    *,
    connections: int,
    quiet: bool,
    referer: str = "",
) -> tuple[int, str]:
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(f"{target.name}.part")
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
    }
    if referer:
        headers["Referer"] = referer
    expected = head_size(media_url, headers)
    aria2c = shutil.which("aria2c")
    if aria2c:
        eprint(f"开始多连接下载（{connections} connections）…", quiet)
        command = [
            aria2c,
            "--continue=true",
            f"--max-connection-per-server={connections}",
            f"--split={connections}",
            "--min-split-size=1M",
            "--file-allocation=none",
            "--auto-file-renaming=false",
            "--allow-overwrite=true",
            "--summary-interval=1",
            "--console-log-level=warn",
            f"--dir={partial.parent}",
            f"--out={partial.name}",
            f"--header=User-Agent: {USER_AGENT}",
        ]
        if referer:
            command.append(f"--header=Referer: {referer}")
        command.append(media_url)
        completed = subprocess.run(
            command,
            stdout=subprocess.DEVNULL if quiet else None,
            stderr=subprocess.DEVNULL if quiet else None,
            check=False,
        )
        engine = "aria2"
        if completed.returncode != 0 and shutil.which("curl"):
            eprint("多连接下载不可用，自动切换 curl 续传…", quiet)
            control = partial.with_name(f"{partial.name}.aria2")
            try:
                control.unlink()
            except FileNotFoundError:
                pass
            aria2c = None
    if not aria2c:
        curl = shutil.which("curl")
        if not curl:
            raise JobError("dependency_missing", "缺少 curl，无法执行下载。")
        eprint("开始可续传下载（curl）…", quiet)
        command = [
            curl,
            "--location",
            "--fail",
            "--retry",
            "5",
            "--retry-delay",
            "1",
            "--continue-at",
            "-",
            "--user-agent",
            USER_AGENT,
            "--output",
            str(partial),
        ]
        if referer:
            command.extend(["--referer", referer])
        if not quiet:
            command.append("--progress-bar")
        command.append(media_url)
        completed = subprocess.run(
            command,
            stdout=subprocess.DEVNULL if quiet else None,
            stderr=subprocess.DEVNULL if quiet else None,
            check=False,
        )
        engine = "curl"
    if completed.returncode != 0:
        raise JobError(
            "download_failed",
            f"{engine} 下载失败（exit {completed.returncode}），已保留续传文件。",
            f"重新运行同一条 download 命令以续传 {partial}",
        )
    partial.replace(target)
    return expected, engine


def choose_target(target: Path, overwrite: bool) -> tuple[Path, bool]:
    if not target.exists() or overwrite:
        return target, False
    existing = verify_media(target)
    if existing.get("ok"):
        return target, True
    digest = hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:8]
    return target.with_name(f"{target.stem}-{digest}{target.suffix}"), False


def mediacrawler_root(value: str) -> Path:
    configured = value or os.environ.get("LOV_MEDIA_CRAWLER_ROOT", "")
    return Path(configured).expanduser() if configured else DEFAULT_CACHE_ROOT / "MediaCrawler"


def setup_mediacrawler(args: argparse.Namespace) -> dict[str, Any]:
    ctx = context_id()
    if not args.accept_noncommercial_license:
        raise JobError(
            "license_acceptance_required",
            "MediaCrawler 使用非商业学习许可证；必须显式确认后才能安装。",
            "重新运行并添加 --accept-noncommercial-license",
        )
    root = mediacrawler_root(args.mediacrawler_root)
    if root.exists():
        raise JobError(
            "setup_target_exists",
            f"目标已存在：{root}",
            "运行 doctor 核对现有 checkout；本命令不会覆盖它。",
        )
    git = shutil.which("git")
    uv = shutil.which("uv")
    if not git or not uv:
        raise JobError("dependency_missing", "准备 MediaCrawler 需要 git 与 uv。")
    root.parent.mkdir(parents=True, exist_ok=True)
    commands = [
        [git, "init", str(root)],
        [git, "-C", str(root), "remote", "add", "origin", MEDIACRAWLER_REPOSITORY],
        [git, "-C", str(root), "fetch", "--depth", "1", "origin", MEDIACRAWLER_COMMIT],
        [git, "-C", str(root), "checkout", "--detach", "FETCH_HEAD"],
        [uv, "sync", "--frozen"],
    ]
    for index, command in enumerate(commands):
        cwd = root if index == len(commands) - 1 else None
        completed = subprocess.run(command, cwd=cwd, check=False)
        if completed.returncode != 0:
            raise JobError(
                "setup_failed",
                f"MediaCrawler 准备失败（step {index + 1}, exit {completed.returncode}）。",
                f"检查保留的目录 {root} 后重试或手动修复。",
            )
    return {
        "status": "ready",
        "context_id": ctx,
        "path": str(root),
        "commit": MEDIACRAWLER_COMMIT,
        "license": "NON-COMMERCIAL LEARNING LICENSE 1.1",
    }


def run_mediacrawler(
    url: str,
    platform_id: str,
    platform_label: str,
    output_dir: Path,
    root: Path,
    *,
    json_only: bool,
) -> dict[str, Any]:
    if not (root / "main.py").is_file():
        raise JobError(
            "mediacrawler_missing",
            "没有找到已验证的 MediaCrawler checkout。",
            "python3 scripts/media_crawler.py setup-mediacrawler --accept-noncommercial-license",
        )
    uv = shutil.which("uv")
    if not uv:
        raise JobError("dependency_missing", "MediaCrawler 路径需要 uv。")
    output_dir.mkdir(parents=True, exist_ok=True)
    before = {path.resolve() for path in output_dir.rglob("*") if path.is_file()}
    log_path = output_dir / f".mediacrawler-{int(time.time())}.log"
    code = (
        "import asyncio,config;"
        "config.ENABLE_GET_MEIDAS=True;"
        "config.ENABLE_CDP_MODE=True;"
        "config.CDP_CONNECT_EXISTING=False;"
        "config.CDP_DEBUG_PORT=9333;"
        "config.USER_DATA_DIR='lov_media_crawler_%s_user_data_dir';"
        "import main;asyncio.run(main.main())"
    )
    command = [
        uv,
        "run",
        "python",
        "-c",
        code,
        "--platform",
        platform_id,
        "--type",
        "detail",
        "--specified_id",
        url,
        "--get_comment",
        "false",
        "--get_sub_comment",
        "false",
        "--crawler_max_notes_count",
        "1",
        "--max_concurrency_num",
        "4",
        "--save_data_path",
        str(output_dir),
        "--headless",
        "false",
    ]
    eprint("启动 MediaCrawler 单链接模式；首次运行可能需要扫码登录…", json_only)
    started = time.monotonic()
    with log_path.open("w", encoding="utf-8") as log:
        completed = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT, check=False)
    elapsed = time.monotonic() - started
    if completed.returncode != 0:
        raise JobError(
            "mediacrawler_failed",
            f"MediaCrawler 退出码为 {completed.returncode}。",
            f"检查本地诊断日志 {log_path}",
        )
    after = [path for path in output_dir.rglob("*") if path.is_file() and path.resolve() not in before]
    media_files = [
        path for path in after if path.suffix.lower() in DIRECT_SUFFIXES and not path.name.endswith(".part")
    ]
    verified = []
    for path in media_files:
        check = verify_media(path)
        if check.get("ok"):
            verified.append((path, check))
    if not verified:
        raise JobError(
            "mediacrawler_failed",
            "MediaCrawler 已完成，但没有产生可验证的媒体文件。",
            f"检查登录、内容是否含媒体，以及日志 {log_path}",
        )
    total = sum(item[0].stat().st_size for item in verified)
    return {
        "status": "verified",
        "platform": platform_label,
        "source_url": safe_url(url),
        "output_path": str(verified[0][0].resolve()),
        "output_paths": [str(item[0].resolve()) for item in verified],
        "bytes": total,
        "elapsed_seconds": round(elapsed, 3),
        "average_mbps": round((total * 8 / 1_000_000) / max(elapsed, 0.001), 3),
        "engine": "MediaCrawler",
        "verification": verified[0][1],
        "diagnostic_log": str(log_path),
    }


def probe_command(args: argparse.Namespace) -> dict[str, Any]:
    url = normalize_url(args.url)
    kind, label = url_kind(url)
    result: dict[str, Any] = {
        "status": "resolved",
        "context_id": context_id(),
        "platform": label,
        "source_url": safe_url(url),
        "resolver": kind,
    }
    if kind == "wechat":
        data = public_wechat_probe(url)
        result["metadata"] = feed_metadata(data)
        result["media_url_available"] = bool(feed_video_url(data))
        result["authorization_available"] = bool(resolve_cookie())
        if not result["media_url_available"]:
            result["status"] = "authorization_required" if not resolve_cookie() else "resolver_pending"
    elif kind == "unknown":
        raise JobError("unsupported_url", "该链接不在当前支持的平台矩阵中。")
    elif kind not in {"direct"}:
        root = mediacrawler_root(args.mediacrawler_root)
        result["mediacrawler_ready"] = (root / "main.py").is_file()
        result["mediacrawler_root"] = str(root)
    return result


def download_command(args: argparse.Namespace) -> dict[str, Any]:
    url = normalize_url(args.url)
    kind, label = url_kind(url)
    output_dir = Path(args.output_dir).expanduser().resolve()
    if kind == "unknown":
        raise JobError(
            "unsupported_url",
            "该链接不是直接媒体地址，也不属于当前 MediaCrawler 平台。",
        )
    if kind not in {"wechat", "direct"}:
        result = run_mediacrawler(
            url,
            kind,
            label,
            output_dir,
            mediacrawler_root(args.mediacrawler_root),
            json_only=args.json,
        )
        result["context_id"] = context_id()
        return result

    started = time.monotonic()
    metadata: dict[str, Any] = {}
    resolver = "direct_url"
    media_url = url
    if kind == "wechat":
        eprint("正在解析视频号分享链接…", args.json)
        media_url, metadata, resolver = resolve_wechat(
            url,
            worker_url=args.worker_url,
            allow_public_resolver=args.allow_public_resolver,
        )
        eprint("已取得媒体地址，开始传输…", args.json)
    title = args.filename or metadata.get("title") or Path(urllib.parse.urlparse(media_url).path).stem or "media"
    target, reused = choose_target(destination_path(output_dir, title, media_url), args.overwrite)
    if reused:
        verification = verify_media(target)
        elapsed = time.monotonic() - started
        return {
            "status": "verified",
            "context_id": context_id(),
            "platform": label,
            "source_url": safe_url(url),
            "output_path": str(target),
            "bytes": target.stat().st_size,
            "elapsed_seconds": round(elapsed, 3),
            "average_mbps": 0.0,
            "engine": "existing_file",
            "resolver": resolver,
            "reused": True,
            "metadata": metadata,
            "verification": verification,
        }
    expected, engine = run_downloader(
        media_url,
        target,
        connections=max(1, min(args.connections, 16)),
        quiet=args.json,
        referer="https://channels.weixin.qq.com/" if kind == "wechat" else "",
    )
    verification = verify_media(target, expected)
    elapsed = time.monotonic() - started
    if not verification.get("ok"):
        raise JobError(
            "verification_failed",
            f"文件已落盘但媒体检查失败：{verification.get('reason', 'unknown')}。",
            f"检查报告后重试；当前文件 {target}",
            metadata=metadata,
        )
    size = target.stat().st_size
    return {
        "status": "verified",
        "context_id": context_id(),
        "platform": label,
        "source_url": safe_url(url),
        "output_path": str(target),
        "bytes": size,
        "elapsed_seconds": round(elapsed, 3),
        "average_mbps": round((size * 8 / 1_000_000) / max(elapsed, 0.001), 3),
        "engine": engine,
        "resolver": resolver,
        "reused": False,
        "metadata": metadata,
        "verification": verification,
    }


def doctor_command(args: argparse.Namespace) -> dict[str, Any]:
    root = mediacrawler_root(args.mediacrawler_root)
    tools = {
        name: shutil.which(name) or ""
        for name in ("python3", "curl", "aria2c", "ffprobe", "git", "uv", "node")
    }
    commit = ""
    if (root / ".git").exists() and shutil.which("git"):
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode == 0:
            commit = completed.stdout.strip()
    return {
        "status": "ready" if tools["python3"] and tools["curl"] else "missing_required_dependency",
        "context_id": context_id(),
        "version": VERSION,
        "tools": tools,
        "keychain_authorization": bool(read_keychain_cookie()),
        "environment_authorization": bool(os.environ.get(COOKIE_ENV, "").strip()),
        "mediacrawler": {
            "path": str(root),
            "ready": (root / "main.py").is_file(),
            "commit": commit,
            "expected_commit": MEDIACRAWLER_COMMIT,
        },
    }


def self_test_command() -> dict[str, Any]:
    failures: list[str] = []
    detections = {
        "https://weixin.qq.com/sph/example": "wechat",
        "https://www.douyin.com/video/123": "dy",
        "https://example.com/a.mp4": "direct",
    }
    for url, expected in detections.items():
        actual = url_kind(url)[0]
        if actual != expected:
            failures.append(f"detect:{expected}!={actual}")
    with tempfile.TemporaryDirectory(prefix="lov-media-crawler-test-") as temp:
        sample = Path(temp) / "sample.mp4"
        sample.write_bytes(b"\x00\x00\x00\x18ftypisom" + b"0" * 64)
        check = verify_media(sample, run_ffprobe=False)
        if not check.get("ok"):
            failures.append("verify:synthetic-mp4")
    return {
        "status": "passed" if not failures else "failed",
        "context_id": context_id(),
        "checks": 4,
        "failures": failures,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Inspect local runtime readiness")
    doctor.add_argument("--mediacrawler-root", default="")
    doctor.add_argument("--json", action="store_true")

    probe = subparsers.add_parser("probe", help="Detect a URL and fetch safe metadata")
    probe.add_argument("url")
    probe.add_argument("--mediacrawler-root", default="")
    probe.add_argument("--json", action="store_true")

    download = subparsers.add_parser("download", help="Resolve and download one media URL")
    download.add_argument("url")
    download.add_argument("--output-dir", default="downloads")
    download.add_argument("--filename", default="")
    download.add_argument("--connections", type=int, default=8)
    download.add_argument("--worker-url", default="")
    download.add_argument("--allow-public-resolver", action="store_true")
    download.add_argument("--mediacrawler-root", default="")
    download.add_argument("--overwrite", action="store_true")
    download.add_argument("--json-report", default="")
    download.add_argument("--json", action="store_true")

    setup = subparsers.add_parser("setup-mediacrawler", help="Prepare a pinned upstream checkout")
    setup.add_argument("--accept-noncommercial-license", action="store_true")
    setup.add_argument("--mediacrawler-root", default="")
    setup.add_argument("--json", action="store_true")

    test = subparsers.add_parser("self-test", help="Run deterministic offline checks")
    test.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    report_path = Path(args.json_report).expanduser() if getattr(args, "json_report", "") else None
    try:
        if args.command == "doctor":
            result = doctor_command(args)
        elif args.command == "probe":
            result = probe_command(args)
        elif args.command == "download":
            result = download_command(args)
        elif args.command == "setup-mediacrawler":
            result = setup_mediacrawler(args)
        else:
            result = self_test_command()
        write_json(report_path, result)
        output_result(result, getattr(args, "json", False))
        return 0 if result.get("status") not in {"failed", "missing_required_dependency"} else 1
    except JobError as exc:
        result = {
            "status": exc.code,
            "code": exc.code,
            "message": exc.message,
            "next_action": exc.next_action,
            "metadata": exc.metadata,
            "context_id": context_id(),
        }
        write_json(report_path, result)
        output_result(result, getattr(args, "json", False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
