#!/usr/bin/env python3
"""see_image — 给纯文本模型看图：把图片发给智谱 GLM-4V-Flash，返回文字描述。

用法:
    describe_image.py <image_path> [question]

环境变量:
    ZHIPU_API_KEY  智谱开放平台 key（https://bigmodel.cn/apikey/platform，格式 id.secret）
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

BASE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL = "glm-4v-flash"
MAX_TOKENS = 1024              # glm-4v-flash 的 max_tokens 上限就是 1024，设大会被 400 拒绝
MAX_BYTES = 5 * 1024 * 1024    # 超过则用 sips 降采样，避免尺寸/载荷拒绝
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
MIME_BY_EXT = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
}
DEFAULT_PROMPT = (
    "请详细描述这张图片：主要物体、人物、场景、布局、颜色、风格，以及图中出现的所有文字（请完整转录）。"
    "如果图片是截图或图表，请说明其结构和关键信息。"
)


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: describe_image.py <图片路径> [具体问题]", file=sys.stderr)
        return 2
    path = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2].strip() else DEFAULT_PROMPT

    api_key = os.environ.get("ZHIPU_API_KEY", "").strip()
    if not api_key:
        print(
            "lov-describe-image: 未设置 ZHIPU_API_KEY。请到 https://bigmodel.cn/apikey/platform 注册，"
            "然后执行 export ZHIPU_API_KEY='你的key'（写入 ~/.zshenv 长期生效）。",
            file=sys.stderr,
        )
        return 1

    if not os.path.isfile(path):
        print(f"lov-describe-image: 找不到文件 {path}", file=sys.stderr)
        return 1
    ext = os.path.splitext(path)[1].lower()
    if ext not in IMAGE_EXT:
        print(f"lov-describe-image: 不支持的图片格式 {ext or '(无扩展名)'}，支持 {sorted(IMAGE_EXT)}", file=sys.stderr)
        return 1

    data = open(path, "rb").read()
    mime = MIME_BY_EXT[ext]
    if len(data) > MAX_BYTES:
        if shutil.which("sips") is None:
            print(f"lov-describe-image: 图片 {len(data)} 字节超过 {MAX_BYTES} 且无 sips 可降采样", file=sys.stderr)
            return 1
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            subprocess.run(["sips", "-Z", "2048", path, "--out", tmp_path], check=True, capture_output=True)
            data = open(tmp_path, "rb").read()
            mime = "image/jpeg"
        finally:
            os.unlink(tmp_path)

    body = {
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": question},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{base64.b64encode(data).decode()}"}},
            ],
        }],
        "max_tokens": MAX_TOKENS,
    }
    req = urllib.request.Request(
        BASE_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"lov-describe-image: 视觉 API 返回 HTTP {e.code}: {e.read().decode()[:500]}", file=sys.stderr)
        return 1
    except Exception as e:  # 网络/超时/解析
        print(f"lov-describe-image: 请求失败: {e}", file=sys.stderr)
        return 1

    content = payload.get("choices", [{}])[0].get("message", {}).get("content")
    if content is None:
        print(f"lov-describe-image: 视觉 API 返回空响应: {json.dumps(payload, ensure_ascii=False)[:300]}", file=sys.stderr)
        return 1
    text = "".join(p.get("text", "") for p in content) if isinstance(content, list) else str(content)
    if not text.strip():
        print("lov-describe-image: 视觉 API 返回了空文本", file=sys.stderr)
        return 1
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
