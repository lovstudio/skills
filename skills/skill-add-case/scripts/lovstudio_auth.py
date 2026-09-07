#!/usr/bin/env python3
"""Bundled LovStudio login adapter; no transcript discovery or upload.

Auth functions adapted from lov-share-session 0.4.1 (MIT, LovStudio contributors).
Kept in the installable package so a new user needs no unpublished sibling Skill.
The credential cache and device/refresh API contract remain compatible.
"""
from __future__ import annotations
import argparse
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional

AUTH_SCOPE = "yoda"
GZIP_THRESHOLD_BYTES = 1024 * 1024

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class ShareError(Exception):
    """Raised for any failing step; carries an exit-code hint."""

    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code

def load_access_token(args: argparse.Namespace) -> str:
    """Resolve a Lovstudio access token with the skill-creator precedence.

    Order: explicit --token > env LOVSTUDIO_ACCESS_TOKEN > stored local cache/cookie
    > refresh from a stored refresh token > device-flow login.
    """
    if args.token:
        return args.token
    for env in ("LOVSTUDIO_ACCESS_TOKEN", "YODA_ACCESS_TOKEN"):
        value = os.environ.get(env)
        if value and value.strip():
            return value.strip()

    cached = load_cached_token(args.profile_path)
    if cached:
        return cached

    refresh = load_refresh_token(args.profile_path)
    if refresh:
        try:
            return run_refresh(args.base_url, refresh, args.timeout, args.profile_path)
        except ShareError:
            # Fall through to a full device-flow sign-in rather than fail hard.
            pass

    return device_flow_signin(args)

def credential_store_path(profile_path: Optional[Path]) -> Path:
    """Where tokens are cached. Not part of durable profile records."""
    base = profile_path.parent if profile_path else Path.home() / ".lovstudio"
    return base / ".session-share-credentials.json"

def load_cached_token(profile_path: Optional[Path]) -> Optional[str]:
    path = credential_store_path(profile_path)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data.get("access_token")

def load_refresh_token(profile_path: Optional[Path]) -> Optional[str]:
    path = credential_store_path(profile_path)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data.get("refresh_token")

def save_credentials(profile_path: Optional[Path], access: str, refresh: Optional[str]) -> None:
    path = credential_store_path(profile_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {}
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    data["access_token"] = access
    if refresh:
        data["refresh_token"] = refresh
    try:
        path.write_text(json.dumps(data), encoding="utf-8")
        os.chmod(path, 0o600)
    except OSError:
        # Non-fatal: never let a cache write block the share.
        pass

def run_refresh(
    base_url: str,
    refresh_token: str,
    timeout: int,
    profile_path: Optional[Path] = None,
) -> str:
    resp = http_json(
        "POST", f"{base_url}/api/cli/auth/refresh",
        body={"refreshToken": refresh_token},
        jwt=None,
        timeout=timeout,
    )
    if "accessToken" not in resp:
        raise ShareError("Lovstudio refresh did not return an access token", 2)
    access = resp["accessToken"]
    save_credentials(profile_path, access, resp.get("refreshToken") or refresh_token)
    return access

def device_flow_signin(args: argparse.Namespace) -> str:
    """Interactive OAuth device flow: print a URL, poll until the user approves."""
    start = http_json(
        "POST", f"{args.base_url}/api/cli/auth/start",
        body={"clientName": "Skill case contributor", "scope": AUTH_SCOPE},
        jwt=None,
        timeout=args.timeout,
    )
    if "verificationUri" not in start or "deviceCode" not in start:
        raise ShareError("Lovstudio device flow did not return a verification URI", 2)

    print("请在浏览器打开以下链接并登录授权：", file=sys.stderr)
    print(f"  {start.get('verificationUriComplete') or start['verificationUri']}", file=sys.stderr)
    if start.get("userCode"):
        print(f"  授权码：{start['userCode']}", file=sys.stderr)

    device_code = start["deviceCode"]
    interval = max(int(start.get("interval", 5)), 1)
    deadline = time.time() + int(start.get("expiresIn", 600))
    while time.time() < deadline:
        time.sleep(interval)
        try:
            poll = http_json(
                "POST", f"{args.base_url}/api/cli/auth/poll",
                body={"deviceCode": device_code},
                jwt=None,
                timeout=args.timeout,
            )
        except ShareError as exc:
            poll = getattr(exc, "payload", {}) or {}
        if poll.get("status") == "authenticated":
            access = poll["accessToken"]
            save_credentials(args.profile_path, access, poll.get("refreshToken"))
            return access
        error = poll.get("error", "")
        if error == "authorization_pending":
            continue
        if error == "slow_down":
            interval *= 2
            continue
        if error == "expired_token":
            raise ShareError("加载授权码已过期，请重试", 2)
        if error == "access_denied":
            raise ShareError("授权被拒绝", 2)
    raise ShareError("加载授权超时，请重试", 2)

def http_json(
    method: str,
    url: str,
    body: Optional[dict[str, Any]],
    jwt: Optional[str],
    timeout: int,
) -> dict[str, Any]:
    if not url.startswith("https://lovstudio.ai/api/cli/auth/"):
        raise ShareError("Unexpected authentication endpoint", 2)
    data = None
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        # Cloudflare rejects the bare Python urllib fingerprint with 403 error
        # 1010. Sending a browser-like User-Agent + Accept head the TLS/HTTP
        # fingerprint check off, regardless of whether the request routes via a proxy.
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"
    if body is not None:
        raw = json.dumps(body).encode("utf-8")
        if len(raw) > GZIP_THRESHOLD_BYTES:
            data = gzip.compress(raw)
            headers["Content-Encoding"] = "gzip"
        else:
            data = raw
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            payload = response.read()
            if payload:
                return json.loads(payload.decode("utf-8"))
            return {}
    except urllib.error.HTTPError as exc:
        payload: dict[str, Any] = {}
        raw = exc.read()
        if raw:
            try:
                payload = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                payload = {"message": raw.decode("utf-8", errors="replace")}
        err = ShareError(f"HTTP {exc.code}: {payload.get('error') or payload.get('message', '')}", 3)
        err.payload = payload
        err.status = exc.code
        raise err
    except urllib.error.URLError as exc:
        raise ShareError(f"网络请求失败: {exc.reason}", 2) from exc
    except OSError as exc:
        raise ShareError(f"网络请求失败: {exc}", 2) from exc
