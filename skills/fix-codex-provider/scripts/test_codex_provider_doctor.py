#!/usr/bin/env python3
"""End-to-end checks for codex_provider_doctor.py against a synthetic home."""

from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("codex_provider_doctor.py")


def build_fixture(root: Path) -> None:
    (root / "config.toml").write_text(
        "\n".join(
            [
                'model_provider = "custom"',
                'model = "deepseek-flash"',
                "",
                "[model_providers.custom]",
                'name = "deepseek"',
                'base_url = "https://api.deepseek.com"',
                'wire_api = "responses"',
                "requires_openai_auth = false",
                'experimental_bearer_token = "test-token"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    sessions = root / "sessions" / "2026" / "09" / "11"
    sessions.mkdir(parents=True)
    rollouts = {}
    for thread_id, provider in (
        ("thread-yoda-active", "yoda"),
        ("thread-yoda-archived", "yoda"),
        ("thread-custom", "custom"),
    ):
        path = sessions / f"rollout-{thread_id}.jsonl"
        meta = {
            "ordinal": 0,
            "payload": {"model_provider": provider, "id": thread_id},
            "timestamp": "2026-09-11T10:00:00Z",
            "type": "session_meta",
        }
        path.write_text(
            json.dumps(meta, separators=(",", ":")) + "\n"
            '{"ordinal":1,"payload":{"type":"message"},"type":"event"}\n',
            encoding="utf-8",
        )
        rollouts[thread_id] = str(path)
    con = sqlite3.connect(root / "state_5.sqlite")
    con.execute(
        "CREATE TABLE threads (id TEXT PRIMARY KEY, rollout_path TEXT, "
        "model_provider TEXT, archived INTEGER, created_at INTEGER, updated_at INTEGER)"
    )
    rows = [
        ("thread-yoda-active", rollouts["thread-yoda-active"], "yoda", 0, 1000, 2000),
        ("thread-yoda-archived", rollouts["thread-yoda-archived"], "yoda", 1, 900, 1500),
        ("thread-custom", rollouts["thread-custom"], "custom", 0, 800, 1800),
    ]
    con.executemany("INSERT INTO threads VALUES (?,?,?,?,?,?)", rows)
    con.commit()
    con.close()
    logs = sqlite3.connect(root / "logs_2.sqlite")
    logs.execute(
        "CREATE TABLE logs (id INTEGER PRIMARY KEY, ts REAL, level TEXT, "
        "feedback_log_body TEXT)"
    )
    logs.execute(
        "INSERT INTO logs (ts, level, feedback_log_body) VALUES (?, ?, ?)",
        (
            time.time(),
            "WARN",
            "thread/start failed: failed to load configuration: "
            "Model provider `yoda` not found (code -32600)",
        ),
    )
    logs.commit()
    logs.close()
    desktop = root / "desktop-logs" / "2026" / "09" / "12"
    desktop.mkdir(parents=True)
    (desktop / "codex-desktop-test.log").write_text(
        "2026-09-12T09:21:13.000Z error [electron-message-handler] "
        "Failed to resume conversation conversationId=thread-yoda-active "
        'errorMessage="failed to load configuration: Model provider `yoda` not found"\n',
        encoding="utf-8",
    )


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class DoctorTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)
        build_fixture(self.home)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_report_flags_missing_history_provider(self) -> None:
        result = run(
            "--codex-home",
            str(self.home),
            "--desktop-log-root",
            str(self.home / "desktop-logs"),
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertIn("yoda", report["unavailable_history"])
        self.assertNotIn("custom", report["unavailable_history"])
        self.assertEqual(report["threads"]["yoda"]["total"], 2)
        self.assertEqual(report["log_evidence"]["yoda"]["count"], 1)
        self.assertEqual(
            report["desktop_log_evidence"]["yoda"]["resume_failures"], 1
        )
        codes = {finding["code"] for finding in report["findings"]}
        self.assertIn("history_provider_missing", codes)
        self.assertIn("desktop_resume_failed", codes)

    def test_retag_updates_index_and_rollout_with_backup(self) -> None:
        result = run(
            "--codex-home",
            str(self.home),
            "--fix-retag",
            "custom",
            "--yes",
            "--force",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        con = sqlite3.connect(self.home / "state_5.sqlite")
        providers = dict(con.execute("SELECT id, model_provider FROM threads"))
        con.close()
        self.assertEqual(providers["thread-yoda-active"], "custom")
        self.assertEqual(providers["thread-yoda-archived"], "custom")
        self.assertEqual(providers["thread-custom"], "custom")
        for thread_id in ("thread-yoda-active", "thread-yoda-archived"):
            first = (
                self.home / "sessions" / "2026" / "09" / "11" / f"rollout-{thread_id}.jsonl"
            ).read_text(encoding="utf-8").splitlines()[0]
            meta = json.loads(first)
            self.assertEqual(meta["payload"]["model_provider"], "custom")
            self.assertEqual(meta["payload"]["id"], thread_id)
        backups = list((self.home / "provider-repair-backups").glob("*"))
        self.assertEqual(len(backups), 1)
        self.assertTrue((backups[0] / "state_5.sqlite").is_file())
        self.assertTrue(list((backups[0] / "rollouts").rglob("*.firstline")))
        follow_up = run("--codex-home", str(self.home), "--json")
        self.assertNotIn("yoda", json.loads(follow_up.stdout)["unavailable_history"])

    def test_active_only_keeps_archived_threads(self) -> None:
        result = run(
            "--codex-home",
            str(self.home),
            "--fix-retag",
            "custom",
            "--active-only",
            "--yes",
            "--force",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        con = sqlite3.connect(self.home / "state_5.sqlite")
        providers = dict(con.execute("SELECT id, model_provider FROM threads"))
        con.close()
        self.assertEqual(providers["thread-yoda-active"], "custom")
        self.assertEqual(providers["thread-yoda-archived"], "yoda")

    def test_restore_returns_original_state(self) -> None:
        self.assertEqual(
            run(
                "--codex-home",
                str(self.home),
                "--fix-retag",
                "custom",
                "--yes",
                "--force",
            ).returncode,
            0,
        )
        backup = next((self.home / "provider-repair-backups").glob("*"))
        result = run(
            "--codex-home",
            str(self.home),
            "--restore",
            str(backup),
            "--yes",
            "--force",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        con = sqlite3.connect(self.home / "state_5.sqlite")
        providers = dict(con.execute("SELECT id, model_provider FROM threads"))
        con.close()
        self.assertEqual(providers["thread-yoda-active"], "yoda")
        first = (
            self.home
            / "sessions"
            / "2026"
            / "09"
            / "11"
            / "rollout-thread-yoda-active.jsonl"
        ).read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual(json.loads(first)["payload"]["model_provider"], "yoda")

    def test_retag_rejects_unknown_target(self) -> None:
        result = run(
            "--codex-home", str(self.home), "--fix-retag", "nope", "--yes", "--force"
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("not defined", result.stderr)

    def test_retag_without_confirmation_only_prints_plan(self) -> None:
        result = run("--codex-home", str(self.home), "--fix-retag", "custom", "--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Dry run", result.stdout)
        con = sqlite3.connect(self.home / "state_5.sqlite")
        providers = dict(con.execute("SELECT id, model_provider FROM threads"))
        con.close()
        self.assertEqual(providers["thread-yoda-active"], "yoda")
        self.assertFalse((self.home / "provider-repair-backups").exists())

    def test_report_reads_a_cold_wal_copy(self) -> None:
        con = sqlite3.connect(self.home / "state_5.sqlite")
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("UPDATE threads SET model_provider='yoda' WHERE id='thread-custom'")
        con.commit()
        con.close()
        copy_dir = self.home / "cold-copy"
        copy_dir.mkdir()
        shutil.copy2(self.home / "state_5.sqlite", copy_dir / "state_5.sqlite")
        result = run("--codex-home", str(copy_dir), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["threads"]["yoda"]["total"], 3)


if __name__ == "__main__":
    unittest.main()
