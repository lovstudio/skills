#!/usr/bin/env python3
"""黑白人像 CLI：把单人照片重绘成身份保真的黑白棚拍头像。

子命令：
  prepare   把 HEIC/PNG/JPEG 规整成可上传的 sRGB JPEG 参考图（可裁切、可水平翻转）
  balance   只读查询 OpenRouter 余额，低于生图下限时以退出码 3 结束
  generate  按风格预设组装提示词并调用生图模型，保存 PNG 与所用提示词
  fix       在已有成品上只改一个事实（例如牙齿），其余保持不变
  compare   修改前后并排、局部放大并给出整体像素差异
  thumb     把若干张图缩到头像尺寸拼成一条，检查小尺寸辨识度
  export    把 PNG 成品导出为去元数据的 JPEG

只依赖 Python 标准库；图像规整与对比调用本机的 ImageMagick（magick）或 macOS sips。
密钥只从环境变量 OPENROUTER_API_KEY 读取，不打印、不写入任何文件。
生成后不打开图片，不抢占前台。
"""
from __future__ import annotations

import argparse
import base64
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Optional

DEFAULT_MODEL = "openai/gpt-5.4-image-2"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
MIN_BALANCE_USD = 1.0
EST_COST_PER_IMAGE_USD = 0.30
ATTEMPTS = 3
TIMEOUT_SECONDS = 420
SRGB_ICC = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"
GEOMETRY = re.compile(r"^\d+x\d+\+\d+\+\d+$")

STYLES = {
    "airy": (
        "Style: a bright, airy, premium black-and-white studio portrait, like a magazine profile "
        "photograph. Smooth mid-gray to light-gray seamless studio backdrop, slightly brighter behind "
        "the head. Large soft wraparound key light from the front left, low contrast on the skin, clear "
        "catchlights in the eyes, clean highlights, soft detailed shadows, fine film grain, shallow "
        "depth of field, 85mm editorial portrait look."
    ),
    "studio": (
        "Style: a fine-art black-and-white studio portrait with a gallery-print finish. Soft "
        "directional key light from the upper left with gentle fill so the shadow side keeps open "
        "detail, clear catchlights in the eyes, dark charcoal seamless backdrop with a subtle soft "
        "gradient glow behind the shoulders, full tonal range with deep blacks and detailed "
        "highlights, fine film grain, shallow depth of field, 85mm portrait lens look."
    ),
}

FRAMINGS = {
    "close": (
        "Framing: reframe closer as a head-and-shoulders portrait for a social media avatar. The face "
        "is large and centered, the whole head including hair or headwear stays inside the frame, and "
        "the frame ends at the upper chest. Hands and anything below the chest are out of frame. The "
        "face must stay readable when the image is shown very small."
    ),
    "keep": (
        "Framing: keep the same composition, crop, pose, hand gestures and visible objects as Image 1."
    ),
}

FIX_PRESETS = {
    "teeth": (
        "the teeth. Make them neat, even and healthy: a regular, well-aligned row of upper teeth with "
        "natural shape and natural spacing, no gaps, no chipped, crooked or overlapping teeth, no dark "
        "stains or dark spots between them. The lower teeth are mostly hidden behind the lower lip, "
        "with at most a subtle, even hint of them. Natural enamel tone that fits a black-and-white "
        "photo, clean but not artificially bright. The mouth stays open or closed to the same degree "
        "and the lips keep exactly the same shape."
    ),
}


def die(message: str, code: int = 1) -> "None":
    print(message, file=sys.stderr)
    raise SystemExit(code)


def run(cmd: List[str]) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-3:]
        die("命令失败：%s\n%s" % (Path(cmd[0]).name, "\n".join(tail)))
    return proc


def require_magick() -> str:
    magick = shutil.which("magick")
    if not magick:
        die("需要 ImageMagick 7（magick 命令）。macOS 可用 brew install imagemagick 安装。", 2)
    return magick


