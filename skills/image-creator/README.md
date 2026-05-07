# lovstudio:image-creator

![Version](https://img.shields.io/badge/version-0.2.1-CC785C)

Generate images through the right mechanism: end-to-end AI generation, code-rendered layouts, or optimized prompts for external image models.

Part of [lovstudio general skills](https://github.com/lovstudio/general-skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx lovstudio skills add image-creator -g -y
```

## Usage

End-to-end generation through ZenMux/Gemini:

```bash
python3 gen_image.py "a warm academic poster for an AI workshop" -o poster.png -q medium
```

Render an HTML layout to PNG:

```bash
python3 scripts/render_to_png.py poster.html -o poster.png -W 1200 -H 630 --scale 2
```

Use the prompt mechanism when the user wants a Midjourney, nano-banana-pro, or other external image-model prompt instead of a local file.

## Configuration

Set `ZENMUX_API_KEY` for end-to-end image generation. `gen_image.py` installs `google-genai` and `Pillow` into the user Python environment if they are missing.

Code rendering requires Playwright Python:

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
```

## Output

Write generated files to the current project or a user-provided output path, then report the absolute path.

## License

MIT
