#!/usr/bin/env python3
"""发系统通知 + 语音播报，用于需要用户到场的交互卡点。

这个脚本存在的理由是「被叫到」这件事不能靠记得：发布流程里有两处必须让用户
真的看见——交出浏览器控制权等扫码，以及提交前确认终稿。两处都可能发生在用户
不看终端的时候，光把文字打在对话里等于没通知。

只做通知，不做等待，也不做任何页面操作。等待逻辑留给调用方（控制权轮询 /
停下来等用户回话），这样通知失败不会连带阻塞流程。

行为：
- `--tts-provider auto` 有 `VOLC_APPID` / `VOLC_TOKEN` 时优先调火山 TTS，然后用 `afplay` 后台播放。
- 火山 TTS 未配置或请求失败时，macOS 降级到 `say` 播报（默认中文语音 Tingting）。
- 其他平台只在 stdout 打印，退出码仍为 0——通知不是任务的一部分，缺它不该让
  发布失败。
- 播报在后台起，不等它念完；通知与播报各自失败都只降级为 warning。

用法：

    python3 notify_user.py --title "视频号发布" \
        --message "终稿待确认：短标题/描述/话题/封面已就绪，等你确认后再发表" \
        --speech "视频号终稿已准备好，请确认后我再发表"
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import uuid


def _osascript_literal(text: str) -> str:
    """转义成 AppleScript 字符串字面量，避免文案里的引号截断脚本。"""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def send_notification(title: str, message: str, sound: str = "Ping") -> dict:
    if platform.system() != "Darwin" or not shutil.which("osascript"):
        return {"sent": False, "reason": "osascript unavailable"}
    script = (
        f'display notification "{_osascript_literal(message)}"'
        f' with title "{_osascript_literal(title)}"'
        f' sound name "{_osascript_literal(sound)}"'
    )
    try:
        subprocess.run(
            ["osascript", "-e", script],
            check=True, capture_output=True, timeout=10,
        )
        return {"sent": True}
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return {"sent": False, "reason": str(exc)}


def _play_audio_in_background(audio: bytes, suffix: str = ".mp3") -> dict:
    if platform.system() != "Darwin" or not shutil.which("afplay"):
        return {"spoken": False, "provider": "volcengine", "reason": "afplay unavailable"}
    try:
        with tempfile.NamedTemporaryFile(prefix="lov-publisher-tts-", suffix=suffix, delete=False) as handle:
            handle.write(audio)
            audio_path = handle.name
        cleanup_program = (
            "import os,subprocess,sys; "
            "p=sys.argv[1]; "
            "subprocess.run(['/usr/bin/afplay', p], check=False, "
            "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
            "os.unlink(p) if os.path.exists(p) else None"
        )
        subprocess.Popen(
            [sys.executable, "-c", cleanup_program, audio_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return {"spoken": True, "provider": "volcengine"}
    except OSError as exc:
        return {"spoken": False, "provider": "volcengine", "reason": str(exc)}


def speak_volcengine(text: str) -> dict:
    app_id = os.environ.get("VOLC_APPID")
    token = os.environ.get("VOLC_TOKEN")
    if not app_id or not token:
        return {"spoken": False, "provider": "volcengine", "reason": "credentials unavailable"}

    body = {
        "app": {"appid": app_id, "token": token, "cluster": os.environ.get("VOLC_TTS_CLUSTER", "volcano_tts")},
        "user": {"uid": "lov-media-publisher"},
        "audio": {
            "voice_type": os.environ.get("VOLC_TTS_VOICE", "zh_female_wanqudashu_moon_bigtts"),
            "encoding": "mp3",
            "speed_ratio": 1.0,
            "rate": 24000,
            "bitrate": 160,
        },
        "request": {"reqid": str(uuid.uuid4()), "text": text, "operation": "query"},
    }
    request = urllib.request.Request(
        "https://openspeech.bytedance.com/api/v1/tts",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer;{token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload.get("code") != 3000 or not payload.get("data"):
            return {
                "spoken": False,
                "provider": "volcengine",
                "reason": f"TTS response code {payload.get('code')}: {payload.get('message', 'unknown')}",
            }
        return _play_audio_in_background(base64.b64decode(payload["data"]))
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return {"spoken": False, "provider": "volcengine", "reason": str(exc)}


def speak_system(text: str, voice: str = "Tingting") -> dict:
    if platform.system() != "Darwin" or not shutil.which("say"):
        return {"spoken": False, "provider": "system", "reason": "say unavailable"}
    try:
        # 不等播报结束：它可能念好几秒，而调用方要立刻进入等待逻辑。
        subprocess.Popen(
            ["say", "-v", voice, text],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return {"spoken": True, "provider": "system"}
    except OSError as exc:
        return {"spoken": False, "provider": "system", "reason": str(exc)}


def speak(text: str, provider: str = "auto", voice: str = "Tingting") -> dict:
    if provider in {"auto", "volcengine"}:
        result = speak_volcengine(text)
        if result["spoken"] or provider == "volcengine":
            return result
    return speak_system(text, voice)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="系统通知 + 语音播报")
    p.add_argument("--title", default="视频号发布", help="通知标题")
    p.add_argument("--message", required=True, help="通知正文，一行，简短")
    p.add_argument("--speech", default=None,
                   help="播报文本；缺省时用 --message")
    p.add_argument("--voice", default="Tingting", help="macOS 语音名")
    p.add_argument(
        "--tts-provider",
        choices=("auto", "volcengine", "system"),
        default="auto",
        help="语音提供方；auto 优先火山 TTS，失败降级系统语音",
    )
    p.add_argument("--sound", default="Ping", help="通知提示音")
    p.add_argument("--no-speech", action="store_true", help="只发通知，不播报")
    p.add_argument("--json", action="store_true", help="输出 JSON")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    result = {
        "platform": platform.system(),
        "notification": send_notification(args.title, args.message, args.sound),
        "speech": {"spoken": False, "reason": "disabled"} if args.no_speech
        else speak(args.speech or args.message, args.tts_provider, args.voice),
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        n, s = result["notification"], result["speech"]
        print(f"通知：{'已发' if n['sent'] else '未发（' + n.get('reason', '') + '）'}"
              f" · 播报：{'已起' if s['spoken'] else '未起（' + s.get('reason', '') + '）'}"
              f" · TTS：{s.get('provider', 'disabled')}")
        if not n["sent"]:
            print(f"[fallback] {args.title}：{args.message}", file=sys.stderr)

    # 通知失败不阻塞发布流程。
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
