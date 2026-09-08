from __future__ import annotations

import argparse
import base64
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import submit_case as client

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a/WQAAAAASUVORK5CYII=")


def sample():
    return {"case": {
        "id": "accepted-result", "type": "case", "skillIds": ["skill-add-case"], "title": "Accepted result",
        "description": "A real accepted result.", "input": {"text": "Public notes"},
        "prompt": "Organize the public notes.", "output": {"items": ["Readable notes"]},
        "evidence": {"acceptance": "user-confirmed", "verified_at": "2026-09-01",
                     "method": "Compared with the original.", "privacy": "Public notes only.", "artifact_type": "other"},
    }, "images": [], "consent": False, "dryRun": True}


class SubmitCaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.file = self.root / "submission.json"
        self.file.write_text(json.dumps(sample()))
        self.args = argparse.Namespace(action="check", skill="skill-add-case", submission=self.file,
                                       timeout=10, profile_path=None, share_session_script=None)
        self.contract = {"schemaVersion": 2, "endpoint": client.ORIGIN + "/api/cases", "skills": [{"id": "skill-add-case"}, {"id": "media-creator"}]}
        self.validated = {"status": "validated", "caseId": "accepted-result"}
        self.published = {"status": "published", "caseId": "accepted-result", "url": "/cases/accepted-result", "skillIds": ["skill-add-case"],
                          "fingerprint": "server-fingerprint", "commit": "source-commit", "duplicate": False, "cacheRefreshed": False}

    def test_offline_prepare_needs_no_account_source_checkout_or_session(self):
        case = sample()["case"]
        del case["id"]
        path = self.root / "case.json"
        path.write_text(json.dumps(case))
        args = client.build_args(["prepare", "skill-add-case", "--case", str(path), "--output", str(self.root / "out.json")])
        with patch.object(client, "contract", side_effect=AssertionError("network")), patch.object(client, "load_auth", side_effect=AssertionError("login")):
            result = client.run(args)
        prepared = json.loads(args.output.read_text())
        self.assertEqual(result["status"], "prepared")
        self.assertEqual(result["contract"], "not_checked")
        self.assertFalse(prepared["consent"])
        self.assertNotIn("sessionUrl", prepared)
        self.assertEqual(prepared, client.prepare(path, [], None))
        with self.assertRaises(FileExistsError):
            client.run(args)

    def test_image_bytes_export_in_cover_first_order_and_roundtrip(self):
        case = sample()["case"]
        case["evidence"]["artifact_type"] = "visual"
        path = self.root / "case.json"
        path.write_text(json.dumps(case))
        image = self.root / "final.png"
        image.write_bytes(PNG)
        data = client.prepare(path, [image], None)
        self.assertEqual(data["case"]["cover"], "upload:0")
        self.assertEqual(base64.b64decode(data["images"][0]["dataBase64"]), PNG)
        self.assertEqual(client.validate(data), data)
        self.assertNotIn(str(self.root), json.dumps(data))
        image.write_bytes(PNG + b"0" * client.MIB)
        with self.assertRaisesRegex(client.SubmissionError, "images_too_large"):
            client.prepare(path, [image], None)

    def test_rejects_legacy_paid_record_without_downgrading_or_stripping(self):
        for extra in ({"session": {"access": "paid"}}, {"priceCredits": 10}, {"messages": []}):
            payload = sample()
            payload["case"].update(extra)
            before = copy.deepcopy(payload)
            with self.assertRaisesRegex(client.SubmissionError, "unsupported"):
                client.validate(payload)
            self.assertEqual(payload, before)

    def test_visual_privacy_date_and_upload_limits(self):
        payloads = []
        visual = sample(); visual["case"]["evidence"]["artifact_type"] = "visual"; payloads.append(visual)
        secret = sample(); secret["case"]["prompt"] = "Read /" + "/".join(("Users", "example", "customer.txt")); payloads.append(secret)
        date = sample(); date["case"]["evidence"]["verified_at"] = "2026-02-30"; payloads.append(date)
        legacy = sample(); legacy["case"]["evidence"]["artifact_type"] = "non-visual"; payloads.append(legacy)
        missing = sample(); missing["case"]["cover"] = "upload:0"; payloads.append(missing)
        local = sample(); local["case"]["cover"] = "http://127.0.0.1/art.png"; payloads.append(local)
        wrong = sample(); wrong["case"]["cover"] = "upload:0"; wrong["images"] = [{"contentType": "image/jpeg", "dataBase64": base64.b64encode(PNG).decode()}]; payloads.append(wrong)
        for payload in payloads:
            with self.subTest(payload=payload), self.assertRaises(client.SubmissionError):
                client.validate(payload)

    def test_check_ignores_saved_consent_and_never_publishes(self):
        payload = sample(); payload.update(consent=True, dryRun=False)
        self.file.write_text(json.dumps(payload))
        with patch.object(client, "contract", return_value=self.contract), patch.object(client, "load_auth"), patch.object(client, "authenticated_post", return_value=self.validated) as post:
            result = client.run(self.args)
        self.assertEqual(post.call_count, 1)
        self.assertTrue(post.call_args.args[1]["dryRun"])
        self.assertFalse(post.call_args.args[1]["consent"])
        self.assertEqual(result["status"], "validated")

    def test_publish_requires_unchanged_reviewed_content_before_network(self):
        self.args.action = "publish"
        self.args.confirm = client.fingerprint(sample())
        payload = sample(); payload["case"]["title"] = "Changed after review"
        self.file.write_text(json.dumps(payload))
        with patch.object(client, "contract", side_effect=AssertionError("must not reach network")):
            with self.assertRaisesRegex(client.SubmissionError, "consent_mismatch"):
                client.run(self.args)
        changed = sample(); changed["sessionUrl"] = client.ORIGIN + "/yoda/session/yss_" + "A" * 43
        self.assertNotEqual(client.fingerprint(changed), self.args.confirm)

    def test_publish_preflights_then_sets_consent_preserving_retry_identity(self):
        self.args.action = "publish"; self.args.confirm = client.fingerprint(sample())
        for duplicate in (False, True):
            with patch.object(client, "contract", return_value=self.contract), patch.object(client, "load_auth"), patch.object(client, "authenticated_post", side_effect=[self.validated, {**self.published, "duplicate": duplicate}]) as post:
                result = client.run(self.args)
            preview, publish = [call.args[1] for call in post.call_args_list]
            self.assertTrue(preview["dryRun"])
            self.assertFalse(publish["dryRun"])
            self.assertTrue(publish["consent"])
            self.assertEqual(preview["case"], publish["case"])
            self.assertEqual(result["fingerprint"], "server-fingerprint")
            self.assertEqual(result["liveVerification"], "pending")
            self.assertFalse(result["cacheRefreshed"])
            self.assertEqual(result["duplicate"], duplicate)

    def test_rejected_public_session_stops_before_publication(self):
        self.args.action = "publish"; self.args.confirm = client.fingerprint(sample())
        with patch.object(client, "contract", return_value=self.contract), patch.object(client, "load_auth"), patch.object(client, "authenticated_post", side_effect=client.SubmissionError("session_not_public", 400)) as post:
            with self.assertRaisesRegex(client.SubmissionError, "session_not_public"):
                client.run(self.args)
        self.assertEqual(post.call_count, 1)

    def test_plain_json_transport_does_not_gzip_images_or_follow_redirects(self):
        response = Mock(); response.__enter__ = Mock(return_value=response); response.__exit__ = Mock(return_value=False)
        response.read.return_value = b'{"status":"validated"}'
        opener = Mock(); opener.open.return_value = response
        body = {"large": "A" * (256 * 1024)}
        with patch.object(client.urllib.request, "build_opener", return_value=opener):
            client.http_json("POST", self.contract["endpoint"], body, "test-token")
        req = opener.open.call_args.args[0]
        self.assertEqual(json.loads(req.data), body)
        self.assertIsNone(req.get_header("Content-encoding"))
        self.assertIsNone(client.NoRedirect().redirect_request(None, None, 302, "", {}, "https://elsewhere.invalid"))

    def test_cached_auth_refreshes_once_without_uploading_transcript(self):
        class AuthError(Exception):
            pass
        auth = SimpleNamespace(ShareError=AuthError, load_access_token=Mock(return_value="old"), load_refresh_token=Mock(return_value="refresh"),
                               run_refresh=Mock(return_value="new"), device_flow_signin=Mock(), upload_share=Mock(side_effect=AssertionError("no transcript")))
        with patch.dict(client.os.environ, {}, clear=True), patch.object(client, "http_json", side_effect=[client.SubmissionError("expired", 401), self.validated]) as post:
            result = client.authenticated_post(self.contract["endpoint"], sample(), self.args, auth)
        self.assertEqual(result, self.validated)
        self.assertEqual(post.call_args.args[3], "new")
        auth.run_refresh.assert_called_once()
        auth.device_flow_signin.assert_not_called()
        auth.upload_share.assert_not_called()

    def test_explicit_bad_credentials_do_not_switch_accounts(self):
        class AuthError(Exception):
            pass
        auth = SimpleNamespace(ShareError=AuthError, load_access_token=Mock(return_value="bad"), load_refresh_token=Mock())
        with patch.dict(client.os.environ, {"LOVSTUDIO_ACCESS_TOKEN": "bad"}), patch.object(client, "http_json", side_effect=client.SubmissionError("unauthorized", 401)):
            with self.assertRaises(client.SubmissionError):
                client.authenticated_post(self.contract["endpoint"], sample(), self.args, auth)
        auth.load_refresh_token.assert_not_called()

    def test_contract_refuses_unavailable_source_and_unexpected_endpoint(self):
        good = {"skillId": "skill-add-case", "available": True, **self.contract, "formUrl": client.ORIGIN + "/skills/skill-add-case/cases/new"}
        for changed in ({"available": False}, {"endpoint": "https://elsewhere.invalid"}):
            with patch.object(client, "http_json", return_value={**good, **changed}), self.assertRaises(client.SubmissionError):
                client.contract("skill-add-case", 10)


if __name__ == "__main__":
    unittest.main()


class MultiSkillTests(unittest.TestCase):
    def test_one_preparation_associates_every_requested_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); case = root / "case.json"; output = root / "output.json"
            case.write_text(json.dumps(sample()["case"]))
            args = client.build_args(["prepare", "skill-add-case", "--skill", "media-creator", "--case", str(case), "--output", str(output)])
            with patch.object(client, "http_json", side_effect=AssertionError("offline")):
                result = client.run(args)
            self.assertEqual(result["skillIds"], ["media-creator", "skill-add-case"])
            self.assertEqual(json.loads(output.read_text())["case"]["skillIds"], result["skillIds"])

    def test_relationships_are_part_of_publication_fingerprint(self):
        before = sample(); after = copy.deepcopy(before)
        after["case"]["skillIds"].append("media-creator")
        self.assertNotEqual(client.fingerprint(before), client.fingerprint(after))
        for invalid in [[], ["../private"], ["same", "same"], "skill-add-case"]:
            after["case"]["skillIds"] = invalid
            with self.assertRaisesRegex(client.SubmissionError, "invalid_skill_ids"):
                client.validate(after)
