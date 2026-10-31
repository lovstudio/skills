import http.server
import json
import os
import re
import shutil
import socket
import socketserver
import sys
import tempfile
import threading
import time
from pathlib import Path
import unittest
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import clash_tun_doctor as doctor


SERVICE_PS_OUTPUT = (
    "clash-verge-serv /Library/Application Support/clash-verge-service/clash-verge-service\n"
    "clash-verge      /Applications/Clash Verge.app/Contents/MacOS/clash-verge\n"
    "verge-mihomo     /Library/Application Support/clash-verge-service/cores/verge-mihomo "
    "-d /Library/Application Support/clash-verge-service/users/501/runtime "
    "-f /Library/Application Support/clash-verge-service/users/501/runtime/config.yaml "
    "-ext-ctl-unix /var/run/clash-verge-service/users/501/verge-mihomo.sock\n"
    "zsh              zsh -c curl --unix-socket x -ext-ctl-unix /tmp/not-a-core.sock\n"
)


class _VersionHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'{"meta":true,"version":"test"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


class _UnixHTTPServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


class _LogStreamHandler(socketserver.StreamRequestHandler):
    """Mimic Mihomo /logs: chunked JSON lines, then keep the stream open."""

    def handle(self):
        while self.rfile.readline() not in (b"\r\n", b"\n", b""):
            pass
        self.wfile.write(
            b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
            b"Transfer-Encoding: chunked\r\n\r\n"
        )
        for payload in (
            "[TCP] 127.0.0.1:1(WeChat) --> [240e::1]:443 error: connect: no route to host",
            "[TCP] 127.0.0.1:2(Chrome) --> example.com:443 match Match using PROXY",
        ):
            line = json.dumps({"type": "info", "payload": payload}).encode() + b"\n"
            self.wfile.write(b"%x\r\n%s\r\n" % (len(line), line))
            self.wfile.flush()
        time.sleep(3)


class _MockMihomo(http.server.BaseHTTPRequestHandler):
    """Mihomo controller stand-in: /rules reflect the last config it accepted."""

    def reply(self, status, payload=None):
        body = b"" if payload is None else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        state = self.server.state
        if self.path == "/rules":
            rules = [
                {"type": "Domain", "payload": host, "proxy": proxy}
                for host, proxy in state["rules"]
            ]
            self.reply(200, {"rules": rules})
        elif self.path == "/proxies":
            self.reply(200, {"proxies": state["proxies"]})
        else:
            self.reply(200, {"mode": "rule"})

    def do_PUT(self):
        state = self.server.state
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        state["requests"].append(request)
        if "path" in request and not request["path"].startswith(state["home"] + os.sep):
            message = (
                f"path is not subpath of home directory or SAFE_PATHS: {request['path']} \n"
                f" allowed paths: [{state['home']}]"
            )
            self.reply(400, {"message": message})
            return
        if state.get("delay"):
            time.sleep(state["delay"])  # outlast the client, which has hung up by now
            return
        if state.get("reject"):
            self.reply(400, {"message": state["reject"]})
            return
        text = request.get("payload") or Path(request["path"]).read_text(encoding="utf-8")
        state["rules"] = re.findall(r"(?m)^- DOMAIN,([^,\s]+),(\w+)$", text)
        state["proxies"]["Auto"]["now"] = "SG"  # unpinned automatic groups re-pick
        if state.get("reset_choice"):
            state["proxies"]["Proxy"]["now"] = "DIRECT"
            state["proxies"]["Pinned"].update(now="JP", fixed="")
        self.reply(204)

    def log_message(self, *_args):
        pass


