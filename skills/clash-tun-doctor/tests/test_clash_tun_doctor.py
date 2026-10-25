import http.server
import shutil
import socket
import socketserver
import sys
import tempfile
import threading
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


class SocketDiscoveryTests(unittest.TestCase):
    def setUp(self):
        # AF_UNIX paths are limited to ~104 bytes on macOS; keep the root short.
        self.root = Path(tempfile.mkdtemp(prefix="ctd-", dir="/tmp"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.data_dir = self.root / "data"
        self.data_dir.mkdir()

    def serve(self, name):
        path = self.root / name
        server = _UnixHTTPServer(str(path), _VersionHandler)
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
