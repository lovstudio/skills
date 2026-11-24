#!/usr/bin/env python3
"""Draw an original chibi cartoon of a real person from their photo via OpenRouter.

Only the person's photo is uploaded. The reference character (e.g. a cartoon IP)
is never sent; its pose is described in text so the model cannot copy it.
Every call (ok or failed) is appended to a JSONL cost ledger.
"""
import argparse
import base64
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-5.4-image-2"
# Observed per-image cost for DEFAULT_MODEL at 1:1 with one reference photo.
QUOTE_USD = (0.17, 0.25)

PROMPT = """Draw an ORIGINAL cute chibi cartoon character based on the real person in the attached photo.
Keep their recognizable traits: {features}.
Pose: {pose}.
Style: {style}.
Full body, centered, the character fills about 80% of the image height, plain {background} background, flat colors, clean outlines.
Hard rules: this is a new original character, NOT any existing cartoon, anime, mascot or brand character;
do not imitate any copyrighted character design; no text, letters, numbers, logos, watermarks or speech bubbles."""


def encode_photo(path: Path, max_edge: int) -> str:
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow is required: python3 -m pip install Pillow")
    img = Image.open(path).convert("RGB")
    img.thumbnail((max_edge, max_edge))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode()


def log_cost(ledger: Path, item: str, model: str, status: str, cost, note: str = "") -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    row = {"time": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "service": "openrouter", "model": model,
           "item": item, "status": status, "cost_usd": cost}
    if note:
        row["note"] = note[:300]
    with ledger.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--photo", type=Path, help="Real person photo or video frame (uploaded to OpenRouter)")
    ap.add_argument("--pose", default="standing, facing the viewer, arms relaxed",
                    help="Pose to mimic, described in words (never upload the reference character)")
    ap.add_argument("--features", default="face shape, hairstyle, hat and clothing colors",
                    help="Traits to keep, e.g. 'yellow raincoat, round glasses, curly brown hair'")
    ap.add_argument("--style", default="Chinese sticker-style Q-version illustration, soft pastel, big head small body")
    ap.add_argument("--background", default="light grey")
    ap.add_argument("--out", type=Path, help="Output PNG path")
    ap.add_argument("--item", default="cartoon", help="Ledger item label")
    ap.add_argument("--ledger", type=Path, default=Path("ledger/costs.jsonl"))
    ap.add_argument("--model", default=os.environ.get("LOOKALIKE_MEME_MODEL", DEFAULT_MODEL))
    ap.add_argument("--aspect", default="1:1")
    ap.add_argument("--max-edge", type=int, default=1024, help="Downscale photo before upload")
    ap.add_argument("--quote", action="store_true", help="Print the cost estimate and exit without calling")
    ap.add_argument("--print-prompt", action="store_true", help="Print the prompt and exit")
    args = ap.parse_args()

    prompt = PROMPT.format(features=args.features, pose=args.pose, style=args.style, background=args.background)
    if args.quote:
        print(json.dumps({"model": args.model, "calls": 1, "est_usd_per_call": list(QUOTE_USD),
                          "uploads": "person photo only"}, ensure_ascii=False))
        return 0
    if args.print_prompt:
        print(prompt)
        return 0
    if not args.photo or not args.out:
        ap.error("--photo and --out are required unless --quote/--print-prompt")
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set")

    body = {"model": args.model, "modalities": ["image", "text"], "image_config": {"aspect_ratio": args.aspect},
            "max_tokens": 8000,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + encode_photo(args.photo, args.max_edge)}}]}]}
    req = urllib.request.Request(API_URL, data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        resp = json.load(urllib.request.urlopen(req, timeout=300))
        cost = resp.get("usage", {}).get("cost")
        images = resp["choices"][0]["message"].get("images") or []
        if not images:
            log_cost(args.ledger, args.item, args.model, "no-image", cost,
                     str(resp["choices"][0]["message"].get("content", "")))
            sys.exit("model returned no image (likely refused); see ledger note")
        url = images[0]["image_url"]["url"]
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(base64.b64decode(url.split(",", 1)[1]))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        log_cost(args.ledger, args.item, args.model, f"http-{exc.code}", None, detail)
        sys.exit(f"OpenRouter HTTP {exc.code}: {detail[:500]}")
    except Exception as exc:  # transport errors: the call may still be billed
        log_cost(args.ledger, args.item, args.model, "transport-error", None, repr(exc))
        sys.exit(f"request failed ({exc!r}); logged with unknown cost, not retried automatically")
    log_cost(args.ledger, args.item, args.model, "ok", cost)
    print(json.dumps({"out": str(args.out), "cost_usd": cost, "ledger": str(args.ledger)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