class _UnixSocketTestCase(unittest.TestCase):
    def setUp(self):
        # AF_UNIX paths are limited to ~104 bytes on macOS; keep the root short.
        self.root = Path(tempfile.mkdtemp(prefix="ctd-", dir="/tmp"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.data_dir = self.root / "data"
        self.data_dir.mkdir()

    def serve(self, name, handler=_VersionHandler, state=None):
        path = self.root / name
        server = _UnixHTTPServer(str(path), handler)
        server.state = state
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return path

    def stale_socket(self, name):
        path = self.root / name
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(str(path))
        sock.close()
        return path


class SocketDiscoveryTests(_UnixSocketTestCase):
    def test_parse_ext_ctl_unix_reads_service_core_only(self):
        self.assertEqual(
            doctor.parse_ext_ctl_unix(SERVICE_PS_OUTPUT),
            [Path("/var/run/clash-verge-service/users/501/verge-mihomo.sock")],
        )

    def test_parse_ext_ctl_unix_accepts_equals_and_trailing_flags(self):
        output = (
            "mihomo /usr/local/bin/mihomo --ext-ctl-unix=/tmp/my dir/m.sock -d /etc/mihomo\n"
        )
        self.assertEqual(doctor.parse_ext_ctl_unix(output), [Path("/tmp/my dir/m.sock")])

    def test_generated_controller_socket(self):
        config = self.data_dir / "clash-verge.yaml"
        config.write_text(
            "external-controller: ''\n"
            "external-controller-unix: /var/folders/xx/T/verge-mihomo.sock\n",
            encoding="utf-8",
        )
        self.assertEqual(
            doctor.generated_controller_socket(self.data_dir),
            Path("/var/folders/xx/T/verge-mihomo.sock"),
        )
        config.write_text("external-controller-unix: ''\n", encoding="utf-8")
        self.assertIsNone(doctor.generated_controller_socket(self.data_dir))

    def test_candidate_order_prefers_running_core_then_config_then_service(self):
        (self.data_dir / "clash-verge.yaml").write_text(
            'external-controller-unix: "/var/folders/xx/T/verge-mihomo.sock"\n',
            encoding="utf-8",
        )
        generated = Path("/var/folders/xx/T/verge-mihomo.sock")
        service = Path("/var/run/clash-verge-service/users/501/verge-mihomo.sock")
        with mock.patch.object(doctor.os, "getuid", return_value=501, create=True):
            with mock.patch.object(doctor, "running_core_sockets", return_value=[service]):
                running = doctor.socket_candidates(self.data_dir, None)
            with mock.patch.object(doctor, "running_core_sockets", return_value=[]):
                stopped = doctor.socket_candidates(self.data_dir, None)

        fallbacks = [doctor.DEFAULT_SOCKET, self.data_dir / "mihomo.sock"]
        # The running core's path also equals the service default and is not repeated.
        self.assertEqual([path for _source, path in running], [service, generated] + fallbacks)
        self.assertEqual(running[0][0], "running core -ext-ctl-unix")
        self.assertEqual([path for _source, path in stopped], [generated, service] + fallbacks)

    def test_resolve_skips_missing_and_stale_sockets(self):
        missing = self.root / "missing.sock"
        stale = self.stale_socket("stale.sock")
        live = self.serve("live.sock")
        candidates = [("a", missing), ("b", stale), ("c", live)]
        with mock.patch.object(doctor, "socket_candidates", return_value=candidates):
            self.assertEqual(doctor.resolve_socket(self.data_dir, None), live)
            _path, attempts = doctor.find_runtime_socket(self.data_dir, None)

        self.assertEqual([item["source"] for item in attempts], ["a", "b"])
        self.assertEqual(attempts[0]["reason"], "missing")
        self.assertNotEqual(attempts[1]["reason"], "missing")

    def test_resolve_fails_loudly_when_no_candidate_answers(self):
        stale = self.stale_socket("stale.sock")
        candidates = [("generated", self.root / "missing.sock"), ("service", stale)]
        with mock.patch.object(doctor, "socket_candidates", return_value=candidates):
            with self.assertRaises(SystemExit) as raised:
                doctor.resolve_socket(self.data_dir, None)

        message = str(raised.exception)
        self.assertIn("runtime state was NOT read", message)
        self.assertIn(str(self.root / "missing.sock"), message)
        self.assertIn(str(stale), message)
        self.assertIn("--socket", message)

    def test_explicit_socket_does_not_fall_back_to_auto_discovery(self):
        with mock.patch.object(doctor, "running_core_sockets") as running:
            with self.assertRaises(SystemExit):
                doctor.resolve_socket(self.data_dir, str(self.root / "missing.sock"))
        running.assert_not_called()

    def test_diagnose_reads_runtime_through_discovered_socket(self):
        live = self.serve("live.sock")
        with mock.patch.object(doctor, "running_core_sockets", return_value=[live]):
            socket_path = doctor.resolve_socket(self.data_dir, None)

        def fake_api(_socket, path, method="GET", body=None):
            if path == "/configs":
                return {"ipv6": False}
            if path == "/connections":
                return {
                    "connections": [
                        {"metadata": {"process": "WeChat", "host": "weixin.qq.com"}}
                    ]
                }
            return {"rules": []}

        with mock.patch.object(doctor, "api_json", side_effect=fake_api):
            result = doctor.diagnose(self.data_dir, socket_path, "wechat")

        self.assertEqual(result["socket"], str(live))
        self.assertIs(result["runtime_ipv6"], False)
        self.assertEqual(len(result["connections"]), 1)


class LogDiscoveryTests(_UnixSocketTestCase):
    def write_log(self, directory, name, text, mtime=None):
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / name
        path.write_text(text, encoding="utf-8")
        if mtime is not None:
            os.utime(path, (mtime, mtime))
        return path

    def test_owner_scoped_socket_uses_only_service_owner_logs(self):
        state = self.root / "state"
        owner_socket = Path("/var/run/clash-verge-service/users/501/verge-mihomo.sock")
        with mock.patch.object(doctor, "service_state_dir", return_value=state):
            service = doctor.core_log_dirs(self.data_dir, owner_socket)
            sidecar = doctor.core_log_dirs(self.data_dir, self.root / "verge-mihomo.sock")

        self.assertEqual(service, [("service-mode core log", state / "users/501/logs", "service")])
        self.assertEqual(
            [directory for _label, directory, _prefix in sidecar],
            [
                self.data_dir / "logs/sidecar",
                self.data_dir / "service-logs/service",
                self.data_dir / "logs/service",
            ],
        )

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root bypasses permissions")
    def test_root_only_service_logs_are_reported_not_counted(self):
        state = self.root / "state"
        logs = state / "users/501/logs"
        self.write_log(logs, "service_latest.log", "[TCP] WeChat no route to host\n")
        logs.chmod(0)
        self.addCleanup(logs.chmod, 0o755)
        # Stale data-dir logs from an earlier sidecar run must not be used instead.
        self.write_log(self.data_dir / "logs/sidecar", "sidecar_latest.log", "WeChat\n")
        owner_socket = Path("/var/run/clash-verge-service/users/501/verge-mihomo.sock")
        with mock.patch.object(doctor, "service_state_dir", return_value=state):
            result = doctor.log_findings(self.data_dir, owner_socket, "wechat")

        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["no_route_to_host"])
        self.assertIsNone(result["matched_lines"])
        self.assertEqual(result["tried"][0]["path"], str(logs))
        self.assertEqual(result["tried"][0]["reason"], "Permission denied")
        self.assertIn("--live-logs", result["hint"])
        self.assertIn("sudo tail", result["hint"])

    def test_empty_or_missing_log_dirs_are_unavailable(self):
        (self.data_dir / "service-logs/service").mkdir(parents=True)
        self.write_log(self.data_dir / "logs/service", "service_latest.log", "")
        result = doctor.log_findings(self.data_dir, self.root / "x.sock", "wechat")

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(
            [item["reason"] for item in result["tried"]],
            ["No such file or directory", "no non-empty log files", "no non-empty log files"],
        )

    def test_newest_log_directory_wins_and_latest_file_comes_first(self):
        old = time.time() - 86400 * 60
        self.write_log(self.data_dir / "logs/sidecar", "sidecar_latest.log", "x\n", mtime=old)
        legacy = self.data_dir / "logs/service"
        rotated = self.write_log(legacy, "service_2026-10-24.log", "x\n", mtime=old + 10)
        latest = self.write_log(
            legacy,
            "service_latest.log",
            "[TCP] 127.0.0.1:1(WeChat) --> [240e::1]:443 no route to host\n",
        )
        files, _attempts = doctor.find_core_logs(self.data_dir, None)
        result = doctor.log_findings(self.data_dir, None, "wechat")

        self.assertEqual(files, [latest, rotated])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["source"], str(latest))
        self.assertEqual(result["no_route_to_host"], 1)
        self.assertEqual(result["ipv6_lines"], 1)

    def test_parse_log_stream_handles_chunks_and_truncation(self):
        lines = [json.dumps({"type": "info", "payload": f"line {n}"}).encode() + b"\n" for n in (1, 2)]
        raw = (
            b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n"
            + b"".join(b"%x\r\n%s\r\n" % (len(line), line) for line in lines)
            + b"40\r\n{\"type\":\"info\",\"pay"
        )
        self.assertEqual(doctor.parse_log_stream(raw), ["line 1", "line 2"])
        self.assertEqual(doctor.parse_log_stream(b""), [])
        with self.assertRaises(ValueError):
            doctor.parse_log_stream(b"HTTP/1.1 404 Not Found\r\n\r\n")

    def test_live_logs_sample_the_runtime_stream(self):
        live = self.serve("logs.sock", _LogStreamHandler)
        result = doctor.log_findings(self.data_dir, live, "wechat", live_seconds=0.5)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["source"], "live /logs stream, 0.5s")
        self.assertEqual(result["scanned_lines"], 2)
        self.assertEqual(result["no_route_to_host"], 1)

    def test_live_logs_failure_is_unavailable(self):
        result = doctor.log_findings(
            self.data_dir, self.root / "missing.sock", "wechat", live_seconds=0.2
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["tried"][0]["source"], "live /logs stream")


