"""Behavior regressions: rejected prose families, legitimate prose, review integrity."""
import copy
import importlib.util
from pathlib import Path
import unittest
spec = importlib.util.spec_from_file_location('gate', Path(__file__).parents[1]/'scripts/discourse_gate.py')
gate = importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)

class GateTests(unittest.TestCase):
    def test_user_negative_examples(self):
        examples = ['账号模型和客户端是三件事', '先把这个说准确一点', '这次要做的',
                    'CC-Switch 负责另一段', '这是企业账号场景里需要说清楚的部分',
                    '网关路由和账号会受什么影响？', '账号风险不能写成零',
                    '数据经过的环节变多也值得留意', '解决的是一个很具体的问题']
        for text in examples:
            with self.subTest(text=text):
                self.assertTrue(gate.scan(text.encode())['findings'])
    def test_paraphrases(self):
        for text in ['有必要先厘清几个概念。', '本文要讨论的是权限。',
                     '另一个组件负责的是另一层。', '账号风险不可表述为零。',
                     '这些差异不容忽视。', '解决了一个真实痛点。']:
            with self.subTest(text=text):
                self.assertTrue(gate.scan(text.encode())['findings'])
    def test_legitimate_prose(self):
        text = '先把端口改成 4399，再启动服务。\n\nCopilot 可用 Claude，不等于 Claude Pro 订阅。\n\n接口升级后代理可能失效。\n\n## 安装与启用'
        self.assertFalse(gate.scan(text.encode())['findings'])
    def test_code_and_quotes(self):
        text = '---\ntitle: 先说清楚\n---\n\n```text\n账号风险不能写成零\n```\n\n> 用户批评：“账号风险不能写成零”。\n\n执行 `先说清楚` 命令。'
        report = gate.scan(text.encode())
        self.assertFalse(report['findings']);self.assertEqual(len(report['units']), 2)
    def test_absence_of_matches_is_not_approval(self):
        self.assertEqual(gate.scan('打开设置。'.encode())['status'], 'needs_review')
    def fixture(self):
        report = gate.scan('# 安装\n\n点击 Enable 启动服务。'.encode())
        review = {'schema': gate.REVIEW_SCHEMA, 'reviewer': 'test-fixture',
                  'input_sha256': report['input_sha256'],
                  'units': [{'id':u['id'], 'decision':'accept', 'reason':'测试记录：标题定位安装步骤，正文给出启动动作。'} for u in report['units']]}
        return report, review
    def test_complete_review(self):
        report, review = self.fixture();self.assertEqual(gate.validate_review(report, review), [])
    def test_stale_missing_duplicate_and_unresolved(self):
        report, good = self.fixture()
        for change in ['stale','missing','duplicate','revise','empty_reason']:
            review=copy.deepcopy(good)
            if change=='stale': review['input_sha256']='0'*64
            if change=='missing': review['units'].pop()
            if change=='duplicate': review['units'].append(review['units'][0])
            if change=='revise': review['units'][0]['decision']='revise'
            if change=='empty_reason': review['units'][0]['reason']=''
            with self.subTest(change=change):
                self.assertTrue(gate.validate_review(report,review))
    def test_malformed_review(self):
        report,_=self.fixture()
        for review in [None, [], {'units':[{'id': []}]}]:
            self.assertTrue(gate.validate_review(report,review))

if __name__=='__main__': unittest.main()
