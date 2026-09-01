from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "publish_via_gateway.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("publish_via_gateway", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class GatewayPublisherTests(unittest.TestCase):
    def _write_cover_receipt(self, root: Path, cover: Path) -> Path:
        logo = root / "publication-logo.png"
        logo.write_bytes(b"official-logo")
        receipt = root / "cover-composition.json"
        receipt.write_text(
            json.dumps(
                {
                    "schema": "lov-wechat-cover-composition/v1",
                    "logo": str(logo),
                    "logoSha256": MODULE.hashlib.sha256(logo.read_bytes()).hexdigest(),
                    "logoVariant": "white",
                    "publisherLogoPresent": True,
                    "shareCoverUpload": str(cover),
                    "artifacts": {"wide": {"jpg": str(cover)}},
                }
            ),
            encoding="utf-8",
        )
        return receipt

    def test_content_limit_uses_visible_text_and_utf8_bytes(self) -> None:
        content = '<section style="' + ("color:#111;" * 2_000) + '">正文</section>'

        visible_chars, html_bytes = MODULE.validate_wechat_content_size(content)

        self.assertEqual(visible_chars, 2)
        self.assertGreater(len(content), 20_000)
        self.assertEqual(html_bytes, len(content.encode("utf-8")))

    def test_content_limit_rejects_oversized_visible_text(self) -> None:
        with self.assertRaisesRegex(MODULE.GatewayPublishError, "可见正文"):
            MODULE.validate_wechat_content_size("<p>" + ("文" * 20_000) + "</p>")

    def test_content_limit_rejects_oversized_utf8_html(self) -> None:
        content = '<section style="' + ("a" * 1_000_000) + '">正文</section>'

        with self.assertRaisesRegex(MODULE.GatewayPublishError, "UTF-8 字节"):
            MODULE.validate_wechat_content_size(content)

    def test_compact_renderer_extracts_images_and_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "image.jpg").write_bytes(b"jpeg")
            markdown = root / "article.md"
            markdown.write_text(
                """---
title: 测试文章
author: 手工川
cover: image.jpg
---

# 测试文章

> 一段导语。

## 第一节

普通段落与 **重点**。

![图片说明](image.jpg)

*一段图片说明。*

| 名称 | 用途 |
|---|---|
| 网关 | 固定出口 |
""",
                encoding="utf-8",
            )
            content, images, frontmatter = MODULE.render_compact_markdown(markdown)
        self.assertEqual(frontmatter["title"], "测试文章")
        self.assertEqual(len(images), 1)
        self.assertIn("__LOV_WECHAT_IMAGE_000__", content)
        self.assertIn("<blockquote", content)
        self.assertIn("<table", content)
        self.assertNotIn("<h1", content)
        self.assertLess(len(content), 2_000)

    def test_multipart_builder_does_not_put_secret_in_content_type(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            image = Path(temporary) / "cover.jpg"
            image.write_bytes(b"jpeg")
            body, content_type = MODULE.build_multipart(
                [("app_secret", "dummy-secret-value")],
                [("cover", image, "image/jpeg")],
            )
        self.assertIn(b"dummy-secret-value", body)
        self.assertNotIn("dummy-secret-value", content_type)
        self.assertTrue(content_type.startswith("multipart/form-data; boundary="))

    def test_body_image_upload_retries_only_recoverable_gateway_failures(self) -> None:
        image = MODULE.BodyImage("placeholder", Path("image.jpg"), "alt")
        client = mock.Mock()
        client.upload_body_image.side_effect = [
            MODULE.GatewayPublishError("upload_body_image", "timeout"),
            "https://mmbiz.qpic.cn/example",
        ]
        with mock.patch.object(MODULE.time, "sleep") as sleep:
            result = MODULE.upload_body_image_with_retry(client, image)

        self.assertEqual(result, "https://mmbiz.qpic.cn/example")
        self.assertEqual(client.upload_body_image.call_count, 2)
        sleep.assert_called_once_with(0.5)

    def test_lovpen_wechat_html_only_replaces_local_image_src(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            markdown = root / "article.md"
            markdown.write_text("# 标题\n", encoding="utf-8")
            (root / "image.jpg").write_bytes(b"jpeg")
            source = """<section class="lovpen-renderer typora-newsprint" style="color:#282722">
<h2 class="chapter" style="margin-top:28px"><span style="font-size:28px">标题</span></h2>
<p style="line-height:1.8">正文 <a href="https://example.com" style="color:#315f9d">来源</a></p>
<p style="margin:0"><img src="image.jpg" alt="示意图" style="width:100%"></p>
<table class="comparison" style="border-collapse:collapse"><tr><td style="padding:4px">表格</td></tr></table>
</section>"""
            lovpen_html = root / "article.lovpen.wechat.html"
            lovpen_html.write_text(source, encoding="utf-8")
            content, images, layout, metrics, fingerprint = MODULE.render_lovpen_wechat_html(
                lovpen_html, markdown
            )

        self.assertEqual(len(images), 1)
        self.assertEqual(layout, "lovpen-wechat-copy")
        self.assertEqual(images[0].path.name, "image.jpg")
        self.assertEqual(content, source.replace("image.jpg", "__LOV_WECHAT_IMAGE_000__"))
        self.assertEqual(
            metrics,
            {
                "inlineStyleAttributes": 9,
                "classAttributes": 3,
                "spanTags": 1,
                "tableTags": 1,
                "imageTags": 1,
            },
        )
        self.assertEqual(fingerprint, MODULE.lovpen_fidelity_fingerprint(content))

    def test_lovpen_wechat_html_rejects_standalone_document(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            markdown = root / "article.md"
            markdown.write_text("# 标题\n", encoding="utf-8")
            lovpen_html = root / "article.lovpen.html"
            lovpen_html.write_text(
                """<!doctype html><html><head><style>p{color:red}</style></head>
<body><section id="article-section"><p>正文</p></section></body></html>""",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(MODULE.GatewayPublishError, "--format wechat"):
                MODULE.render_lovpen_wechat_html(lovpen_html, markdown)

    def test_lovpen_wechat_html_allows_native_video_shadow_style(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            markdown = root / "article.md"
            markdown.write_text("# 标题\n", encoding="utf-8")
            source = (
                '<section class="lovpen-renderer" style="color:#111">'
                '<mp-common-videosnap data-pluginname="mpvideosnap" data-id="export/video">'
                '<template shadowrootmode="open"><style>.wx-root{display:flex}</style>'
                '<div class="wx-root"><div style="width:282px">视频号</div></div></template>'
                '</mp-common-videosnap></section>'
            )
            lovpen_html = root / "article.lovpen.wechat.html"
            lovpen_html.write_text(source, encoding="utf-8")
            content, images, layout, _metrics, _fingerprint = MODULE.render_lovpen_wechat_html(
                lovpen_html, markdown
            )

        self.assertEqual(content, source)
        self.assertEqual(images, [])
        self.assertEqual(layout, "lovpen-wechat-copy")

    def test_lovpen_wechat_html_rejects_article_level_style(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            markdown = root / "article.md"
            markdown.write_text("# 标题\n", encoding="utf-8")
            lovpen_html = root / "article.lovpen.wechat.html"
            lovpen_html.write_text(
                '<section class="lovpen-renderer" style="color:#111">'
                '<style>.article{color:red}</style><p style="line-height:1.8">正文</p></section>',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(MODULE.GatewayPublishError, "正文级外部样式"):
                MODULE.render_lovpen_wechat_html(lovpen_html, markdown)

    def test_lovpen_wechat_html_rejects_remote_images(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            markdown = root / "article.md"
            markdown.write_text("# 标题\n", encoding="utf-8")
            lovpen_html = root / "article.lovpen.wechat.html"
            lovpen_html.write_text(
                '<section class="lovpen-renderer" style="color:#111">'
                '<img src="https://example.com/image.jpg" style="width:100%"></section>',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(MODULE.GatewayPublishError, "非本地图片"):
                MODULE.render_lovpen_wechat_html(lovpen_html, markdown)

    def test_lovpen_fidelity_verification_detects_style_loss(self) -> None:
        expected_html = (
            '<section class="lovpen-renderer" style="color:#111">'
            '<span class="label" style="font-size:28px">标题</span>'
            '<img src="local/image.jpg" style="width:100%">'
            '<table style="width:100%"><tr><td>正文</td></tr></table></section>'
        )
        expected = MODULE.lovpen_fidelity_metrics(expected_html)
        fingerprint = MODULE.lovpen_fidelity_fingerprint(expected_html)
        uploaded_html = expected_html.replace(
            "local/image.jpg", "https://mmbiz.qpic.cn/example/image.jpg"
        )

        self.assertEqual(
            MODULE.verify_lovpen_fidelity(uploaded_html, expected, fingerprint), expected
        )
        changed_style = uploaded_html.replace("color:#111", "color:#222")
        with self.assertRaisesRegex(MODULE.GatewayPublishError, "非图片内容发生变化"):
            MODULE.verify_lovpen_fidelity(changed_style, expected, fingerprint)

    def test_remote_lovpen_audit_allows_observed_wechat_sanitization(self) -> None:
        submitted = (
            '<section class="lovpen-renderer" style="color:#111">'
            '<div class="wrapper" style="position:relative;display:block">'
            '<p style="margin:0"><a href="https://example.com" '
            'style="color:#315f75">来源文字</a></p>'
            '<img src="https://mmbiz.qpic.cn/source" style="width:100%">'
            "</div></section>"
        )
        remote = (
            '<section class="lovpen-renderer" style="color:#111">'
            '<div class="wrapper" style="display:block">'
            '<p style="margin:0"> 来源文字 </p>'
            '<img src="https://mmbiz.qpic.cn/remote" style="width:100%">'
            "</div></section>"
        )

        audit = MODULE.audit_remote_lovpen_fidelity(submitted, remote)

        self.assertTrue(audit["remoteFidelityVerified"])
        self.assertEqual(audit["remoteWechatSanitization"]["removedTags"], {"a": 1})
        self.assertEqual(
            audit["remoteWechatSanitization"]["removedStyleProperties"], {"position": 1}
        )

    def test_remote_lovpen_audit_allows_only_external_anchor_to_be_removed(self) -> None:
        submitted = (
            '<section class="lovpen-renderer" style="color:#111">'
            '<p><a href="https://mp.weixin.qq.com/source">微信原文</a></p>'
            '<p>工作室： <a href="https://lovstudio.ai">https://lovstudio.ai</a></p>'
            "</section>"
        )
        remote = (
            '<section class="lovpen-renderer" style="color:#111">'
            '<p><a href="https://mp.weixin.qq.com/source">微信原文</a></p>'
            '<p>工作室：https://lovstudio.ai</p>'
            "</section>"
        )

        audit = MODULE.audit_remote_lovpen_fidelity(submitted, remote)

        self.assertTrue(audit["remoteFidelityVerified"])
        self.assertEqual(audit["remoteWechatSanitization"]["removedTags"], {"a": 1})

    def test_remote_lovpen_audit_allows_wechat_to_own_native_video_shadow_markup(self) -> None:
        submitted = (
            '<section class="lovpen-renderer" style="color:#111">'
            '<p style="margin:0">正文</p>'
            '<mp-common-videosnap class="js_uneditable channels_iframe" '
            'data-id="export/video" data-nonceid="nonce-1" data-username="finder-1" '
            'data-pluginname="mpvideosnap" data-type="video" data-height="1440">'
            '<template shadowrootmode="open"><style>.wx-root{display:flex}</style>'
            '<div class="wx-root"><span>本地预览作者名</span></div></template>'
            '</mp-common-videosnap></section>'
        )
        remote = (
            '<section class="lovpen-renderer" style="color:#111">'
            '<p style="margin:0">正文</p>'
            '<mp-common-videosnap class="js_uneditable channels_iframe" '
            'data-id="export/video" data-nonceid="nonce-1" data-username="finder-1" '
            'data-pluginname="mpvideosnap" data-type="video" data-height="1928" '
            'data-parentwidth="362"></mp-common-videosnap></section>'
        )

        audit = MODULE.audit_remote_lovpen_fidelity(submitted, remote)

        self.assertTrue(audit["remoteFidelityVerified"])
        self.assertEqual(
            audit["remoteWechatSanitization"]["normalizedNativeVideoComponents"], 1
        )

    def test_remote_lovpen_audit_rejects_changed_native_video_identity(self) -> None:
        submitted = (
            '<section class="lovpen-renderer" style="color:#111">'
            '<mp-common-videosnap data-id="export/video" data-nonceid="nonce-1" '
            'data-username="finder-1" data-pluginname="mpvideosnap" data-type="video">'
            '<template shadowrootmode="open"><div>预览</div></template>'
            '</mp-common-videosnap></section>'
        )
        remote = submitted.replace('data-id="export/video"', 'data-id="export/other"')

        with self.assertRaisesRegex(MODULE.GatewayPublishError, "身份字段不一致"):
            MODULE.audit_remote_lovpen_fidelity(submitted, remote)

    def test_remote_lovpen_audit_rejects_other_css_loss(self) -> None:
        submitted = (
            '<section class="lovpen-renderer" style="color:#111">'
            '<p style="font-size:28px;margin:0">正文</p></section>'
        )
        remote = (
            '<section class="lovpen-renderer" style="color:#111">'
            '<p style="margin:0">正文</p></section>'
        )

        with self.assertRaisesRegex(MODULE.GatewayPublishError, "未允许的版式变化"):
            MODULE.audit_remote_lovpen_fidelity(submitted, remote)

    def test_success_receipt_replaces_legacy_direct_ip_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            receipt_path = Path(temporary) / "receipt.json"
            receipt_path.write_text(
                json.dumps(
                    {
                        "transport": "api",
                        "technicalDetail": {
                            "apiErrorCode": 40164,
                            "whitelistIp": "192.0.2.1",
                        },
                    }
                ),
                encoding="utf-8",
            )
            MODULE.update_receipt(
                receipt_path,
                state="draft_created",
                media_id="MEDIA_ID",
                detail={"remoteImageCount": 43, "blocker": None},
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

        self.assertEqual(receipt["transport"], "uni-api-gateway")
        self.assertEqual(receipt["mediaId"], "MEDIA_ID")
        self.assertNotIn("apiErrorCode", receipt["technicalDetail"])
        self.assertNotIn("whitelistIp", receipt["technicalDetail"])

    def test_receipt_can_checkpoint_created_draft_before_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            receipt_path = Path(temporary) / "receipt.json"
            MODULE.update_receipt(
                receipt_path,
                state="draft_created",
                media_id="MEDIA_ID",
                verification_pending=True,
                detail={"blocker": "等待远端回读"},
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

        self.assertEqual(receipt["state"], "draft_created")
        self.assertEqual(receipt["mediaId"], "MEDIA_ID")
        self.assertTrue(receipt["verificationPending"])

    def test_default_publish_requires_lovpen_wechat_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            article = root / "article.md"
            cover = root / "cover.jpg"
            article.write_text("# 标题\n\n正文。\n", encoding="utf-8")
            cover.write_bytes(b"cover")
            receipt = self._write_cover_receipt(root, cover)

            with self.assertRaisesRegex(MODULE.GatewayPublishError, "--lovpen-wechat-html"):
                MODULE.main(
                    [
                        str(article),
                        "--title", "标题",
                        "--app-id", "wx-test",
                        "--wechat-secret-locator", "secret-locator",
                        "--gateway-key-locator", "gateway-locator",
                        "--cover", str(cover),
                        "--cover-composition-receipt", str(receipt),
                        "--dry-run",
                    ]
                )

    def test_default_publish_requires_cover_composition_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            article = root / "article.md"
            cover = root / "cover.jpg"
            article.write_text("# 标题\n\n正文。\n", encoding="utf-8")
            cover.write_bytes(b"cover")

            with self.assertRaisesRegex(MODULE.GatewayPublishError, "--cover-composition-receipt"):
                MODULE.main(
                    [
                        str(article),
                        "--title", "标题",
                        "--app-id", "wx-test",
                        "--wechat-secret-locator", "secret-locator",
                        "--gateway-key-locator", "gateway-locator",
                        "--cover", str(cover),
                        "--allow-compact-markdown",
                        "--dry-run",
                    ]
                )

    def test_gateway_publish_cannot_bypass_body_hero_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            article = root / "article.md"
            cover = root / "cover.jpg"
            article.write_text("# 标题\n\n正文。\n", encoding="utf-8")
            cover.write_bytes(b"cover")
            receipt = self._write_cover_receipt(root, cover)

            with self.assertRaisesRegex(MODULE.GatewayPublishError, "正文第一块"):
                MODULE.main(
                    [
                        str(article),
                        "--title", "标题",
                        "--app-id", "wx-test",
                        "--wechat-secret-locator", "secret-locator",
                        "--gateway-key-locator", "gateway-locator",
                        "--cover", str(cover),
                        "--cover-composition-receipt", str(receipt),
                        "--allow-compact-markdown",
                        "--dry-run",
                    ]
                )

    def test_gateway_publish_cannot_bypass_benchmark_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            article = root / "article.md"
            cover = root / "cover.jpg"
            article.write_text("# 我调研了去 AI 味 Prompt\n\n## 测试结果\n\n第一名。\n", encoding="utf-8")
            cover.write_bytes(b"cover")
            receipt = self._write_cover_receipt(root, cover)

            with self.assertRaisesRegex(MODULE.GatewayPublishError, "测试方法"):
                MODULE.main(
                    [
                        str(article),
                        "--title", "我调研了去 AI 味 Prompt",
                        "--app-id", "wx-test",
                        "--wechat-secret-locator", "secret-locator",
                        "--gateway-key-locator", "gateway-locator",
                        "--cover", str(cover),
                        "--cover-composition-receipt", str(receipt),
                        "--allow-compact-markdown",
                        "--allow-unverified-body-hero",
                        "--dry-run",
                    ]
                )

    def test_cover_composition_receipt_must_match_uploaded_cover(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            composed_cover = root / "share-cover-wide-logo.jpg"
            other_cover = root / "other-cover.jpg"
            composed_cover.write_bytes(b"composed")
            other_cover.write_bytes(b"other")
            receipt = self._write_cover_receipt(root, composed_cover)

            with self.assertRaisesRegex(MODULE.ArtifactContractError, "shareCoverUpload"):
                MODULE.validate_cover_composition_receipt(receipt, other_cover)

    def test_cover_composition_receipt_returns_hash_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cover = root / "share-cover-wide-logo.jpg"
            cover.write_bytes(b"composed")
            receipt = self._write_cover_receipt(root, cover)

            evidence = MODULE.validate_cover_composition_receipt(receipt, cover)

        self.assertTrue(evidence["coverCompositionVerified"])
        self.assertEqual(
            evidence["coverArtifactSha256"],
            MODULE.hashlib.sha256(b"composed").hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
