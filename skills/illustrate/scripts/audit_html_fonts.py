#!/usr/bin/env python3
"""Audit the actual platform fonts used by declared text runs in Chromium."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit actual Chromium platform fonts for selectors in a local HTML file."
    )
    parser.add_argument("--html", required=True, help="Absolute HTML path or http(s) URL")
    parser.add_argument("--spec", required=True, help="JSON file containing a runs array")
    parser.add_argument("--output", help="Optional JSON receipt path")
    parser.add_argument("--browser-channel", default="chrome", help="Playwright browser channel")
    parser.add_argument("--timeout-ms", type=int, default=30_000)
    return parser.parse_args()


def emit(payload: dict[str, Any], output: str | None) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output:
        Path(output).expanduser().resolve().write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)


def document_url(value: str) -> str:
    if value.startswith(("http://", "https://", "file://")):
        return value
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"HTML file not found: {path}")
    return path.as_uri()


def main() -> int:
    args = parse_args()
    spec_path = Path(args.spec).expanduser().resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    runs = spec.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("spec.runs must be a non-empty array")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        payload = {
            "schemaVersion": "lov-illustrate-font-audit/v1",
            "ok": False,
            "error": "Playwright is required for Chromium platform-font introspection",
        }
        emit(payload, args.output)
        raise SystemExit(2) from exc

    url = document_url(args.html)
    results: list[dict[str, Any]] = []
    violations: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=args.browser_channel, headless=True)
        page = browser.new_page()
        page.set_default_timeout(args.timeout_ms)
        page.goto(url, wait_until="load")
        page.evaluate("document.fonts.ready")
        cdp = page.context.new_cdp_session(page)
        cdp.send("DOM.enable")
        cdp.send("CSS.enable")
        root_id = cdp.send("DOM.getDocument", {"depth": -1})["root"]["nodeId"]

        for index, run in enumerate(runs):
            selector = run.get("selector")
            if not isinstance(selector, str) or not selector:
                violations.append(f"runs[{index}].selector is required")
                continue

            locator = page.locator(selector)
            count = locator.count()
            if count != 1:
                violations.append(f"{selector}: expected exactly one node, found {count}")
                results.append({"selector": selector, "nodeCount": count, "ok": False})
                continue

            node_id = cdp.send(
                "DOM.querySelector", {"nodeId": root_id, "selector": selector}
            )["nodeId"]
            fonts = cdp.send("CSS.getPlatformFontsForNode", {"nodeId": node_id})["fonts"]
            actual_families = sorted({font["familyName"] for font in fonts})
            effective_lang = locator.evaluate(
                "el => el.closest('[lang]')?.getAttribute('lang') || document.documentElement.lang || ''"
            )
            allowed = run.get("allowedFamilies", [])
            max_families = int(run.get("maxFamilies", 1))
            expected_lang = run.get("lang")
            run_violations: list[str] = []

            if expected_lang and effective_lang.lower() != str(expected_lang).lower():
                run_violations.append(
                    f"effective lang {effective_lang!r} does not match {expected_lang!r}"
                )
            if len(actual_families) > max_families:
                run_violations.append(
                    f"used {len(actual_families)} families, maximum is {max_families}"
                )
            unexpected = [family for family in actual_families if family not in allowed]
            if unexpected:
                run_violations.append(f"unexpected families: {', '.join(unexpected)}")

            for message in run_violations:
                violations.append(f"{selector}: {message}")
            results.append(
                {
                    "selector": selector,
                    "lang": effective_lang,
                    "allowedFamilies": allowed,
                    "maxFamilies": max_families,
                    "fonts": [
                        {
                            "familyName": font["familyName"],
                            "postScriptName": font["postScriptName"],
                            "glyphCount": font["glyphCount"],
                            "isCustomFont": font["isCustomFont"],
                        }
                        for font in fonts
                    ],
                    "ok": not run_violations,
                }
            )
        browser.close()

    payload = {
        "schemaVersion": "lov-illustrate-font-audit/v1",
        "ok": not violations,
        "document": url,
        "spec": str(spec_path),
        "runs": results,
        "violations": violations,
    }
    emit(payload, args.output)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        sys.stderr.write(f"audit_html_fonts: {exc}\n")
        raise SystemExit(2) from exc
