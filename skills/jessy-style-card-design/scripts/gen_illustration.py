#!/usr/bin/env python3
"""Generate a text-free decorative illustration through OpenRouter image models.

Only decor goes through a generator: logos, names, QR codes and other identity
marks are always official files placed by the renderer.

usage: gen_illustration.py (--prompt TEXT | --prompt-file FILE) --out RAW.png
                           [--model ID] [--aspect 3:2] [--retries 3] [--force]

Requires OPENROUTER_API_KEY in the environment. The key is never printed.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("JESSY_CARD_IMAGE_MODEL", "openai/gpt-5.4-image-2")


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a text-free decor illustration via OpenRouter.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--prompt")
    src.add_argument("--prompt-file")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--aspect", default="3:2", help="image_config.aspect_ratio, e.g. 3:2, 1:1, 2:3")
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print(json.dumps({"status": "error", "error": "OPENROUTER_API_KEY is not set"}))
        return 1
    out = Path(args.out)
    if out.exists() and not args.force:
        print(json.dumps({"status": "refused", "reason": "output exists; pass --force", "file": out.name}))
        return 2
    prompt = args.prompt if args.prompt else Path(args.prompt_file).read_text(encoding="utf-8").strip()
    body = {"model": args.model, "messages": [{"role": "user", "content": prompt}],
            "modalities": ["image", "text"], "image_config": {"aspect_ratio": args.aspect}}
    request = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(),
                                     headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    for attempt in range(1, max(1, args.retries) + 1):
        try:
            with urllib.request.urlopen(request, timeout=300) as resp:
                data = json.load(resp)
            url = data["choices"][0]["message"]["images"][0]["image_url"]["url"]
            raw = base64.b64decode(url.split(",", 1)[1])
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(raw)
            print(json.dumps({"status": "saved", "out": str(out), "bytes": len(raw), "model": args.model,
                              "attempt": attempt}))
            return 0
        except urllib.error.HTTPError as exc:
            detail = exc.read()[:300].decode("utf-8", "replace")
            print(json.dumps({"status": "http_error", "code": exc.code, "attempt": attempt, "body": detail}))
            if exc.code in (400, 401, 402, 403, 404):
                return 1
        except (KeyError, IndexError, ValueError) as exc:
            print(json.dumps({"status": "no_image", "attempt": attempt, "error": str(exc)[:200]}))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(json.dumps({"status": "network_error", "attempt": attempt, "error": str(exc)[:200]}))
        time.sleep(3 * attempt)
    return 1


if __name__ == "__main__":
    sys.exit(main())
