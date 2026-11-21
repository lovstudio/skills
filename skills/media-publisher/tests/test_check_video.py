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

    def test_wechat_channels_warns_on_high_bitrate(self):
        probe = valid_probe()
        probe["streams"][0]["bit_rate"] = "20000000"

        result = check_video.validate_probe(
            Path("master.mp4"),
            probe,
            size_bytes=500 * 1024 ** 2,
            platform="wechat-channels",
        )

        self.assertEqual(
            {item["code"] for item in result["warnings"]},
            {"video_bitrate_high"},
        )
        self.assertEqual(result["notes"], [])

    def test_bilibili_has_no_bitrate_cap(self):
        # 2026-09-27 实际母版：20 Mbps、2.08 GB、13:47，曾因误报被重压到 9 Mbps。
        probe = valid_probe()
        probe["format"]["duration"] = "827.0"
        probe["streams"][0]["bit_rate"] = "20000000"

        result = check_video.validate_probe(
            Path("master.mp4"),
            probe,
            size_bytes=2_080_000_000,
            platform="bilibili",
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["warnings"], [])
        self.assertEqual(
            {item["code"] for item in result["notes"]},
            {"video_bitrate_no_platform_cap"},
        )
        self.assertEqual(result["media"]["video_bitrate_bps"], 20_000_000)

    def test_bilibili_unknown_bitrate_is_not_a_warning(self):
        probe = valid_probe()
        del probe["streams"][0]["bit_rate"]

        result = check_video.validate_probe(
            Path("master.mp4"),
            probe,
            size_bytes=500 * 1024 ** 2,
            platform="bilibili",
        )

        self.assertEqual(result["warnings"], [])
        self.assertIsNone(result["media"]["video_bitrate_bps"])

    def test_bilibili_accepts_mov_and_mkv(self):
        cases = {
            "master.mov": "mov,mp4,m4a,3gp,3g2,mj2",
            "master.mkv": "matroska,webm",
        }
        for filename, format_name in cases.items():
            with self.subTest(filename=filename):
                probe = valid_probe()
                probe["format"]["format_name"] = format_name

                result = check_video.validate_probe(
                    Path(filename),
                    probe,
                    size_bytes=500 * 1024 ** 2,
                    platform="bilibili",
                )

                self.assertEqual(result["warnings"], [])

    def test_container_recommendation_is_platform_specific(self):
        probe = valid_probe()
        probe["format"]["format_name"] = "matroska,webm"

        wechat = check_video.validate_probe(
            Path("master.mkv"),
            probe,
            size_bytes=500 * 1024 ** 2,
            platform="wechat-channels",
        )
        bilibili = check_video.validate_probe(
            Path("master.webm"),
            probe,
            size_bytes=500 * 1024 ** 2,
            platform="bilibili",
        )

        self.assertEqual(
            {item["code"] for item in wechat["warnings"]},
            {"container_not_mp4"},
        )
        self.assertEqual(
            {item["code"] for item in bilibili["warnings"]},
            {"container_not_recommended"},
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


class XiaohongshuTests(unittest.TestCase):
    def test_limits_follow_upload_page(self):
        # 「最大20GB」按十进制 GB 取，与 B 站「16G」同口径：18.6 GiB < 20e9 字节。
        limits = check_video.PLATFORMS["xiaohongshu"]
        self.assertEqual(limits["max_hours"], 4.0)
        self.assertLess(limits["max_gb"] * 1024 ** 3, 20_000_000_000)
        self.assertGreater(limits["max_gb"], 18.5)

    def test_accepts_three_hour_1080p_mp4(self):
        probe = valid_probe()
        probe["format"]["duration"] = str(3 * 3600)

        result = check_video.validate_probe(
            Path("ep02-xiaohongshu-v1.mp4"),
            probe,
            size_bytes=12 * 1024 ** 3,
            platform="xiaohongshu",
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["warnings"], [])
        self.assertEqual(result["platform_label"], "小红书")

    def test_rejects_five_hour_file_and_decimal_20gb(self):
        probe = valid_probe()
        probe["format"]["duration"] = str(5 * 3600)

        result = check_video.validate_probe(
            Path("long.mp4"),
            probe,
            size_bytes=20_000_000_000,
            platform="xiaohongshu",
        )

        self.assertFalse(result["valid"])
        self.assertEqual(
            {item["code"] for item in result["errors"]},
            {"duration_too_long", "file_too_large"},
        )

    def test_accepts_mov_and_warns_on_mkv(self):
        mov_probe = valid_probe()
        mkv_probe = valid_probe()
        mkv_probe["format"]["format_name"] = "matroska,webm"

        mov = check_video.validate_probe(
            Path("master.mov"),
            mov_probe,
            size_bytes=500 * 1024 ** 2,
            platform="xiaohongshu",
        )
        mkv = check_video.validate_probe(
            Path("master.mkv"),
            mkv_probe,
            size_bytes=500 * 1024 ** 2,
            platform="xiaohongshu",
        )

        self.assertEqual(mov["warnings"], [])
        self.assertEqual(
            {item["code"] for item in mkv["warnings"]},
            {"container_not_recommended"},
        )
        self.assertIn("MP4 / MOV", mkv["warnings"][0]["message"])

    def test_has_no_bitrate_cap(self):
        probe = valid_probe()
        probe["streams"][0]["bit_rate"] = "30000000"

        result = check_video.validate_probe(
            Path("master.mp4"),
            probe,
            size_bytes=2 * 1024 ** 3,
            platform="xiaohongshu",
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["warnings"], [])
        self.assertEqual(
            {item["code"] for item in result["notes"]},
            {"video_bitrate_no_platform_cap"},
        )
        self.assertIn("小红书", result["notes"][0]["message"])

    def test_rejects_xiaohongshu_file_for_bilibili(self):
        result = check_video.validate_probe(
            Path("ep02-xiaohongshu.mp4"),
            valid_probe(),
            size_bytes=100 * 1024 ** 2,
            platform="bilibili",
        )

        self.assertFalse(result["valid"])
        self.assertEqual(
            {item["code"] for item in result["errors"]},
            {"cross_platform_filename"},
        )
        self.assertEqual(result["asset_selection"]["foreign_platform_token"], "xiaohongshu")

    def test_short_tokens_match_only_on_letter_boundaries(self):
        flagged = ("ep02-xhs-v1.mp4", "宣传片竖版xhs.mp4", "ep02-REDnote.mp4", "ep02xhs1080p.mp4")
        clean = ("colorednotes-bilibili.mp4", "boxhs-bilibili.mp4", "storednote_bilibili.mp4")
        for filename in flagged:
            with self.subTest(filename=filename):
                result = check_video.validate_probe(
                    Path(filename),
                    valid_probe(),
                    size_bytes=100 * 1024 ** 2,
                    platform="wechat-channels",
                )
                self.assertIn(
                    "cross_platform_filename",
                    {item["code"] for item in result["errors"]},
                )
        for filename in clean:
            with self.subTest(filename=filename):
                result = check_video.validate_probe(
                    Path(filename),
                    valid_probe(),
                    size_bytes=100 * 1024 ** 2,
                    platform="bilibili",
                )
                self.assertTrue(result["valid"])
                self.assertIsNone(result["asset_selection"]["foreign_platform_token"])

    def test_chinese_xiaohongshu_name_is_foreign_to_bilibili(self):
        result = check_video.validate_probe(
            Path("ep02-小红书-竖版.mp4"),
            valid_probe(),
            size_bytes=100 * 1024 ** 2,
            platform="bilibili",
        )

        self.assertFalse(result["valid"])
        self.assertEqual(
            {item["code"] for item in result["errors"]},
            {"cross_platform_filename"},
        )
        self.assertEqual(result["asset_selection"]["foreign_platform_token"], "小红书")

    def test_bilibili_and_wechat_files_are_foreign_to_xiaohongshu(self):
        for filename in ("ep02-bilibili-v2.1.mp4", "ep02-wechat-channels-v2.1.mp4"):
            with self.subTest(filename=filename):
                result = check_video.validate_probe(
                    Path(filename),
                    valid_probe(),
                    size_bytes=100 * 1024 ** 2,
                    platform="xiaohongshu",
                )
                self.assertEqual(
                    {item["code"] for item in result["errors"]},
                    {"cross_platform_filename"},
                )


def foreign_token(filename: str, platform: str):
    result = check_video.validate_probe(
        Path(filename),
        valid_probe(),
        size_bytes=100 * 1024 ** 2,
        platform=platform,
    )
    flagged = "cross_platform_filename" in {item["code"] for item in result["errors"]}
    token = result["asset_selection"]["foreign_platform_token"]
    # 报出的标识和是否拦下必须一致，不能出现「报了标识却放行」。
    assert flagged == (token is not None), (filename, platform, result["errors"])
    return token


class FilenameTokenTests(unittest.TestCase):
    def test_long_tokens_match_as_substrings(self):
        # 字母边界只给短标识用；长标识加边界会放过这些紧贴字母的命名。
        cases = {
            "ep02-bilibiliHD.mp4": "bilibili",
            "EP02BilibiliFinal.mp4": "bilibili",
            "bilibiliv2.mp4": "bilibili",
            "mybilibili.mp4": "bilibili",
            "ep02-wechat-channelsv2.mp4": "wechat-channels",
            "ep02wechat_channelsFinal.mp4": "wechat_channels",
            "ep02-xiaohongshuHD.mp4": "xiaohongshu",
        }
        for filename, token in cases.items():
            own = next(
                name
                for name, tokens in check_video.PLATFORM_FILENAME_TOKENS.items()
                if any(candidate == token for candidate, _ in tokens)
            )
            for platform in check_video.PLATFORMS:
                if platform == own:
                    continue
                with self.subTest(filename=filename, platform=platform):
                    self.assertEqual(foreign_token(filename, platform), token)

    def test_ordinary_words_are_not_short_tokens(self):
        for filename in ("colorednotes.mp4", "boxhs.mp4", "web站点素材.mp4"):
            for platform in check_video.PLATFORMS:
                with self.subTest(filename=filename, platform=platform):
                    self.assertIsNone(foreign_token(filename, platform))

    def test_chinese_tokens_are_foreign_to_other_platforms(self):
        cases = {
            ("ep02-小红书-竖版.mp4", "bilibili"): "小红书",
            ("ep02-小红书-竖版.mp4", "wechat-channels"): "小红书",
            ("ep02-B站-横版.mp4", "xiaohongshu"): "b站",
            ("ep02B站final.mp4", "wechat-channels"): "b站",
            ("ep02-哔哩哔哩.mp4", "xiaohongshu"): "哔哩哔哩",
            ("ep02-视频号-竖版.mp4", "bilibili"): "视频号",
            ("ep02视频号.mp4", "xiaohongshu"): "视频号",
        }
        for (filename, platform), token in cases.items():
            with self.subTest(filename=filename, platform=platform):
                self.assertEqual(foreign_token(filename, platform), token)

    def test_own_platform_tokens_never_flag_themselves(self):
        for platform, tokens in check_video.PLATFORM_FILENAME_TOKENS.items():
            for token, _ in tokens:
                for filename in (
                    f"ep02-{token}-v1.mp4",
                    f"ep02-{token.upper()}-v1.mp4",
                    f"ep02{token}final.mp4",
                ):
                    with self.subTest(filename=filename, platform=platform):
                        self.assertIsNone(foreign_token(filename, platform))

    def test_own_token_does_not_hide_a_foreign_one(self):
        # 带着自己平台名的文件，只要还写着别家的名字，就不能被静默放行。
        cases = {
            ("ep02-bilibili-视频号版.mp4", "bilibili"): "视频号",
            ("ep02-B站-小红书版.mp4", "bilibili"): "小红书",
            ("ep02-xhs-bilibili.mp4", "xiaohongshu"): "bilibili",
            ("ep02-视频号-xhs.mp4", "wechat-channels"): "xhs",
        }
        for (filename, platform), token in cases.items():
            with self.subTest(filename=filename, platform=platform):
                self.assertEqual(foreign_token(filename, platform), token)


def douyin_probe(width=1080, height=1920, duration="54.246", fps="30/1"):
    probe = valid_probe()
    probe["format"]["duration"] = duration
    probe["streams"][0].update(width=width, height=height, avg_frame_rate=fps)
    return probe


def douyin(path="fourier-v0.3.mp4", probe=None, size=32 * 1024 ** 2, **kwargs):
    return check_video.validate_probe(
        Path(path), probe or douyin_probe(), size_bytes=size, platform="douyin", **kwargs
    )


def issue_codes(items):
    return {item["code"] for item in items}


class DouyinTests(unittest.TestCase):
    def test_limits_follow_upload_page(self):
        # 「视频时长 1 小时以内，文件大小 16G 以内」，16G 与 B 站同口径按十进制 GB 取。
        limits = check_video.PLATFORMS["douyin"]
        self.assertEqual(limits["max_hours"], 1.0)
        self.assertLess(limits["max_gb"] * 1024 ** 3, 16_000_000_000)
        self.assertGreater(limits["max_gb"], 14.8)

    def test_vertical_over_40_seconds_warns_but_passes(self):
        # 上传页原文「超过40秒的视频建议上传横版视频」只是建议，不阻断已批准的竖版。
        result = douyin(expected_orientation="vertical")

        self.assertTrue(result["valid"])
        self.assertEqual(issue_codes(result["warnings"]), {"long_vertical_video"})
        self.assertIn("超过40秒的视频建议上传横版视频", result["warnings"][0]["message"])
        self.assertEqual(issue_codes(result["notes"]), {"video_bitrate_no_platform_cap"})
        self.assertEqual(result["platform_label"], "抖音")

    def test_short_vertical_and_long_horizontal_do_not_warn(self):
        for probe in (douyin_probe(duration="40.0"), douyin_probe(1920, 1080, "600")):
            with self.subTest(probe=probe["streams"][0]["width"]):
                self.assertEqual(douyin(probe=probe)["warnings"], [])

    def test_rejects_over_one_hour_and_decimal_16gb(self):
        result = douyin(probe=douyin_probe(1920, 1080, "3601"), size=16_000_000_000)

        self.assertFalse(result["valid"])
        self.assertEqual(
            issue_codes(result["errors"]), {"duration_too_long", "file_too_large"}
        )

    def test_fan_relaxation_is_an_override(self):
        # 粉丝过万「3 小时以内、64G 以内」：按页面原文覆盖后两小时片可以过。
        result = douyin(probe=douyin_probe(1920, 1080, str(2 * 3600)), max_gb=59.6, max_hours=3)

        self.assertTrue(result["valid"])

    def test_accepts_hevc_and_webm_but_warns_on_mov(self):
        hevc = douyin_probe(1920, 1080, "60")
        hevc["streams"][0]["codec_name"] = "hevc"
        webm = douyin_probe(1920, 1080, "60")
        webm["format"]["format_name"] = "matroska,webm"
        vp9 = douyin_probe(1920, 1080, "60")
        vp9["streams"][0]["codec_name"] = "vp9"

        self.assertEqual(douyin(probe=hevc)["warnings"], [])
        self.assertEqual(douyin("master.webm", probe=webm)["warnings"], [])
        mov = douyin("master.mov", probe=douyin_probe(1920, 1080, "60"))
        self.assertEqual(issue_codes(mov["warnings"]), {"container_not_recommended"})
        self.assertIn("MP4 / WEBM", mov["warnings"][0]["message"])
        self.assertEqual(
            issue_codes(douyin(probe=vp9)["warnings"]), {"video_codec_not_supported"}
        )

    def test_aspect_ratio_outside_recommended_list_warns(self):
        square = douyin(probe=douyin_probe(1080, 1080, "30"))
        tall = douyin(probe=douyin_probe(1080, 2340, "30"))  # 9:19.5

        self.assertEqual(issue_codes(square["warnings"]), {"aspect_ratio_not_recommended"})
        self.assertEqual(tall["warnings"], [])

    def test_frame_rate_above_resolution_tier_warns(self):
        # 「视频画质」表：1080p 及以下最高 30 帧，2k / 4k 最高 60 帧。
        fhd60 = douyin(probe=douyin_probe(1080, 1920, "30", fps="60/1"))
        uhd60 = douyin(probe=douyin_probe(2160, 3840, "30", fps="60/1"))

        self.assertEqual(issue_codes(fhd60["warnings"]), {"frame_rate_above_playback_tier"})
        self.assertEqual(uhd60["warnings"], [])

    def test_other_platforms_keep_their_own_rules(self):
        # 抖音的三条建议不能漏到别的平台：同一条 54 秒 60 帧竖版在小红书上不报这些。
        probe = douyin_probe(1080, 1920, fps="60/1")
        result = check_video.validate_probe(
            Path("fourier.mp4"), probe, size_bytes=32 * 1024 ** 2, platform="xiaohongshu"
        )

        self.assertEqual(result["warnings"], [])

    def test_douyin_files_are_foreign_to_other_platforms(self):
        self.assertEqual(foreign_token("ep02-抖音-竖版.mp4", "bilibili"), "抖音")
        self.assertEqual(foreign_token("ep02-douyin.mp4", "xiaohongshu"), "douyin")
        self.assertEqual(foreign_token("ep02-视频号.mp4", "douyin"), "视频号")


if __name__ == "__main__":
    unittest.main()
