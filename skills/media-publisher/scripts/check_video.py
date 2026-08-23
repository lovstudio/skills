#!/usr/bin/env python3
"""Read-only ffprobe preflight for videos uploaded to WeChat Channels or Bilibili.

平台的硬限制差一个数量级，用错一边就会得到假结论：一条 491 MB / 18m45s 的片子
在视频号接近上限，在 B 站是小件。所以文件大小、时长和最短时长都按 `--platform` 取。

    python3 check_video.py 片子.mp4 --platform wechat-channels --json
    python3 check_video.py 片子.mp4 --platform bilibili --json

`--max-gb` / `--max-hours` 仍可覆盖，用于页面显示了灰度放宽时（视频号 20 GiB / 8 小时）。
建议项（编码、分辨率、码率、帧率、音频）两个平台共用，都只报 warning。
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


GIB = 1024 ** 3
DEFAULT_MAX_GB = 4.0
DEFAULT_MAX_HOURS = 2.0
MIN_DURATION_SECONDS = 3.0
MIN_ASPECT_RATIO = 1.0 / 3.0
MAX_ASPECT_RATIO = 3.0
RECOMMENDED_MIN_SHORT_SIDE = 720
RECOMMENDED_MAX_VIDEO_BITRATE = 10_000_000
RECOMMENDED_MAX_FPS = 60.0
RECOMMENDED_MIN_AUDIO_BITRATE = 128_000
RECOMMENDED_MIN_AUDIO_SAMPLE_RATE = 48_000

# 每个平台的硬限制。`max_gb` 的单位是 GiB。
PLATFORMS: Dict[str, Dict[str, Any]] = {
    "wechat-channels": {
        "label": "微信视频号",
        "max_gb": DEFAULT_MAX_GB,
        "max_hours": DEFAULT_MAX_HOURS,
        "min_duration_seconds": MIN_DURATION_SECONDS,
        # 官方前端 chunk-common 常量；enablePost20gVideo 开启时为 20 GiB / 8 小时，
        # 只有页面明确显示放宽文案时才用 --max-gb 20 --max-hours 8 覆盖。
        "source": "视频号助手官方前端常量（2026-08-11 读取）",
    },
    "bilibili": {
        "label": "Bilibili",
        # 上传页原文「视频大小16G以内」未写单位。按十进制 16 GB = 14.90 GiB 取，
        # 宁可早一步拦下，也不要传到 99% 才被服务端拒。
        "max_gb": 14.9,
        "max_hours": 10.0,
        # B 站未在页面上给出最短时长，这里取 1 秒作为「不是空文件」的下限，未实测。
        "min_duration_seconds": 1.0,
        "source": "投稿页原文「视频大小16G以内，时长10小时以内」（2026-08-18 读取）",
    },
}

DEFAULT_PLATFORM = "wechat-channels"


class ProbeError(RuntimeError):
    """Raised when ffprobe cannot produce usable JSON."""


def _number(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _positive_number(value: str) -> float:
    number = _number(value)
    if number is None or number <= 0:
        raise argparse.ArgumentTypeError("必须是大于 0 的数字")
    return number


def _fraction(value: Any) -> Optional[float]:
    if isinstance(value, str) and "/" in value:
        numerator, denominator = value.split("/", 1)
        top = _number(numerator)
        bottom = _number(denominator)
        if top is None or bottom in (None, 0):
            return None
        return top / bottom
    return _number(value)


def _first_stream(probe: Dict[str, Any], codec_type: str) -> Optional[Dict[str, Any]]:
    streams = probe.get("streams")
    if not isinstance(streams, list):
        return None
    return next(
        (
            stream
            for stream in streams
            if isinstance(stream, dict) and stream.get("codec_type") == codec_type
        ),
        None,
    )


def _issue(code: str, message: str) -> Dict[str, str]:
    return {"code": code, "message": message}


def run_ffprobe(path: Path, ffprobe: str = "ffprobe") -> Dict[str, Any]:
    """Run ffprobe without writing to the media file."""

    command = [
        ffprobe,
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-of",
        "json",
        str(path),
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError as exc:
        raise ProbeError(f"未找到 ffprobe：{ffprobe}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ProbeError("ffprobe 在 60 秒内未完成") from exc

    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"退出码 {completed.returncode}"
        raise ProbeError(f"ffprobe 解析失败：{detail}")
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ProbeError("ffprobe 返回了无效 JSON") from exc
    if not isinstance(data, dict):
        raise ProbeError("ffprobe JSON 顶层结构不是对象")
    return data


def validate_probe(
    path: Path,
    probe: Dict[str, Any],
    *,
    size_bytes: int,
    platform: str = DEFAULT_PLATFORM,
    max_gb: Optional[float] = None,
    max_hours: Optional[float] = None,
) -> Dict[str, Any]:
    """Validate supplied ffprobe data; useful for deterministic fixture tests."""

    spec = PLATFORMS[platform]
    if max_gb is None:
        max_gb = spec["max_gb"]
    if max_hours is None:
        max_hours = spec["max_hours"]
    min_duration = spec["min_duration_seconds"]

    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []
    max_bytes = int(max_gb * GIB)
    max_duration = max_hours * 3600.0

    if size_bytes <= 0:
        errors.append(_issue("empty_file", "视频文件为空"))
    elif size_bytes > max_bytes:
        errors.append(
            _issue("file_too_large", f"文件超过 {max_gb:g} GiB 硬限制（{spec['label']}）")
        )

    format_info = probe.get("format") if isinstance(probe.get("format"), dict) else {}
    video = _first_stream(probe, "video")
    audio = _first_stream(probe, "audio")

    duration = _number(format_info.get("duration"))
    if duration is None and video is not None:
        duration = _number(video.get("duration"))
    if duration is None:
        errors.append(_issue("duration_unknown", "未读取到视频时长"))
    elif duration < min_duration:
        errors.append(
            _issue("duration_too_short", f"视频时长必须至少为 {min_duration:g} 秒（{spec['label']}）")
        )
    elif duration > max_duration:
        errors.append(
            _issue("duration_too_long", f"视频时长超过 {max_hours:g} 小时硬限制（{spec['label']}）")
        )

    width: Optional[int] = None
    height: Optional[int] = None
    aspect_ratio: Optional[float] = None
    video_codec: Optional[str] = None
    video_bitrate: Optional[int] = None
    fps: Optional[float] = None

    if video is None:
        errors.append(_issue("video_stream_missing", "未检测到视频流"))
    else:
        width_number = _number(video.get("width"))
        height_number = _number(video.get("height"))
        if width_number is None or height_number is None or width_number <= 0 or height_number <= 0:
            errors.append(_issue("dimensions_unknown", "未读取到有效视频宽高"))
        else:
            width = int(width_number)
            height = int(height_number)
            aspect_ratio = width / height
            if not MIN_ASPECT_RATIO <= aspect_ratio <= MAX_ASPECT_RATIO:
                errors.append(
                    _issue("aspect_ratio_out_of_range", "视频宽高比必须在 1:3 至 3:1 之间")
                )
            if min(width, height) < RECOMMENDED_MIN_SHORT_SIDE:
                warnings.append(
                    _issue("resolution_below_720p", "建议视频短边至少为 720 像素")
                )

        video_codec = str(video.get("codec_name") or "").lower() or None
        if video_codec != "h264":
            warnings.append(_issue("video_codec_not_h264", "建议使用 H.264 视频编码"))

        bitrate_number = _number(video.get("bit_rate"))
        if bitrate_number is None:
            warnings.append(_issue("video_bitrate_unknown", "未读取到视频码率，请确认不超过 10 Mbps"))
        else:
            video_bitrate = int(bitrate_number)
            if video_bitrate > RECOMMENDED_MAX_VIDEO_BITRATE:
                warnings.append(_issue("video_bitrate_high", "建议视频码率不超过 10 Mbps"))

        fps = _fraction(video.get("avg_frame_rate"))
        if fps in (None, 0):
            fps = _fraction(video.get("r_frame_rate"))
        if fps in (None, 0):
            warnings.append(_issue("frame_rate_unknown", "未读取到帧率，请确认不超过 60 fps"))
            fps = None
        elif fps > RECOMMENDED_MAX_FPS:
            warnings.append(_issue("frame_rate_high", "建议帧率不超过 60 fps"))

    format_name = str(format_info.get("format_name") or "").lower()
    if path.suffix.lower() != ".mp4" or "mp4" not in format_name.split(","):
        warnings.append(_issue("container_not_mp4", "建议使用 MP4 容器"))

    audio_codec: Optional[str] = None
    audio_bitrate: Optional[int] = None
    audio_sample_rate: Optional[int] = None
    if audio is not None:
        audio_codec = str(audio.get("codec_name") or "").lower() or None
        if audio_codec != "aac":
            warnings.append(_issue("audio_codec_not_aac", "存在音轨时建议使用 AAC 编码"))

        audio_bitrate_number = _number(audio.get("bit_rate"))
        if audio_bitrate_number is None:
            warnings.append(_issue("audio_bitrate_unknown", "未读取到音频码率，请确认至少为 128 kbps"))
        else:
            audio_bitrate = int(audio_bitrate_number)
            if audio_bitrate < RECOMMENDED_MIN_AUDIO_BITRATE:
                warnings.append(_issue("audio_bitrate_low", "建议音频码率至少为 128 kbps"))

        sample_rate_number = _number(audio.get("sample_rate"))
        if sample_rate_number is None:
            warnings.append(_issue("audio_sample_rate_unknown", "未读取到采样率，请确认至少为 48 kHz"))
        else:
            audio_sample_rate = int(sample_rate_number)
            if audio_sample_rate < RECOMMENDED_MIN_AUDIO_SAMPLE_RATE:
                warnings.append(_issue("audio_sample_rate_low", "建议音频采样率至少为 48 kHz"))

    media = {
        "size_bytes": size_bytes,
        "duration_seconds": round(duration, 3) if duration is not None else None,
        "width": width,
        "height": height,
        "aspect_ratio": round(aspect_ratio, 4) if aspect_ratio is not None else None,
        "container": format_name or None,
        "video_codec": video_codec,
        "video_bitrate_bps": video_bitrate,
        "fps": round(fps, 3) if fps is not None else None,
        "audio_codec": audio_codec,
        "audio_bitrate_bps": audio_bitrate,
        "audio_sample_rate_hz": audio_sample_rate,
    }
    return {
        "valid": not errors,
        "status": "pass" if not errors else "fail",
        "path": str(path),
        "read_only": True,
        "platform": platform,
        "platform_label": spec["label"],
        "limits": {
            "max_gb": max_gb,
            "max_bytes": max_bytes,
            "min_duration_seconds": min_duration,
            "max_hours": max_hours,
            "max_duration_seconds": max_duration,
            "min_aspect_ratio": MIN_ASPECT_RATIO,
            "max_aspect_ratio": MAX_ASPECT_RATIO,
            "source": spec["source"],
        },
        "media": media,
        "errors": errors,
        "warnings": warnings,
    }


def _failure_result(
    path: Path,
    message: str,
    *,
    platform: str,
    max_gb: Optional[float],
    max_hours: Optional[float],
) -> Dict[str, Any]:
    spec = PLATFORMS[platform]
    if max_gb is None:
        max_gb = spec["max_gb"]
    if max_hours is None:
        max_hours = spec["max_hours"]
    return {
        "valid": False,
        "status": "fail",
        "path": str(path),
        "read_only": True,
        "platform": platform,
        "platform_label": spec["label"],
        "limits": {
            "max_gb": max_gb,
            "max_bytes": int(max_gb * GIB),
            "min_duration_seconds": spec["min_duration_seconds"],
            "max_hours": max_hours,
            "max_duration_seconds": max_hours * 3600.0,
            "min_aspect_ratio": MIN_ASPECT_RATIO,
            "max_aspect_ratio": MAX_ASPECT_RATIO,
            "source": spec["source"],
        },
        "media": {},
        "errors": [_issue("probe_failed", message)],
        "warnings": [],
    }


def check_video(
    path: Path,
    *,
    platform: str = DEFAULT_PLATFORM,
    max_gb: Optional[float] = None,
    max_hours: Optional[float] = None,
    ffprobe: str = "ffprobe",
) -> Dict[str, Any]:
    def fail(msg: str) -> Dict[str, Any]:
        return _failure_result(
            path, msg, platform=platform, max_gb=max_gb, max_hours=max_hours
        )

    if not path.exists():
        return fail("视频文件不存在")
    if not path.is_file():
        return fail("输入路径不是文件")
    try:
        size_bytes = path.stat().st_size
        probe = run_ffprobe(path, ffprobe=ffprobe)
    except (OSError, ProbeError) as exc:
        return fail(str(exc))
    return validate_probe(
        path,
        probe,
        size_bytes=size_bytes,
        platform=platform,
        max_gb=max_gb,
        max_hours=max_hours,
    )


def _human_size(size_bytes: Optional[int]) -> str:
    if size_bytes is None:
        return "未知"
    value = float(size_bytes)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} GiB"


def format_human(result: Dict[str, Any]) -> str:
    media = result.get("media", {})
    dimensions = "未知"
    if media.get("width") and media.get("height"):
        dimensions = f"{media['width']}x{media['height']}"
    limits = result.get("limits", {})
    lines = [
        f"视频发布预检（{result.get('platform_label', '?')}）："
        f"{'通过' if result['valid'] else '未通过'}",
        f"文件：{result['path']}",
        (
            f"限制：≤ {limits.get('max_gb')} GiB / ≤ {limits.get('max_hours')} 小时"
            f"（{limits.get('source', '')}）"
        ),
        (
            "检测："
            f"{_human_size(media.get('size_bytes'))}；"
            f"{media.get('duration_seconds', '未知')} 秒；"
            f"{dimensions}；"
            f"视频 {media.get('video_codec') or '未知'}；"
            f"音频 {media.get('audio_codec') or '无/未知'}"
        ),
    ]
    if result["errors"]:
        lines.append("硬错误：")
        lines.extend(f"- [{item['code']}] {item['message']}" for item in result["errors"])
    if result["warnings"]:
        lines.append("建议警告：")
        lines.extend(f"- [{item['code']}] {item['message']}" for item in result["warnings"])
    lines.append("只读检查：未写入、转码或替换源视频。")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="只读检查待发布视频（视频号 / B 站）")
    parser.add_argument("video", type=Path, help="本地视频文件")
    parser.add_argument(
        "--platform",
        choices=sorted(PLATFORMS),
        default=DEFAULT_PLATFORM,
        help=f"目标平台，决定大小/时长硬限制（默认 {DEFAULT_PLATFORM}）",
    )
    parser.add_argument(
        "--max-gb",
        type=_positive_number,
        default=None,
        help="覆盖文件上限（GiB）。页面显示灰度放宽时才用",
    )
    parser.add_argument(
        "--max-hours",
        type=_positive_number,
        default=None,
        help="覆盖时长上限（小时）。页面显示灰度放宽时才用",
    )
    parser.add_argument("--ffprobe", default="ffprobe", help="ffprobe 可执行文件")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    result = check_video(
        args.video,
        platform=args.platform,
        max_gb=args.max_gb,
        max_hours=args.max_hours,
        ffprobe=args.ffprobe,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_human(result))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