def image_size(path: Path) -> str:
    magick = shutil.which("magick")
    if magick:
        proc = subprocess.run([magick, "identify", "-format", "%wx%h", str(path)],
                              capture_output=True, text=True)
        if proc.returncode == 0:
            return proc.stdout.strip()
    return "?"


def refuse_overwrite(path: Path, force: bool) -> None:
    if path.exists() and not force:
        die("目标已存在，未覆盖：%s（确认要覆盖时加 --force）" % path, 2)


# ---------------------------------------------------------------- prepare

def cmd_prepare(args: argparse.Namespace) -> int:
    src = Path(args.input).expanduser()
    if not src.is_file():
        die("找不到输入图片：%s" % src, 2)
    if args.crop and not GEOMETRY.match(args.crop):
        die("--crop 的格式是 宽x高+左+上，例如 1200x1200+905+1450", 2)
    out = Path(args.out).expanduser()
    refuse_overwrite(out, args.force)
    out.parent.mkdir(parents=True, exist_ok=True)
    magick = shutil.which("magick")
    sips = shutil.which("sips")
    is_heif = src.suffix.lower() in (".heic", ".heif")
    side = str(args.max_side)
    with tempfile.TemporaryDirectory() as tmp:
        work = src
        if is_heif:
            if not sips:
                die("读取 HEIC 需要 macOS 的 sips；其他系统请先自行转成 JPEG 或 PNG。", 2)
            work = Path(tmp) / "normalized.png"
            cmd = [sips, "-s", "format", "png"]
            if Path(SRGB_ICC).is_file():
                cmd += ["--matchTo", SRGB_ICC]
            run(cmd + [str(src), "--out", str(work)])
        if magick:
            cmd = [magick, str(work), "-auto-orient", "-background", "white",
                   "-alpha", "remove", "-alpha", "off"]
            if args.crop:
                cmd += ["-crop", args.crop, "+repage"]
            if args.flip:
                cmd += ["-flop"]
            cmd += ["-resize", "%sx%s>" % (side, side), "-strip", "-quality", "93", str(out)]
            run(cmd)
        elif sips:
            if args.crop or args.flip:
                die("裁切和翻转需要 ImageMagick 7（magick 命令）。", 2)
            run([sips, "-s", "format", "jpeg", "-s", "formatOptions", "93", "-Z", side,
                 str(work), "--out", str(out)])
        else:
            die("需要 ImageMagick 7 或 macOS sips 来规整图片。", 2)
    print("prepared %s size=%s bytes=%d flipped=%s" % (
        out, image_size(out), out.stat().st_size, "yes" if args.flip else "no"))
    return 0


# ---------------------------------------------------------------- provider

def api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        die("缺少环境变量 OPENROUTER_API_KEY。", 2)
    return key


def base_url() -> str:
    return os.environ.get("OPENROUTER_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def read_balance() -> float:
    req = urllib.request.Request(base_url() + "/credits",
                                 headers={"Authorization": "Bearer " + api_key()})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read()).get("data") or {}
    except urllib.error.HTTPError as exc:
        die("查询余额失败：http %s" % exc.code)
    except Exception as exc:  # 网络错误
        die("查询余额失败：%s" % type(exc).__name__)
    return float(data.get("total_credits") or 0) - float(data.get("total_usage") or 0)


def cmd_balance(args: argparse.Namespace) -> int:
    need = max(MIN_BALANCE_USD, MIN_BALANCE_USD + args.images * EST_COST_PER_IMAGE_USD)
    balance = read_balance()
    ok = balance >= need
    print("balance=%.2f need>=%.2f images=%d %s" % (balance, need, args.images, "ok" if ok else "insufficient"))
    if not ok:
        print("余额不足：生图要求账户余额不低于 %.2f 美元，调低 max_tokens 无效，需要充值。" % MIN_BALANCE_USD,
              file=sys.stderr)
        return 3
    return 0


