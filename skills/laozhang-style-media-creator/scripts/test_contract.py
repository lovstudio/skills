#!/usr/bin/env python3
"""Focused regression checks for the actual shipped reference and creation case."""
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('style_media',ROOT/'scripts/style_media.py')
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile,_=api.profile_check(api.DEFAULT)
        cls.brief=api.read(ROOT/'cases/new-topic/brief.json')
        cls.plan=api.read(ROOT/'cases/new-topic/edit-plan.json')

    def test_real_profile(self):
        _,result=api.profile_check(api.DEFAULT)
        self.assertEqual((result['rules'],result['evidence_items']),(23,157))

    def test_real_plan(self):
        self.assertEqual(api.plan_check(self.plan,self.brief,self.profile)['status'],'passed')

    def test_gap_is_rejected(self):
        bad=copy.deepcopy(self.plan);bad['sections'][1]['start_seconds']+=1
        with self.assertRaisesRegex(AssertionError,'gap/overlap'):api.plan_check(bad,self.brief,self.profile)

    def test_unknown_fact_is_rejected(self):
        bad=copy.deepcopy(self.plan);bad['sections'][0]['fact_ids']=['NONEXISTENT']
        with self.assertRaisesRegex(AssertionError,'unknown fact'):api.plan_check(bad,self.brief,self.profile)

    def test_mismatched_subtitle_is_rejected(self):
        bad=copy.deepcopy(self.plan);bad['sections'][0]['subtitles'][0]['lines']=['different words']
        with self.assertRaisesRegex(AssertionError,'preserve narration'):api.plan_check(bad,self.brief,self.profile)

    def test_wrong_profile_version_is_rejected(self):
        bad=copy.deepcopy(self.plan);bad['profile_version']='0.9.0'
        with self.assertRaisesRegex(AssertionError,'wrong style/version'):api.plan_check(bad,self.brief,self.profile)

    def test_holdout_leakage_is_rejected(self):
        bad=copy.deepcopy(self.profile);bad['training_sample_ids'].append(bad['holdout_sample_ids'][0])
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'profile.json';path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(AssertionError,'leakage'):api.profile_check(path)


if __name__=='__main__':unittest.main()