class DirectListTests(unittest.TestCase):
    def test_merge_prepend_preserves_existing_rules(self):
        original = (
            "prepend:\n"
            '  - "PROCESS-NAME,WeChat,DIRECT"\n'
            "\n"
            "append: []\n"
        )

        updated = doctor.merge_prepend(
            original,
            [
                "DOMAIN,apply.miracleplus.com,DIRECT",
                "PROCESS-NAME,WeChat,DIRECT",
            ],
        )

        self.assertEqual(updated.count("PROCESS-NAME,WeChat,DIRECT"), 1)
        self.assertIn('  - "DOMAIN,apply.miracleplus.com,DIRECT"\n', updated)
        self.assertIn("append: []\n", updated)

    def test_discovery_keeps_non_direct_and_explicit_hosts(self):
        with tempfile.TemporaryDirectory() as raw_dir:
            data_dir = Path(raw_dir)
            profiles = data_dir / "profiles"
            logs = data_dir / "service-logs/service"
            profiles.mkdir(parents=True)
            logs.mkdir(parents=True)
            (data_dir / "profiles.yaml").write_text(
                "current: remote\n"
                "- uid: remote\n"
                "  type: remote\n"
                "  option:\n"
                "    rules: rules-id\n",
                encoding="utf-8",
            )
            (profiles / "rules-id.yaml").write_text(
                "prepend:\n"
                '  - "DOMAIN,apply.miracleplus.com,DIRECT"\n',
                encoding="utf-8",
            )
            (logs / "service_latest.log").write_text(
                '[TCP] 127.0.0.1:1(Chrome) --> apply-cdn.miracleplus.com:443 '
                'match Match using PROXY\n'
                '[TCP] 127.0.0.1:2(Chrome) --> miracleplus.datasink.sensorsdata.cn:443 '
                'match DomainSuffix(cn) using DIRECT\n',
                encoding="utf-8",
            )

            def fake_api(_socket, path, method="GET", body=None):
                if path == "/connections":
                    return {"connections": []}
                if path == "/rules":
                    return {
                        "rules": [
                            {
                                "type": "Domain",
                                "payload": "apply.miracleplus.com",
                                "proxy": "DIRECT",
                            }
                        ]
                    }
                return {}

            with mock.patch.object(doctor, "api_json", side_effect=fake_api):
                result = doctor.discover_direct_list(
                    data_dir,
                    data_dir / "mihomo.sock",
                    "miracleplus",
                    explicit_hosts=["apply.miracleplus.com"],
                )

        self.assertEqual(
            result["rules"],
            [
                "DOMAIN,apply-cdn.miracleplus.com,DIRECT",
                "DOMAIN,apply.miracleplus.com,DIRECT",
            ],
        )
        self.assertEqual(
            result["missing_rules"],
            ["DOMAIN,apply-cdn.miracleplus.com,DIRECT"],
        )
        self.assertEqual(
            result["ignored_direct_hosts"],
            ["miracleplus.datasink.sensorsdata.cn"],
        )

    def test_merge_generated_rules_is_idempotent(self):
        original = (
            "mixed-port: 7897\n"
            "rules:\n"
            "- DOMAIN,apply.miracleplus.com,DIRECT\n"
            "- MATCH,PROXY\n"
        )

        updated = doctor.merge_generated_rules(
            original,
            [
                "DOMAIN,apply.miracleplus.com,DIRECT",
                "DOMAIN,apply-cdn.miracleplus.com,DIRECT",
            ],
        )
        updated_again = doctor.merge_generated_rules(
            updated,
            ["DOMAIN,apply-cdn.miracleplus.com,DIRECT"],
        )

        self.assertEqual(updated, updated_again)
        self.assertEqual(updated.count("DOMAIN,apply-cdn.miracleplus.com,DIRECT"), 1)
        self.assertLess(
            updated.index("DOMAIN,apply-cdn.miracleplus.com,DIRECT"),
            updated.index("MATCH,PROXY"),
        )

    def test_pin_controller_socket_replaces_or_adds_the_line(self):
        sock = Path("/var/run/clash-verge-service/users/501/verge-mihomo.sock")
        line = f'external-controller-unix: "{sock}"\n'
        self.assertEqual(
            doctor.pin_controller_socket(
                "mixed-port: 7897\n"
                "external-controller-unix: '/tmp/verge/verge-mihomo.sock'\n"
                "rules:\n",
                sock,
            ),
            "mixed-port: 7897\n" + line + "rules:\n",
        )
        self.assertEqual(
            doctor.pin_controller_socket("mixed-port: 7897", sock),
            "mixed-port: 7897\n" + line,
        )


