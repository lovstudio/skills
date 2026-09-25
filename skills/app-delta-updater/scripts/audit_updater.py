#!/usr/bin/env python3
"""Audit Tauri or Electron updater wiring without reading secrets.

This is a static readiness check. It verifies local wiring and deliberately does
not treat a passing result as proof that a public feed or an installed older
version completed an update.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
import re
from pathlib import Path
from typing import Any, Iterable


IGNORED_DIRECTORIES = frozenset(
    {
        ".git",
        ".next",
        ".turbo",
        ".venv",
        ".worktrees",
        "build",
        "coverage",
        "dist",
        "node_modules",
        "out",
        "release",
        "target",
        "vendor",
    }
)
SOURCE_SUFFIXES = frozenset({".cjs", ".js", ".jsx", ".mjs", ".ts", ".tsx"})
MAX_SOURCE_FILE_BYTES = 1_000_000
PLACEHOLDER_RE = re.compile(r"(?:example|placeholder|replace|todo|your[-_ ]|changeme)", re.I)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(read_text(path))
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def iter_source_files(root: Path, suffixes: frozenset[str]) -> Iterable[Path]:
    """Yield bounded source files while skipping dependencies and build output."""
    if not root.is_dir():
        return
    for directory, children, names in os.walk(root):
        children[:] = [name for name in children if name not in IGNORED_DIRECTORIES]
        for name in names:
            path = Path(directory) / name
            if path.suffix.lower() not in suffixes:
                continue
            try:
                if path.stat().st_size > MAX_SOURCE_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield path


def source_text(root: Path, suffixes: frozenset[str]) -> str:
    return "\n".join(read_text(path) for path in iter_source_files(root, suffixes))


def add(checks: list[dict[str, str]], check_id: str, ok: bool, detail: str) -> None:
    checks.append({"id": check_id, "status": "pass" if ok else "fail", "detail": detail})


def add_info(checks: list[dict[str, str]], check_id: str, detail: str) -> None:
    checks.append({"id": check_id, "status": "info", "detail": detail})


def configured_endpoint(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    endpoint = value.strip()
    return bool(endpoint and endpoint.startswith("https://") and not PLACEHOLDER_RE.search(endpoint))


def configured_tauri_public_key(value: Any) -> bool:
    """Recognize Tauri's base64-encoded Minisign public-key payload.

    The check intentionally accepts only public-key-shaped data and never opens
    private key files or environment variables.
    """
    if not isinstance(value, str):
        return False
    encoded = "".join(value.split())
    if len(encoded) < 64 or PLACEHOLDER_RE.search(encoded):
        return False
    try:
        decoded = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        return False
    return b"minisign public key" in decoded.lower()


def capability_values(directory: Path) -> list[str]:
    values: list[str] = []
    for path in directory.glob("*.json"):
        value = read_json(path)
        stack: list[Any] = [value]
        while stack:
            current = stack.pop()
            if isinstance(current, str):
                values.append(current)
            elif isinstance(current, list):
                stack.extend(current)
            elif isinstance(current, dict):
                stack.extend(current.values())
    return values


def has_tauri_runtime_check(source: str) -> bool:
    return "@tauri-apps/plugin-updater" in source and bool(
        re.search(r"\b(?:check|checkForUpdate)\s*\(", source)
    )


def has_tauri_restart_handoff(source: str) -> bool:
    return "@tauri-apps/plugin-process" in source and bool(re.search(r"\brelaunch\s*\(", source))


def audit_tauri(root: Path) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    package = read_json(root / "package.json")
    dependencies = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    cargo = read_text(root / "src-tauri" / "Cargo.toml")
    config = read_json(root / "src-tauri" / "tauri.conf.json")
    capabilities = capability_values(root / "src-tauri" / "capabilities")
    rust_sources = source_text(root / "src-tauri" / "src", frozenset({".rs"}))
    frontend_sources = source_text(root, SOURCE_SUFFIXES)
    workflows = source_text(root / ".github" / "workflows", frozenset({".yaml", ".yml"}))
    bundle = config.get("bundle", {})
    updater = config.get("plugins", {}).get("updater", {})
    endpoints = updater.get("endpoints", []) if isinstance(updater, dict) else []

    add(checks, "js-updater", "@tauri-apps/plugin-updater" in dependencies, "JavaScript updater binding")
    add(checks, "js-process", "@tauri-apps/plugin-process" in dependencies, "JavaScript relaunch binding")
    add(checks, "rust-updater", "tauri-plugin-updater" in cargo, "Rust updater plugin")
    add(checks, "rust-process", "tauri-plugin-process" in cargo, "Rust process plugin")
    add(
        checks,
        "runtime-registration",
        bool(re.search(r"\.plugin\s*\(\s*tauri_plugin_updater", rust_sources))
        and bool(re.search(r"\.plugin\s*\(\s*tauri_plugin_process", rust_sources)),
        "Runtime plugins registered",
    )
    add(
        checks,
        "runtime-check",
        has_tauri_runtime_check(frontend_sources),
        "Runtime check invokes the JavaScript updater binding",
    )
    add(
        checks,
        "restart-handoff",
        has_tauri_restart_handoff(frontend_sources),
        "Runtime uses the process plugin to relaunch after installation",
    )
    add(
        checks,
        "capabilities",
        any(value.startswith("updater:") for value in capabilities)
        and any(value.startswith("process:") for value in capabilities),
        "Updater and process capabilities",
    )
    add(checks, "signed-artifacts", bundle.get("createUpdaterArtifacts") is True, "Signed updater artifacts enabled")
    add(
        checks,
        "endpoint",
        isinstance(endpoints, list) and any(configured_endpoint(endpoint) for endpoint in endpoints),
        "HTTPS updater endpoint configured without a placeholder",
    )
    add(
        checks,
        "public-key",
        configured_tauri_public_key(updater.get("pubkey") if isinstance(updater, dict) else None),
        "Non-placeholder Minisign updater public key configured",
    )
    add(checks, "ci-signing", "TAURI_SIGNING_PRIVATE_KEY" in workflows, "CI references updater signing secret")
    add(
        checks,
        "manifest",
        "uploadUpdaterJson" in workflows
        or ("latest.json" in workflows and ("gh release upload" in workflows or "tauri-action" in workflows)),
        "Release workflow includes an updater manifest publication path",
    )
    return checks


def audit_electron(root: Path) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    package = read_json(root / "package.json")
    dependencies = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    source = source_text(root, SOURCE_SUFFIXES)
    package_text = json.dumps(package)

    updater_dependency = any(name in dependencies for name in ("electron-updater", "update-electron-app"))
    add(checks, "updater-dependency", updater_dependency, "Electron updater dependency")
    add(
        checks,
        "runtime-check",
        "checkForUpdates" in source or "autoUpdater" in source,
        "Runtime update check",
    )
    add(checks, "publish-config", "publish" in package_text, "Packager publish configuration")
    add(checks, "artifact-signing", any(token in package_text for token in ("afterSign", "notarize", "identity")), "Signing or notarization hook")
    if any(token in package_text + source for token in ("appcast", "blockmap", ".delta")):
        add_info(checks, "delta-metadata", "Delta-capable metadata detected; verify its source-version contract at release time")
    else:
        add_info(checks, "delta-metadata", "No delta metadata detected; report this as signed full-package updating, not a failed updater")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    root = args.project.expanduser().resolve()

    if (root / "src-tauri" / "tauri.conf.json").is_file():
        framework = "tauri"
        checks = audit_tauri(root)
    elif (root / "package.json").is_file() and "electron" in read_text(root / "package.json").lower():
        framework = "electron"
        checks = audit_electron(root)
    else:
        framework = "unknown"
        checks = []

    failed = sum(check["status"] == "fail" for check in checks)
    passed = sum(check["status"] == "pass" for check in checks)
    info = sum(check["status"] == "info" for check in checks)
    result = {"framework": framework, "checks": checks, "passed": passed, "info": info, "failed": failed}
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"framework={framework} passed={passed} info={info} failed={failed}")
        for check in checks:
            print(f"{check['status'].upper():4} {check['id']}: {check['detail']}")
    return 0 if framework != "unknown" and failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
