#!/usr/bin/env python3
"""Minimal HTTPS Synology File Station simulator for local end-to-end tests."""

from __future__ import annotations

import argparse
import email
import email.policy
import hashlib
import json
import os
import posixpath
import ssl
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

SID = "fake-sid"
TOKEN = "fake-token"


class State:
    def __init__(self, root: Path, corrupt_name: str | None = None) -> None:
        self.root = root.resolve()
        self.corrupt_name = corrupt_name
        self.tasks: dict[str, str] = {}
        self.lock = threading.Lock()

    def path_for(self, remote: str) -> Path:
        return self.root / remote.lstrip("/")

    def new_task(self, remote: str) -> str:
        task_id = f"md5-{len(self.tasks) + 1}"
        with self.lock:
            self.tasks[task_id] = remote
        return task_id

    def md5(self, remote: str) -> str | None:
        target = self.path_for(remote)
        if not target.is_file():
            return None
        h = hashlib.md5()
        with target.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()


STATE: State


def _json(handler: BaseHTTPRequestHandler, payload: Any, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _form_values(raw: bytes, content_type: str = "") -> dict[str, Any]:
    values = urllib.parse.parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
    return {k: v[-1] if v else "" for k, v in values.items()}


def _multipart_values(raw: bytes, content_type: str) -> tuple[dict[str, str], dict[str, tuple[str, bytes]]]:
    if "multipart/form-data" not in content_type.lower():
        return {}, {}
    message = email.message_from_bytes(
        (f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n").encode("utf-8") + raw,
        policy=email.policy.default,
    )
    fields: dict[str, str] = {}
    files: dict[str, tuple[str, bytes]] = {}
    for part in message.iter_parts():
        disposition = part.get_content_disposition()
        name = part.get_param("name", header="content-disposition")
        if disposition != "form-data" or not name:
            continue
        data = part.get_payload(decode=True) or b""
        filename = part.get_filename()
        if filename:
            files[name] = (filename, data)
        else:
            fields[name] = data.decode("utf-8", errors="replace")
    return fields, files


def _api_info() -> dict[str, Any]:
    return {
        "SYNO.API.Auth": {"path": "auth.cgi", "minVersion": 1, "maxVersion": 7},
        "SYNO.FileStation.List": {"path": "entry.cgi", "minVersion": 1, "maxVersion": 2},
        "SYNO.FileStation.Upload": {"path": "entry.cgi", "minVersion": 1, "maxVersion": 2},
        "SYNO.FileStation.MD5": {"path": "entry.cgi", "minVersion": 1, "maxVersion": 2},
        "SYNO.FileStation.CheckPermission": {"path": "entry.cgi", "minVersion": 1, "maxVersion": 3},
    }


def _file_info(remote: str) -> dict[str, Any] | None:
    target = STATE.path_for(remote)
    if not target.is_file():
        return None
    stat = target.stat()
    return {
        "name": target.name,
        "path": remote,
        "isdir": False,
        "additional": {"size": stat.st_size, "time": {"mtime": int(stat.st_mtime)},"type": "file"},
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "FakeDSM/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        if os.environ.get("FAKE_DSM_VERBOSE"):
            super().log_message(fmt, *args)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or "0")
        return self.rfile.read(length) if length else b""

    def _all_params(self, raw: bytes) -> dict[str, str]:
        query = _form_values(urllib.parse.urlparse(self.path).query.encode("utf-8"))
        ctype = self.headers.get("Content-Type", "")
        if "multipart/form-data" in ctype.lower():
            fields, _ = _multipart_values(raw, ctype)
            query.update(fields)
        elif raw:
            query.update(_form_values(raw, ctype))
        return query

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.endswith("/query.cgi") or parsed.path.endswith("query.cgi"):
            _json(self, {"success": True, "data": _api_info()})
            return
        if not parsed.path.endswith("/entry.cgi"):
            _json(self, {"success": True, "data": {"message": "fake dsm"}})
            return
        params = _form_values(parsed.query.encode("utf-8"))
        api = params.get("api")
        method = params.get("method")
        if api == "SYNO.FileStation.List" and method == "list_share":
            _json(self, {"success": True, "data": {"offset": 0, "total": 1, "shares": [
                {"name": "home", "path": STATE.root.as_posix(), "isdir": True}
            ]}})
            return
        if api == "SYNO.FileStation.List" and method == "getinfo":
            raw_paths = params.get("path", "[]")
            try:
                paths = json.loads(raw_paths)
            except Exception:
                paths = [raw_paths]
            remote = paths[0] if paths else "/"
            info = _file_info(remote)
            if info is None:
                _json(self, {"success": False, "error": {"code": 408}})
            else:
                _json(self, {"success": True, "data": {"files": [info]}})
            return
        if api == "SYNO.FileStation.MD5" and method == "start":
            remote = params.get("file_path", "")
            if not _file_info(remote):
                _json(self, {"success": False, "error": {"code": 408}})
                return
            _json(self, {"success": True, "data": {"taskid": STATE.new_task(remote)}})
            return
        if api == "SYNO.FileStation.MD5" and method == "status":
            remote = STATE.tasks.get(params.get("taskid", ""), "")
            if not remote:
                _json(self, {"success": False, "error": {"code": 599}})
                return
            md5 = STATE.md5(remote)
            if md5 is None:
                _json(self, {"success": False, "error": {"code": 408}})
                return
            _json(self, {"success": True, "data": {"finished": True, "md5": md5}})
            return
        if api == "SYNO.FileStation.CheckPermission" and method == "write":
            _json(self, {"success": True, "data": {"write": True}})
            return
        _json(self, {"success": False, "error": {"code": 102, "api": api, "method": method}})

    def do_POST(self) -> None:  # noqa: N802
        raw = self._read_body()
        parsed = urllib.parse.urlparse(self.path)
        params = self._all_params(raw)
        api = params.get("api") or urllib.parse.parse_qs(parsed.query).get("api", [""])[-1]
        method = params.get("method") or urllib.parse.parse_qs(parsed.query).get("method", [""])[-1]

        if api == "SYNO.API.Auth":
            if method == "login":
                _json(self, {"success": True, "data": {"sid": SID, "synotoken": TOKEN}})
                return
            if method == "logout":
                _json(self, {"success": True, "data": {}})
                return

        if api == "SYNO.FileStation.Upload":
            if params.get("_sid") != SID and not urllib.parse.parse_qs(parsed.query).get("_sid", [None])[-1] == SID:
                _json(self, {"success": False, "error": {"code": 119}})
                return
            ctype = self.headers.get("Content-Type", "")
            fields, files = _multipart_values(raw, ctype)
            if not files:
                _json(self, {"success": False, "error": {"code": 1802}})
                return
            filename, content = next(iter(files.values()))
            destination_dir = fields.get("path") or params.get("path") or "/"
            remote = posixpath.join(destination_dir.rstrip("/"), filename)
            if filename == STATE.corrupt_name:
                content = content[: max(1, len(content) // 2)]
            target = STATE.path_for(remote)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            _json(self, {"success": True, "data": {}})
            return

        _json(self, {"success": False, "error": {"code": 102, "api": api, "method": method}})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--cert")
    parser.add_argument("--key")
    parser.add_argument("--corrupt-name")
    parser.add_argument("--print-port", action="store_true")
    args = parser.parse_args()
    global STATE
    STATE = State(Path(args.root), args.corrupt_name)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    if args.cert and args.key:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(args.cert, args.key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
    if args.print_port:
        print(server.server_address[1], flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
