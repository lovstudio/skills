#!/usr/bin/env python3
"""Upload local files to a Synology NAS and prune them after verification.

The default mutation policy is deliberately safe:
- files are uploaded first;
- remote size and optionally MD5 are verified;
- local files are moved to a trash directory, not unlinked;
- a failed upload or verification never deletes the local source.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import mimetypes
import os
import posixpath
import shutil
import subprocess
import sys
import time
import urllib.parse
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    import requests
    from requests_toolbelt import MultipartEncoder
    import synology_api.auth as syno_auth
except Exception as exc:  # pragma: no cover - import error path is environment dependent
    sys.stderr.write(
        "Missing runtime dependency. Run scripts/install.sh from the skill directory first.\n"
        f"Import error: {exc}\n"
    )
    raise SystemExit(2)

try:
    from urllib3.exceptions import InsecureRequestWarning
    warnings.filterwarnings("ignore", category=InsecureRequestWarning)
except Exception:
    pass

APP = "synology-cli"
DEFAULT_CONFIG = Path.home() / ".config" / APP / "config.json"
DEFAULT_TRASH = Path.home() / ".local" / "share" / APP / "trash"
DEFAULT_AUDIT = Path.home() / ".local" / "state" / APP / "audit.jsonl"
DEFAULT_KEYCHAIN_SERVICE = APP
DEFAULT_REMOTE_DIR = "/home/Music/MP3"
DEFAULT_QC_DOMAIN = "cn"
QC_SERV_URLS = {
    "cn": "https://global.quickconnect.cn/Serv.php",
    "to": "https://global.quickconnect.to/Serv.php",
}
USER_AGENT = "synology-cli/1.0"


class SynoUploadError(RuntimeError):
    """Base error for this tool."""


class SynologyAPIError(SynoUploadError):
    """A DSM API response with success=false."""

    def __init__(self, api: str, method: str, code: int | None, detail: Any = None) -> None:
        self.api = api
        self.method = method
        self.code = code
        self.detail = detail
        super().__init__(f"{api}.{method} failed (code={code}): {detail}")


@dataclass
class Settings:
    source: Path
    remote_dir: str
    quickconnect_id: str | None
    quickconnect_domain: str
    base_url: str | None
    username: str
    password: str
    dsm_version: int
    cert_verify: bool
    timeout: int
    retries: int
    verify_md5: bool
    recursive: bool
    pattern: str | None
    limit: int | None
    dry_run: bool
    delete_mode: str
    trash_dir: Path
    audit_log: Path
    json_output: bool
    config_path: Path


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _redact(value: str | None) -> str:
    if not value:
        return "<empty>"
    if len(value) <= 4:
        return "***"
    return value[:2] + "***" + value[-2:]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SynoUploadError(f"Cannot parse config {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SynoUploadError(f"Config must be a JSON object: {path}")
    return data


def _pick(cli_value: Any, config: Mapping[str, Any], key: str, env_name: str, default: Any) -> Any:
    if cli_value is not None:
        return cli_value
    if env_name in os.environ and os.environ[env_name] != "":
        return os.environ[env_name]
    if key in config and config[key] not in (None, ""):
        return config[key]
    return default


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on", "y"}


def _keychain_password(service: str, account: str) -> str | None:
    try:
        proc = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    value = proc.stdout.strip()
    return value or None


def _resolve_password(config: Mapping[str, Any], username: str, keychain_service: str) -> str:
    for key in ("password",):
        value = config.get(key)
        if isinstance(value, str) and value:
            return value
    env_password = os.environ.get("SYNO_PASSWORD")
    if env_password:
        return env_password
    stored = _keychain_password(keychain_service, username)
    if stored:
        return stored
    raise SynoUploadError(
        "No DSM password available. Set SYNO_PASSWORD for a one-off run, or store it in "
        f"macOS Keychain with service={keychain_service!r}, account={username!r}."
    )


def _iter_files(source: Path, recursive: bool, pattern: str | None) -> list[Path]:
    if source.is_file():
        return [source]
    if not source.is_dir():
        raise SynoUploadError(f"Source path does not exist: {source}")
    iterator: Iterable[Path]
    if recursive:
        iterator = source.rglob("*")
    else:
        iterator = source.iterdir()
    files = [p for p in iterator if p.is_file()]
    if pattern:
        files = [p for p in files if p.match(pattern)]
    return sorted(files, key=lambda p: str(p))


def _sha_md5(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _rel_posix(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def _remote_join(*parts: str) -> str:
    cleaned = [p.strip("/") for p in parts if p and p.strip("/")]
    return "/" + "/".join(cleaned) if cleaned else "/"


def _multipart_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _decode_json_param(value: str) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return value


def _decode_api_response(response: requests.Response, api: str, method: str) -> dict[str, Any]:
    try:
        payload = response.json()
    except Exception as exc:
        raise SynologyAPIError(api, method, response.status_code, response.text[:500]) from exc
    if response.status_code != 200 or not isinstance(payload, dict) or not payload.get("success"):
        error = payload.get("error") if isinstance(payload, dict) else payload
        code = error.get("code") if isinstance(error, dict) else None
        raise SynologyAPIError(api, method, code, error)
    return payload


def _extract_quickconnect_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def resolve_quickconnect(
    quickconnect_id: str,
    domain: str = DEFAULT_QC_DOMAIN,
    serv_url: str | None = None,
    verify: bool = True,
    timeout: int = 30,
) -> tuple[str, dict[str, str], requests.Session]:
    """Resolve a QuickConnect ID to a relay HTTPS origin.

    This follows the protocol used by the QuickConnect web portal: ask a
    control server for server info, request a tunnel when needed, then ping
    the relay host before using it for DSM Web API calls.
    """
    domain = domain if domain in {"cn", "to"} else DEFAULT_QC_DOMAIN
    control_url = serv_url or QC_SERV_URLS[domain]
    portal_origin = f"https://{quickconnect_id}.quickconnect.{domain}"
    headers = {
        "Origin": portal_origin,
        "Referer": portal_origin + "/",
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/json",
    }
    session = requests.Session()
    # The portal sets relay cookies before the XHR calls.
    try:
        session.get(portal_origin + "/", headers=headers, timeout=min(timeout, 15), verify=verify)
    except Exception:
        pass

    def post_control(url: str, command: str) -> list[dict[str, Any]]:
        payload = [{
            "version": 1,
            "command": command,
            "stop_when_error": False,
            "stop_when_success": command == "request_tunnel",
            "id": "mainapp_https",
            "serverID": quickconnect_id,
            "is_gofile": False,
            "path": "",
        }]
        response = session.post(url, json=payload, headers=headers, timeout=timeout, verify=verify)
        response.raise_for_status()
        return _extract_quickconnect_items(response.json())

    def find_success(items: list[dict[str, Any]]) -> dict[str, Any] | None:
        for item in items:
            if item.get("errno") == 0 and isinstance(item.get("server"), dict):
                return item
        return None

    initial = post_control(control_url, "get_server_info")
    item = find_success(initial)
    if item is None:
        detail = initial[0] if initial else {"error": "empty QuickConnect response"}
        raise SynoUploadError(
            f"QuickConnect get_server_info failed for {quickconnect_id!r}: {detail}"
        )

    server = item.get("server") or {}
    env = item.get("env") or {}
    server_id = server.get("serverID") or quickconnect_id
    control_host = str(env.get("control_host") or "").strip()
    relay_region = env.get("relay_region")
    pingpong_path = server.get("pingpong_path")

    if not relay_region or not pingpong_path:
        if not control_host:
            raise SynoUploadError("QuickConnect response did not include env.control_host")
        tunnel_url = f"https://{control_host}/Serv.php"
        tunnel_items = post_control(tunnel_url, "request_tunnel")
        tunnel_item = find_success(tunnel_items)
        if tunnel_item is None:
            detail = tunnel_items[0] if tunnel_items else {"error": "empty tunnel response"}
            raise SynoUploadError(f"QuickConnect request_tunnel failed: {detail}")
        server = tunnel_item.get("server") or {}
        env = tunnel_item.get("env") or {}
        server_id = server.get("serverID") or server_id
        relay_region = env.get("relay_region") or relay_region
        pingpong_path = server.get("pingpong_path") or pingpong_path

    if not relay_region:
        raise SynoUploadError("QuickConnect response did not include env.relay_region")
    if not pingpong_path:
        pingpong_path = "/webman/pingpong.cgi?action=cors&quickconnect=true"

    relay_origin = f"https://{server_id}.{relay_region}.quickconnect.{domain}"
    ping_url = relay_origin + pingpong_path
    ping = session.get(ping_url, headers=headers, timeout=min(timeout, 15), verify=verify)
    ping.raise_for_status()
    return relay_origin.rstrip("/"), headers, session


class DSMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.auth: syno_auth.Authentication | None = None
        self.base_url: str = ""
        self.connected_via = ""
        self.last_connection_error: Exception | None = None

    def connect(self) -> None:
        errors: list[str] = []
        if self.settings.quickconnect_id:
            try:
                relay, headers, session = resolve_quickconnect(
                    self.settings.quickconnect_id,
                    self.settings.quickconnect_domain,
                    verify=True,
                    timeout=self.settings.timeout,
                )
                self._connect_auth(
                    base_url=relay,
                    quickconnect=True,
                    quickconnect_headers=headers,
                    session=session,
                )
                self.connected_via = f"quickconnect:{self.settings.quickconnect_id}"
                return
            except Exception as exc:
                errors.append(f"QuickConnect: {exc}")
                self.last_connection_error = exc

        if self.settings.base_url:
            try:
                self._connect_auth(base_url=self.settings.base_url, quickconnect=False)
                self.connected_via = f"base_url:{self.settings.base_url}"
                return
            except Exception as exc:
                errors.append(f"Base URL: {exc}")
                self.last_connection_error = exc

        raise SynoUploadError("; ".join(errors) if errors else "No connection method configured")

    def _connect_auth(
        self,
        base_url: str,
        quickconnect: bool,
        quickconnect_headers: dict[str, str] | None = None,
        session: requests.Session | None = None,
    ) -> None:
        parsed = urllib.parse.urlparse(base_url)
        if not parsed.scheme or not parsed.hostname:
            raise SynoUploadError(f"Invalid DSM base URL: {base_url!r}")
        if parsed.path not in ("", "/", "/webapi", "/webapi/"):
            raise SynoUploadError("DSM base URL must not contain an application path")
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        secure = parsed.scheme == "https"
        auth = syno_auth.Authentication(
            ip_address=parsed.hostname,
            port=str(port),
            username=self.settings.username,
            password=self.settings.password,
            secure=secure,
            cert_verify=self.settings.cert_verify,
            dsm_version=self.settings.dsm_version,
            debug=False,
            otp_code=None,
        )
        if quickconnect:
            if not quickconnect_headers:
                raise SynoUploadError("QuickConnect connection is missing relay headers")
            if session is None:
                session = requests.Session()
            auth._quickconnect_id = self.settings.quickconnect_id
            auth._base_url = base_url.rstrip("/") + "/webapi/"
            auth._quickconnect_headers = dict(quickconnect_headers)
            auth._requests_session = session
            auth._secure = True
        auth.login()
        auth.get_api_list()
        self.auth = auth
        self.base_url = auth._base_url

    def close(self) -> None:
        if self.auth is None:
            return
        try:
            self.auth.logout()
        except Exception:
            pass

    def _api_info(self, api: str) -> dict[str, Any]:
        assert self.auth is not None
        info = self.auth.full_api_list.get(api)
        return info if isinstance(info, dict) else {}

    def _api_version(self, api: str, fallback: int) -> int:
        info = self._api_info(api)
        try:
            return int(info.get("maxVersion") or fallback)
        except Exception:
            return fallback

    def api_get(self, api: str, method: str, version: int | None = None, **params: Any) -> dict[str, Any]:
        if self.auth is None:
            raise SynoUploadError("Not connected")
        version = version or self._api_version(api, 2)
        query: dict[str, Any] = {
            "api": api,
            "version": version,
            "method": method,
            "_sid": self.auth._sid,
        }
        query.update(params)
        try:
            response = self.auth._get(
                self.base_url + "entry.cgi",
                params=query,
                headers=self.auth._get_request_headers(),
                verify=self.settings.cert_verify,
                timeout=self.settings.timeout,
            )
        except Exception as exc:
            raise SynoUploadError(f"{api}.{method} request failed: {exc}") from exc
        return _decode_api_response(response, api, method)

    def list_shares(self) -> list[dict[str, Any]]:
        payload = self.api_get("SYNO.FileStation.List", "list_share", version=2)
        data = payload.get("data") or {}
        shares = data.get("shares") or []
        return [s for s in shares if isinstance(s, dict)]

    def remote_info(self, remote_path: str) -> dict[str, Any] | None:
        try:
            payload = self.api_get(
                "SYNO.FileStation.List",
                "getinfo",
                version=2,
                path=json.dumps([remote_path], ensure_ascii=False),
                additional=json.dumps(["size", "time", "type", "name", "perm"], ensure_ascii=False),
            )
        except SynologyAPIError as exc:
            if exc.code in {408, 900, 1003}:
                return None
            raise
        data = payload.get("data") or {}
        files = data.get("files") or data.get("items") or []
        if not files:
            return None
        first = files[0]
        if not isinstance(first, dict):
            return None
        additional = first.get("additional") if isinstance(first.get("additional"), dict) else {}
        return {
            "name": first.get("name"),
            "path": first.get("path") or remote_path,
            "isdir": bool(first.get("isdir")),
            "size": additional.get("size"),
            "mtime": additional.get("time", {}).get("mtime") if isinstance(additional.get("time"), dict) else additional.get("mtime"),
            "raw": first,
        }

    def upload(self, local_path: Path, remote_dir: str, overwrite: str = "overwrite") -> dict[str, Any]:
        if self.auth is None:
            raise SynoUploadError("Not connected")
        upload_info = self._api_info("SYNO.FileStation.Upload")
        version = self._api_version("SYNO.FileStation.Upload", 2)
        if version >= 3 and overwrite in {"overwrite", "skip"}:
            overwrite_value: Any = overwrite
        else:
            overwrite_value = overwrite == "overwrite"
        fields: dict[str, Any] = {
            "path": remote_dir,
            "create_parents": "true",
            "overwrite": _multipart_value(overwrite_value),
        }
        mime_type = mimetypes.guess_type(local_path.name)[0] or "application/octet-stream"
        params = {
            "api": "SYNO.FileStation.Upload",
            "version": version or 2,
            "method": "upload",
            "_sid": self.auth._sid,
        }
        with local_path.open("rb") as fh:
            fields["file"] = (local_path.name, fh, mime_type)
            encoder = MultipartEncoder(fields=fields)
            headers = self.auth._get_request_headers({
                "X-SYNO-TOKEN": self.auth._syno_token or "",
                "Content-Type": encoder.content_type,
            })
            try:
                response = self.auth._post(
                    self.base_url + "entry.cgi",
                    data=encoder,
                    params=params,
                    headers=headers,
                    verify=self.settings.cert_verify,
                    timeout=self.settings.timeout,
                )
            except Exception as exc:
                raise SynoUploadError(f"Upload request failed for {local_path}: {exc}") from exc
        return _decode_api_response(response, "SYNO.FileStation.Upload", "upload").get("data") or {}

    def remote_md5(self, remote_path: str) -> str:
        started = self.api_get(
            "SYNO.FileStation.MD5",
            "start",
            version=2,
            file_path=remote_path,
        )
        task_id = (started.get("data") or {}).get("taskid")
        if not task_id:
            raise SynoUploadError(f"MD5 task did not return a taskid for {remote_path}")
        deadline = time.monotonic() + max(self.settings.timeout, 30)
        while True:
            status = self.api_get(
                "SYNO.FileStation.MD5",
                "status",
                version=2,
                taskid=task_id,
            )
            data = status.get("data") or {}
            if data.get("finished"):
                md5 = data.get("md5")
                if not md5:
                    raise SynoUploadError(f"MD5 status finished without a hash for {remote_path}")
                return str(md5).lower()
            if time.monotonic() > deadline:
                raise SynoUploadError(f"Timed out waiting for remote MD5: {remote_path}")
            time.sleep(0.5)


def _load_settings(args: argparse.Namespace) -> Settings:
    config_path = Path(args.config).expanduser().resolve()
    config = _read_json(config_path)

    source_raw = _pick(getattr(args, "source", None), config, "source", "SYNO_SOURCE", None)
    if not source_raw:
        raise SynoUploadError("--source is required (or set source in the config file)")
    source = Path(str(source_raw)).expanduser().resolve()

    qcid = _pick(getattr(args, "quickconnect_id", None), config, "quickconnect_id", "SYNO_QUICKCONNECT_ID", None)
    base_url = _pick(getattr(args, "base_url", None), config, "base_url", "SYNO_BASE_URL", None)
    username = _pick(getattr(args, "username", None), config, "username", "SYNO_USERNAME", None)
    if not username:
        raise SynoUploadError("No DSM username. Set --username, config.username, or SYNO_USERNAME.")
    password = _resolve_password(
        config,
        str(username),
        str(_pick(getattr(args, "password_keychain_service", None), config, "password_keychain_service", "SYNO_KEYCHAIN_SERVICE", DEFAULT_KEYCHAIN_SERVICE)),
    )

    remote_dir = _pick(getattr(args, "remote_dir", None), config, "remote_dir", "SYNO_REMOTE_DIR", DEFAULT_REMOTE_DIR)
    domain = str(_pick(getattr(args, "quickconnect_domain", None), config, "quickconnect_domain", "SYNO_QUICKCONNECT_DOMAIN", DEFAULT_QC_DOMAIN)).lower()
    if domain not in {"cn", "to"}:
        raise SynoUploadError("quickconnect_domain must be 'cn' or 'to'")
    if not qcid and not base_url:
        raise SynoUploadError("No QuickConnect ID and no --base-url configured.")

    delete_mode = str(_pick(getattr(args, "delete_mode", None), config, "delete_mode", "SYNO_DELETE_MODE", "trash"))
    if delete_mode not in {"trash", "unlink", "none"}:
        raise SynoUploadError("delete_mode must be one of: trash, unlink, none")

    return Settings(
        source=source,
        remote_dir=str(remote_dir).rstrip("/") or "/",
        quickconnect_id=str(qcid) if qcid else None,
        quickconnect_domain=domain,
        base_url=str(base_url).rstrip("/") if base_url else None,
        username=str(username),
        password=password,
        dsm_version=int(_pick(getattr(args, "dsm_version", None), config, "dsm_version", "SYNO_DSM_VERSION", 7)),
        cert_verify=_as_bool(_pick(getattr(args, "cert_verify", None), config, "cert_verify", "SYNO_CERT_VERIFY", False), False),
        timeout=int(_pick(getattr(args, "timeout", None), config, "timeout", "SYNO_TIMEOUT", 60)),
        retries=int(_pick(getattr(args, "retries", None), config, "retries", "SYNO_RETRIES", 2)),
        verify_md5=_as_bool(_pick(getattr(args, "verify_md5", None), config, "verify_md5", "SYNO_VERIFY_MD5", True), True),
        recursive=_as_bool(_pick(getattr(args, "recursive", None), config, "recursive", "SYNO_RECURSIVE", True), True),
        pattern=str(_pick(getattr(args, "pattern", None), config, "pattern", "SYNO_PATTERN", "")) or None,
        limit=int(_pick(getattr(args, "limit", None), config, "limit", "SYNO_LIMIT", 0)) or None,
        dry_run=bool(getattr(args, "dry_run", False)),
        delete_mode=delete_mode,
        trash_dir=Path(str(_pick(getattr(args, "trash_dir", None), config, "trash_dir", "SYNO_TRASH_DIR", DEFAULT_TRASH))).expanduser().resolve(),
        audit_log=Path(str(_pick(getattr(args, "audit_log", None), config, "audit_log", "SYNO_AUDIT_LOG", DEFAULT_AUDIT))).expanduser().resolve(),
        json_output=bool(getattr(args, "json", False)),
        config_path=config_path,
    )


def _write_audit(path: Path, record: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _print_record(record: Mapping[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
        return
    action = record.get("action", "unknown")
    local = record.get("local_path", "")
    remote = record.get("remote_path", "")
    detail = record.get("detail", "")
    print(f"[{action}] {local} -> {remote}" + (f" ({detail})" if detail else ""))


def _remove_local(local: Path, settings: Settings, relative: str, timestamp: str) -> str | None:
    if settings.delete_mode == "none":
        return None
    if settings.dry_run:
        return "dry-run: local deletion skipped"
    if settings.delete_mode == "unlink":
        local.unlink()
        return None
    destination = settings.trash_dir / timestamp / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination = destination.with_name(f"{destination.name}.{int(time.time())}")
    shutil.move(str(local), str(destination))
    return str(destination)


def run(args: argparse.Namespace) -> int:
    settings = _load_settings(args)
    files = _iter_files(settings.source, settings.recursive, settings.pattern)
    if settings.limit:
        files = files[: settings.limit]
    if not files:
        print(json.dumps({"ok": True, "action": "no_files", "source": str(settings.source)}))
        return 0

    client = DSMClient(settings)
    connected = False
    try:
        client.connect()
        connected = True
    except Exception as exc:
        if not settings.dry_run:
            raise
        # Dry-run is still useful for planning if the NAS is temporarily offline.
        client.last_connection_error = exc

    base = settings.source if settings.source.is_dir() else settings.source.parent
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    totals = {"files": len(files), "uploaded": 0, "skipped": 0, "deleted": 0, "failed": 0}
    overall_ok = True
    for local in files:
        relative = local.name if settings.source.is_file() else _rel_posix(local, base)
        if settings.source.is_file():
            remote_dir = settings.remote_dir
        else:
            parent_rel = Path(relative).parent.as_posix()
            remote_dir = settings.remote_dir if parent_rel in ("", ".") else _remote_join(settings.remote_dir, parent_rel)
        remote_path = _remote_join(remote_dir, local.name)
        record: dict[str, Any] = {
            "timestamp": _now_iso(),
            "action": "plan",
            "local_path": str(local),
            "remote_path": remote_path,
            "size": local.stat().st_size,
        }
        try:
            if not connected:
                record.update({"action": "dry_run_unreachable", "detail": str(client.last_connection_error or "NAS not connected")})
                _print_record(record, settings.json_output)
                continue

            local_md5 = _sha_md5(local)
            existing = client.remote_info(remote_path)
            if existing and existing.get("size") == local.stat().st_size:
                if not settings.verify_md5 or client.remote_md5(remote_path) == local_md5:
                    record.update({"action": "already_present", "md5": local_md5})
                    if not settings.dry_run:
                        trash_path = _remove_local(local, settings, relative, timestamp)
                        if trash_path:
                            record["trash_path"] = trash_path
                        if not settings.dry_run and settings.delete_mode != "none" and not local.exists():
                            totals["deleted"] += 1
                    totals["skipped"] += 1
                    _write_audit(settings.audit_log, record)
                    _print_record(record, settings.json_output)
                    continue

            if settings.dry_run:
                record.update({"action": "dry_run_upload", "md5": local_md5, "detail": "no remote mutation"})
                _print_record(record, settings.json_output)
                continue

            last_error: Exception | None = None
            for attempt in range(settings.retries + 1):
                try:
                    client.upload(local, remote_dir, overwrite="overwrite")
                    last_error = None
                    break
                except Exception as exc:
                    last_error = exc
                    if attempt < settings.retries:
                        time.sleep(min(2 ** attempt, 5))
            if last_error:
                raise last_error

            remote_info = client.remote_info(remote_path)
            if not remote_info:
                raise SynoUploadError("Upload completed but remote file was not found")
            if remote_info.get("size") != local.stat().st_size:
                raise SynoUploadError(
                    f"Remote size mismatch: local={local.stat().st_size}, remote={remote_info.get('size')}"
                )
            remote_md5 = client.remote_md5(remote_path) if settings.verify_md5 else None
            if settings.verify_md5 and remote_md5 != local_md5:
                raise SynoUploadError(f"Remote MD5 mismatch: local={local_md5}, remote={remote_md5}")

            # Protect against a file changing during transfer.
            if _sha_md5(local) != local_md5:
                raise SynoUploadError("Local file changed during transfer; refusing to delete it")

            record.update({
                "action": "uploaded",
                "md5": local_md5,
                "remote_md5": remote_md5,
                "size": local.stat().st_size,
            })
            trash_path = _remove_local(local, settings, relative, timestamp)
            if trash_path:
                record["trash_path"] = trash_path
            if not settings.dry_run and settings.delete_mode != "none" and not local.exists():
                totals["deleted"] += 1
            totals["uploaded"] += 1
            _write_audit(settings.audit_log, record)
            _print_record(record, settings.json_output)
        except Exception as exc:
            overall_ok = False
            totals["failed"] += 1
            record.update({"action": "failed", "detail": str(exc)})
            _write_audit(settings.audit_log, record)
            _print_record(record, settings.json_output)
    if connected:
        client.close()
    summary = {"ok": overall_ok, "action": "summary", "server": client.connected_via, "totals": totals}
    if settings.json_output:
        print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(summary, ensure_ascii=False))
    return 0 if overall_ok else 1


def doctor(args: argparse.Namespace) -> int:
    # doctor does not require --source
    if getattr(args, "source", None) is None:
        args.source = "."
    config_path = Path(args.config).expanduser().resolve()
    config = _read_json(config_path)
    tmp_source = _pick(None, config, "source", "SYNO_SOURCE", None) or "."
    args.source = tmp_source
    settings = _load_settings(args)
    client = DSMClient(settings)
    try:
        client.connect()
        shares = client.list_shares()
        result = {
            "ok": True,
            "connected_via": client.connected_via,
            "base_url": client.base_url,
            "shares": [{"name": s.get("name"), "path": s.get("path")} for s in shares],
            "upload_api": client._api_info("SYNO.FileStation.Upload"),
            "md5_api": client._api_info("SYNO.FileStation.MD5"),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({
            "ok": False,
            "error": str(exc),
            "quickconnect_id": settings.quickconnect_id,
            "base_url": settings.base_url,
            "hint": "Check that QuickConnect is enabled and the alias is registered, or configure a reachable base_url / DDNS / VPN address.",
        }, ensure_ascii=False, indent=2))
        return 1
    finally:
        client.close()


def shares(args: argparse.Namespace) -> int:
    if getattr(args, "source", None) is None:
        args.source = "."
    settings = _load_settings(args)
    client = DSMClient(settings)
    try:
        client.connect()
        print(json.dumps({"ok": True, "shares": [
            {"name": s.get("name"), "path": s.get("path"), "isdir": s.get("isdir")}
            for s in client.list_shares()
        ]}, ensure_ascii=False, indent=2))
        return 0
    finally:
        client.close()


def config_cmd(args: argparse.Namespace) -> int:
    path = Path(args.config).expanduser().resolve()
    if args.init:
        payload = {
            "quickconnect_id": args.quickconnect_id or "",
            "quickconnect_domain": args.quickconnect_domain or DEFAULT_QC_DOMAIN,
            "base_url": args.base_url or "",
            "username": args.username or "",
            "remote_dir": args.remote_dir or DEFAULT_REMOTE_DIR,
            "cert_verify": bool(args.cert_verify),
            "dsm_version": args.dsm_version or 7,
            "delete_mode": args.delete_mode or "trash",
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass
        print(f"Wrote {path}")
        return 0
    data = _read_json(path)
    safe = dict(data)
    if "password" in safe:
        safe["password"] = "<redacted>"
    print(json.dumps({"config_path": str(path), "config": safe}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", default=str(DEFAULT_CONFIG))
    common.add_argument("--quickconnect-id")
    common.add_argument("--quickconnect-domain", choices=["cn", "to"])
    common.add_argument("--base-url", help="Reachable DSM origin, e.g. https://nas.example:5001")
    common.add_argument("--username")
    common.add_argument("--password-keychain-service", default=None)
    common.add_argument("--remote-dir")
    common.add_argument("--dsm-version", type=int, choices=[6, 7])
    common.add_argument("--cert-verify", action=argparse.BooleanOptionalAction, default=None)
    common.add_argument("--timeout", type=int)
    common.add_argument("--retries", type=int)
    common.add_argument("--json", action="store_true")
    common.add_argument("--source")

    parser = argparse.ArgumentParser(
        prog="synology-cli",
        description="Upload files to Synology File Station and prune local files after verification.",
    )
    sub = parser.add_subparsers(dest="command")
    run_p = sub.add_parser("run", parents=[common], help="Upload and prune a file or directory")
    run_p.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=None)
    run_p.add_argument("--pattern")
    run_p.add_argument("--limit", type=int)
    run_p.add_argument("--dry-run", action="store_true")
    run_p.add_argument("--delete-mode", choices=["trash", "unlink", "none"])
    run_p.add_argument("--trash-dir")
    run_p.add_argument("--audit-log")
    run_p.add_argument("--verify-md5", action=argparse.BooleanOptionalAction, default=None)

    doctor_p = sub.add_parser("doctor", parents=[common], help="Check connectivity, shares, and API support")
    shares_p = sub.add_parser("shares", parents=[common], help="List File Station shares")
    config_p = sub.add_parser("config", help="Show or initialize local config")
    config_p.add_argument("--init", action="store_true")
    config_p.add_argument("--config", default=str(DEFAULT_CONFIG))
    config_p.add_argument("--quickconnect-id")
    config_p.add_argument("--quickconnect-domain", choices=["cn", "to"])
    config_p.add_argument("--base-url")
    config_p.add_argument("--username")
    config_p.add_argument("--remote-dir")
    config_p.add_argument("--dsm-version", type=int, choices=[6, 7])
    config_p.add_argument("--cert-verify", action=argparse.BooleanOptionalAction, default=False)
    config_p.add_argument("--delete-mode", choices=["trash", "unlink", "none"])

    if len(sys.argv) > 1 and sys.argv[1] not in {"run", "doctor", "shares", "config", "-h", "--help"}:
        sys.argv.insert(1, "run")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            return doctor(args)
        if args.command == "shares":
            return shares(args)
        if args.command == "config":
            return config_cmd(args)
        return run(args)
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
