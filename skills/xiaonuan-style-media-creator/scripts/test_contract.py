#!/usr/bin/env python3
"""Focused regression checks for the shipped style profile, the demo case and the render-plan builder."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('style_media', ROOT / 'scripts/style_media.py')
api = importlib.util.module_from_spec(spec); spec.loader.exec_module(api)


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile, _ = api.profile_check(api.DEFAULT)
        cls.brief = api.read(ROOT / 'cases/yiqimao-demo/brief.json')
        cls.plan = api.read(ROOT / 'cases/yiqimao-demo/edit-plan.json')

    def test_real_profile(self):
        _, result = api.profile_check(api.DEFAULT)
        self.assertEqual((result['rules'], result['evidence_items'], result['training_samples'], result['holdout_samples']), (32, 219, 10, 2))

    def test_frozen_profile_unchanged(self):
        import hashlib
        frozen = api.read(ROOT / 'assets/xiaonuan-v0.1/FROZEN.json')
        self.assertEqual(hashlib.sha256(api.DEFAULT.read_bytes()).hexdigest(), frozen['profile_sha256'])

    def test_real_plan(self):
        self.assertEqual(api.plan_check(self.plan, self.brief, self.profile)['status'], 'passed')

    def test_gap_is_rejected(self):
        bad = copy.deepcopy(self.plan); bad['sections'][2]['start_seconds'] += 1
        with self.assertRaisesRegex(AssertionError, 'gap/overlap'): api.plan_check(bad, self.brief, self.profile)

    def test_separator_must_follow_cold_open(self):
        bad = copy.deepcopy(self.plan); bad['sections'][0]['role'] = 'ask'
        with self.assertRaisesRegex(AssertionError, 'separator must follow the cold open'): api.plan_check(bad, self.brief, self.profile)

    def test_multiline_subtitle_is_rejected(self):
        bad = copy.deepcopy(self.plan); cue = bad['sections'][0]['subtitles'][0]; cue['text'] = cue['text'][:2] + '\n' + cue['text'][2:]
        with self.assertRaisesRegex(AssertionError, 'single-line'): api.plan_check(bad, self.brief, self.profile)

    def test_mismatched_subtitle_is_rejected(self):
        bad = copy.deepcopy(self.plan); bad['sections'][0]['subtitles'][0]['text'] = '不一样的话'
        with self.assertRaisesRegex(AssertionError, 'preserve dialogue'): api.plan_check(bad, self.brief, self.profile)

    def test_unknown_fact_is_rejected(self):
        bad = copy.deepcopy(self.plan); bad['sections'][0]['fact_ids'] = ['NONEXISTENT']
        with self.assertRaisesRegex(AssertionError, 'unknown fact'): api.plan_check(bad, self.brief, self.profile)

    def test_title_must_yield_to_card(self):
        bad = copy.deepcopy(self.plan); bad['title']['end_seconds'] = bad['card']['start_seconds'] + 3
        with self.assertRaisesRegex(AssertionError, 'title yields to the card'): api.plan_check(bad, self.brief, self.profile)

    def test_safe_area_and_peak(self):
        bad = copy.deepcopy(self.plan); bad['loudness']['true_peak_dbtp'] = 0.5
        with self.assertRaisesRegex(AssertionError, 'true peak'): api.plan_check(bad, self.brief, self.profile)

    def test_wrong_profile_version_is_rejected(self):
        bad = copy.deepcopy(self.plan); bad['profile_version'] = '0.9.0'
        with self.assertRaisesRegex(AssertionError, 'wrong style/version'): api.plan_check(bad, self.brief, self.profile)

    def test_holdout_leakage_is_rejected(self):
        bad = copy.deepcopy(self.profile); bad['training_sample_ids'].append(bad['holdout_sample_ids'][0])
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'profile.json'; path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(AssertionError, 'leakage'): api.profile_check(path)

    def test_render_plan_matches_shipped_example(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / 'render-plan.json'
            subprocess.run([sys.executable, str(ROOT / 'scripts/build_render_plan.py'), '--plan', str(ROOT / 'cases/yiqimao-demo/edit-plan.json'),
                            '--media', 'mezz=media/mezz.mp4', '--audio', 'audio/demo-mix.m4a', '--output', str(out)], check=True, capture_output=True)
            built = json.loads(out.read_text()); shipped = api.read(ROOT / 'templates/remotion/src/data/render-plan.json')
            for key in ('frames', 'bars', 'callIn', 'subtitles'):
                self.assertEqual(built[key], shipped[key], key)
            self.assertEqual((built['title']['fromF'], built['title']['toF']), (shipped['title']['fromF'], shipped['title']['toF']))
            self.assertEqual((built['card']['fromF'], built['card']['toF'], built['card']['lines']), (shipped['card']['fromF'], shipped['card']['toF'], shipped['card']['lines']))

    def test_route(self):
        def route(text):
            r = subprocess.run([sys.executable, str(ROOT / 'scripts/style_media.py'), 'route', '--request', text], capture_output=True, text=True)
            return json.loads(r.stdout)['activate']
        self.assertTrue(route('用晓暖的风格，把这段连麦录像剪成切片'))
        self.assertTrue(route('Use the xiaonuan call-in clip style to plan this'))
        self.assertFalse(route('只要下载晓暖这条视频'))
        self.assertFalse(route('用她的视频做一条晓暖风格切片'))
        self.assertFalse(route('帮我剪一条旅行 vlog'))


if __name__ == '__main__':
    unittest.main()
