from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "filing_record.py"


class FilingRecordCliTest(unittest.TestCase):
    def run_cli(self, *args: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(expected, result.returncode, result.stderr)
        return result

    def test_init_append_compare_and_check(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            record = Path(temporary) / "record.md"
            self.run_cli(
                "init", "--path", str(record), "--subject", "示例公司",
                "--service", "示例网站", "--domain", "example.cn",
                "--provider", "示例接入商",
            )
            first = self.run_cli(
                "append", "--path", str(record),
                "--time", "2026-08-14T10:00:00+08:00",
                "--authority", "接入商订单详情", "--stage", "icp",
                "--status", "authority-review", "--domain-status", "held-off",
                "--action", "等待审核", "--evidence", "页面显示已提交管局",
            )
            self.assertTrue(json.loads(first.stdout)["changed"])
            same = self.run_cli(
                "compare", "--path", str(record),
                "--time", "2026-08-15T10:00:00+08:00",
                "--authority", "接入商订单详情", "--stage", "icp",
                "--status", "authority-review", "--domain-status", "held-off",
                "--action", "等待审核", "--evidence", "状态未变化",
            )
            self.assertFalse(json.loads(same.stdout)["changed"])
            checked = self.run_cli("check", "--path", str(record))
            self.assertTrue(json.loads(checked.stdout)["valid"])

    def test_user_action_and_duplicate_time(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            record = Path(temporary) / "record.md"
            self.run_cli(
                "init", "--path", str(record), "--subject", "示例公司",
                "--service", "示例网站", "--domain", "example.cn",
                "--provider", "示例接入商",
            )
            args = (
                "append", "--path", str(record),
                "--time", "2026-08-14T10:00:00+08:00",
                "--authority", "工信部系统", "--stage", "icp",
                "--status", "blocked-user-action", "--domain-status", "held-off",
                "--action", "完成短信核验", "--evidence", "需要验证码",
            )
            result = self.run_cli(*args)
            self.assertTrue(json.loads(result.stdout)["needs_user_action"])
            duplicate = self.run_cli(*args, expected=2)
            self.assertIn("already exists", duplicate.stderr)

    def test_naive_timestamp_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            record = Path(temporary) / "record.md"
            self.run_cli(
                "init", "--path", str(record), "--subject", "示例公司",
                "--service", "示例网站", "--domain", "example.cn",
                "--provider", "示例接入商",
            )
            result = self.run_cli(
                "compare", "--path", str(record),
                "--time", "2026-08-14T10:00:00", "--authority", "系统",
                "--stage", "monitor", "--status", "unable-to-verify",
                "--domain-status", "unverified", "--action", "登录",
                "--evidence", "会话失效", expected=2,
            )
            self.assertIn("timezone offset", result.stderr)

    def test_mainland_website_launch_pipeline(self) -> None:
        expected_modules = [
            "filing-readiness",
            "icp-filing",
            "domain-cutover",
            "public-security-filing",
            "filing-monitor",
        ]
        kit_text = (ROOT / "kit.yaml").read_text(encoding="utf-8")
        pipeline = kit_text.split("mainland-website-launch:", 1)[1].split("  icp-only:", 1)[0]
        positions = [pipeline.index(f"- {module}") for module in expected_modules]
        self.assertEqual(positions, sorted(positions))

        with tempfile.TemporaryDirectory() as temporary:
            record = Path(temporary) / "pipeline.md"
            self.run_cli(
                "init", "--path", str(record), "--subject", "示例公司",
                "--service", "示例网站", "--domain", "example.cn",
                "--provider", "示例接入商",
            )
            observations = [
                ("readiness", "completed", "held-off", "准备完成"),
                ("icp", "approved", "held-off", "取得服务备案号"),
                ("cutover", "completed", "footer-verified", "域名上线"),
                ("public-security", "authority-review", "footer-verified", "等待公安审核"),
                ("monitor", "authority-review", "footer-verified", "继续巡检"),
            ]
            for index, (stage, status, domain_status, action) in enumerate(observations, start=1):
                result = self.run_cli(
                    "append", "--path", str(record),
                    "--time", f"2026-08-{index:02d}T10:00:00+08:00",
                    "--authority", "演练权威页", "--stage", stage,
                    "--status", status, "--domain-status", domain_status,
                    "--action", action, "--evidence", "离线流水线演练",
                )
                self.assertTrue(json.loads(result.stdout)["changed"])
            final = json.loads(self.run_cli("check", "--path", str(record)).stdout)
            self.assertEqual("monitor", final["last"]["stage"])


class SkillRoutingContractTest(unittest.TestCase):
    def test_documented_trigger_routing(self) -> None:
        routes = {
            "filing-readiness": "备案前检查",
            "icp-filing": "继续 ICP 备案",
            "domain-cutover": "备案通过了，部署并绑定域名",
            "public-security-filing": "继续公安备案",
            "filing-monitor": "每天检查备案状态",
        }
        for module, phrase in routes.items():
            text = (ROOT / "skills" / module / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("## Triggers", text)
            self.assertIn(phrase, text)
            self.assertIn("### Do not activate when", text)

    def test_adjacent_non_trigger_is_documented(self) -> None:
        root_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("只生成隐私政策或服务条款页面", root_skill)
        self.assertIn("lov-legal-pages", root_skill)


if __name__ == "__main__":
    unittest.main()
