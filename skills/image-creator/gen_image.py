#!/usr/bin/env python3
"""Optional legacy Vertex-compatible adapter; prefer native host image tools."""
import argparse
import io
import os
from pathlib import Path
import sys


def generate_image(prompt, output_file, quality="high", show_ascii=False, model=None):
    model = model or os.environ.get("ZENMUX_IMAGE_MODEL")
    if not model:
        raise ValueError("provide --model or ZENMUX_IMAGE_MODEL after checking current provider availability")
    api_key = os.environ.get("ZENMUX_API_KEY")
    if not api_key:
        raise ValueError("ZENMUX_API_KEY is not configured")
    output = Path(output_file)
    if output.exists() or output.is_symlink():
        raise ValueError("output already exists; choose a new filename")
    try:
        from google import genai
        from google.genai import types
        from PIL import Image
    except ImportError as exc:
        raise ValueError("install google-genai and Pillow in the selected project environment") from exc
    client = genai.Client(api_key=api_key, vertexai=True,
        http_options=types.HttpOptions(api_version="v1",
            base_url="https://zenmux.ai/api/vertex-ai"))
    resolutions = {"low": types.MediaResolution.MEDIA_RESOLUTION_LOW,
                   "medium": types.MediaResolution.MEDIA_RESOLUTION_MEDIUM,
                   "high": types.MediaResolution.MEDIA_RESOLUTION_HIGH}
    response = client.models.generate_content(model=model, contents=[prompt],
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"],
            media_resolution=resolutions[quality]))
    for part in response.parts or []:
        if part.inline_data is None:
            continue
        data = part.inline_data.data
        with Image.open(io.BytesIO(data)) as generated:
            generated.load()
            width, height = generated.size
            fmt = generated.format
            if output.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                raise ValueError("choose a PNG, JPEG or WebP output suffix")
            formats = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".webp": "WEBP"}
            target_format = formats[output.suffix.lower()]
            if target_format != fmt:
                converted = io.BytesIO()
                (generated.convert("RGB") if target_format == "JPEG" else generated).save(converted, format=target_format)
                data = converted.getvalue()
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("xb") as file:
                file.write(data)
            if show_ascii:
                preview = generated.convert("L").resize((60, max(1, round(height / width * 30))))
                chars = "@#S%?*+;:,."
                pixels = list(preview.getdata())
                print("\n".join("".join(chars[v * (len(chars)-1) // 255] for v in pixels[i:i+60]) for i in range(0,len(pixels),60)))
        print("saved=" + str(output.resolve()))
        print("dimensions=" + str(width) + "x" + str(height))
        return
    raise ValueError("provider returned no image")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt")
    parser.add_argument("-o", "--output", default="generated_image.png")
    parser.add_argument("--model", help="Currently available Vertex-compatible image model")
    parser.add_argument("-q", "--quality", choices=["low", "medium", "high"], default="high")
    parser.add_argument("--ascii", action="store_true")
    args = parser.parse_args()
    try:
        generate_image(args.prompt,args.output,args.quality,args.ascii,args.model)
    except ValueError as exc:
        print("ERROR: " + str(exc),file=sys.stderr)
        return 1
    except Exception as exc:
        print("ERROR: image provider request failed (" + type(exc).__name__ + "); inspect provider status without logging credentials",file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
