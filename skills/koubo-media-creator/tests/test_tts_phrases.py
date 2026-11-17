#!/usr/bin/env python3
"""Regression tests for tts.py phrases_of: the words.json phrases keep 3.0 and Node.js whole, like the captions.

run: python3 -m unittest discover -s tests
"""
import importlib.util
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tts = load("tts")
build = load("build")


class Phrases(unittest.TestCase):
    def test_joined_tokens_stay_in_one_phrase(self):
        self.assertEqual(tts.phrases_of("这是 3.0，用 Node.js 写的。1,000 张票、10:30 开抢"),
                         ["这是 3.0", "用 Node.js 写的", "1,000 张票", "10:30 开抢"])

    def test_ordinary_punctuation_still_breaks(self):
        self.assertEqual(tts.phrases_of("第一步，打开终端。然后等它跑完……好了"), ["第一步", "打开终端", "然后等它跑完", "好了"])
        self.assertEqual(tts.phrases_of("跑了 3, 4 次. 好了"), ["跑了 3", " 4 次", " 好了"])
        self.assertEqual(tts.phrases_of("我用的是GPT.然后呢"), ["我用的是GPT", "然后呢"])

    def test_same_pattern_as_captions(self):
        self.assertEqual(tts.JOINED.pattern, build.JOINED.pattern)


if __name__ == "__main__":
    unittest.main()