def data_url(path: Path) -> str:
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "webp": "image/webp"}.get(path.suffix.lower().lstrip("."))
    if not mime:
        die("参考图只支持 JPEG、PNG、WebP：%s（HEIC 请先用 prepare 规整）" % path, 2)
    return "data:%s;base64,%s" % (mime, base64.b64encode(path.read_bytes()).decode())


def call_model(prompt: str, refs: List[str], model: str) -> dict:
    content = [{"type": "text", "text": prompt}]
    for ref in refs:
        content.append({"type": "image_url", "image_url": {"url": ref}})
    body = {
        "model": model,
        "modalities": ["image", "text"],
        "image_config": {"aspect_ratio": "1:1"},
        "messages": [{"role": "user", "content": content}],
    }
    req = urllib.request.Request(
        base_url() + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + api_key(), "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read())


def extract_image(data: dict) -> Optional[str]:
    message = (data.get("choices") or [{}])[0].get("message") or {}
    for image in message.get("images") or []:
        url = (image.get("image_url") or {}).get("url")
        if url:
            return url
    content = message.get("content")
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict):
                url = (part.get("image_url") or {}).get("url")
                if url:
                    return url
    return None


def generate_one(name: str, prompt: str, refs: List[str], model: str, out_dir: Path) -> bool:
    last = "unknown"
    for attempt in range(1, ATTEMPTS + 1):
        started = time.time()
        try:
            data = call_model(prompt, refs, model)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            try:
                detail = json.dumps((json.loads(detail).get("error") or {}).get("message"), ensure_ascii=False)
            except Exception:
                detail = detail[:300]
            last = "http %s: %s" % (exc.code, detail)
            print("[%s] attempt %d failed: %s" % (name, attempt, last), flush=True)
            if exc.code == 402:
                print("[%s] 余额不足：生图要求账户余额不低于 %.2f 美元，需要充值后重试。" % (name, MIN_BALANCE_USD),
                      flush=True)
            if exc.code in (400, 401, 402, 403, 404):
                break
            time.sleep(5 * attempt)
            continue
        except Exception as exc:  # 断连、超时
            last = "%s: %s" % (type(exc).__name__, exc)
            print("[%s] attempt %d failed: %s" % (name, attempt, last), flush=True)
            time.sleep(5 * attempt)
            continue
        url = extract_image(data)
        if not url or not url.startswith("data:"):
            last = "response carried no image"
            print("[%s] attempt %d failed: %s" % (name, attempt, last), flush=True)
            time.sleep(5 * attempt)
            continue
        header, payload = url.split(",", 1)
        ext = "jpg" if ("jpeg" in header or "jpg" in header) else ("webp" if "webp" in header else "png")
        path = out_dir / ("%s.%s" % (name, ext))
        raw = base64.b64decode(payload)
        path.write_bytes(raw)
        (out_dir / (name + ".prompt.txt")).write_text(prompt + "\n", encoding="utf-8")
        cost = (data.get("usage") or {}).get("cost")
        print("[%s] saved %s size=%s bytes=%d seconds=%.0f cost=%s" % (
            name, path, image_size(path), len(raw), time.time() - started, cost), flush=True)
        return True
    print("[%s] GAVE UP: %s" % (name, last), flush=True)
    return False


def run_jobs(names: List[str], prompt: str, ref_paths: List[Path], model: str, out_dir: Path,
             force: bool) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        for ext in ("png", "jpg", "webp"):
            refuse_overwrite(out_dir / ("%s.%s" % (name, ext)), force)
    api_key()
    refs = [data_url(path) for path in ref_paths]
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(names)) as pool:
        results = list(pool.map(lambda n: generate_one(n, prompt, refs, model, out_dir), names))
    print("done ok=%d fail=%d" % (sum(results), len(results) - sum(results)))
    return 0 if all(results) else 1


