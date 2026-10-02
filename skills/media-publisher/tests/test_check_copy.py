from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "check_copy.py"
SPEC = importlib.util.spec_from_file_location("check_copy", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
check_copy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_copy)


def run(*argv: str):
    """Run main(argv) with --json and return (exit code, parsed report)."""

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        code = check_copy.main([*argv, "--json"])
    return code, json.loads(stdout.getvalue())


def codes(report) -> set:
    return {item["code"] for item in report["findings"]}


class XiaohongshuCopyTests(unittest.TestCase):
    def test_title_of_20_chars_passes(self):
        code, report = run("--platform", "xiaohongshu", "--title", "国" * 20)

        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(codes(report), {"title_ok"})
        self.assertEqual(report["limits"]["title_max"], 20)

    def test_title_of_21_chars_fails(self):
        code, report = run("--platform", "xiaohongshu", "--title", "国" * 21)

        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "fail")
        self.assertEqual(codes(report), {"title_too_long"})
        self.assertNotIn("n/20", report["findings"][0]["message"])

    def test_description_of_1000_chars_passes(self):
        code, report = run("--platform", "xiaohongshu", "--description", "字" * 1000)

        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(codes(report), set())

    def test_description_of_1001_chars_fails(self):
        code, report = run("--platform", "xiaohongshu", "--description", "字" * 1001)

        self.assertEqual(code, 1)
        self.assertEqual(codes(report), {"description_too_long"})

    def test_topics_get_suggestion_list_notice(self):
        code, report = run("--platform", "xiaohongshu", "--topic", "南头古城")

        self.assertEqual(code, 0)
        self.assertEqual(codes(report), {"topic_pick_from_suggestions"})
        self.assertEqual(report["findings"][0]["level"], "info")

    def test_short_title_is_not_a_xiaohongshu_field(self):
        code, report = run("--platform", "xiaohongshu", "--short-title", "南头古城")

        self.assertEqual(code, 1)
        self.assertEqual(codes(report), {"field_not_on_platform"})

    def test_unknown_collection_limit_warns_instead_of_failing(self):
        # 上限没实测过不是文案的错，报 error 会让预检卡在一个改文案也修不好的状态。
        code, report = run("--platform", "xiaohongshu", "--collection", "南头古城共居实验")

        self.assertEqual(code, 0)
        self.assertNotEqual(report["status"], "fail")
        self.assertEqual(codes(report), {"collection_limit_unknown"})
        finding = report["findings"][0]
        self.assertEqual(finding["level"], "warn")
        self.assertEqual(
            finding["message"],
            "小红书合集标题上限未实测，去页面读输入框 maxLength / 计数器",
        )

    def test_empty_collection_still_fails_when_limit_unknown(self):
        code, report = run("--platform", "xiaohongshu", "--collection", "  ")

        self.assertEqual(code, 1)
        self.assertEqual(codes(report), {"collection_empty"})

    def test_inline_hashtag_in_description_warns(self):
        code, report = run(
            "--platform", "xiaohongshu",
            "--description", "八个人住进古城 #南头古城 #AI共居",
        )

        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(codes(report), {"description_inline_hashtag"})
        finding = report["findings"][0]
        self.assertEqual(finding["level"], "warn")
        self.assertEqual(finding["samples"], ["#南头古城", "#AI共居"])
        self.assertIn("#南头古城", finding["message"])
        self.assertIn("不会自动成为话题", finding["message"])
        self.assertIn("--topic", finding["message"])
        self.assertIn("联想列表", finding["message"])


class RegressionTests(unittest.TestCase):
    def test_wechat_channels_short_title_with_comma_still_fails(self):
        code, report = run("--platform", "wechat-channels", "--short-title", "南头古城，共居实验")

        self.assertEqual(code, 1)
        self.assertIn("short_title_rejected_symbol", codes(report))

    def test_wechat_channels_inline_hashtag_message_unchanged(self):
        code, report = run("--platform", "wechat-channels", "--description", "古城共居 #南头古城")

        self.assertEqual(code, 0)
        self.assertEqual(codes(report), {"description_inline_hashtag"})
        self.assertEqual(
            report["findings"][0]["message"],
            "描述文本里出现 1 处 `#…`：平台不会把纯文本解析成话题，"
            "必须点编辑区工具栏「#话题」按钮让平台生成标签节点。"
            "若这些就是本次话题，改用 --topic 传入并在页面上逐个生成",
        )

    def test_bilibili_inline_hashtag_is_plain_text(self):
        code, report = run("--platform", "bilibili", "--description", "古城共居 #南头古城")

        self.assertEqual(code, 0)
        self.assertEqual(codes(report), set())

    def test_wechat_channels_edit_stage_collection_still_unavailable(self):
        code, report = run(
            "--platform", "wechat-channels",
            "--collection", "古城共居",
            "--collection-stage", "edit",
        )

        self.assertEqual(code, 1)
        self.assertEqual(codes(report), {"collection_stage_unavailable"})

    def test_bilibili_title_of_80_chars_still_ok(self):
        code, report = run("--platform", "bilibili", "--title", "国" * 80)

        self.assertEqual(code, 0)
        self.assertEqual(codes(report), {"title_ok"})

    def test_bilibili_title_overflow_keeps_counter_wording(self):
        code, report = run("--platform", "bilibili", "--title", "国" * 81)

        self.assertEqual(code, 1)
        self.assertEqual(codes(report), {"title_too_long"})
        self.assertIn("n/80", report["findings"][0]["message"])


if __name__ == "__main__":
    unittest.main()
