#!/usr/bin/env python3
"""Authorize Tencent Yuanbao in a visible browser and save its Cookie securely."""

from __future__ import annotations

import argparse
import getpass
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from media_crawler import (  # noqa: E402
    KEYCHAIN_SERVICE,
    JobError,
    normalize_url,
    resolve_wechat_direct,
)


def cookie_header(cookies: list[dict]) -> str:
    pairs: list[str] = []
    for item in cookies:
        name = str(item.get("name", "")).strip()
        value = str(item.get("value", "")).strip()
        if name and value:
            pairs.append(f"{name}={value}")
    return "; ".join(pairs)


def save_keychain(cookie: str) -> None:
    if sys.platform != "darwin" or not shutil.which("security"):
        raise RuntimeError(
            "当前系统不支持自动凭据存储；请在当前进程设置 LOV_MEDIA_CRAWLER_YUANBAO_COOKIE。"
        )
    completed = subprocess.run(
        [
            "security",
            "add-generic-password",
            "-U",
            "-s",
            KEYCHAIN_SERVICE,
            "-a",
            getpass.getuser(),
            "-w",
            cookie,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("无法写入 macOS Keychain。")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-url", required=True, help="A WeChat Channels sph share URL")
    parser.add_argument("--timeout", type=int, default=300)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    url = normalize_url(args.test_url)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "缺少 Playwright。可用 uv 临时运行：\n"
            "uv run --with playwright python scripts/authorize_yuanbao.py --test-url URL",
            file=sys.stderr,
        )
        return 2

    print("将打开独立 Chrome 窗口。请登录腾讯元宝；检测成功后窗口会自动关闭。")
    deadline = time.monotonic() + max(30, args.timeout)
    with tempfile.TemporaryDirectory(prefix="lov-media-crawler-yuanbao-") as profile:
        with sync_playwright() as playwright:
            try:
                context = playwright.chromium.launch_persistent_context(
                    profile, channel="chrome", headless=False
                )
            except Exception:
                context = playwright.chromium.launch_persistent_context(profile, headless=False)
            try:
                page = context.pages[0] if context.pages else context.new_page()
                page.goto("https://yuanbao.tencent.com/", wait_until="domcontentloaded", timeout=60_000)
                last_error = ""
                while time.monotonic() < deadline:
                    header = cookie_header(context.cookies(["https://yuanbao.tencent.com/"]))
                    if header:
                        try:
                            data = resolve_wechat_direct(url, header)
                            feed = data.get("feedInfo", {})
                            if isinstance(feed, dict) and (
                                feed.get("videoUrl")
                                or feed.get("h264VideoInfo")
                                or feed.get("h265VideoInfo")
                            ):
                                save_keychain(header)
                                print(f"授权成功，已保存到 macOS Keychain service={KEYCHAIN_SERVICE}")
                                return 0
                        except JobError as exc:
                            last_error = exc.code
                    page.wait_for_timeout(2000)
                print(
                    f"授权超时，未保存凭据。last_status={last_error or 'login_not_detected'}",
                    file=sys.stderr,
                )
                return 2
            finally:
                context.close()


if __name__ == "__main__":
    raise SystemExit(main())