def existing(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if not path.is_file():
        die("找不到图片：%s" % path, 2)
    return path


def variant_names(name: str, count: int) -> List[str]:
    if count <= 1:
        return [name]
    return ["%s-%d" % (name, index) for index in range(1, count + 1)]


# ---------------------------------------------------------------- generate

def compose_prompt(args: argparse.Namespace) -> str:
    image_index = 1
    parts = ["Create a square 1:1 black-and-white portrait photograph of the person in Image 1."]
    refs = ["Image 1 is the content reference: the only source of truth for who the person is, "
            "what they wear and what they are doing."]
    if args.subject:
        refs.append("What Image 1 shows: %s" % args.subject.strip())
    if args.face_ref:
        image_index += 1
        refs.append("Image %d is a close-up of the same person's face: use it for the exact facial "
                    "features, facial hair and eyewear." % image_index)
    if args.style_ref:
        image_index += 1
        refs.append("Image %d is the style reference: match its lighting, background, tonal range and "
                    "overall finish. Do not copy its expression, pose, clothing or accessories."
                    % image_index)
    parts.append(" ".join(refs))

    identity = ("Identity: keep exactly the same person. Same face shape, facial features and "
                "proportions, natural skin texture and facial hair. Do not beautify, slim, smooth or "
                "make the person look younger. Keep eyewear, headwear, earphones, jewellery and "
                "clothing as in Image 1.")
    if args.keep:
        identity += " These must stay exactly as in Image 1: %s" % args.keep.strip()
    parts.append(identity)

    removal = ("If Image 1 carries a colour cast, halftone dots, filters, poster shapes or any other "
               "stylised treatment, remove it completely.")
    if args.remove:
        removal += " Also remove entirely: %s" % args.remove.strip()
    parts.append(removal)

    if args.expression:
        parts.append("Expression: %s Keep it natural and unposed." % args.expression.strip())
    else:
        parts.append("Expression: keep the same expression, gaze direction and head angle as Image 1.")

    parts.append(FRAMINGS[args.framing])
    parts.append(STYLES[args.style])
    if args.note:
        parts.append("Creator note: %s" % args.note.strip())
    parts.append("A true black-and-white photograph with neutral gray tones and no colour tint. "
                 "Photorealistic, not an illustration. No added text, watermark or border.")
    return "\n\n".join(parts)


def cmd_generate(args: argparse.Namespace) -> int:
    ref_paths = [existing(args.photo)]
    if args.face_ref:
        ref_paths.append(existing(args.face_ref))
    if args.style_ref:
        ref_paths.append(existing(args.style_ref))
    if args.prompt_file:
        prompt = existing(args.prompt_file).read_text(encoding="utf-8").strip()
    else:
        prompt = compose_prompt(args)
    names = variant_names(args.name, args.variants)
    model = args.model or os.environ.get("BW_PORTRAIT_MODEL") or DEFAULT_MODEL
    if args.dry_run:
        print("model: %s" % model)
        print("outputs: %s" % ", ".join(names))
        for index, path in enumerate(ref_paths, 1):
            print("image %d: %s (%s)" % (index, path, image_size(path)))
        print("--- prompt ---")
        print(prompt)
        return 0
    return run_jobs(names, prompt, ref_paths, model, Path(args.out_dir).expanduser(), args.force)


# ---------------------------------------------------------------- fix

def compose_fix_prompt(args: argparse.Namespace) -> str:
    change = FIX_PRESETS.get(args.preset) if args.preset else None
    if args.change:
        change = args.change.strip()
    if not change:
        die("需要 --preset 或 --change 说明要改的那一个事实。", 2)
    keep = ("the same person and face, the same expression, head angle and gaze, the same eyewear, "
            "headwear, hair and facial hair, the same clothing and accessories")
    if args.keep:
        keep += ", %s" % args.keep.strip()
    keep += ", the same framing, background, lighting, black-and-white tones and film grain"
    return "\n\n".join([
        "Edit the attached black-and-white photograph. Square 1:1.",
        "Keep everything exactly as it is: %s. Do not change age, skin or facial proportions." % keep,
        "Change only %s" % change,
        "Photorealistic photograph. No added text, watermark or border.",
    ])


def cmd_fix(args: argparse.Namespace) -> int:
    image = existing(args.image)
    prompt = compose_fix_prompt(args)
    model = args.model or os.environ.get("BW_PORTRAIT_MODEL") or DEFAULT_MODEL
    if args.dry_run:
        print("model: %s" % model)
        print("image 1: %s (%s)" % (image, image_size(image)))
        print("--- prompt ---")
        print(prompt)
        return 0
    return run_jobs([args.name], prompt, [image], model, Path(args.out_dir).expanduser(), args.force)


# ---------------------------------------------------------------- review helpers

def cmd_compare(args: argparse.Namespace) -> int:
    magick = require_magick()
    before, after = existing(args.before), existing(args.after)
    if args.zoom and not GEOMETRY.match(args.zoom):
        die("--zoom 的格式是 宽x高+左+上，例如 300x220+330+470", 2)
    out = Path(args.out).expanduser()
    refuse_overwrite(out, args.force)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        row = Path(tmp) / "row.png"
        run([magick, str(before), "-resize", "1000x1000", str(after), "-resize", "1000x1000",
             "+append", str(row)])
        rows = [str(row)]
        if args.zoom:
            zoom = Path(tmp) / "zoom.png"
            run([magick,
                 "(", str(before), "-crop", args.zoom, "+repage", "-filter", "Lanczos", "-resize", "1000x", ")",
                 "(", str(after), "-crop", args.zoom, "+repage", "-filter", "Lanczos", "-resize", "1000x", ")",
                 "+append", str(zoom)])
            rows.append(str(zoom))
        run([magick] + rows + ["-append", "-strip", "-quality", "90", str(out)])
    rmse = "n/a"
    if image_size(before) == image_size(after):
        proc = subprocess.run([magick, "compare", "-metric", "RMSE", str(before), str(after), "null:"],
                              capture_output=True, text=True)
        match = re.search(r"\(([0-9.eE+-]+)\)", proc.stderr or "")
        if match:
            rmse = "%.3f" % float(match.group(1))
    print("compare %s size=%s rmse=%s" % (out, image_size(out), rmse))
    print("rmse 是整体归一化差异：约 0.1 以内说明构图基本没动，明显更高说明模型重画了位置或背景。")
    return 0


def cmd_thumb(args: argparse.Namespace) -> int:
    magick = require_magick()
    images = [str(existing(item)) for item in args.images]
    out = Path(args.out).expanduser()
    refuse_overwrite(out, args.force)
    out.parent.mkdir(parents=True, exist_ok=True)
    size = "%dx%d" % (args.size, args.size)
    run([magick] + images + ["-resize", size, "+append", "-strip", str(out)])
    print("thumb %s size=%s each=%s" % (out, image_size(out), size))
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    image = existing(args.image)
    out = Path(args.out).expanduser()
    refuse_overwrite(out, args.force)
    out.parent.mkdir(parents=True, exist_ok=True)
    magick = shutil.which("magick")
    sips = shutil.which("sips")
    if magick:
        run([magick, str(image), "-strip", "-quality", str(args.quality), str(out)])
    elif sips:
        run([sips, "-s", "format", "jpeg", "-s", "formatOptions", str(args.quality),
             str(image), "--out", str(out)])
    else:
        die("需要 ImageMagick 7 或 macOS sips 来导出 JPEG。", 2)
    print("exported %s size=%s bytes=%d" % (out, image_size(out), out.stat().st_size))
    return 0


# ---------------------------------------------------------------- cli

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bw_portrait.py",
        description="把单人照片重绘成身份保真的黑白棚拍头像。")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prepare", help="规整参考图：sRGB JPEG，可裁切与水平翻转")
    p.add_argument("input", help="原始照片（HEIC、JPEG、PNG、WebP）")
    p.add_argument("--out", required=True, help="输出的 JPEG 路径")
    p.add_argument("--max-side", type=int, default=1400, help="长边上限，默认 1400")
    p.add_argument("--crop", help="先裁切：宽x高+左+上（原图像素）")
    p.add_argument("--flip", action="store_true", help="水平翻转，用于还原镜子自拍")
    p.add_argument("--force", action="store_true", help="允许覆盖已有文件")
    p.set_defaults(func=cmd_prepare)

    p = sub.add_parser("balance", help="只读查询 OpenRouter 余额")
    p.add_argument("--images", type=int, default=1, help="本轮计划生成的张数，用于估算所需余额")
    p.set_defaults(func=cmd_balance)

    p = sub.add_parser("generate", help="生成黑白头像")
    p.add_argument("--photo", required=True, help="参考照片（Image 1，prepare 的输出）")
    p.add_argument("--style", choices=sorted(STYLES), default="airy",
                   help="airy 浅灰背景明亮编辑风（默认）；studio 深色背景棚拍")
    p.add_argument("--framing", choices=sorted(FRAMINGS), default="close",
                   help="close 头肩特写（默认）；keep 保持原构图")
    p.add_argument("--subject", help="英文一两句：原图里的人在做什么、穿戴什么、原图带有什么处理")
    p.add_argument("--keep", help="英文：必须原样保留的事实，例如眼镜形状、头巾、麦克风")
    p.add_argument("--remove", help="英文：必须去掉的东西，例如手机和举手机的手")
    p.add_argument("--expression", help="英文：需要改变表情时的描述；不填则保持原图表情")
    p.add_argument("--face-ref", help="可选：脸部近景参考，用于对齐五官和眼镜")
    p.add_argument("--style-ref", help="可选：风格参考成品；会把表情和饰品往它上面拉，改表情时不要给")
    p.add_argument("--note", help="英文：其他补充，不得覆盖身份约束")
    p.add_argument("--prompt-file", help="完全自定义提示词时使用，覆盖上面的组装结果")
    p.add_argument("--name", required=True, help="输出文件名（不含扩展名）")
    p.add_argument("--variants", type=int, default=1, help="同一提示词并行生成的张数")
    p.add_argument("--out-dir", required=True, help="输出目录")
    p.add_argument("--model", help="模型 ID，默认 %s，也可用 BW_PORTRAIT_MODEL 指定" % DEFAULT_MODEL)
    p.add_argument("--dry-run", action="store_true", help="只打印提示词与参考图，不调用模型")
    p.add_argument("--force", action="store_true", help="允许覆盖同名输出")
    p.set_defaults(func=cmd_generate)

    p = sub.add_parser("fix", help="在成品上只改一个事实")
    p.add_argument("--image", required=True, help="要修改的成品图")
    p.add_argument("--preset", choices=sorted(FIX_PRESETS), help="内置修正：teeth 牙齿")
    p.add_argument("--change", help="英文：自定义要改的那一个事实，接在 Change only 之后")
    p.add_argument("--keep", help="英文：额外点名必须不变的东西，例如衣服上的印花、手势")
    p.add_argument("--name", required=True, help="输出文件名（不含扩展名）")
    p.add_argument("--out-dir", required=True, help="输出目录")
    p.add_argument("--model", help="模型 ID")
    p.add_argument("--dry-run", action="store_true", help="只打印提示词，不调用模型")
    p.add_argument("--force", action="store_true", help="允许覆盖同名输出")
    p.set_defaults(func=cmd_fix)

    p = sub.add_parser("compare", help="修改前后并排对比，可局部放大")
    p.add_argument("--before", required=True)
    p.add_argument("--after", required=True)
    p.add_argument("--zoom", help="局部放大区域：宽x高+左+上")
    p.add_argument("--out", required=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("thumb", help="缩到头像尺寸拼成一条")
    p.add_argument("images", nargs="+")
    p.add_argument("--size", type=int, default=132, help="每张的边长，默认 132")
    p.add_argument("--out", required=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_thumb)

    p = sub.add_parser("export", help="导出为去元数据的 JPEG")
    p.add_argument("--image", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--quality", type=int, default=95)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_export)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
