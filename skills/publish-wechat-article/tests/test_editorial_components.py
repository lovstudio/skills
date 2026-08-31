from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from editorial_components import EditorialComponentError, validate_editorial_components  # noqa: E402


class EditorialComponentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.card = self.root / "card.jpg"
        self.poster = self.root / "poster.jpg"
        self.card.write_bytes(b"card")
        self.poster.write_bytes(b"poster")
        self.profile = self.root / "brand.json"
        self.profile.write_text(
            json.dumps(
                {
                    "blocks": {
                        "endcap": {
                            "enabled": True,
                            "title": "关于手工川",
                            "paragraphs": ["长期品牌介绍。"],
                            "links": [{"url": "https://example.com/about"}],
                            "card": {
                                "enabled": True,
                                "asset": str(self.card),
                                "marker": "个人介绍卡片",
                            },
                        },
                        "campaigns": [
                            {
                                "id": "camp",
                                "enabled": True,
                                "status": "open",
                                "capacity_state": "available",
                                "ends_at": "2026-09-06T18:00:00+08:00",
                                "title": "活动招募",
                                "required_text": ["https://example.com/signup"],
                                "asset": str(self.poster),
                            }
                        ],
                    }
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_accepts_active_campaign_before_permanent_endcap(self) -> None:
        source = self.root / "article.md"
        content = """## 活动招募

<img src="poster.jpg" aria-label="活动海报">

报名：https://example.com/signup

## 关于手工川

长期品牌介绍。

<img src="card.jpg" aria-label="个人介绍卡片">

个人主页：https://example.com/about
"""
        source.write_text(content, encoding="utf-8")

        evidence = validate_editorial_components(
            source,
            content,
            self.profile,
            now=datetime(2026, 8, 31, tzinfo=timezone.utc),
        )

        self.assertTrue(evidence["publicationComponentsVerified"])
        self.assertEqual([item["id"] for item in evidence["activeCampaigns"]], ["camp"])

    def test_full_campaign_is_not_required(self) -> None:
        profile = json.loads(self.profile.read_text(encoding="utf-8"))
        profile["blocks"]["campaigns"][0]["capacity_state"] = "full"
        self.profile.write_text(json.dumps(profile), encoding="utf-8")
        source = self.root / "article.md"
        content = """## 关于手工川

长期品牌介绍。

<img src="card.jpg" aria-label="个人介绍卡片">

个人主页：https://example.com/about
"""
        source.write_text(content, encoding="utf-8")

        evidence = validate_editorial_components(source, content, self.profile)

        self.assertEqual(evidence["activeCampaigns"], [])

    def test_rejects_missing_personal_card(self) -> None:
        source = self.root / "article.md"
        content = """## 活动招募

<img src="poster.jpg">

https://example.com/signup

## 关于手工川

长期品牌介绍。

https://example.com/about
"""
        source.write_text(content, encoding="utf-8")

        with self.assertRaisesRegex(EditorialComponentError, "个人介绍卡片"):
            validate_editorial_components(
                source,
                content,
                self.profile,
                now=datetime(2026, 8, 31, tzinfo=timezone.utc),
            )


if __name__ == "__main__":
    unittest.main()
