#!/usr/bin/env python3
"""Offline tests for WeChat Channels resolver fallback and resolver-service errors.

Every network call goes through a fake ``urlopen``; the credential lookup and
``subprocess.run`` are patched so no real Keychain entry is ever read.

Run from the repository root:

    python3 -B -m unittest discover -s tests -v
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from typing import Any
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import authorize_yuanbao  # noqa: E402
import media_crawler as mc  # noqa: E402


SPH_URL = "https://weixin.qq.com/sph/EXAMPLE123"
CUSTOM_WORKER = "https://resolver.example.invalid/api/fetch_video_profile"
STALE_COOKIE = "hy_user=offline-test; hy_token=stale-test-value"
VIDEO_URL = "https://finder.video.qq.com/stream/sample.mp4?token=signed"
FEED = {
    "feedInfo": {"description": "测试标题\n第二行", "videoUrl": VIDEO_URL},
    "authorInfo": {"nickname": "测试作者"},
}
PARSE_OK = {
    "code": 0,
    "data": {
        "wx_export_id": "export-1",
        "playable_url": "https://channels.weixin.qq.com/play?token=tok&eid=export-1",
    },
}
PARSE_EMPTY = {"code": 0, "data": {"wx_export_id": ""}}
WXCLIENT_DOWN = urllib.error.URLError("connection refused")


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: Any) -> bool:
        return False


class FakeNetwork:
    """Route requests by URL prefix: an int is an HTTP status, a dict a JSON body."""

    def __init__(self, routes: dict[str, Any]) -> None:
        self.routes = routes
        self.requests: list[Any] = []

    @property
    def urls(self) -> list[str]:
        return [request.full_url.split("?", 1)[0] for request in self.requests]

    def headers_for(self, prefix: str) -> dict[str, str]:
        for request in self.requests:
            if request.full_url.startswith(prefix):
                return {key.lower(): value for key, value in request.header_items()}
        raise AssertionError(f"no request was sent to {prefix}")

    def urlopen(self, request: Any, timeout: float = 0) -> FakeResponse:
        self.requests.append(request)
        url = request.full_url
        for prefix, outcome in self.routes.items():
            if not url.startswith(prefix):
                continue
            if isinstance(outcome, int):
                raise urllib.error.HTTPError(
                    url, outcome, "error", None, io.BytesIO(b'{"error":"unauthorized"}')
                )
            if isinstance(outcome, Exception):
                raise outcome
            return FakeResponse(outcome)
        raise AssertionError(f"unexpected network call: {url}")


class OfflineCase(unittest.TestCase):
    def offline(self, routes: dict[str, Any], *, cookie: str) -> FakeNetwork:
        network = FakeNetwork(routes)
        forbidden = AssertionError("tests must not read the Keychain or spawn processes")
        for target, replacement in (
            ("urllib.request.urlopen", network.urlopen),
            ("media_crawler.resolve_cookie", lambda: cookie),
            ("media_crawler.read_keychain_cookie", mock.Mock(side_effect=forbidden)),
            ("media_crawler.subprocess.run", mock.Mock(side_effect=forbidden)),
        ):
            patcher = mock.patch(target, replacement)
            patcher.start()
            self.addCleanup(patcher.stop)
        return network


class ResolveWechatFallbackTest(OfflineCase):
    def test_rejected_credential_falls_back_to_public_resolver_when_opted_in(self) -> None:
        network = self.offline(
            {mc.YUANBAO_PARSE_URL: 401, mc.PUBLIC_WORKER_URL: FEED}, cookie=STALE_COOKIE
        )
        media_url, metadata, resolver, fallback_from = mc.resolve_wechat(
            SPH_URL, worker_url="", allow_public_resolver=True
        )
        self.assertEqual(media_url, VIDEO_URL)
        self.assertEqual(metadata["title"], "测试标题")
        self.assertEqual(resolver, "public_worker")
        self.assertEqual(fallback_from, "authorization_failed")
        self.assertEqual(network.urls, [mc.YUANBAO_PARSE_URL, mc.PUBLIC_WORKER_URL])
        # The rejected Cookie must never be forwarded to the third-party service.
        worker_headers = network.headers_for(mc.PUBLIC_WORKER_URL)
        self.assertNotIn("cookie", worker_headers)
        self.assertNotIn("stale-test-value", json.dumps(worker_headers))

    def test_rejected_credential_falls_back_to_custom_worker(self) -> None:
        network = self.offline(
            {mc.YUANBAO_PARSE_URL: 403, CUSTOM_WORKER: {"data": FEED}}, cookie=STALE_COOKIE
        )
        media_url, _, resolver, fallback_from = mc.resolve_wechat(
            SPH_URL, worker_url=CUSTOM_WORKER, allow_public_resolver=False
        )
        self.assertEqual(media_url, VIDEO_URL)
        self.assertEqual(resolver, "custom_worker")
        self.assertEqual(fallback_from, "authorization_failed")
        self.assertEqual(network.urls, [mc.YUANBAO_PARSE_URL, CUSTOM_WORKER])

    def test_rejected_credential_without_opt_in_keeps_authorization_failed(self) -> None:
        network = self.offline({mc.YUANBAO_PARSE_URL: 401}, cookie=STALE_COOKIE)
        with self.assertRaises(mc.JobError) as caught:
            mc.resolve_wechat(SPH_URL, worker_url="", allow_public_resolver=False)
        self.assertEqual(caught.exception.code, "authorization_failed")
        self.assertIn("authorize_yuanbao.py", caught.exception.next_action)
        self.assertEqual(network.urls, [mc.YUANBAO_PARSE_URL])

    def test_non_authorization_failure_does_not_fall_back(self) -> None:
        network = self.offline({mc.YUANBAO_PARSE_URL: PARSE_EMPTY}, cookie=STALE_COOKIE)
        with self.assertRaises(mc.JobError) as caught:
            mc.resolve_wechat(SPH_URL, worker_url="", allow_public_resolver=True)
        self.assertEqual(caught.exception.code, "resolver_failed")
        self.assertEqual(network.urls, [mc.YUANBAO_PARSE_URL])

    def test_valid_credential_never_contacts_the_resolver_service(self) -> None:
        network = self.offline(
            {mc.YUANBAO_PARSE_URL: PARSE_OK, mc.WECHAT_FEED_URL: FEED}, cookie=STALE_COOKIE
        )
        _, _, resolver, fallback_from = mc.resolve_wechat(
            SPH_URL, worker_url=CUSTOM_WORKER, allow_public_resolver=True
        )
        self.assertEqual(resolver, "yuanbao_direct")
        self.assertEqual(fallback_from, "")
        self.assertEqual(network.urls, [mc.YUANBAO_PARSE_URL, mc.WECHAT_FEED_URL])

    def test_rejected_credential_and_refused_resolver_report_both(self) -> None:
        self.offline({mc.YUANBAO_PARSE_URL: 401, mc.PUBLIC_WORKER_URL: 401}, cookie=STALE_COOKIE)
        with self.assertRaises(mc.JobError) as caught:
            mc.resolve_wechat(SPH_URL, worker_url="", allow_public_resolver=True)
        error = caught.exception
        self.assertEqual(error.code, "authorization_failed")
        self.assertIn("resolver_unauthorized", error.message)
        self.assertIn("解析服务拒绝访问", error.message)
        self.assertIn("authorize_yuanbao.py", error.next_action)
        self.assertNotIn("stale-test-value", error.message + error.next_action)


class ResolverServiceErrorTest(OfflineCase):
    def test_resolver_service_401_and_403_use_a_distinct_code(self) -> None:
        for status in (401, 403):
            with self.subTest(status=status):
                self.offline({mc.PUBLIC_WORKER_URL: status}, cookie="")
                with self.assertRaises(mc.JobError) as caught:
                    mc.resolve_wechat(SPH_URL, worker_url="", allow_public_resolver=True)
                error = caught.exception
                self.assertEqual(error.code, "resolver_unauthorized")
                self.assertIn(f"HTTP {status}", error.message)
                self.assertIn("解析服务拒绝访问", error.message)
                self.assertNotIn("authorize_yuanbao", error.next_action)
                self.assertNotIn("重新授权", error.next_action)

    def test_custom_worker_401_uses_the_same_distinct_code(self) -> None:
        self.offline({CUSTOM_WORKER: 401}, cookie="")
        with self.assertRaises(mc.JobError) as caught:
            mc.resolve_wechat(SPH_URL, worker_url=CUSTOM_WORKER, allow_public_resolver=False)
        self.assertEqual(caught.exception.code, "resolver_unauthorized")

    def test_yuanbao_401_is_still_authorization_failed(self) -> None:
        self.offline({mc.YUANBAO_PARSE_URL: 401}, cookie="")
        with self.assertRaises(mc.JobError) as caught:
            mc.resolve_wechat_direct(SPH_URL, STALE_COOKIE)
        self.assertEqual(caught.exception.code, "authorization_failed")
        self.assertIn("authorize_yuanbao.py", caught.exception.next_action)

    def test_resolver_service_500_stays_resolver_failed(self) -> None:
        self.offline({mc.PUBLIC_WORKER_URL: 500}, cookie="")
        with self.assertRaises(mc.JobError) as caught:
            mc.resolve_wechat(SPH_URL, worker_url="", allow_public_resolver=True)
        self.assertEqual(caught.exception.code, "resolver_failed")


class DownloadCommandTest(OfflineCase):
    def run_main(self, argv: list[str]) -> tuple[int, dict[str, Any], str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", ["media_crawler.py", *argv]):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = mc.main()
        return code, json.loads(stdout.getvalue()), stdout.getvalue() + stderr.getvalue()

    def test_resolver_refusal_is_reported_without_yuanbao_reauthorization(self) -> None:
        self.offline({mc.PUBLIC_WORKER_URL: 401, mc.WXCLIENT_API: WXCLIENT_DOWN}, cookie="")
        with tempfile.TemporaryDirectory() as temp:
            code, report, output = self.run_main(
                ["download", SPH_URL, "--output-dir", temp, "--allow-public-resolver", "--json"]
            )
            self.assertEqual(list(Path(temp).iterdir()), [])
        self.assertEqual(code, 2)
        self.assertEqual(report["code"], "resolver_unauthorized")
        self.assertNotIn("authorize_yuanbao", report["next_action"])
        self.assertIn("wxclient.sh", report["next_action"])
        self.assertNotIn("stale-test-value", output)

    def test_download_marks_the_fallback_in_the_report(self) -> None:
        self.offline({mc.YUANBAO_PARSE_URL: 401, mc.PUBLIC_WORKER_URL: FEED}, cookie=STALE_COOKIE)

        def fake_downloader(media_url: str, target: Path, **_: Any) -> tuple[int, str]:
            self.assertEqual(media_url, VIDEO_URL)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"\x00\x00\x00\x18ftypisom" + b"0" * 64)
            return 0, "fake"

        with tempfile.TemporaryDirectory() as temp:
            report_path = Path(temp) / "result.json"
            with mock.patch("media_crawler.run_downloader", fake_downloader), mock.patch(
                "media_crawler.shutil.which", lambda _name: None
            ):
                code, report, output = self.run_main(
                    [
                        "download",
                        SPH_URL,
                        "--output-dir",
                        temp,
                        "--allow-public-resolver",
                        "--json-report",
                        str(report_path),
                        "--json",
                    ]
                )
            saved = report_path.read_text(encoding="utf-8")
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "verified")
        self.assertEqual(report["resolver"], "public_worker")
        self.assertEqual(report["fallback_from"], "authorization_failed")
        self.assertNotIn("stale-test-value", output + saved)


class AuthorizeYuanbaoArgsTest(unittest.TestCase):
    def test_timeout_defaults_to_ten_minutes_and_can_be_overridden(self) -> None:
        with mock.patch.object(sys, "argv", ["authorize_yuanbao.py", "--test-url", SPH_URL]):
            self.assertEqual(authorize_yuanbao.parse_args().timeout, 600)
        with mock.patch.object(
            sys, "argv", ["authorize_yuanbao.py", "--test-url", SPH_URL, "--timeout", "1800"]
        ):
            self.assertEqual(authorize_yuanbao.parse_args().timeout, 1800)


if __name__ == "__main__":
    unittest.main()
