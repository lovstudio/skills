#!/usr/bin/env python3
"""Render Video Chapter projects with Pillow and FFmpeg."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from chapter_project import format_clock, load_valid_project

VERSION = "0.2.0"


def require_executable(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise ValueError(f"{name} is required and was not found on PATH")
    return path


def load_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise ValueError(
            "Pillow is required; install it with 'python3 -m pip install Pillow'"
        ) from exc
    return Image, ImageDraw, ImageFont


def rgba(value: str) -> Tuple[int, int, int, int]:
    cleaned = value.lstrip("#")
    if len(cleaned) == 6:
        cleaned += "FF"
    return tuple(int(cleaned[index : index + 2], 16) for index in range(0, 8, 2))


def find_font(project: Dict[str, Any], ImageFont: Any):
    style = project["style"]
    requested = style.get("fontFile")
    candidates = [
        requested,
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).expanduser().is_file():
            try:
                return ImageFont.truetype(
                    str(Path(candidate).expanduser()),
                    size=round(style["fontSize"]),
                )
            except OSError:
                continue
    return ImageFont.load_default()


def rounded_segment(
    draw: Any,
    box: Tuple[int, int, int, int],
    radius: int,
    fill: Tuple[int, int, int, int],
) -> None:
    draw.rounded_rectangle(box, radius=max(0, radius), fill=fill)


def calculate_segments(project: Dict[str, Any]) -> Tuple[int, int, List[Tuple[int, int]]]:
    video = project["video"]
    style = project["style"]
    track_width = int(video["width"] - 2 * style["marginX"])
    bar_height = max(2, round(style["barHeight"]))
    gap = max(0, round(style["gap"]))
    count = len(project["chapters"])
    available = track_width - gap * (count - 1)
    if available < count:
        raise ValueError("style margins and gaps leave no room for chapter segments")
    duration = float(video["duration"])
    widths: List[int] = []
    assigned = 0
    for index, chapter in enumerate(project["chapters"]):
        if index == count - 1:
            width = available - assigned
        else:
            ratio = (float(chapter["end"]) - float(chapter["start"])) / duration
            width = max(1, round(available * ratio))
            assigned += width
        widths.append(width)
    overflow = sum(widths) - available
    if overflow:
        widths[-1] -= overflow
    segments: List[Tuple[int, int]] = []
    cursor = 0
    for width in widths:
        segments.append((cursor, width))
        cursor += width + gap
    return track_width, bar_height, segments


def truncate_text(draw: Any, value: str, font: Any, max_width: int) -> str:
    if draw.textbbox((0, 0), value, font=font)[2] <= max_width:
        return value
    ellipsis = "…"
    candidate = value
    while candidate:
        candidate = candidate[:-1]
        rendered = candidate.rstrip() + ellipsis
        if draw.textbbox((0, 0), rendered, font=font)[2] <= max_width:
            return rendered
    return ellipsis


def build_layers(
    project: Dict[str, Any],
    directory: Path,
) -> Tuple[Path, Path, Path, List[Path], int, int, int, int]:
    Image, ImageDraw, ImageFont = load_pillow()
    video = project["video"]
    style = project["style"]
    width, height = int(video["width"]), int(video["height"])
    track_width, bar_height, segments = calculate_segments(project)
    radius = min(round(style["cornerRadius"]), bar_height // 2)

    base = Image.new("RGBA", (track_width, bar_height), (0, 0, 0, 0))
    active = Image.new("RGBA", (track_width, bar_height), (0, 0, 0, 0))
    empty = Image.new("RGBA", (track_width, bar_height), (0, 0, 0, 0))
    base_draw = ImageDraw.Draw(base)
    active_draw = ImageDraw.Draw(active)
    for x, segment_width in segments:
        box = (x, 0, x + segment_width - 1, bar_height - 1)
        rounded_segment(base_draw, box, radius, rgba(style["inactiveColor"]))
        rounded_segment(active_draw, box, radius, rgba(style["activeColor"]))

    base_path = directory / "bar-base.png"
    active_path = directory / "bar-active.png"
    empty_path = directory / "bar-empty.png"
    base.save(base_path)
    active.save(active_path)
    empty.save(empty_path)

    margin_x = round(style["marginX"])
    edge_margin = round(style["marginBottom"])
    if style["position"] == "bottom":
        bar_y = height - edge_margin - bar_height
    else:
        bar_y = edge_margin

    title_paths: List[Path] = []
    if style["showTitle"]:
        font = find_font(project, ImageFont)
        font_size = round(style["fontSize"])
        panel_height = max(round(font_size * 1.85), font_size + 16)
        text_padding_x = max(14, round(font_size * 0.6))
        title_y = (
            bar_y - round(style["labelGap"]) - panel_height
            if style["position"] == "bottom"
            else bar_y + bar_height + round(style["labelGap"])
        )
        title_y = max(0, min(title_y, height - panel_height))
        for index, chapter in enumerate(project["chapters"], start=1):
            layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(layer)
            prefix = f"{index:02d}  " if style["showIndex"] else ""
            text = prefix + chapter["title"]
            max_text_width = max(80, width - 2 * margin_x - 2 * text_padding_x)
            text = truncate_text(draw, text, font, max_text_width)
            bounds = draw.textbbox((0, 0), text, font=font)
            text_width = bounds[2] - bounds[0]
            text_height = bounds[3] - bounds[1]
            panel_width = min(
                width - 2 * margin_x,
                text_width + 2 * text_padding_x,
            )
            panel_box = (
                margin_x,
                title_y,
                margin_x + panel_width,
                title_y + panel_height,
            )
            draw.rounded_rectangle(
                panel_box,
                radius=max(4, round(style["cornerRadius"] * 1.6)),
                fill=rgba(style["panelColor"]),
            )
            text_y = title_y + (panel_height - text_height) / 2 - bounds[1]
            draw.text(
                (margin_x + text_padding_x, text_y),
                text,
                font=font,
                fill=rgba(style["textColor"]),
            )
            title_path = directory / f"title-{index:02d}.png"
            layer.save(title_path)
            title_paths.append(title_path)
    return (
        base_path,
        empty_path,
        active_path,
        title_paths,
        margin_x,
        bar_y,
        track_width,
        bar_height,
    )


def run(command: List[str], print_command: bool) -> None:
    if print_command:
        print(" ".join(json.dumps(part) for part in command))
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"FFmpeg exited with status {exc.returncode}") from exc


def render_overlay(
    project: Dict[str, Any],
    output: Path,
    *,
    print_command: bool = False,
) -> None:
    ffmpeg = require_executable("ffmpeg")
    video = project["video"]
    duration = float(video["duration"])
    fps = float(video["fps"])
    width, height = int(video["width"]), int(video["height"])
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="video-chapter-") as temp:
        temp_dir = Path(temp)
        (
            base_path,
            empty_path,
            active_path,
            title_paths,
            bar_x,
            bar_y,
            track_width,
            bar_height,
        ) = build_layers(project, temp_dir)

        command = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-f",
            "lavfi",
            "-i",
            (
                f"color=c=black@0.0:s={width}x{height}:r={fps}:d={duration},"
                "format=rgba"
            ),
        ]
        for layer in (base_path, empty_path, active_path):
            command.extend(["-loop", "1", "-framerate", str(fps), "-i", str(layer)])
        command.extend(
            [
                "-f",
                "lavfi",
                "-i",
                (
                    f"nullsrc=s={track_width}x{bar_height}:r={fps}:d={duration},"
                    "format=gray,"
                    f"geq=lum='if(lte(X,W*T/{duration}),255,0)'"
                ),
            ]
        )
        for title_path in title_paths:
            command.extend(
                ["-loop", "1", "-framerate", str(fps), "-i", str(title_path)]
            )

        filters = [
            "[2:v][3:v][4:v]maskedmerge[progress]",
            f"[0:v][1:v]overlay={bar_x}:{bar_y}:format=auto[stage0]",
            f"[stage0][progress]overlay={bar_x}:{bar_y}:format=auto[stage1]",
        ]
        current = "stage1"
        for offset, (input_index, chapter) in enumerate(
            zip(range(5, 5 + len(title_paths)), project["chapters"]),
            start=2,
        ):
            target = f"stage{offset}"
            start = float(chapter["start"])
            end = float(chapter["end"])
            filters.append(
                f"[{current}][{input_index}:v]overlay=0:0:format=auto:"
                f"enable='between(t,{start},{end})'[{target}]"
            )
            current = target
        filters.append(f"[{current}]format=yuva444p10le[outv]")
        command.extend(
            [
                "-filter_complex",
                ";".join(filters),
                "-map",
                "[outv]",
                "-t",
                str(duration),
                "-an",
                "-c:v",
                "prores_ks",
                "-profile:v",
                "4",
                "-pix_fmt",
                "yuva444p10le",
                "-vendor",
                "apl0",
                "-bits_per_mb",
                "8000",
                str(output),
            ]
        )
        run(command, print_command)


def burn_overlay(
    project: Dict[str, Any],
    output: Path,
    *,
    print_command: bool = False,
) -> None:
    source = Path(project["video"]["src"]).expanduser()
    if not source.is_file():
        raise ValueError(f"source video not found: {source}")
    ffmpeg = require_executable("ffmpeg")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="video-chapter-burn-") as temp:
        overlay_path = Path(temp) / "chapter-overlay.mov"
        render_overlay(project, overlay_path, print_command=print_command)
        export = project.get("export", {})
        command = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-i",
            str(source),
            "-i",
            str(overlay_path),
            "-filter_complex",
            "[0:v][1:v]overlay=0:0:format=auto:shortest=1[v]",
            "-map",
            "[v]",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            str(export.get("crf", 18)),
            "-preset",
            str(export.get("preset", "medium")),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(output),
        ]
        run(command, print_command)


def write_package_files(project: Dict[str, Any], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    project_path = output / "chapter-project.json"
    project_path.write_text(
        json.dumps(project, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    timestamp_lines = [
        f"{format_clock(float(chapter['start']))} {chapter['title']}"
        for chapter in project["chapters"]
    ]
    (output / "chapters.txt").write_text(
        "\n".join(timestamp_lines) + "\n",
        encoding="utf-8",
    )
    with (output / "chapters.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["index", "start", "end", "title", "summary"])
        for index, chapter in enumerate(project["chapters"], start=1):
            writer.writerow(
                [
                    index,
                    format_clock(float(chapter["start"])),
                    format_clock(float(chapter["end"])),
                    chapter["title"],
                    chapter["summary"],
                ]
            )
    instructions = """剪映 / CapCut 导入

