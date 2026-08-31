from __future__ import annotations

import sys
import unittest
from unittest.mock import patch
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from publish_existing_draft import (  # noqa: E402
    PublishError,
    credentials_from_environment,
    extract_ipv4,
    post_gateway_json,
    poll_until_terminal,
    receipt_from_status,
)


class PublishExistingDraftTests(unittest.TestCase):
    def test_gateway_request_uses_stable_backend_and_api_key(self) -> None:
        observed: dict[str, object] = {}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self) -> bytes:
                return b'{"publish_id":"PUBLISH_ID"}'

        def fake_urlopen(request, timeout):
            observed["url"] = request.full_url
            observed["headers"] = dict(request.header_items())
            observed["payload"] = request.data
            observed["timeout"] = timeout
            return Response()

        with patch("publish_existing_draft.urlopen", fake_urlopen):
            result = post_gateway_json(
                "https://api.lovstudio.ai/wechat/official-account/",
                "/freepublish/submit",
                {"media_id": "MEDIA_ID"},
                "gateway-key",
                "freepublish_submit",
                12,
            )

        self.assertEqual(result["publish_id"], "PUBLISH_ID")
        self.assertEqual(
            observed["url"],
            "https://api.lovstudio.ai/wechat/official-account/freepublish/submit",
        )
        headers = observed["headers"]
        self.assertEqual(headers["X-api-key"], "gateway-key")
        self.assertEqual(headers["User-agent"], "LovStudio-WeChat-Gateway-Publisher/1.0")
        self.assertNotIn(b"gateway-key", observed["payload"])

    def test_builds_published_receipt_with_article_url(self) -> None:
        receipt = receipt_from_status(
            "PUBLISH_ID",
            {
                "publish_status": 0,
                "article_id": "ARTICLE_ID",
                "article_detail": {
                    "item": [{"article_url": "https://mp.weixin.qq.com/s/example"}],
                },
            },
            action="status",
        )

        self.assertEqual(receipt["state"], "published")
        self.assertEqual(receipt["articleId"], "ARTICLE_ID")
        self.assertEqual(receipt["articleUrls"], ["https://mp.weixin.qq.com/s/example"])

    def test_maps_platform_rejection_to_publish_failed(self) -> None:
        receipt = receipt_from_status(
            "PUBLISH_ID",
            {"publish_status": 4, "fail_idx": [1]},
            action="publish",
        )

        self.assertEqual(receipt["state"], "publish_failed")
        self.assertEqual(receipt["failIndexes"], [1])

    def test_success_without_article_identifier_stays_pending_verification(self) -> None:
        receipt = receipt_from_status(
            "PUBLISH_ID",
            {"publish_status": 0},
            action="status",
        )

        self.assertEqual(receipt["state"], "publishing")
        self.assertTrue(receipt["verificationPending"])

    def test_polls_until_terminal_without_sleeping_after_success(self) -> None:
        payloads = iter([
            {"publish_status": 1},
            {"publish_status": 0, "article_id": "ARTICLE_ID"},
        ])
        sleeps: list[float] = []
        clock = iter([0.0, 0.0])

        payload, timed_out = poll_until_terminal(
            lambda: next(payloads),
            wait_seconds=30,
            poll_seconds=5,
            sleep=sleeps.append,
            monotonic=lambda: next(clock),
        )

        self.assertFalse(timed_out)
        self.assertEqual(payload["publish_status"], 0)
        self.assertEqual(sleeps, [5])

    def test_keeps_polling_after_status_zero_until_identifier_appears(self) -> None:
        payloads = iter([
            {"publish_status": 0},
            {"publish_status": 0, "article_id": "ARTICLE_ID"},
        ])
        sleeps: list[float] = []
        clock = iter([0.0, 0.0])

        payload, timed_out = poll_until_terminal(
            lambda: next(payloads),
            wait_seconds=30,
            poll_seconds=5,
            sleep=sleeps.append,
            monotonic=lambda: next(clock),
        )

        self.assertFalse(timed_out)
        self.assertEqual(payload["article_id"], "ARTICLE_ID")
        self.assertEqual(sleeps, [5])

    def test_extracts_ipv4_and_validates_environment_credentials(self) -> None:
        self.assertEqual(
            extract_ipv4("invalid ip ::ffff:61.169.208.170, not in whitelist"),
            "61.169.208.170",
        )
        credentials = credentials_from_environment({
            "WECHAT_APP_ID": "wx1234567890abcdef",
            "WECHAT_APP_SECRET": "1234567890abcdef1234567890abcdef",
        })
        self.assertIsNotNone(credentials)
        self.assertEqual(credentials.source, "environment")

    def test_rejects_non_numeric_publish_status_as_structured_error(self) -> None:
        with self.assertRaises(PublishError) as raised:
            receipt_from_status(
                "PUBLISH_ID",
                {"publish_status": "unexpected"},
                action="status",
            )

        self.assertEqual(raised.exception.stage, "freepublish_get")


if __name__ == "__main__":
    unittest.main()
