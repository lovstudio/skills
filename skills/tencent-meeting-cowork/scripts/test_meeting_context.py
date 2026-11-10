#!/usr/bin/env python3
"""meeting_context.py 的回归测试：用合成的分享页跑通解析、渲染、身份判断与清理。

不联网，不含任何真实会议内容。运行：python3 scripts/test_meeting_context.py
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("meeting_context", HERE / "meeting_context.py")
mc = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mc)

LIN, ZHOU = "900001", "900002"
MEETING_ID, ROOM_ID = "777000111", "555000"

SUMMARY = "\n".join(
    [
        "**会议主题**：样例团建活动筹备沟通",
        f"**发言人**：@@({LIN})@@、@@({ZHOU})@@",
        "**会议摘要**：双方讨论了团建活动的安排与后续分工。",
        "**会议类型**：筹备沟通",
        "",
        "---",
        "",
        "### 一、过往情况",
        "#### 1. 规模与费用",
        "- **已办三场**：早期每场 30 人，人均 800元。",
        "- 没有标签的一行说明。",
        "这一行不是列表项，也要保留。",
        "",
        "### 二、分工方式",
        f"- **物料准备**：@@({ZHOU})@@一方负责采购。",
        "",
        "---",
        "",
        "### 三、待办事项",
        f"- 整理往期反馈并发给对方。 @@({ZHOU})@@",
        f"- 发送活动方案供确认。 @@({LIN})@@",
        "- 确认场地档期。",
    ]
)

GRAPHIC = {
    "theme": "样例团建活动筹备沟通",
    "description": "双方讨论了团建活动的安排与后续分工。",
    "speaker": "林晓、周衡",
    "components": [
        {
            "type": "todos",
            "position_id": 3,
            "title": "待办事项",
            "color": "purple",
            "items": [
                {"task": "整理往期反馈并发给对方", "owners": ["周衡"]},
                {"task": "发送活动方案供确认", "owners": ["林晓"]},
                {"task": "确认场地档期", "owners": []},
            ],
        },
        {"type": "highlight", "position_id": 1, "title": "核心共识", "color": "red", "content": ["先办一场小型活动。"]},
        {
            "type": "table",
            "position_id": 2,
            "title": "往期情况",
            "columns": ["场次", "人数"],
            "rows": [{"人数": "30人", "场次": "第一场"}],
        },
        {
            "type": "columns",
            "position_id": 4,
            "title": "分工",
            "columns_count": 2,
            "columns": [
                {"sub_title": "甲方", "items": ["提供主持人"], "icon": "cube", "color": "red"},
                {"sub_title": "乙方", "items": ["提供场地"]},
            ],
        },
        {"type": "timeline", "position_id": 5, "title": "节奏", "steps": [{"when": "下周", "what": "交方案"}]},
    ],
}

DIALOGUES = [
    {"note_type": 4, "note_info": "hi，我是你的会议助手。", "note_timestamp": "00:00", "status": 1},
    {
        "note_type": 1,
        "note_timestamp": "02:10",
        "status": 1,
        "note_info": (
            f"- @@({LIN})@@介绍了过往三场活动的情况，每场 30 人，**意在说明自己有组织经验**。\n"
            f"- @@({ZHOU})@@询问单场费用，@@({LIN})@@表示约 5000 元，**对方借此估算整体预算**。"
            f"随后，@@({ZHOU})@@要求补充往期照片。"
        ),
    },
    {
        "note_type": 1,
        "note_timestamp": "05:40",
        "status": 1,
        "note_info": (
            "- 双方确认先办 **小型** 活动一场，人均 1200元。\n"
            f"- **结论**：由@@({LIN})@@出方案。\n"
            f"- @@({ZHOU})@@提出需要主持人资料**这是为了走内部报销流程。**"
        ),
    },
    {"note_type": 7, "note_timestamp": "06:00", "status": 1, "note_info": "一条未知类型的记录，提到 @@(999999)@@。"},
]


def make_html(page: str = "/yuanbao/minutes", **overrides) -> str:
    props = {
        "isSharePage": True,
        "minutesSummary": {"note_type": 2, "note_info": SUMMARY, "status": 1},
        "graphicMinuteSummaryInfo": {
            "note_type": 10,
            "note_info": json.dumps(GRAPHIC, ensure_ascii=False),
            "status": 1,
        },
        "dialogues": DIALOGUES,
        "userInfoList": [
            {"uid": LIN, "nickname": "林晓", "user_type": 0},
            {"uid": ZHOU, "nickname": "周衡", "user_type": 0},
        ],
        "meetingId": MEETING_ID,
        "roomId": ROOM_ID,
        "abnormalMinutesInfo": None,
        "query": {"short_link": "SAMPLE0000000000"},
        "sharePingRoomId": f"{MEETING_ID}:{ROOM_ID}:{LIN}",
        "uid": LIN,
    }
    props.update(overrides)
    data = {"props": {"pageProps": props}, "page": page, "query": props["query"]}
    return (
        "<!DOCTYPE html><html><head><title>元宝笔记</title></head><body><div id=\"__next\"></div>"
        f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(data, ensure_ascii=False)}</script>'
        "</body></html>"
    )


def run(*argv: str) -> tuple[int, dict]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = mc.main(list(argv))
    return code, json.loads(buffer.getvalue())


def mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="tmc-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.out = self.tmp / "ctx"

    def page(self, **overrides) -> Path:
        path = self.tmp / "page.html"
        path.write_text(make_html(**overrides), encoding="utf-8")
        return path

    def build(self, *extra: str, **overrides) -> tuple[int, dict]:
        return run("context", "--html", str(self.page(**overrides)), "--out", str(self.out), *extra)

    def context(self) -> dict:
        return json.loads((self.out / "context.json").read_text(encoding="utf-8"))

    def notes(self) -> str:
        return (self.out / "notes.md").read_text(encoding="utf-8")


class ContextFiles(Base):
    def test_writes_private_files_with_marker(self) -> None:
        code, result = self.build()
        self.assertEqual(code, 0)
        self.assertTrue(result["ok"])
        self.assertEqual(result["schema"], "lov-tencent-meeting-cowork/v1")
        self.assertEqual(result["source"]["input"], "html")
        self.assertEqual(result["source"]["shortLink"], "SAMPLE0000000000")
        self.assertEqual(mode(self.out), 0o700)
        for name in ("notes.md", "context.json", mc.MARKER):
            self.assertEqual(mode(self.out / name), 0o600, name)
        self.assertEqual(result["files"]["notes"], str(self.out / "notes.md"))
        self.assertEqual(
            result["counts"],
            {"summaryPoints": 4, "cards": 5, "todos": 3, "liveNotes": 3, "liveNoteBullets": 6},
        )

    def test_internal_ids_never_leak(self) -> None:
        _, result = self.build()
        blob = self.notes() + (self.out / "context.json").read_text(encoding="utf-8") + json.dumps(result)
        for secret in ("@@(", LIN, ZHOU, MEETING_ID, ROOM_ID, "999999"):
            self.assertNotIn(secret, blob)

    def test_refuses_foreign_out_dir_and_reuses_own(self) -> None:
        self.out.mkdir()
        keep = self.out / "keep.txt"
        keep.write_text("mine", encoding="utf-8")
        code, result = self.build()
        self.assertEqual(code, 1)
        self.assertEqual(result["error"]["code"], "out-not-empty")
        self.assertEqual(keep.read_text(encoding="utf-8"), "mine")
        self.assertFalse((self.out / "notes.md").exists())
        keep.unlink()
        self.assertEqual(self.build()[0], 0)
        self.assertEqual(self.build()[0], 0)

    def test_clean_only_removes_marked_directories(self) -> None:
        plain = self.tmp / "plain"
        plain.mkdir()
        (plain / "notes.md").write_text("x", encoding="utf-8")
        code, result = run("clean", "--out", str(plain))
        self.assertEqual((code, result["error"]["code"]), (1, "not-a-context-dir"))
        self.assertTrue(plain.exists())

        self.build()
        link = self.tmp / "link"
        link.symlink_to(self.out, target_is_directory=True)
        self.assertEqual(run("clean", "--out", str(link))[0], 1)
        self.assertTrue(self.out.exists())

        code, result = run("clean", "--out", str(self.out))
        self.assertEqual(code, 0)
        self.assertEqual(result["removed"], str(self.out))
        self.assertFalse(self.out.exists())


class SummaryAndTodos(Base):
    def test_meta_sections_and_points(self) -> None:
        self.build()
        context = self.context()
        meeting = context["meeting"]
        self.assertEqual(meeting["title"], "样例团建活动筹备沟通")
        self.assertEqual(meeting["abstract"], "双方讨论了团建活动的安排与后续分工。")
        self.assertEqual(meeting["speakers"], ["林晓", "周衡"])
        self.assertIsNone(meeting["date"])
        self.assertEqual(meeting["meta"], {"会议类型": "筹备沟通"})

        first, second, third = context["summary"]["sections"]
        self.assertEqual(first["heading"], "一、过往情况")
        points = first["subsections"][0]["points"]
        self.assertEqual(first["subsections"][0]["heading"], "1. 规模与费用")
        self.assertEqual(
            points,
            [
                {"id": "s1", "label": "已办三场", "text": "早期每场 30 人，人均 800元。"},
                {"id": "s2", "label": None, "text": "没有标签的一行说明。"},
                {"id": "s3", "label": None, "text": "这一行不是列表项，也要保留。"},
            ],
        )
        self.assertEqual(second["points"], [{"id": "s4", "label": "物料准备", "text": "周衡一方负责采购。"}])
        self.assertTrue(third["isTodo"])
        self.assertEqual(third["points"], [])
        notes = self.notes()
        self.assertIn("- s1 **已办三场**：早期每场 30 人，人均 800元。", notes)
        self.assertNotIn("### 三、待办事项", notes)
        self.assertEqual(notes.count("- 发言人："), 1)

    def test_todos_owners_and_default_self_is_sharer(self) -> None:
        _, result = self.build()
        self.assertEqual(result["self"], {"name": "林晓", "source": "sharer", "match": "sharer"})
        self.assertEqual(
            result["todos"],
            [
                {"id": "t1", "task": "整理往期反馈并发给对方。", "owners": ["周衡"], "mine": False, "source": "summary"},
                {"id": "t2", "task": "发送活动方案供确认。", "owners": ["林晓"], "mine": True, "source": "summary"},
                {"id": "t3", "task": "确认场地档期。", "owners": [], "mine": False, "source": "summary"},
            ],
        )
        self.assertEqual(
            result["signals"]["todoIds"],
            {"mine": ["t2"], "others": ["t1"], "unassigned": ["t3"], "unknown": []},
        )
        self.assertTrue(any("按笔记归属人" in hint for hint in result["hints"]))
        notes = self.notes()
        self.assertIn("- t2 ★我 发送活动方案供确认。 — 负责人：林晓", notes)
        self.assertIn("- t3 确认场地档期。 — 负责人：未指定", notes)
        self.assertIn("林晓（我）、周衡", notes)

    def test_self_name_exact_partial_unmatched_ambiguous(self) -> None:
        _, exact = self.build("--self-name", "周 衡")
        self.assertEqual(exact["self"], {"name": "周衡", "source": "self-name", "match": "exact"})
        self.assertEqual(exact["signals"]["todoIds"]["mine"], ["t1"])

        _, partial = self.build("--self-name", "周衡-市场部")
        self.assertEqual(partial["self"]["match"], "partial")
        self.assertTrue(any("部分匹配" in hint for hint in partial["hints"]))

        _, unmatched = self.build("--self-name", "王五")
        self.assertIsNone(unmatched["self"])
        self.assertEqual([todo["mine"] for todo in unmatched["todos"]], [None, None, None])
        self.assertEqual(unmatched["signals"]["todoIds"]["unknown"], ["t1", "t2"])
        self.assertTrue(any("不在发言人里" in warning for warning in unmatched["warnings"]))
        self.assertIn("我是谁：未确定", self.notes())

        _, ambiguous = self.build("--self-name", "林晓", "--self-name", "周衡")
        self.assertIsNone(ambiguous["self"])
        self.assertTrue(any("不止一位" in warning for warning in ambiguous["warnings"]))

        _, single_char = self.build("--self-name", "周")
        self.assertIsNone(single_char["self"])

    def test_no_sharer_and_no_name_leaves_self_unknown(self) -> None:
        _, result = self.build(uid="")
        self.assertIsNone(result["self"])
        self.assertTrue(any("没有笔记归属人" in warning for warning in result["warnings"]))

    def test_card_todos_fill_in_when_summary_has_none(self) -> None:
        summary = SUMMARY.split("### 三、待办事项")[0]
        _, result = self.build(minutesSummary={"note_type": 2, "note_info": summary, "status": 1})
        self.assertEqual([todo["source"] for todo in result["todos"]], ["card"] * 3)
        self.assertEqual(result["todos"][1]["task"], "发送活动方案供确认")
        self.assertTrue(result["todos"][1]["mine"])
        self.assertEqual(result["warnings"], [w for w in result["warnings"] if "两处都要对照" not in w])

    def test_todo_count_mismatch_is_flagged(self) -> None:
        graphic = json.loads(json.dumps(GRAPHIC))
        graphic["components"][0]["items"].pop()
        _, result = self.build(
            graphicMinuteSummaryInfo={"note_type": 10, "note_info": json.dumps(graphic), "status": 1}
        )
        self.assertEqual(len(result["todos"]), 3)
        self.assertTrue(any("两处都要对照" in warning for warning in result["warnings"]))

    def test_unfinished_summary_status_is_flagged(self) -> None:
        _, result = self.build(minutesSummary={"note_type": 2, "note_info": SUMMARY, "status": 0})
        self.assertTrue(any("状态值是 0" in warning for warning in result["warnings"]))


class CardsAndLiveNotes(Base):
    def test_cards_follow_position_and_keep_unknown_types(self) -> None:
        self.build()
        cards = self.context()["cards"]
        self.assertEqual([card["type"] for card in cards], ["highlight", "table", "todos", "columns", "timeline"])
        self.assertEqual([card["id"] for card in cards], ["c1", "c2", "c3", "c4", "c5"])
        self.assertEqual(cards[0]["items"], ["先办一场小型活动。"])
        self.assertEqual(cards[1]["table"], {"columns": ["场次", "人数"], "rows": [["第一场", "30人"]]})
        self.assertEqual(cards[2]["todos"][0], {"task": "整理往期反馈并发给对方", "owners": ["周衡"]})
        self.assertEqual(
            cards[3]["groups"],
            [{"title": "甲方", "items": ["提供主持人"]}, {"title": "乙方", "items": ["提供场地"]}],
        )
        self.assertEqual(cards[4]["items"], ["下周", "交方案"])
        notes = self.notes()
        self.assertIn("| 场次 | 人数 |\n| --- | --- |\n| 第一场 | 30人 |", notes)
        self.assertIn("### c5 节奏（timeline）", notes)

    def test_live_notes_split_narration_from_commentary(self) -> None:
        _, result = self.build()
        context = self.context()
        first, second, third = context["liveNotes"]
        self.assertEqual((first["id"], first["at"], first["kind"]), ("n1", "02:10", "live-note"))
        self.assertEqual(
            [(bullet["id"], bullet["text"], bullet["commentary"]) for bullet in first["bullets"]],
            [
                ("n1.1", "林晓介绍了过往三场活动的情况，每场 30 人。", ["意在说明自己有组织经验"]),
                (
                    "n1.2",
                    "周衡询问单场费用，林晓表示约 5000 元。随后，周衡要求补充往期照片。",
                    ["对方借此估算整体预算"],
                ),
            ],
        )
        self.assertEqual(first["bullets"][1]["people"], ["周衡", "林晓"])
        self.assertEqual(
            [(bullet["text"], bullet["commentary"]) for bullet in second["bullets"]],
            [
                ("双方确认先办 小型 活动一场，人均 1200元。", []),
                ("结论：由林晓出方案。", []),
                ("周衡提出需要主持人资料。", ["这是为了走内部报销流程"]),
            ],
        )
        self.assertEqual(third["kind"], "type-7")
        self.assertIn(mc.UNKNOWN_PERSON, third["bullets"][0]["text"])
        self.assertEqual(context["assistantMessages"], [{"at": "00:00", "text": "hi，我是你的会议助手。"}])
        self.assertEqual(result["signals"]["unresolvedMentions"], 1)
        self.assertTrue(any("没能对上发言人" in warning for warning in result["warnings"]))
        notes = self.notes()
        self.assertIn("- n1.1 林晓介绍了过往三场活动的情况，每场 30 人。\n  - 解读：意在说明自己有组织经验", notes)
        self.assertIn("### n3 · 06:00 · 类型 type-7", notes)
        self.assertNotIn("会议助手。", notes)

    def test_split_commentary_punctuation(self) -> None:
        cases = {
            "甲说了一件事，**这是一段足够长的解读文字**。": ("甲说了一件事。", ["这是一段足够长的解读文字"]),
            "甲说了一件事，**这是一段足够长的解读文字。**": ("甲说了一件事。", ["这是一段足够长的解读文字"]),
            "甲说了一件事。**这是一段足够长的解读文字**": ("甲说了一件事。", ["这是一段足够长的解读文字"]),
            "**这是一段足够长的解读文字**，然后甲说了一件事。": ("然后甲说了一件事。", ["这是一段足够长的解读文字"]),
            "甲强调 **重点** 很重要。": ("甲强调 重点 很重要。", []),
            "**这是一个很长很长的标签**：后面是正文。": ("这是一个很长很长的标签：后面是正文。", []),
            "没有任何加粗。": ("没有任何加粗。", []),
        }
        for raw, expected in cases.items():
            self.assertEqual(mc.split_commentary(raw), expected, raw)

    def test_numbers_missing_from_summary_and_cards(self) -> None:
        _, result = self.build()
        self.assertEqual(
            result["signals"]["numbersOnlyInLiveNotes"],
            [{"value": "5000元", "refs": ["n1.2"]}, {"value": "1200元", "refs": ["n2.1"]}],
        )
        self.assertTrue(any("2 个数字没进摘要" in hint for hint in result["hints"]))
        self.assertIn("5000元（n1.2）、1200元（n2.1）", self.notes())

    def test_self_mentions_point_at_bullets(self) -> None:
        _, result = self.build()
        self.assertEqual(result["signals"]["selfMentionRefs"], ["n1.1", "n1.2", "n2.2"])
        self.assertIn("实时笔记共 6 点，其中提到我的有 3 处：n1.1、n1.2、n2.2", self.notes())

    def test_duplicate_nicknames_stay_distinct(self) -> None:
        users = [
            {"uid": LIN, "nickname": "林晓"},
            {"uid": ZHOU, "nickname": "林晓"},
        ]
        _, result = self.build(userInfoList=users)
        self.assertEqual(result["meeting"]["speakers"], ["林晓", "林晓（同名2）"])


class SourceErrors(Base):
    def test_missing_link_exits_4_without_writing(self) -> None:
        code, result = self.build(
            minutesSummary={},
            graphicMinuteSummaryInfo={},
            dialogues=[],
            userInfoList=[],
            abnormalMinutesInfo={"type": "short_link_not_found"},
        )
        self.assertEqual(code, 4)
        self.assertEqual(result["error"]["stage"], "source")
        self.assertEqual(result["error"]["code"], "short_link_not_found")
        self.assertIn("hint", result["error"])
        self.assertFalse(self.out.exists())

    def test_other_abnormal_state_is_passed_through(self) -> None:
        code, result = self.build(abnormalMinutesInfo={"type": "no_permission"})
        self.assertEqual((code, result["error"]["code"]), (4, "no_permission"))
        self.assertIn("no_permission", result["error"]["message"])

    def test_empty_minutes_exits_4(self) -> None:
        code, result = self.build(minutesSummary={}, graphicMinuteSummaryInfo={}, dialogues=[])
        self.assertEqual((code, result["error"]["code"]), (4, "empty-minutes"))

    def test_other_pages_and_broken_data(self) -> None:
        code, result = self.build(page="/cloud-record/share")
        self.assertEqual((code, result["error"]["code"]), (1, "unsupported-page"))
        self.assertIn("/cloud-record/share", result["error"]["debug"])

        plain = self.tmp / "plain.html"
        plain.write_text("<html><body>请先登录</body></html>", encoding="utf-8")
        code, result = run("context", "--html", str(plain), "--out", str(self.out))
        self.assertEqual((code, result["error"]["code"]), (1, "no-page-data"))

        broken = self.tmp / "broken.html"
        broken.write_text('<script id="__NEXT_DATA__" type="application/json">{oops</script>', encoding="utf-8")
        code, result = run("context", "--html", str(broken), "--out", str(self.out))
        self.assertEqual((code, result["error"]["code"]), (1, "bad-page-data"))

        code, result = run("context", "--html", str(self.tmp / "missing.html"), "--out", str(self.out))
        self.assertEqual((code, result["error"]["code"]), (1, "html-not-found"))

    def test_only_meeting_host_over_https_is_fetched(self) -> None:
        with mock.patch.object(mc.urllib.request, "build_opener", side_effect=AssertionError("network")):
            for url in (
                "https://example.com/ys/abc",
                "http://meeting.tencent.com/ys/abc",
                "https://meeting.tencent.com.evil.example/ys/abc",
                "https://user@evil.example/meeting.tencent.com/ys/abc",
                "https://meeting.tencent.com/",
                "file:///etc/hosts",
            ):
                code, result = run("context", "--url", url, "--out", str(self.out))
                self.assertEqual((code, result["error"]["code"]), (1, "unsupported-url"), url)
        self.assertFalse(self.out.exists())

    def test_redirect_to_another_host_is_refused(self) -> None:
        handler = mc._SameHostRedirect()
        for target in ("https://passport.example.com/login", "http://meeting.tencent.com/ys/abc"):
            with self.assertRaises(mc.CoworkError) as caught:
                handler.redirect_request(None, None, 302, "Found", {}, target)
            self.assertEqual(caught.exception.code, "redirected-away")

    def test_url_input_records_the_link(self) -> None:
        url = "https://meeting.tencent.com/ys/SAMPLE0000000000"
        with mock.patch.object(mc, "fetch_html", return_value=make_html()) as fetch:
            code, result = run("context", "--url", url, "--out", str(self.out))
        self.assertEqual(code, 0)
        fetch.assert_called_once_with(url, 20.0)
        self.assertEqual(result["source"]["input"], "url")
        self.assertEqual(result["source"]["url"], url)

    def test_network_failure_is_reported_with_stage(self) -> None:
        opener = mock.Mock()
        opener.open.side_effect = mc.urllib.error.URLError("timed out")
        with mock.patch.object(mc.urllib.request, "build_opener", return_value=opener):
            code, result = run("context", "--url", "https://meeting.tencent.com/ys/abc", "--out", str(self.out))
        self.assertEqual(code, 1)
        self.assertEqual((result["error"]["stage"], result["error"]["code"]), ("fetch", "network"))
        self.assertIn("timed out", result["error"]["debug"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
