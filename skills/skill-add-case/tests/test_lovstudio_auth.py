import argparse
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import lovstudio_auth as auth
import submit_case


class BundledAuthTests(unittest.TestCase):
    def test_default_auth_is_bundled_without_resolving_a_sibling(self):
        with patch.dict(os.environ, {}, clear=True), patch("add_case_with_session.resolve_share_script", side_effect=AssertionError("unpublished dependency")):
            module = submit_case.load_auth(None)
        self.assertIs(module, auth)
        self.assertFalse(hasattr(module, "upload_share"))
        self.assertFalse(hasattr(module, "resolve_transcript_paths"))

    def test_device_login_handles_pending_slowdown_and_caches_private_credentials(self):
        with tempfile.TemporaryDirectory() as temp:
            args = argparse.Namespace(base_url="https://lovstudio.ai", timeout=10, profile_path=Path(temp) / "profile.json")
            complete = "https://lovstudio.ai/auth/device?user_code=TEST-CODE"
            replies = [{"verificationUri": "https://lovstudio.ai/auth/device", "verificationUriComplete": complete, "deviceCode": "device", "userCode": "TEST-CODE", "interval": 1, "expiresIn": 20},
                       {"error": "authorization_pending"}, {"error": "slow_down"},
                       {"status": "authenticated", "accessToken": "fake-access", "refreshToken": "fake-refresh"}]
            output = io.StringIO()
            with patch.object(auth, "http_json", side_effect=replies), patch.object(auth.time, "sleep") as sleep, contextlib.redirect_stderr(output):
                token = auth.device_flow_signin(args)
            self.assertEqual(token, "fake-access")
            self.assertIn(complete, output.getvalue())
            self.assertNotIn("fake-access", output.getvalue())
            self.assertNotIn("fake-refresh", output.getvalue())
            self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 1, 2])
            cache = auth.credential_store_path(args.profile_path)
            self.assertEqual(cache.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(cache.read_text())["refresh_token"], "fake-refresh")

    def test_denied_or_expired_device_login_never_publishes_or_saves(self):
        args = argparse.Namespace(base_url="https://lovstudio.ai", timeout=10, profile_path=None)
        for code in ("access_denied", "expired_token"):
            replies = [{"verificationUri": "https://lovstudio.ai/auth/device", "deviceCode": "device"}, {"error": code}]
            with patch.object(auth, "http_json", side_effect=replies), patch.object(auth.time, "sleep"), patch.object(auth, "save_credentials") as save, contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(auth.ShareError):
                    auth.device_flow_signin(args)
            save.assert_not_called()

    def test_credentials_cannot_be_forwarded_to_a_different_auth_service(self):
        with self.assertRaisesRegex(auth.ShareError, "Unexpected authentication"):
            auth.http_json("POST", "https://example.invalid/api/cli/auth/refresh", {"refreshToken": "fake"}, None, 10)
        self.assertIsNone(auth.NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.invalid"))


if __name__ == "__main__":
    unittest.main()
