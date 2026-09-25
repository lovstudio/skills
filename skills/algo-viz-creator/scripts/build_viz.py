#!/usr/bin/env python3
"""Merge a lov-algo-viz-creator step model JSON into the engine template -> standalone HTML.

Usage:
    python3 scripts/build_viz.py model.json -o output/demo.html

Reads the model, validates it (errors abort), substitutes the JSON into
assets/template.html, and writes a self-contained file that opens directly
in a browser. No npm, no build step, no external CDN.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from validate_viz import validate_model
except ImportError:  # allow running from any cwd
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from validate_viz import validate_model  # type: ignore


def _template_path() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "template.html"


def build(model_path: Path, output_path: Path, *, strict: bool = False) -> None:
    try:
        with open(model_path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read {model_path}: {exc}", file=sys.stderr)
        raise SystemExit(2)

    errors, warnings = validate_model(data)
    for warning in warnings:
        print(f"WARN  {warning}")
    for error in errors:
        print(f"ERROR {error}")
    if errors or (strict and warnings):
        print("validation failed; aborting build", file=sys.stderr)
        raise SystemExit(1)

    template = _template_path()
    if not template.exists():
        print(f"ERROR: engine template missing: {template}", file=sys.stderr)
        raise SystemExit(2)
    html = template.read_text(encoding="utf-8")

    # Embed the model as a JS object literal. Escape "</" so a note containing
    # "</script>" cannot break out of the inline script (\/ is a valid JSON escape).
    payload = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")

    marker = "__MODEL_JSON__"
    if marker not in html:
        print(f"ERROR: template marker {marker!r} not found in {template}", file=sys.stderr)
        raise SystemExit(2)
    html = html.replace(marker, payload)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"built={output_path} ({output_path.stat().st_size} bytes, {len(data['frames'])} frames)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", help="path to the step model JSON")
    parser.add_argument("-o", "--output", default="", help="output HTML path (default: ./output/<model>.html)")
    parser.add_argument("--strict", action="store_true", help="fail on warnings too")
    args = parser.parse_args()

    model_path = Path(args.model)
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path.cwd() / "output" / f"{model_path.stem}.html"

    build(model_path, output_path, strict=args.strict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
