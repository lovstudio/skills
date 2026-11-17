#!/usr/bin/env python3
"""Regression tests for build.py split_caption: numbers stay whole, ordinary punctuation still breaks.

run: python3 -m unittest discover -s tests    (with or without jieba installed; both tokenizers are covered)
"""
import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("build", Path(__file__).resolve().parents[1] / "scripts" / "build.py")
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)
JIEBA = build.jieba
LIMIT = 14  # build.py --max-caption default
MODES = ["jieba", "chars"] if JIEBA else ["chars"]


def split(text, mode):
    build.jieba = JIEBA if mode == "jieba" else None
    try:
        return build.split_caption(text, None, LIMIT)
    finally:
        build.jieba = JIEBA


class NumbersStayWhole(unittest.TestCase):
    def test_short_phrases(self):
        cases = {
            "这是我常用的编辑器刚出的 3.0。": ["这是我常用的编辑器刚出的 3.0"],
            "3.0 要到下个月才进稳定版": ["3.0 要到下个月才进稳定版"],
            "一共 1,000 张票，10:30 开抢。": ["一共 1,000 张票", "10:30 开抢"],
        }
        for mode in MODES:
            for text, want in cases.items():
                with self.subTest(mode=mode, text=text):
                    self.assertEqual(split(text, mode), want)

    def test_long_line_balanced_cut(self):
        cases = {
            "今天在会上我们一共宣布了10:30准时开抢先到先得": "10:30",
            "这次大家都在等的插件版本3.0明天正式开放下载使用": "3.0",
            "今天在会上我们宣布了1,000张票明天准时开抢先到先得": "1,000",
        }
        for mode in MODES:
            for text, number in cases.items():
                with self.subTest(mode=mode, text=text):
                    chunks = split(text, mode)
                    self.assertGreater(len(chunks), 1)
                    self.assertEqual(sum(number in c for c in chunks), 1, chunks)
                    self.assertEqual("".join(chunks).replace(" ", ""), text)


class DottedNamesStayWhole(unittest.TestCase):
    def test_short_phrases(self):
        cases = {
            "把 build.py 跑一遍。然后看结果": ["把 build.py 跑一遍", "然后看结果"],
            "升级到 v0.4.2 就好": ["升级到 v0.4.2 就好"],
            "Node.js 和 claude.ai 都能用。": ["Node.js 和", "claude.ai 都能用"],
        }
        for mode in MODES:
            for text, want in cases.items():
                with self.subTest(mode=mode, text=text):
                    self.assertEqual(split(text, mode), want)

    def test_long_line_balanced_cut(self):
        cases = {
            "今天大家都在讨论的框架是Next.js明天正式开放下载使用": "Next.js",
            "这次我们把整个后端都迁到了Node.js上面效果还不错": "Node.js",
        }
        for mode in MODES:
            for text, name in cases.items():
                with self.subTest(mode=mode, text=text):
                    chunks = split(text, mode)
                    self.assertGreater(len(chunks), 1)
                    self.assertEqual(sum(name in c for c in chunks), 1, chunks)
                    self.assertEqual("".join(chunks).replace(" ", ""), text)

    def test_period_before_cjk_or_space_still_breaks(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                self.assertEqual(split("我用的是GPT.然后呢", mode), ["我用的是GPT", "然后呢"])
                self.assertEqual(split("It works. Then stop.", mode), ["It works", "Then stop"])


class OrdinaryBreaksUnchanged(unittest.TestCase):
    def test_punctuation_still_breaks(self):
        cases = {
            "第一步，打开终端。然后，等它跑完！": ["第一步", "打开终端", "然后", "等它跑完"],
            "先装好依赖：再跑脚本；最后看报告？": ["先装好依赖", "再跑脚本", "最后看报告"],
            "First, open it. Then wait!": ["First", "open it", "Then wait"],
            "It costs 99. Then pay.": ["It costs 99", "Then pay"],
            "跑了 3, 4 次. 好了": ["跑了 3", "4 次", "好了"],
            "第 1，2 步": ["第 1", "2 步"],
        }
        for mode in MODES:
            for text, want in cases.items():
                with self.subTest(mode=mode, text=text):
                    self.assertEqual(split(text, mode), want)

    def test_list_comma_becomes_space(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                self.assertEqual(split("苹果、香蕉和梨", mode), ["苹果 香蕉和梨"])


if __name__ == "__main__":
    unittest.main()
