import sys
import tempfile
from pathlib import Path
import unittest
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import clash_tun_doctor as doctor


class DirectListTests(unittest.TestCase):
    def test_merge_prepend_preserves_existing_rules(self):
        original = (
            "prepend:\n"
            '  - "PROCESS-NAME,WeChat,DIRECT"\n'
            "\n"
            "append: []\n"
        )

        updated = doctor.merge_prepend(
            original,
            [
                "DOMAIN,apply.miracleplus.com,DIRECT",
                "PROCESS-NAME,WeChat,DIRECT",
            ],
        )

        self.assertEqual(updated.count("PROCESS-NAME,WeChat,DIRECT"), 1)
        self.assertIn('  - "DOMAIN,apply.miracleplus.com,DIRECT"\n', updated)
        self.assertIn("append: []\n", updated)

    def test_discovery_keeps_non_direct_and_explicit_hosts(self):
        with tempfile.TemporaryDirectory() as raw_dir:
            data_dir = Path(raw_dir)
            profiles = data_dir / "profiles"
            logs = data_dir / "service-logs/service"
            profiles.mkdir(parents=True)
            logs.mkdir(parents=True)
            (data_dir / "profiles.yaml").write_text(
                "current: remote\n"
                "- uid: remote\n"
                "  type: remote\n"
                "  option:\n"
                "    rules: rules-id\n",
                encoding="utf-8",
            )
            (profiles / "rules-id.yaml").write_text(
                "prepend:\n"
                '  - "DOMAIN,apply.miracleplus.com,DIRECT"\n',
                encoding="utf-8",
            )
            (logs / "service_latest.log").write_text(
                '[TCP] 127.0.0.1:1(Chrome) --> apply-cdn.miracleplus.com:443 '
                'match Match using PROXY\n'
                '[TCP] 127.0.0.1:2(Chrome) --> miracleplus.datasink.sensorsdata.cn:443 '
                'match DomainSuffix(cn) using DIRECT\n',
                encoding="utf-8",
            )

            def fake_api(_socket, path, method="GET", body=None):
                if path == "/connections":
                    return {"connections": []}
                if path == "/rules":
                    return {
                        "rules": [
                            {
                                "type": "Domain",
                                "payload": "apply.miracleplus.com",
                                "proxy": "DIRECT",
                            }
                        ]
                    }
                return {}

            with mock.patch.object(doctor, "api_json", side_effect=fake_api):
                result = doctor.discover_direct_list(
                    data_dir,
                    data_dir / "mihomo.sock",
                    "miracleplus",
                    explicit_hosts=["apply.miracleplus.com"],
                )

        self.assertEqual(
            result["rules"],
            [
                "DOMAIN,apply-cdn.miracleplus.com,DIRECT",
                "DOMAIN,apply.miracleplus.com,DIRECT",
            ],
        )
        self.assertEqual(
            result["missing_rules"],
            ["DOMAIN,apply-cdn.miracleplus.com,DIRECT"],
        )
        self.assertEqual(
            result["ignored_direct_hosts"],
            ["miracleplus.datasink.sensorsdata.cn"],
        )

    def test_merge_generated_rules_is_idempotent(self):
        original = (
            "mixed-port: 7897\n"
            "rules:\n"
            "- DOMAIN,apply.miracleplus.com,DIRECT\n"
            "- MATCH,PROXY\n"
        )

        updated = doctor.merge_generated_rules(
            original,
            [
                "DOMAIN,apply.miracleplus.com,DIRECT",
                "DOMAIN,apply-cdn.miracleplus.com,DIRECT",
            ],
        )
        updated_again = doctor.merge_generated_rules(
            updated,
            ["DOMAIN,apply-cdn.miracleplus.com,DIRECT"],
        )

        self.assertEqual(updated, updated_again)
        self.assertEqual(updated.count("DOMAIN,apply-cdn.miracleplus.com,DIRECT"), 1)
        self.assertLess(
            updated.index("DOMAIN,apply-cdn.miracleplus.com,DIRECT"),
            updated.index("MATCH,PROXY"),
        )


if __name__ == "__main__":
    unittest.main()
