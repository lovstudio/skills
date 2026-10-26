import http.server
import json
import os
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


class _UnixSocketTestCase(unittest.TestCase):
    def setUp(self):
        # AF_UNIX paths are limited to ~104 bytes on macOS; keep the root short.
        self.root = Path(tempfile.mkdtemp(prefix="ctd-", dir="/tmp"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.data_dir = self.root / "data"
        self.data_dir.mkdir()

    def serve(self, name, handler=_VersionHandler):
        path = self.root / name
        server = _UnixHTTPServer(str(path), handler)
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


if __name__ == "__main__":
    unittest.main()
