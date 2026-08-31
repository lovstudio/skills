#!/usr/bin/env python3
"""Submit an existing WeChat draft for publication and verify its final state."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from publish_via_gateway import (
    DEFAULT_GATEWAY_BASE,
    USER_AGENT,
    GatewayPublishError,
    resolve_env_manager_path,
    resolve_managed_secrets,
)


TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/stable_token"
SUBMIT_URL = "https://api.weixin.qq.com/cgi-bin/freepublish/submit"
STATUS_URL = "https://api.weixin.qq.com/cgi-bin/freepublish/get"
KEYCHAIN_SERVICE = "ai.lovstudio.oneshot"
KEYCHAIN_ACCOUNT = "wechat-credentials-v1"
STATUS_LABELS = {
    0: "成功",
    1: "发布中",
    2: "原创声明失败",
    3: "常规失败",
    4: "平台审核未通过",
    5: "成功后用户删除全部文章",
    6: "成功后系统封禁全部文章",
}
TERMINAL_STATUSES = {0, 2, 3, 4, 5, 6}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class Credentials:
    app_id: str
    app_secret: str
    source: str


class PublishError(RuntimeError):
    def __init__(
        self,
        stage: str,
        message: str,
        *,
        code: int | None = None,
        recovery: str | None = None,
        whitelist_ip: str | None = None,
    ) -> None:
        super().__init__(message)
        self.stage = stage
        self.code = code
        self.recovery = recovery
        self.whitelist_ip = whitelist_ip

    def as_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "platform": "wechat_official_account",
            "state": "failed",
            "stage": self.stage,
            "code": self.code,
            "message": str(self),
            "recovery": self.recovery,
            "whitelistIp": self.whitelist_ip,
            "checkedAt": utc_now(),
        }


def extract_ipv4(message: str) -> str | None:
    candidates = re.findall(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])", message)
    for candidate in candidates:
        octets = candidate.split(".")
        if all(0 <= int(octet) <= 255 for octet in octets):
            return candidate
    return None


def recovery_for_code(code: int, message: str) -> tuple[str | None, str | None]:
    if code == 40164:
        address = extract_ipv4(message)
        return "仅 direct 诊断模式需要把提取出的 IPv4 加入公众号 API IP 白名单；默认网关模式请检查后端固定出口。", address
    if code == 40013:
        return "重新核对以 wx 开头的 AppID。", None
    if code in {40001, 40125}:
        return "在微信开发者平台重新获取或重置 AppSecret。", None
    if code == 48001:
        return "检查公众号认证状态以及草稿箱、发布接口权限。", None
    return "复制完整错误详情并在公众号接口权限与请求记录中核对。", None


def parse_integer_field(
    value: object,
    *,
    field: str,
    stage: str,
    default: int | None = None,
) -> int:
    if value is None and default is not None:
        return default
    if isinstance(value, bool):
        raise PublishError(stage, f"微信接口字段 {field} 不是有效整数：{value!r}")
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise PublishError(
            stage,
            f"微信接口字段 {field} 不是有效整数：{value!r}",
        ) from error


def validate_credentials(app_id: str, app_secret: str, source: str) -> Credentials:
    app_id = app_id.strip()
    app_secret = app_secret.strip()
    if not re.fullmatch(r"wx[A-Za-z0-9]{16}", app_id):
        raise PublishError("credentials", "AppID 应以 wx 开头，共 18 位。")
    if len(app_secret) < 16:
        raise PublishError("credentials", "AppSecret 长度异常，请重新获取完整值。")
    return Credentials(app_id, app_secret, source)


def credentials_from_environment(environ: Mapping[str, str] | None = None) -> Credentials | None:
    values = os.environ if environ is None else environ
    app_id = values.get("WECHAT_APP_ID", "").strip()
    app_secret = values.get("WECHAT_APP_SECRET", "").strip()
    if not app_id and not app_secret:
        return None
    if not app_id or not app_secret:
        raise PublishError(
            "credentials",
            "WECHAT_APP_ID 与 WECHAT_APP_SECRET 需要成对设置。",
        )
    return validate_credentials(app_id, app_secret, "environment")


def credentials_from_oneshot_keychain(
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> Credentials | None:
    if platform.system() != "Darwin":
        return None
    try:
        result = runner(
            [
                "security",
                "find-generic-password",
                "-s",
                KEYCHAIN_SERVICE,
                "-a",
                KEYCHAIN_ACCOUNT,
                "-w",
            ],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise PublishError("credentials", f"OneShot Keychain 记录格式异常：{error}") from error
    status = str(payload.get("status", "")).lower()
    if status != "connected":
        raise PublishError("credentials", "OneShot 中的公众号连接状态尚未标记为 connected。")
    return validate_credentials(
        str(payload.get("appId") or payload.get("app_id") or ""),
        str(payload.get("appSecret") or payload.get("app_secret") or ""),
        "oneshot-keychain",
    )


def resolve_credentials(source: str) -> Credentials:
    if source in {"auto", "env"}:
        credentials = credentials_from_environment()
        if credentials:
            return credentials
        if source == "env":
            raise PublishError(
                "credentials",
                "请在当前进程设置 WECHAT_APP_ID 与 WECHAT_APP_SECRET。",
            )
    if source in {"auto", "oneshot-keychain"}:
        credentials = credentials_from_oneshot_keychain()
        if credentials:
            return credentials
    raise PublishError(
        "credentials",
        "未找到可用公众号凭据；请连接 OneShot 公众号账号，或为当前进程设置 WECHAT_APP_ID 与 WECHAT_APP_SECRET。",
    )


def post_json(url: str, payload: Mapping[str, object], stage: str, timeout: float) -> dict[str, object]:
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read()
    except HTTPError as error:
        raise PublishError(stage, f"微信接口返回 HTTP {error.code}。") from error
    except URLError as error:
        raise PublishError(stage, f"连接微信接口失败：{error.reason}") from error
    except TimeoutError as error:
        raise PublishError(stage, "连接微信接口超时。") from error

    try:
        result = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PublishError(stage, "微信接口响应不是有效 JSON。") from error
    if not isinstance(result, dict):
        raise PublishError(stage, "微信接口响应结构异常。")

    raw_code = result.get("errcode")
    code = parse_integer_field(raw_code, field="errcode", stage=stage, default=0)
    if code != 0:
        message = str(result.get("errmsg") or "微信接口未返回详细原因")
        recovery, address = recovery_for_code(code, message)
        raise PublishError(
            stage,
            message,
            code=code,
            recovery=recovery,
            whitelist_ip=address,
        )
    return result


def post_gateway_json(
    base_url: str,
    path: str,
    payload: Mapping[str, object],
    gateway_api_key: str,
    stage: str,
    timeout: float,
) -> dict[str, object]:
    request = Request(
        base_url.rstrip("/") + path,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": USER_AGENT,
            "X-API-Key": gateway_api_key,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read()
    except HTTPError as error:
        try:
            response_payload = json.loads(error.read().decode("utf-8", "replace"))
        except json.JSONDecodeError:
            response_payload = {}
        detail = response_payload.get("detail") if isinstance(response_payload, dict) else None
        if not isinstance(detail, str):
            detail = f"微信网关返回 HTTP {error.code}。"
        raise PublishError(stage, detail, code=error.code) from None
    except URLError as error:
        raise PublishError(stage, f"连接微信网关失败：{error.reason}") from error
    except TimeoutError as error:
        raise PublishError(stage, "连接微信网关超时。") from error

    try:
        result = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PublishError(stage, "微信网关响应不是有效 JSON。") from error
    if not isinstance(result, dict):
        raise PublishError(stage, "微信网关响应结构异常。")
    return result


def fetch_access_token(credentials: Credentials, timeout: float) -> str:
    result = post_json(
        TOKEN_URL,
        {
            "grant_type": "client_credential",
            "appid": credentials.app_id,
            "secret": credentials.app_secret,
            "force_refresh": False,
        },
        "stable_token",
        timeout,
    )
    token = result.get("access_token")
    if not isinstance(token, str) or not token:
        raise PublishError("stable_token", "微信接口未返回 access_token。")
    return token


def _token_url(base: str, access_token: str) -> str:
    return f"{base}?{urlencode({'access_token': access_token})}"


def submit_draft(access_token: str, media_id: str, timeout: float) -> dict[str, object]:
    media_id = media_id.strip()
    if not media_id:
        raise PublishError("freepublish_submit", "media_id 为空。")
    result = post_json(
        _token_url(SUBMIT_URL, access_token),
        {"media_id": media_id},
        "freepublish_submit",
        timeout,
    )
    publish_id = result.get("publish_id")
    if not isinstance(publish_id, str) or not publish_id:
        raise PublishError("freepublish_submit", "发布接口未返回 publish_id。")
    return result


def query_status(access_token: str, publish_id: str, timeout: float) -> dict[str, object]:
    publish_id = publish_id.strip()
    if not publish_id:
        raise PublishError("freepublish_get", "publish_id 为空。")
    return post_json(
        _token_url(STATUS_URL, access_token),
        {"publish_id": publish_id},
        "freepublish_get",
        timeout,
    )


def submit_draft_via_gateway(
    *,
    base_url: str,
    app_id: str,
    app_secret: str,
    gateway_api_key: str,
    media_id: str,
    timeout: float,
) -> dict[str, object]:
    media_id = media_id.strip()
    if not media_id:
        raise PublishError("freepublish_submit", "media_id 为空。")
    result = post_gateway_json(
        base_url,
        "/freepublish/submit",
        {"app_id": app_id, "app_secret": app_secret, "media_id": media_id},
        gateway_api_key,
        "freepublish_submit",
        timeout,
    )
    publish_id = result.get("publish_id")
    if not isinstance(publish_id, str) or not publish_id:
        raise PublishError("freepublish_submit", "微信网关未返回 publish_id。")
    return result


def query_status_via_gateway(
    *,
    base_url: str,
    app_id: str,
    app_secret: str,
    gateway_api_key: str,
    publish_id: str,
    timeout: float,
) -> dict[str, object]:
    publish_id = publish_id.strip()
    if not publish_id:
        raise PublishError("freepublish_get", "publish_id 为空。")
    return post_gateway_json(
        base_url,
        "/freepublish/get",
        {"app_id": app_id, "app_secret": app_secret, "publish_id": publish_id},
        gateway_api_key,
        "freepublish_get",
        timeout,
    )


def article_urls(payload: Mapping[str, object]) -> list[str]:
    detail = payload.get("article_detail")
    if not isinstance(detail, Mapping):
        return []
    items = detail.get("item")
    if isinstance(items, Mapping):
        items = [items]
    if not isinstance(items, list):
        return []
    urls: list[str] = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        url = item.get("article_url")
        if isinstance(url, str) and url and url not in urls:
            urls.append(url)
    return urls


def receipt_from_status(
    publish_id: str,
    payload: Mapping[str, object],
    *,
    action: str,
) -> dict[str, object]:
    raw_status = payload.get("publish_status")
    status = parse_integer_field(
        raw_status,
        field="publish_status",
        stage="freepublish_get",
    )
    urls = article_urls(payload)
    article_id = payload.get("article_id")
    has_article_identifier = bool(article_id) or bool(urls)
    if status == 0 and has_article_identifier:
        state = "published"
    elif status == 0:
        state = "publishing"
    elif status == 1:
        state = "publishing"
    elif status in TERMINAL_STATUSES:
        state = "publish_failed"
    else:
        raise PublishError("freepublish_get", f"未知 publish_status：{raw_status}")

    fail_indexes = payload.get("fail_idx")
    if not isinstance(fail_indexes, list):
        fail_indexes = []
    return {
        "schemaVersion": 1,
        "platform": "wechat_official_account",
        "action": action,
        "state": state,
        "publishId": publish_id,
        "publishStatus": status,
        "publishStatusLabel": STATUS_LABELS.get(status, "未知"),
        "articleId": article_id,
        "articleUrls": urls,
        "failIndexes": fail_indexes,
        "verificationPending": status == 0 and not has_article_identifier,
        "checkedAt": utc_now(),
        "technicalDetail": None,
    }


def poll_until_terminal(
    fetch: Callable[[], dict[str, object]],
    *,
    wait_seconds: float,
    poll_seconds: float,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> tuple[dict[str, object], bool]:
    deadline = monotonic() + max(0.0, wait_seconds)
    while True:
        payload = fetch()
        status = parse_integer_field(
            payload.get("publish_status"),
            field="publish_status",
            stage="freepublish_get",
        )
        if status == 0 and (payload.get("article_id") or article_urls(payload)):
            return payload, False
        if status in TERMINAL_STATUSES - {0}:
            return payload, False
        now = monotonic()
        if now >= deadline:
            return payload, True
        sleep(max(0.1, min(poll_seconds, deadline - now)))


def write_receipt(receipt: Mapping[str, object], path: Path | None) -> None:
    if path is None:
        return
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--transport",
        choices=("gateway", "direct"),
        default="gateway",
        help="默认经 uni-api 固定出口调用微信；direct 仅用于显式诊断。",
    )
    parser.add_argument("--app-id")
    parser.add_argument("--wechat-secret-locator")
    parser.add_argument("--gateway-key-locator")
    parser.add_argument("--gateway-base", default=DEFAULT_GATEWAY_BASE)
    parser.add_argument("--env-manager-script")
    parser.add_argument(
        "--credential-source",
        choices=("auto", "env", "oneshot-keychain"),
        default="auto",
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--receipt", type=Path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    submit = subparsers.add_parser("submit", help="提交 media_id 并可选等待终态")
    submit.add_argument("--media-id", required=True)
    submit.add_argument("--wait-seconds", type=float, default=300.0)
    submit.add_argument("--poll-seconds", type=float, default=5.0)
    _add_common_options(submit)

    status = subparsers.add_parser("status", help="查询既有 publish_id")
    status.add_argument("--publish-id", required=True)
    _add_common_options(status)
    return parser


def run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    gateway_context: tuple[Credentials, str] | None = None
    token: str | None = None
    if args.transport == "gateway":
        if not args.app_id or not args.wechat_secret_locator or not args.gateway_key_locator:
            raise PublishError(
                "credentials",
                "网关模式需要 --app-id、--wechat-secret-locator 与 --gateway-key-locator。",
            )
        try:
            secrets = resolve_managed_secrets(
                env_manager_script=resolve_env_manager_path(args.env_manager_script),
                wechat_secret_locator=args.wechat_secret_locator,
                gateway_key_locator=args.gateway_key_locator,
            )
        except (GatewayPublishError, KeyError, OSError, RuntimeError) as error:
            raise PublishError("credentials", f"读取受管密钥失败：{error}") from None
        credentials = validate_credentials(args.app_id, secrets.app_secret, "lov-env-management")
        gateway_context = (credentials, secrets.gateway_api_key)
    else:
        credentials = resolve_credentials(args.credential_source)
        token = fetch_access_token(credentials, args.timeout)

    def get_status(publish_id: str) -> dict[str, object]:
        if gateway_context:
            managed_credentials, gateway_api_key = gateway_context
            return query_status_via_gateway(
                base_url=args.gateway_base,
                app_id=managed_credentials.app_id,
                app_secret=managed_credentials.app_secret,
                gateway_api_key=gateway_api_key,
                publish_id=publish_id,
                timeout=args.timeout,
            )
        assert token is not None
        return query_status(token, publish_id, args.timeout)

    if args.command == "status":
        payload = get_status(args.publish_id)
        receipt = receipt_from_status(args.publish_id.strip(), payload, action="status")
    else:
        if gateway_context:
            managed_credentials, gateway_api_key = gateway_context
            submitted = submit_draft_via_gateway(
                base_url=args.gateway_base,
                app_id=managed_credentials.app_id,
                app_secret=managed_credentials.app_secret,
                gateway_api_key=gateway_api_key,
                media_id=args.media_id,
                timeout=args.timeout,
            )
        else:
            assert token is not None
            submitted = submit_draft(token, args.media_id, args.timeout)
        publish_id = str(submitted["publish_id"])
        if args.wait_seconds <= 0:
            receipt = {
                "schemaVersion": 1,
                "platform": "wechat_official_account",
                "action": "publish",
                "state": "publish_submitted",
                "mediaId": args.media_id.strip(),
                "publishId": publish_id,
                "checkedAt": utc_now(),
                "technicalDetail": None,
            }
        else:
            payload, timed_out = poll_until_terminal(
                lambda: get_status(publish_id),
                wait_seconds=args.wait_seconds,
                poll_seconds=args.poll_seconds,
            )
            receipt = receipt_from_status(publish_id, payload, action="publish")
            receipt["mediaId"] = args.media_id.strip()
            if timed_out:
                receipt["timedOut"] = True

    state = receipt["state"]
    exit_code = 0 if state in {"publish_submitted", "published"} else 3 if state == "publishing" else 4
    return receipt, exit_code


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        receipt, exit_code = run(args)
    except PublishError as error:
        receipt = error.as_dict()
        write_receipt(receipt, getattr(args, "receipt", None))
        print(json.dumps(receipt, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    write_receipt(receipt, args.receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
