#!/usr/bin/env python3
"""渲染开场静帧之前，先判定它和成片的画幅能不能对上。

这个脚本存在的理由是**开场静帧和封面是两个交付物**，画幅通常不同：视频号封面槽是
3:4（1080x1440，服务主页九宫格与分享卡片），竖版成片是 9:16（1080x1920，服务信息流
全屏播放）。把封面直接 `-loop 1` 喂进去，FFmpeg 会按 scale/pad 的写法悄悄补黑边或
拉伸，成片的第一印象就毁在这里，而且渲染完才看得出来——一次几分钟的重编码换一个
本来能算出来的结论。

所以画幅不一致时默认拒绝，必须由调用方显式选 --allow-crop 或 --allow-pad，把
「裁掉多少」「补多少边」变成一个记录在交付报告里的决定。

`--still` 应该传一张与成片同画幅的开场静帧，不是主页卡片用的 3:4 封面。

只读：不改图、不改视频、不做渲染。输出可直接用的 FFmpeg 片段。

用法：

    python3 check_opening_still.py --still opening-still.png --video final.mp4 --json
    python3 check_opening_still.py --still opening-still.png --canvas 1080x1920 \
        --hold 1.2 --allow-crop --json
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

# 停留时长：低于这个值观众来不及读完标题，等于白留一帧。
MIN_HOLD_SECONDS = 0.6
# 裁切损失超过这个比例时，标题组几乎必然被切到，只报 crop 方案已经不够，要出声。
CROP_LOSS_WARN = 0.12


def _ffprobe(path: Path, extra: list[str]) -> str:
    if not shutil.which("ffprobe"):
        raise RuntimeError("ffprobe 不在 PATH 中；本脚本只依赖 ffprobe，请先安装 FFmpeg")
    cmd = ["ffprobe", "-v", "error", *extra, str(path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe 读取失败：{path}\n{proc.stderr.strip()}")
    return proc.stdout.strip()


def probe_size(path: Path) -> tuple[int, int]:
    out = _ffprobe(path, [
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0:s=x",
    ])
    first = out.splitlines()[0] if out else ""
    try:
        w, h = (int(v) for v in first.split("x")[:2])
    except ValueError as exc:
        raise RuntimeError(f"无法从 ffprobe 输出解析尺寸：{out!r}") from exc
    return w, h


def probe_fps(path: Path) -> float:
    out = _ffprobe(path, [
        "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate",
        "-of", "default=nw=1:nk=1",
    ])
    num, _, den = out.partition("/")
    try:
        return int(num) / int(den or 1)
    except (ValueError, ZeroDivisionError):
        return 30.0


def parse_canvas(text: str) -> tuple[int, int]:
    sep = "x" if "x" in text else ":"
    try:
        w, h = (int(v) for v in text.split(sep)[:2])
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"画幅写法应为 1080x1920，收到 {text!r}") from exc
    if w <= 0 or h <= 0:
        raise argparse.ArgumentTypeError(f"画幅必须为正数，收到 {text!r}")
    return w, h


def plan(still: tuple[int, int], canvas: tuple[int, int]) -> dict:
    """算出把 still 铺满 canvas 的两条路，以及各自的代价。"""
    sw, sh = still
    tw, th = canvas
    if (sw, sh) == (tw, th):
        return {"mode": "match", "loss_ratio": 0.0}

    still_ar, canvas_ar = sw / sh, tw / th

    # crop：居中裁切到目标比例再缩放，绝不补边，代价是裁掉的那部分画面。
    if still_ar > canvas_ar:              # 静帧偏宽，裁两侧
        keep = round(sh * canvas_ar)
        crop = {"w": keep, "h": sh, "x": (sw - keep) // 2, "y": 0}
        loss = 1 - keep / sw
        axis = "左右"
    else:                                  # 静帧偏高，裁上下
        keep = round(sw / canvas_ar)
        crop = {"w": sw, "h": keep, "x": 0, "y": (sh - keep) // 2}
        loss = 1 - keep / sh
        axis = "上下"

    upscale = max(tw / crop["w"], th / crop["h"])
    return {
        "mode": "mismatch",
        "still_aspect": round(still_ar, 4),
        "canvas_aspect": round(canvas_ar, 4),
        "crop": {**crop, "axis": axis, "loss_ratio": round(loss, 4),
                 "upscale": round(upscale, 3)},
        "pad": {"axis": "上下" if still_ar > canvas_ar else "左右"},
        "loss_ratio": round(loss, 4),
    }


def build_filter(canvas: tuple[int, int], detail: dict,
                 allow: str, fps: float) -> str:
    tw, th = canvas
    if detail["mode"] == "match":
        return f"fps={fps:g},setsar=1"
    if allow == "crop":
        c = detail["crop"]
        return (f"crop={c['w']}:{c['h']}:{c['x']}:{c['y']},"
                f"scale={tw}:{th},fps={fps:g},setsar=1")
    return (f"scale={tw}:{th}:force_original_aspect_ratio=decrease,"
            f"pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2:black,fps={fps:g},setsar=1")


def build_command(still: Path, video: Path | None, canvas: tuple[int, int],
                  hold: float, vf: str, fps: float) -> str:
    tw, th = canvas
    target = str(video) if video else "FINAL_MP4"
    # 音频侧先垫一段等长静音，否则 concat 后声画会整体前移 hold 秒。
    # 成片无音轨时删掉 anullsrc/[a] 两行并改成 -an，见 references/cover-and-title.md。
    return (
        "ffmpeg -y -hide_banner \\\n"
        f"  -loop 1 -t {hold:g} -i {still} \\\n"
        f"  -i {target} \\\n"
        f'  -filter_complex "[0:v]{vf}[head];'
        f"[1:v]fps={fps:g},setsar=1[body];"
        f"[head][body]concat=n=2:v=1:a=0[v];"
        f'anullsrc=r=48000:cl=stereo,atrim=0:{hold:g}[sil];'
        f'[sil][1:a]concat=n=2:v=0:a=1[a]" \\\n'
        "  -map \"[v]\" -map \"[a]\" \\\n"
        "  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \\\n"
        "  -c:a aac -b:a 192k -ar 48000 -ac 2 \\\n"
        f"  -movflags +faststart OUT_{tw}x{th}.mp4"
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="判定开场静帧与成片画幅是否匹配，并给出可执行的 FFmpeg 片段")
    p.add_argument("--still", required=True, type=Path,
                   help="开场静帧图片路径（应与成片同画幅，不是 3:4 主页封面）")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--video", type=Path, help="成片路径，画幅与帧率从它读")
    src.add_argument("--canvas", type=parse_canvas,
                     help="目标画幅，如 1080x1920（没有成片时用）")
    p.add_argument("--fps", type=float, default=None,
                   help="目标帧率；缺省时从 --video 读，无成片则 30")
    p.add_argument("--hold", type=float, default=1.5,
                   help="静帧停留秒数，默认 1.5")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--allow-crop", action="store_true",
                       help="允许居中裁切补齐画幅，代价是裁掉画面边缘")
    group.add_argument("--allow-pad", action="store_true",
                       help="允许补黑边补齐画幅，代价是第一帧出现黑边")
    p.add_argument("--json", action="store_true", help="输出 JSON")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.still.is_file():
        print(f"静帧图不存在：{args.still}", file=sys.stderr)
        return 1
    if args.video and not args.video.is_file():
        print(f"成片不存在：{args.video}", file=sys.stderr)
        return 1

    try:
        still = probe_size(args.still)
        canvas = probe_size(args.video) if args.video else args.canvas
        fps = args.fps or (probe_fps(args.video) if args.video else 30.0)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    detail = plan(still, canvas)
    allow = "crop" if args.allow_crop else "pad" if args.allow_pad else None
    errors: list[str] = []
    warnings: list[str] = []

    if detail["mode"] == "mismatch" and allow is None:
        errors.append(
            f"画幅不一致：静帧 {still[0]}x{still[1]}，成片 {canvas[0]}x{canvas[1]}。"
            f"若传的是 3:4 主页封面，那是拿错了素材——它和开场静帧是两个交付物。"
            f"要么另做一张 {canvas[0]}x{canvas[1]} 的静帧，"
            f"要么显式选 --allow-crop（裁掉{detail['crop']['axis']}"
            f" {detail['crop']['loss_ratio']:.1%}）或 --allow-pad（第一帧带黑边）"
        )
    if allow == "crop" and detail["mode"] == "mismatch":
        c = detail["crop"]
        if c["loss_ratio"] > CROP_LOSS_WARN:
            warnings.append(
                f"裁切损失 {c['loss_ratio']:.1%} 超过 {CROP_LOSS_WARN:.0%}，"
                f"标题组很可能被切到，裁完必须目视确认")
        if c["upscale"] > 1.05:
            warnings.append(
                f"裁完还需放大 {c['upscale']:.2f}x，第一帧会比正片软")
    if allow == "pad":
        warnings.append("第一帧带黑边：它是观众看到的第一画面，除非确实要这个效果，"
                        "否则另做一张同画幅的静帧")
    if args.hold < MIN_HOLD_SECONDS:
        warnings.append(f"停留 {args.hold:g}s 低于 {MIN_HOLD_SECONDS:g}s，"
                        "观众来不及读完标题")
    if math.isclose(args.hold, 0.0):
        errors.append("--hold 为 0，等于没有开场静帧")

    vf = build_filter(canvas, detail, allow or "pad", fps)
    result = {
        "still": str(args.still),
        "still_size": f"{still[0]}x{still[1]}",
        "canvas": f"{canvas[0]}x{canvas[1]}",
        "fps": fps,
        "hold_seconds": args.hold,
        "decision": detail["mode"] if allow is None else f"{detail['mode']}:{allow}",
        "plan": detail,
        "ffmpeg_filter": vf,
        "ffmpeg_command": build_command(args.still, args.video, canvas,
                                        args.hold, vf, fps),
        "errors": errors,
        "warnings": warnings,
        "ok": not errors,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"静帧 {result['still_size']} → 成片 {result['canvas']} @ {fps:g}fps"
              f"，停留 {args.hold:g}s")
        print(f"结论：{result['decision']}")
        for e in errors:
            print(f"[error] {e}")
        for w in warnings:
            print(f"[warn]  {w}")
        if not errors:
            print("\n" + result["ffmpeg_command"])

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
