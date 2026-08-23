from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "env_manager.py"


class EnvManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.home = self.root / "credential-store"
        self.secret_one = "dummy-openai-personal-primary-0001"
        self.secret_two = "dummy-openai-personal-rotation-0002"
        self.secret_three = "dummy-openai-work-primary-0003"
        self.run_cli("init")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(
        self,
        *args: str,
        secret: str | None = None,
        expected: int = 0,
    ) -> tuple[dict, subprocess.CompletedProcess[str]]:
        command = [
            sys.executable,
            str(SCRIPT),
            "--home",
            str(self.home),
            "--json",
            *args,
        ]
        completed = subprocess.run(
            command,
            input=(secret + "\n") if secret is not None else None,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            expected,
            msg="stdout:\n" + completed.stdout + "\nstderr:\n" + completed.stderr,
        )
        raw = completed.stdout if expected == 0 else completed.stderr
        payload = json.loads(raw)
        return payload, completed

    def add(
        self,
        *,
        account: str,
        key: str,
        secret: str,
        status: str = "standby",
        expires_at: str | None = None,
    ) -> None:
        arguments = [
            "add",
            "--platform",
            "openai",
            "--account",
            account,
            "--key",
            key,
            "--env-var",
            "OPENAI_API_KEY",
            "--backend",
            "file",
            "--secret-stdin",
            "--status",
            status,
        ]
        if expires_at:
            arguments.extend(["--expires-at", expires_at])
        self.run_cli(*arguments, secret=secret)

    def mark_valid(self, locator: str) -> None:
        self.run_cli(
            "mark-validation",
            locator,
            "--result",
            "valid",
            "--note",
            "Provider accepted a scoped metadata request.",
        )

    def test_multi_account_rotation_is_redacted_and_non_destructive(self) -> None:
        future = (date.today() + timedelta(days=180)).isoformat()
        self.add(
            account="personal",
            key="primary",
            secret=self.secret_one,
            status="active",
            expires_at=future,
        )
        self.add(
            account="personal",
            key="rotation-2026-08",
            secret=self.secret_two,
            expires_at=future,
        )
        self.add(
            account="work",
            key="primary",
            secret=self.secret_three,
            status="active",
            expires_at=future,
        )
        state, completed = self.run_cli("list")
        self.assertEqual(len(state["items"]), 3)
        self.assertEqual(
            {item["locator"] for item in state["items"]},
            {
                "openai/personal/primary",
                "openai/personal/rotation-2026-08",
                "openai/work/primary",
            },
        )
        combined = completed.stdout + completed.stderr
        for secret in (self.secret_one, self.secret_two, self.secret_three):
            self.assertNotIn(secret, combined)
        registry_text = (self.home / "registry.json").read_text(encoding="utf-8")
        self.assertNotIn(self.secret_one, registry_text)
        self.assertNotIn(self.secret_two, registry_text)
        self.assertNotIn(self.secret_three, registry_text)
        duplicate, _ = self.run_cli(
            "add",
            "--platform",
            "openai",
            "--account",
            "personal",
            "--key",
            "primary",
            "--env-var",
            "OPENAI_API_KEY",
            "--backend",
            "file",
            "--secret-stdin",
            secret="replacement-must-not-win-9999",
            expected=2,
        )
        self.assertEqual(duplicate["code"], "key_already_exists")
        shown, _ = self.run_cli("show", "openai/personal/primary", "--fingerprint")
        expected_fingerprint = hashlib.sha256(self.secret_one.encode()).hexdigest()[:12]
        self.assertEqual(shown["fingerprint"], "sha256:" + expected_fingerprint)

    @unittest.skipUnless(
        sys.platform == "darwin" and shutil.which("security"),
        "requires the macOS Keychain CLI",
    )
    def test_keychain_backend_writes_confirmed_secret_without_echo(self) -> None:
        key_id = "probe-" + hashlib.sha256(str(self.root).encode()).hexdigest()[:12]
        locator = f"openai/keychain-test/{key_id}"
        secret = "dummy-keychain-confirmed-secret-0005"
        try:
            added, add_process = self.run_cli(
                "add",
                "--platform",
                "openai",
                "--account",
                "keychain-test",
                "--key",
                key_id,
                "--env-var",
                "OPENAI_API_KEY",
                "--backend",
                "keychain",
                "--secret-stdin",
                "--status",
                "standby",
                secret=secret,
            )
            self.assertEqual(added["backend"], "keychain")
            shown, show_process = self.run_cli("show", locator, "--fingerprint")
            expected = hashlib.sha256(secret.encode()).hexdigest()[:12]
            self.assertEqual(shown["fingerprint"], "sha256:" + expected)
            self.assertNotIn(
                secret,
                add_process.stdout
                + add_process.stderr
                + show_process.stdout
                + show_process.stderr,
            )
        finally:
            subprocess.run(
                [
                    "security",
                    "delete-generic-password",
                    "-a",
                    locator,
                    "-s",
                    "lov-env-management",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )

    def test_binding_rotation_and_unhealthy_rejection(self) -> None:
        future = (date.today() + timedelta(days=180)).isoformat()
        self.add(account="personal", key="primary", secret=self.secret_one, status="active", expires_at=future)
        self.add(account="personal", key="rotation-2026-08", secret=self.secret_two, status="active", expires_at=future)
        self.mark_valid("openai/personal/primary")
        self.mark_valid("openai/personal/rotation-2026-08")
        first, _ = self.run_cli(
            "bind",
            "openai/personal/primary",
            "--target",
            "shell",
            "--env-var",
            "OPENAI_API_KEY",
        )
        self.assertIsNone(first["previous_locator"])
        second, _ = self.run_cli(
            "bind",
            "openai/personal/rotation-2026-08",
            "--target",
            "shell",
            "--env-var",
            "OPENAI_API_KEY",
        )
        self.assertEqual(second["previous_locator"], "openai/personal/primary")
        state, _ = self.run_cli("list")
        self.assertEqual(
            state["bindings"]["shell"]["OPENAI_API_KEY"],
            "openai/personal/rotation-2026-08",
        )
        self.assertEqual(len(state["items"]), 2)
        self.add(
            account="personal",
            key="expired",
            secret="dummy-expired-secret-0004",
            status="active",
            expires_at="2020-01-01",
        )
        rejected, _ = self.run_cli(
            "bind",
            "openai/personal/expired",
            "--target",
            "shell",
            "--env-var",
            "OPENAI_API_KEY",
            expected=2,
        )
        self.assertEqual(rejected["code"], "unhealthy_key")

    def test_shell_projection_is_idempotent_and_mode_0600(self) -> None:
        future = (date.today() + timedelta(days=180)).isoformat()
        self.add(account="personal", key="primary", secret=self.secret_one, status="active", expires_at=future)
        self.mark_valid("openai/personal/primary")
        self.run_cli(
            "bind",
            "openai/personal/primary",
            "--target",
            "shell",
            "--env-var",
            "OPENAI_API_KEY",
        )
        rcfile = self.root / ".zshenv"
        rcfile.write_text("export EXISTING_VALUE=kept\n", encoding="utf-8")
        preview, preview_process = self.run_cli("sync-shell", "--rcfile", str(rcfile))
        self.assertEqual(preview["status"], "preview")
        self.assertNotIn(self.secret_one, preview_process.stdout)
        applied, applied_process = self.run_cli(
            "sync-shell",
            "--rcfile",
            str(rcfile),
            "--apply",
        )
        self.assertEqual(applied["status"], "applied")
        self.assertNotIn(self.secret_one, applied_process.stdout + applied_process.stderr)
        generated = self.home / "active.zsh"
        self.assertEqual(stat.S_IMODE(generated.stat().st_mode), 0o600)
        rc_text = rcfile.read_text(encoding="utf-8")
        self.assertIn("export EXISTING_VALUE=kept", rc_text)
        self.assertEqual(rc_text.count("# >>> lov-env-management >>>"), 1)
        self.run_cli("sync-shell", "--rcfile", str(rcfile), "--apply")
        self.assertEqual(
            rcfile.read_text(encoding="utf-8").count("# >>> lov-env-management >>>"),
            1,
        )
        check = subprocess.run(
            [
                "zsh",
                "-f",
                "-c",
                'source "$1"; test -n "$OPENAI_API_KEY" && test "$EXISTING_VALUE" = kept',
                "zsh",
                str(rcfile),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(check.returncode, 0, msg=check.stderr)

    def test_guarded_probe_and_system_preview(self) -> None:
        future = (date.today() + timedelta(days=180)).isoformat()
        self.add(account="work", key="primary", secret=self.secret_three, status="active", expires_at=future)
        expected_header = "Bearer " + self.secret_three

        class ProbeHandler(BaseHTTPRequestHandler):
            def log_message(self, format_string: str, *args: object) -> None:
                return

            def do_GET(self) -> None:
                status_code = 200 if self.headers.get("Authorization") == expected_header else 401
                self.send_response(status_code)
                self.end_headers()

        server = ThreadingHTTPServer(("127.0.0.1", 0), ProbeHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = "http://127.0.0.1:" + str(server.server_address[1]) + "/models"
            probe, process = self.run_cli(
                "probe",
                "openai/work/primary",
                "--url",
                url,
                "--auth",
                "bearer",
                "--allow-local-http",
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
        self.assertEqual(probe["result"], "valid")
        self.assertNotIn(self.secret_three, process.stdout + process.stderr)
        self.run_cli(
            "bind",
            "openai/work/primary",
            "--target",
            "system",
            "--env-var",
            "OPENAI_API_KEY",
        )
        preview, preview_process = self.run_cli("sync-system")
        self.assertEqual(preview["status"], "preview")
        self.assertNotIn(self.secret_three, preview_process.stdout + preview_process.stderr)
        audit, _ = self.run_cli("audit")
        self.assertEqual(audit["counts"]["errors"], 0)

    def test_dashboard_serves_only_redacted_state(self) -> None:
        future = (date.today() + timedelta(days=5)).isoformat()
        self.add(account="personal", key="primary", secret=self.secret_one, status="active", expires_at=future)
        process = subprocess.Popen(
            [
                sys.executable,
                str(SCRIPT),
                "--home",
                str(self.home),
                "dashboard",
                "--port",
                "0",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            assert process.stdout is not None
            first_line = process.stdout.readline()
            serving = json.loads(first_line)
            with urllib.request.urlopen(serving["url"], timeout=5) as response:
                html = response.read().decode("utf-8")
            token_match = re.search(r'const TOKEN = "([^"]+)";', html)
            self.assertIsNotNone(token_match)
            token = token_match.group(1) if token_match else ""
            request = urllib.request.Request(
                serving["url"] + "api/state",
                headers={"X-Lov-Token": token},
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                state_text = response.read().decode("utf-8")
            state = json.loads(state_text)
            self.assertEqual(state["summary"]["keys"], 1)
            self.assertEqual(state["summary"]["expiring"], 1)
            self.assertNotIn(self.secret_one, html)
            self.assertNotIn(self.secret_one, state_text)
            self.assertNotIn("secret_ref", state_text)
            self.assertIn("Secrets stay off the glass", html)
            blocked_request = urllib.request.Request(
                serving["url"] + "api/bind",
                data=json.dumps(
                    {
                        "target": "shell",
                        "env_var": "OPENAI_API_KEY",
                        "locator": "openai/personal/primary",
                    }
                ).encode("utf-8"),
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "X-Lov-Token": token,
                },
            )
            with self.assertRaises(urllib.error.HTTPError) as blocked:
                urllib.request.urlopen(blocked_request, timeout=5)
            self.assertEqual(blocked.exception.code, 403)
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()

    def test_trigger_and_non_trigger_contract(self) -> None:
        instructions = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("管理我的环境变量", instructions)
        self.assertIn("rotate an environment variable", instructions)
        non_trigger = instructions.split("### Do not activate when", 1)[1].split("##", 1)[0]
        self.assertIn("单次命令临时传一个环境变量", non_trigger)
        self.assertIn("云端 Secret", non_trigger)


if __name__ == "__main__":
    unittest.main()
