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

    def test_ten_topics_pass(self):
        topics = [arg for i in range(10) for arg in ("--topic", f"话题{i}")]
        code, report = run("--platform", "xiaohongshu", *topics)

        self.assertEqual(code, 0)
        self.assertNotIn("topics_too_many", codes(report))
        self.assertEqual(report["limits"]["topic_max"], 10)

    def test_eleven_topics_fail_with_page_wording(self):
        # 2026-10-29：12 个话题点「发布」只闪出「最多支持添加10个话题」，删到 10 个后发布成功。
        topics = [arg for i in range(11) for arg in ("--topic", f"话题{i}")]
        code, report = run("--platform", "xiaohongshu", *topics)

        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "fail")
        finding = next(f for f in report["findings"] if f["code"] == "topics_too_many")
        self.assertEqual(finding["level"], "error")
        self.assertEqual(finding["limit"], 10)
        self.assertEqual(finding["actual"], 11)
        self.assertIn("最多支持添加10个话题", finding["message"])

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

    def test_description_plus_topic_names_within_limit_passes(self):
        # 990 字正文 + 话题名「南头古城」4 字 = 994，未超 1000。
        code, report = run(
            "--platform", "xiaohongshu",
            "--description", "字" * 990, "--topic", "南头古城",
        )

        self.assertEqual(code, 0)
        self.assertNotIn("description_with_topics_over_limit", codes(report))

    def test_description_plus_topic_names_over_limit_warns(self):
        # 997 字正文 + 话题名 4 字 = 1001：正文本身没超，但计数器会算上话题。
        code, report = run(
            "--platform", "xiaohongshu",
            "--description", "字" * 997, "--topic", "#南头古城",
        )

        self.assertEqual(code, 0)
        self.assertNotIn("description_too_long", codes(report))
        finding = next(f for f in report["findings"]
                       if f["code"] == "description_with_topics_over_limit")
        self.assertEqual(finding["level"], "warn")
        self.assertEqual(finding["field"], "description")
        self.assertEqual(finding["estimate_floor"], 1001)

    def test_newlines_are_not_counted_in_the_floor(self):
        # 30 段 × 32 字 = 960 字 + 29 个换行；加 6 个话题名 21 字 = 981，不应报超。
        body = "\n".join(["字" * 32] * 30)
        topics = [arg for name in ("算法", "编程", "动态规划", "背包问题", "背包九讲", "NOIP")
                  for arg in ("--topic", name)]
        code, report = run("--platform", "xiaohongshu", "--description", body, *topics)

        self.assertEqual(code, 0)
        self.assertNotIn("description_with_topics_over_limit", codes(report))

    def test_floor_excludes_newlines_when_still_over(self):
        # 2 段 × 500 字 + 1 个换行，加话题名 4 字：下限 1004，不含换行。
        body = "字" * 500 + "\n" + "字" * 500
        code, report = run("--platform", "xiaohongshu", "--description", body, "--topic", "南头古城")

        finding = next(f for f in report["findings"]
                       if f["code"] == "description_with_topics_over_limit")
        self.assertEqual(finding["estimate_floor"], 1004)

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


class WechatChannelsShortTitleTests(unittest.TestCase):
    def test_four_char_short_title_fails_minimum(self):
        # 2026-10-12 页面原文「标题至少6个字」，触发值就是这个 4 字短标题。
        code, report = run("--platform", "wechat-channels", "--short-title", "背包九讲")

        self.assertEqual(code, 1)
        self.assertEqual(codes(report), {"short_title_too_short"})
        finding = report["findings"][0]
        self.assertEqual(finding["limit"], 6)
        self.assertEqual(finding["actual"], 4)
        self.assertIn("标题至少6个字", finding["message"])

    def test_six_char_short_title_passes(self):
        # 同日按提示改成的 6 字短标题，页面提示消失。
        code, report = run("--platform", "wechat-channels", "--short-title", "背包问题九讲")

        self.assertEqual(code, 0)
        self.assertEqual(codes(report), set())
        self.assertEqual(report["limits"]["short_title_min"], 6)
        self.assertEqual(report["limits"]["short_title_max"], 16)

    def test_sixteen_char_short_title_with_spaces_still_passes(self):
        code, report = run("--platform", "wechat-channels", "--short-title", "第一时间读 Harness 架构")

        self.assertEqual(code, 0)
        self.assertEqual(codes(report), set())

    def test_other_platforms_have_no_short_title_minimum(self):
        for platform in ("bilibili", "xiaohongshu"):
            code, report = run("--platform", platform, "--title", "标题")
            self.assertEqual(code, 0)
            self.assertIsNone(report["limits"]["short_title_min"])


class BilibiliTagTests(unittest.TestCase):
    def test_vibecoding_is_refused_as_topic_only(self):
        # 2026-10-06 投稿页 toast：「当前tag为话题专用，不允许自定义添加」
        code, report = run("--platform", "bilibili", "--topic", "vibecoding")

        self.assertEqual(code, 1)
        self.assertIn("topic_reserved_for_topics", codes(report))
        self.assertIn("vibecoding", report["limits"]["topic_refused"])

    def test_vibecoding_refusal_ignores_case_and_hash(self):
        code, report = run("--platform", "bilibili", "--topic", "#VibeCoding")

        self.assertEqual(code, 1)
        self.assertIn("topic_reserved_for_topics", codes(report))

    def test_ai_programming_replacement_passes(self):
        code, report = run("--platform", "bilibili", "--topic", "AI编程")

        self.assertEqual(code, 0)
        self.assertEqual(codes(report), {"topic_refusal_list_partial"})

    def test_earlier_refused_tags_still_listed(self):
        code, report = run("--platform", "bilibili", "--topic", "插件开发")

        self.assertEqual(code, 1)
        self.assertEqual(
            report["limits"]["topic_refused"][:3],
            ["DeepSeekHarness", "独立开发者", "插件开发"],
        )


class RegressionTests(unittest.TestCase):
    def test_wechat_channels_eight_topics_within_template_range(self):
        topics = [arg for i in range(8) for arg in ("--topic", f"话题{i}")]
        code, report = run("--platform", "wechat-channels", *topics)

        self.assertEqual(code, 0)
        self.assertNotIn("topics_many", codes(report))

    def test_wechat_channels_eleven_topics_warn(self):
        topics = [arg for i in range(11) for arg in ("--topic", f"话题{i}")]
        code, report = run("--platform", "wechat-channels", *topics)

        self.assertEqual(code, 0)
        self.assertIn("topics_many", codes(report))

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

    def test_bilibili_tags_do_not_count_toward_description(self):
        code, report = run(
            "--platform", "bilibili",
            "--description", "字" * 1999, "--topic", "架构设计",
        )

        self.assertEqual(code, 0)
        self.assertNotIn("description_with_topics_over_limit", codes(report))

    def test_bilibili_eleven_tags_message_unchanged(self):
        topics = [arg for i in range(11) for arg in ("--topic", f"标签{i}")]
        code, report = run("--platform", "bilibili", *topics)

        self.assertEqual(code, 1)
        finding = next(f for f in report["findings"] if f["code"] == "topics_too_many")
        self.assertEqual(finding["message"], "标签 11 个，超过平台 10 个上限")

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
