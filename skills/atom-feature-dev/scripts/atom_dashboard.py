#!/usr/bin/env python3
"""Serve the local Atom Feature companion dashboard."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import urllib.request
import urllib.error
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import unquote, urlparse


STATIC_ROOT = Path(__file__).resolve().parents[1] / "dashboard"
MAX_REQUEST_BYTES = 1_000_000
MAX_OUTPUT_CHARS = 120_000
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$", re.I)
SECRET_PATTERNS = (
    re.compile(r"(?i)((?:api[_-]?key|token|secret|password)\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"\b(?:sk|rk|pk)_(?:live|test)_[A-Za-z0-9_-]+\b"),
)


class DashboardError(ValueError):
    """A safe error that may be returned to the local dashboard."""


def read_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DashboardError(f"invalid JSON: {path.name}: {exc}") from exc


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=str(path.parent), delete=False
    ) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    temporary.replace(path)


def redact_text(value: str) -> str:
    redacted = value
    for pattern in SECRET_PATTERNS:
        if pattern.groups:
            redacted = pattern.sub(r"\1[redacted]", redacted)
        else:
            redacted = pattern.sub("[redacted]", redacted)
    return redacted[:MAX_OUTPUT_CHARS]


class DashboardState:
    def __init__(
        self,
        root: Path,
        allow_run: bool = False,
        allow_write: bool = False,
        timeout_seconds: int = 60,
    ) -> None:
        self.root = root.expanduser().resolve()
        self.atom_root = self.root / ".atom-feature"
        self.allow_run = allow_run
        self.allow_write = allow_write
        self.timeout_seconds = max(1, min(timeout_seconds, 300))
        self.lock = threading.Lock()
        if not (self.atom_root / "manifest.json").is_file():
            raise DashboardError(
                "missing .atom-feature/manifest.json; initialize the atom feature first"
            )

    def workspace(self) -> Dict[str, Any]:
        manifest = read_json(self.atom_root / "manifest.json", {})
        contracts = manifest.get("contracts", {}) if isinstance(manifest, dict) else {}
        return {
            "workspace": {
                "name": self.root.name,
                "connected": True,
                "run_enabled": self.allow_run,
                "write_enabled": self.allow_write,
            },
            "manifest": manifest,
            "contract": self._read_contract(contracts.get("feature")),
            "profiles_schema": self._read_contract(contracts.get("profiles")),
            "acceptance": self._read_contract(contracts.get("acceptance"), {"vectors": []}),
            "presets": read_json(
                self.atom_root / "presets.json", {"active": None, "presets": []}
            ),
            "status": read_json(self.atom_root / "status.json", {"runs": []}),
        }

    def _read_contract(self, relative: Any, default: Any = None) -> Any:
        if not isinstance(relative, str) or not relative:
            return default
        path = (self.root / relative).resolve()
        if self.root not in (path, *path.parents):
            raise DashboardError("contract path escapes the selected project")
        return read_json(path, default)

    def save_presets(self, payload: Any) -> Dict[str, Any]:
        if not self.allow_write:
            raise PermissionError("preset writes are disabled; restart with --allow-write")
        if not isinstance(payload, dict):
            raise DashboardError("preset payload must be an object")
        presets = payload.get("presets")
        active = payload.get("active")
        if not isinstance(presets, list):
            raise DashboardError("presets must be an array")
        ids = set()
        for preset in presets:
            if not isinstance(preset, dict):
                raise DashboardError("each preset must be an object")
            preset_id = preset.get("id")
            if not isinstance(preset_id, str) or not SAFE_ID.fullmatch(preset_id):
                raise DashboardError("preset id must be a safe identifier")
            if preset_id in ids:
                raise DashboardError("preset ids must be unique")
            ids.add(preset_id)
            if not isinstance(preset.get("name"), str) or not preset["name"].strip():
                raise DashboardError("preset name is required")
            if not isinstance(preset.get("values"), dict):
                raise DashboardError("preset values must be an object")
        if active is not None and active not in ids:
            raise DashboardError("active preset must reference an existing preset")
        document = {"active": active, "presets": presets}
        with self.lock:
            write_json_atomic(self.atom_root / "presets.json", document)
        return document

    def run_surface(self, payload: Any) -> Dict[str, Any]:
        if not self.allow_run:
            raise PermissionError("surface execution is disabled; restart with --allow-run")
        if not isinstance(payload, dict):
            raise DashboardError("run payload must be an object")
        surface_name = payload.get("surface")
        if not isinstance(surface_name, str) or not SAFE_ID.fullmatch(surface_name):
            raise DashboardError("surface is required")
        workspace = self.workspace()
        surfaces = workspace.get("manifest", {}).get("surfaces", {})
        surface = surfaces.get(surface_name)
        if not isinstance(surface, dict):
            raise DashboardError(f"unknown surface: {surface_name}")
        command = surface.get("command")
        if not isinstance(command, list) or not command or not all(
            isinstance(item, str) and item for item in command
        ):
            raise DashboardError(f"surface {surface_name} has no executable command array")
        vector = self._find_item(
            workspace.get("acceptance", {}).get("vectors", []), payload.get("vector")
        )
        preset = self._find_item(
            workspace.get("presets", {}).get("presets", []), payload.get("preset")
        )
        overrides = payload.get("overrides", {})
        if not isinstance(overrides, dict):
            raise DashboardError("overrides must be an object")
        resolved: Dict[str, Any] = {}
        if preset:
            resolved.update(preset.get("values", {}))
        if vector:
            resolved.update(vector.get("input", {}))
        resolved.update(overrides)

        started = time.monotonic()
        created_at = datetime.now(timezone.utc).isoformat()
        try:
            completed = subprocess.run(
                command,
                cwd=str(self.root),
                input=json.dumps(resolved, ensure_ascii=False),
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                shell=False,
                env=os.environ.copy(),
                check=False,
            )
            exit_code: Optional[int] = completed.returncode
            stdout = redact_text(completed.stdout)
            stderr = redact_text(completed.stderr)
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            exit_code = None
            stdout = redact_text(exc.stdout or "")
            stderr = redact_text(exc.stderr or "")
            timed_out = True
        duration_ms = int((time.monotonic() - started) * 1000)
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        result = {
            "id": run_id,
            "created_at": created_at,
            "surface": surface_name,
            "vector": vector.get("id") if vector else None,
            "preset": preset.get("id") if preset else None,
            "resolved_input": resolved,
            "command": command,
            "exit_code": exit_code,
            "timed_out": timed_out,
            "duration_ms": duration_ms,
            "stdout": stdout,
            "stderr": stderr,
        }
        with self.lock:
            write_json_atomic(self.atom_root / "runs" / f"{run_id}.json", result)
            status_path = self.atom_root / "status.json"
            status = read_json(status_path, {"runs": []})
            runs = status.get("runs", []) if isinstance(status, dict) else []
            summary = {
                key: result[key]
                for key in (
                    "id",
                    "created_at",
                    "surface",
                    "vector",
                    "preset",
                    "exit_code",
                    "timed_out",
                    "duration_ms",
                )
            }
            write_json_atomic(status_path, {"runs": [summary, *runs][:100]})
        return result

    @staticmethod
    def _find_item(items: Any, item_id: Any) -> Optional[Dict[str, Any]]:
        if item_id in (None, ""):
            return None
        if not isinstance(items, list):
            raise DashboardError("workspace item collection is invalid")
        for item in items:
            if isinstance(item, dict) and item.get("id") == item_id:
                return item
        raise DashboardError(f"unknown workspace item: {item_id}")


class DashboardHandler(BaseHTTPRequestHandler):
    state: DashboardState
    verbose = False

    def log_message(self, format_string: str, *args: Any) -> None:
        if self.verbose:
            super().log_message(format_string, *args)

    def do_GET(self) -> None:
        if not self._host_is_allowed():
            self._send_json({"error": "invalid Host for local dashboard"}, HTTPStatus.FORBIDDEN)
            return
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send_json({"ok": True, "workspace": self.state.root.name})
            return
        if path == "/api/workspace":
            self._guarded_json(self.state.workspace)
            return
        self._serve_static(path)

    def do_POST(self) -> None:
        if not self._host_is_allowed():
            self._send_json({"error": "invalid Host for local dashboard"}, HTTPStatus.FORBIDDEN)
            return
        path = urlparse(self.path).path
        try:
            payload = self._read_payload()
            if path == "/api/run":
                self._send_json(self.state.run_surface(payload))
                return
            if path == "/api/presets":
                self._send_json(self.state.save_presets(payload))
                return
            self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except PermissionError as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.FORBIDDEN)
        except DashboardError as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception:
            self._send_json({"error": "internal dashboard error"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def _guarded_json(self, callback: Any) -> None:
        try:
            self._send_json(callback())
        except DashboardError as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def _read_payload(self) -> Any:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_REQUEST_BYTES:
            raise DashboardError("request body is empty or too large")
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DashboardError("request body must be UTF-8 JSON") from exc

    def _send_json(self, value: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._security_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path in ("", "/") else unquote(request_path.lstrip("/"))
        candidate = (STATIC_ROOT / relative).resolve()
        if STATIC_ROOT.resolve() not in (candidate, *candidate.parents) or not candidate.is_file():
            candidate = STATIC_ROOT / "index.html"
        payload = candidate.read_bytes()
        content_type = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".svg": "image/svg+xml",
        }.get(candidate.suffix.lower(), "application/octet-stream")
        self.send_response(HTTPStatus.OK)
        self._security_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'",
        )

    def _host_is_allowed(self) -> bool:
        port = int(self.server.server_address[1])
        allowed = {
            "127.0.0.1",
            "localhost",
            "[::1]",
            f"127.0.0.1:{port}",
            f"localhost:{port}",
            f"[::1]:{port}",
        }
        return self.headers.get("Host", "") in allowed


class IPv6ThreadingHTTPServer(ThreadingHTTPServer):
    address_family = socket.AF_INET6


def make_server(
    state: DashboardState, host: str, port: int, verbose: bool = False
) -> ThreadingHTTPServer:
    handler = type(
        "BoundDashboardHandler",
        (DashboardHandler,),
        {"state": state, "verbose": verbose},
    )
    server_class = IPv6ThreadingHTTPServer if host == "::1" else ThreadingHTTPServer
    return server_class((host, port), handler)


def serve_command(args: argparse.Namespace) -> int:
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        raise DashboardError("the dashboard bridge only binds to a loopback host")
    state = DashboardState(
        args.root,
        allow_run=args.allow_run,
        allow_write=args.allow_write,
        timeout_seconds=args.timeout,
    )
    server = make_server(state, args.host, args.port, args.verbose)
    host, port = server.server_address[:2]
    display_host = f"[{host}]" if ":" in host else host
    url = f"http://{display_host}:{port}/"
    print(f"dashboard={url}")
    print(f"workspace={state.root.name}")
    print(f"run_enabled={str(state.allow_run).lower()}")
    print(f"write_enabled={str(state.allow_write).lower()}")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def request_json(url: str, payload: Optional[Dict[str, Any]] = None) -> Any:
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def selftest_command(_: argparse.Namespace) -> int:
    demo = STATIC_ROOT / "demo-project"
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "demo-project"
        shutil.copytree(demo, root)
        read_only = DashboardState(root)
        try:
            read_only.run_surface({"surface": "sdk"})
            raise AssertionError("read-only dashboard unexpectedly executed a surface")
        except PermissionError:
            pass
        try:
            read_only.save_presets({"active": None, "presets": []})
            raise AssertionError("read-only dashboard unexpectedly wrote presets")
        except PermissionError:
            pass
        assert "[redacted]" in redact_text("API_KEY=local-test-value")
        state = DashboardState(root, allow_run=True, allow_write=True, timeout_seconds=5)
        server = make_server(state, "127.0.0.1", 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        port = int(server.server_address[1])
        base = f"http://127.0.0.1:{port}"
        try:
            health = request_json(base + "/api/health")
            workspace = request_json(base + "/api/workspace")
            run = request_json(
                base + "/api/run",
                {"surface": "sdk", "vector": "balanced-export", "preset": "balanced"},
            )
            assert health["ok"] is True
            assert workspace["manifest"]["feature"]["id"] == "markdown-to-pdf"
            assert run["exit_code"] == 0
            assert "demo.pdf" in run["stdout"]
            index = urllib.request.urlopen(base + "/", timeout=5).read().decode("utf-8")
            assert "Atom Workbench" in index
            assert 'href="./styles.css"' in index
            assert 'src="./demo-workspace.js"' in index
            assert 'src="./app.js"' in index
            demo_bundle = (
                urllib.request.urlopen(base + "/demo-workspace.js", timeout=5)
                .read()
                .decode("utf-8")
            )
            assert "window.ATOM_WORKBENCH_DEMO" in demo_bundle
            hostile = urllib.request.Request(
                base + "/api/health", headers={"Host": "outside.invalid"}
            )
            try:
                urllib.request.urlopen(hostile, timeout=5)
                raise AssertionError("dashboard accepted a non-local Host header")
            except urllib.error.HTTPError as exc:
                assert exc.code == HTTPStatus.FORBIDDEN
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
    print(
        "PASSED: atom dashboard read-only gates, Host guard, redaction, HTTP workspace and surface-run selftest"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    serve = subparsers.add_parser("serve", help="serve the dashboard for one atom project")
    serve.add_argument("--root", type=Path, required=True)
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=6174)
    serve.add_argument("--timeout", type=int, default=60)
    serve.add_argument("--allow-run", action="store_true")
    serve.add_argument("--allow-write", action="store_true")
    serve.add_argument("--open", action="store_true")
    serve.add_argument("--verbose", action="store_true")
    serve.set_defaults(handler=serve_command)
    selftest = subparsers.add_parser("selftest", help="exercise the local HTTP workbench")
    selftest.set_defaults(handler=selftest_command)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except DashboardError as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