1. 导入 chapter-overlay.mov。
2. 放到最上方视频轨道并对齐 00:00。
3. 保持缩放 100%，不要裁切透明画面。
4. 项目分辨率、帧率应与 chapter-project.json 一致。
5. 若尾部因帧取整多出极短空白，只裁掉素材末尾。

chapters.txt 可直接用于 YouTube、Bilibili 等平台章节字段。
chapters.csv 可用于其他剪辑软件或自动化脚本。
"""
    (output / "剪映导入说明.txt").write_text(instructions, encoding="utf-8")


def command_overlay(args: argparse.Namespace) -> int:
    project, warnings = load_valid_project(Path(args.project).expanduser())
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    output = Path(args.output).expanduser()
    render_overlay(project, output, print_command=args.print_command)
    print(f"Wrote transparent overlay: {output}")
    return 0


def command_burn(args: argparse.Namespace) -> int:
    project, warnings = load_valid_project(Path(args.project).expanduser())
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    output = Path(args.output).expanduser()
    burn_overlay(project, output, print_command=args.print_command)
    print(f"Wrote burned video: {output}")
    return 0


def command_package(args: argparse.Namespace) -> int:
    project, warnings = load_valid_project(Path(args.project).expanduser())
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    output = Path(args.output).expanduser()
    write_package_files(project, output)
    render_overlay(
        project,
        output / "chapter-overlay.mov",
        print_command=args.print_command,
    )
    print(f"Wrote editor package: {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, function, help_text in (
        ("overlay", command_overlay, "Render a transparent ProRes overlay"),
        ("burn", command_burn, "Burn the overlay into the source video"),
        ("package", command_package, "Build a 剪映/editor import package"),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("--project", required=True)
        command.add_argument("--output", required=True)
        command.add_argument(
            "--print-command",
            action="store_true",
            help="Print FFmpeg commands before execution",
        )
        command.set_defaults(func=function)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        return args.func(args)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

