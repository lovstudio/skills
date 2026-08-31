from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "enrich_via_wechat_web_api.py"
SPEC = importlib.util.spec_from_file_location("enrich_via_wechat_web_api", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class WeChatWebApiEnrichmentTests(unittest.TestCase):
    def test_redact_url_removes_session_token(self) -> None:
        redacted = MODULE._redact_url(
            "https://mp.weixin.qq.com/cgi-bin/appmsg?action=edit&token=secret-token&lang=zh_CN"
        )

        self.assertNotIn("secret-token", redacted)
        self.assertIn("token=[REDACTED]", redacted)

    def test_expression_uses_private_api_and_original_fields_without_secrets(self) -> None:
        expression = MODULE._build_expression(
            title="日本文字排版技术与艺术 | 深度调研",
            author="手工川",
            digest="向隔壁偷学点排版技术，有用。",
            source_url="https://lovstudio.ai/blog/japanese-typography-2026-08-26",
            category="艺术文化",
            reprint_permit_type=1,
        )

        self.assertIn("/cgi-bin/operate_appmsg", expression)
        self.assertIn("copyright_type0", expression)
        self.assertIn("original_article_type0", expression)
        self.assertIn("reprint_permit_type0", expression)
        self.assertIn("艺术文化", expression)
        self.assertIn("location.href", expression)
        self.assertIn("document.querySelectorAll('input[name], textarea[name], select[name]')", expression)
        self.assertNotIn("set('need_open_comment0'", expression)
        self.assertNotIn("set('show_cover_pic0'", expression)
        self.assertNotIn("secret-token", expression)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for JavaScript syntax validation")
    def test_generated_expression_is_valid_javascript(self) -> None:
        expression = MODULE._build_expression(
            title="标题",
            author="手工川",
            digest="推荐语",
            source_url="https://lovstudio.ai/blog/example",
            category="艺术文化",
            reprint_permit_type=1,
        )

        subprocess.run(
            ["node", "-e", "new Function(process.argv[1]);", expression],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_main_requires_explicit_rights_confirmation_before_target_lookup(self) -> None:
        args = [
            "--title",
            "标题",
            "--author",
            "手工川",
            "--original-category",
            "艺术文化",
        ]

        with mock.patch.object(MODULE, "_find_target") as find_target:
            with self.assertRaisesRegex(MODULE.EnrichmentError, "显式传入"):
                MODULE.main(args)

        find_target.assert_not_called()

    def test_receipt_stays_pending_and_never_persists_session_token(self) -> None:
        result = {
            "appMsgId": "100014941",
            "ret": 0,
            "originalVerified": False,
            "author": "手工川",
            "category": "艺术文化",
            "observedCopyrightType": None,
            "observedOriginalArticleType": None,
            "coverPreserved": True,
            "verificationSource": "not observed after save",
        }
        target = MODULE.ChromeTarget(
            url=(
                "https://mp.weixin.qq.com/cgi-bin/appmsg?action=edit&"
                "appmsgid=100014941&token=secret-token"
            ),
            websocket_url="ws://127.0.0.1/devtools/page/example",
        )

        with tempfile.TemporaryDirectory() as temporary:
            receipt = Path(temporary) / "receipt.json"
            MODULE._write_receipt(receipt, result, target)
            raw = receipt.read_text(encoding="utf-8")
            payload = json.loads(raw)

        self.assertEqual(payload["state"], "draft_enriching")
        self.assertTrue(payload["verificationPending"])
        self.assertFalse(payload["editorFields"]["editorFieldsVerified"])
        self.assertEqual(payload["editorFields"]["originalCategoryRequested"], "艺术文化")
        self.assertEqual(payload["technicalDetail"]["transport"], "wechat-web-private-api")
        self.assertNotIn("secret-token", raw)
        self.assertIn("[REDACTED]", raw)


if __name__ == "__main__":
    unittest.main()