class ReloadTests(_UnixSocketTestCase):
    SERVICE_SOCKET = "clash-verge-service/users/501/verge-mihomo.sock"
    DISCOVERY = {
        "rules": ["DOMAIN,apply.example.com,DIRECT"],
        "items": [{"host": "apply.example.com"}],
    }

    def setUp(self):
        super().setUp()
        (self.data_dir / "profiles").mkdir()
        (self.data_dir / "profiles.yaml").write_text(
            "current: remote\n"
            "- uid: remote\n"
            "  type: remote\n"
            "  option:\n"
            "    rules: rules-id\n",
            encoding="utf-8",
        )
        self.rules_file = self.data_dir / "profiles/rules-id.yaml"
        self.rules_file.write_text("prepend: []\n", encoding="utf-8")
        self.generated = self.data_dir / "clash-verge.yaml"
        self.generated.write_text(
            "mixed-port: 7897\n"
            "external-controller-unix: /tmp/verge/verge-mihomo.sock\n"
            "rules:\n"
            "- MATCH,Proxy\n",
            encoding="utf-8",
        )

    def controller(self, name, **options):
        # By default the core's home is a runtime dir that the data dir is not under.
        state = {
            "home": str(self.root / "runtime"),
            "requests": [],
            "rules": [],
            "proxies": {
                "Proxy": {"type": "Selector", "now": "HK"},
                "Auto": {"type": "Fallback", "now": "JP", "fixed": ""},
                "Pinned": {"type": "URLTest", "now": "US", "fixed": "US"},
            },
        }
        state.update(options)
        (self.root / name).parent.mkdir(parents=True, exist_ok=True)
        path = self.serve(name, _MockMihomo, state)
        # main() resolves --socket the same way before applying.
        return doctor.resolve_socket(self.data_dir, str(path)), state

    def apply(self, socket_path):
        return doctor.apply_direct_list(
            self.data_dir, socket_path, self.DISCOVERY, True, cli_socket=str(socket_path)
        )

    def test_service_mode_reloads_by_payload_on_the_live_socket(self):
        socket_path, state = self.controller(self.SERVICE_SOCKET)
        code, result = self.apply(socket_path)

        self.assertEqual(code, 0, result.get("reason"))
        self.assertEqual([item["method"] for item in result["reload_attempts"]], ["payload"])
        self.assertEqual(len(state["requests"]), 1)
        payload = state["requests"][0]["payload"]
        self.assertIn(f'external-controller-unix: "{socket_path}"\n', payload)
        self.assertNotIn("/tmp/verge/verge-mihomo.sock", payload)
        self.assertIn("- DOMAIN,apply.example.com,DIRECT\n", payload)
        verification = result["verification"]
        self.assertEqual(verification["socket"], str(socket_path))
        self.assertEqual(verification["missing_direct_hosts"], [])
        # The unpinned Fallback re-picked during the reload; that is not a user choice.
        self.assertEqual(verification["selection_changes"], [])
        self.assertTrue(result["runtime_verified"])
        self.assertIn("DOMAIN,apply.example.com,DIRECT", self.rules_file.read_text(encoding="utf-8"))
        # The data-dir config keeps Clash Verge's own controller path.
        self.assertIn(
            "external-controller-unix: /tmp/verge/verge-mihomo.sock\n",
            self.generated.read_text(encoding="utf-8"),
        )

    def test_sidecar_reloads_by_path_inside_core_home(self):
        socket_path, state = self.controller("m.sock", home=str(self.data_dir))
        code, result = self.apply(socket_path)

        self.assertEqual(code, 0, result.get("reason"))
        self.assertEqual(state["requests"], [{"path": str(self.generated)}])

    def test_path_outside_safe_paths_falls_back_to_payload(self):
        socket_path, state = self.controller("m.sock")
        code, result = self.apply(socket_path)

        self.assertEqual(code, 0, result.get("reason"))
        refused, loaded = result["reload_attempts"]
        self.assertEqual((refused["method"], refused["status"]), ("path", 400))
        self.assertIn("SAFE_PATHS", refused["error"])
        self.assertIn(str(self.generated), refused["error"])
        self.assertEqual((loaded["method"], loaded["ok"]), ("payload", True))
        self.assertEqual(state["requests"][0], {"path": str(self.generated)})
        self.assertTrue(result["runtime_verified"])

    def test_refused_reload_surfaces_mihomo_error_and_restores_files(self):
        originals = {
            path: path.read_text(encoding="utf-8") for path in (self.rules_file, self.generated)
        }
        socket_path, _state = self.controller(
            self.SERVICE_SOCKET, reject="yaml: line 4: did not find expected key"
        )
        code, result = self.apply(socket_path)

        self.assertEqual(code, 2)
        self.assertFalse(result["ok"])
        self.assertFalse(result["runtime_reloaded"])
        self.assertEqual(
            result["reload_attempts"][-1]["error"],
            "HTTP 400: yaml: line 4: did not find expected key",
        )
        self.assertIn("yaml: line 4: did not find expected key", result["reason"])
        self.assertEqual(sorted(result["restored_files"]), sorted(map(str, originals)))
        for path, text in originals.items():
            self.assertEqual(path.read_text(encoding="utf-8"), text)
        self.assertTrue(Path(result["backup"]).is_dir())
        self.assertIsNone(result["verification"])

    def test_reload_without_response_reports_transport_error(self):
        socket_path, _state = self.controller(self.SERVICE_SOCKET, delay=0.5)
        with mock.patch.object(doctor, "RELOAD_TIMEOUT", 0.1):
            code, result = self.apply(socket_path)

        self.assertEqual(code, 2)
        attempt = result["reload_attempts"][-1]
        self.assertIsNone(attempt["status"])
        self.assertTrue(attempt["error"].startswith("no HTTP response: "), attempt["error"])
        self.assertIn("timed out", attempt["error"])
        self.assertNotIn("apply.example.com", self.rules_file.read_text(encoding="utf-8"))

    def test_lost_group_choice_fails_verification(self):
        socket_path, _state = self.controller(self.SERVICE_SOCKET, reset_choice=True)
        code, result = self.apply(socket_path)

        self.assertEqual(code, 2)
        self.assertTrue(result["runtime_reloaded"])
        self.assertFalse(result["runtime_verified"])
        self.assertEqual(
            result["verification"]["selection_changes"],
            [
                {"group": "Pinned", "before": "US", "after": None},
                {"group": "Proxy", "before": "HK", "after": "DIRECT"},
            ],
        )
        self.assertIn("Group choices changed: Pinned: US -> None, Proxy: HK -> DIRECT.", result["reason"])
        self.assertEqual(result["restored_files"], [])


if __name__ == "__main__":
    unittest.main()
