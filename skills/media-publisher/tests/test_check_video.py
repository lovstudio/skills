from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "check_video.py"
SPEC = importlib.util.spec_from_file_location("check_video", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
check_video = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_video)


def valid_probe():
    return {
        "format": {
            "duration": "60.000",
            "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
        },
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "bit_rate": "8000000",
                "avg_frame_rate": "30000/1001",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "bit_rate": "128000",
                "sample_rate": "48000",
            },
        ],
    }


class ValidateProbeTests(unittest.TestCase):
    def test_qualified_video_has_no_issues(self):
        result = check_video.validate_probe(
            Path("qualified.mp4"),
            valid_probe(),
            size_bytes=500 * 1024 ** 2,
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["warnings"], [])
        self.assertTrue(result["read_only"])

    def test_hard_limit_errors_are_non_valid(self):
        probe = valid_probe()
        probe["format"]["duration"] = "2.5"
        probe["streams"][0]["width"] = 4000
        probe["streams"][0]["height"] = 1000

        result = check_video.validate_probe(
            Path("blocked.mp4"),
            probe,
            size_bytes=5 * 1024 ** 3,
        )

        self.assertFalse(result["valid"])
        self.assertEqual(
            {item["code"] for item in result["errors"]},
            {"file_too_large", "duration_too_short", "aspect_ratio_out_of_range"},
        )

    def test_recommendations_are_warnings_only(self):
        probe = valid_probe()
        video = probe["streams"][0]
        video.update(
            {
                "codec_name": "hevc",
                "width": 1280,
                "height": 600,
                "bit_rate": "12000000",
                "avg_frame_rate": "120/1",
            }
        )
        audio = probe["streams"][1]
        audio.update(
            {
                "codec_name": "mp3",
                "bit_rate": "96000",
                "sample_rate": "44100",
            }
        )

        result = check_video.validate_probe(
            Path("warning.mov"),
            probe,
            size_bytes=100 * 1024 ** 2,
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(
            {item["code"] for item in result["warnings"]},
            {
                "resolution_below_720p",
                "video_codec_not_h264",
                "video_bitrate_high",
                "frame_rate_high",
                "container_not_mp4",
                "audio_codec_not_aac",
                "audio_bitrate_low",
                "audio_sample_rate_low",
            },
        )

    def test_live_page_limit_overrides(self):
        probe = copy.deepcopy(valid_probe())
        probe["format"]["duration"] = str(3 * 3600)
        size = 10 * 1024 ** 3

        default_result = check_video.validate_probe(
            Path("extended.mp4"), probe, size_bytes=size
        )
        override_result = check_video.validate_probe(
            Path("extended.mp4"),
            probe,
            size_bytes=size,
            max_gb=20,
            max_hours=8,
        )

        self.assertFalse(default_result["valid"])
        self.assertEqual(
            {item["code"] for item in default_result["errors"]},
            {"file_too_large", "duration_too_long"},
        )
        self.assertTrue(override_result["valid"])

    def test_rejects_file_named_for_another_platform(self):
        result = check_video.validate_probe(
            Path("ep02-wechat-channels-v2.1.mp4"),
            valid_probe(),
            size_bytes=100 * 1024 ** 2,
            platform="bilibili",
        )

        self.assertFalse(result["valid"])
        self.assertEqual(
            {item["code"] for item in result["errors"]},
            {"cross_platform_filename"},
        )

    def test_cross_platform_name_requires_explicit_override(self):
        result = check_video.validate_probe(
            Path("ep02-wechat-channels-v2.1.mp4"),
            valid_probe(),
            size_bytes=100 * 1024 ** 2,
            platform="bilibili",
            allow_cross_platform_name=True,
        )

        self.assertTrue(result["valid"])
        self.assertTrue(result["asset_selection"]["cross_platform_name_override"])

    def test_rejects_orientation_mismatch_from_project_contract(self):
        probe = valid_probe()
        probe["streams"][0]["width"] = 1080
        probe["streams"][0]["height"] = 1920

        result = check_video.validate_probe(
            Path("ep02-bilibili-v2.1.mp4"),
            probe,
            size_bytes=100 * 1024 ** 2,
            platform="bilibili",
            expected_orientation="horizontal",
        )

        self.assertFalse(result["valid"])
        self.assertEqual(result["media"]["orientation"], "vertical")
        self.assertEqual(
            {item["code"] for item in result["errors"]},
            {"orientation_mismatch"},
        )

    def test_accepts_matching_project_orientation(self):
        result = check_video.validate_probe(
            Path("ep02-bilibili-v2.1.mp4"),
            valid_probe(),
            size_bytes=100 * 1024 ** 2,
            platform="bilibili",
            expected_orientation="horizontal",
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["media"]["orientation"], "horizontal")


if __name__ == "__main__":
    unittest.main()
