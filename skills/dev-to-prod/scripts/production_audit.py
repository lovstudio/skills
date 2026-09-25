#!/usr/bin/env python3
"""Create a small, read-only production-readiness baseline for a project."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def read_toml_version(path: Path) -> str | None:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            normalized = line.strip()
            if normalized.startswith("version") and "=" in normalized:
                value = normalized.split("=", 1)[1].strip().strip('"')
                return value or None
    except OSError:
        return None
    return None


def git_state(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except (OSError, subprocess.SubprocessError):
        return "not-a-git-worktree-or-unavailable"
    if result.returncode != 0:
        return "not-a-git-worktree-or-unavailable"
    return "clean" if not result.stdout.strip() else "has-local-changes"


def check(identifier: str, status: str, detail: str) -> dict[str, str]:
    return {"id": identifier, "status": status, "detail": detail}


def project_report(root: Path) -> dict[str, Any]:
    package_path = root / "package.json"
    cargo_path = root / "src-tauri" / "Cargo.toml"
    tauri_paths = (
        root / "src-tauri" / "tauri.conf.json",
        root / "src-tauri" / "tauri.conf.json5",
    )
    package = read_json(package_path)
    tauri_path = next((path for path in tauri_paths if path.is_file()), None)
    tauri = read_json(tauri_path) if tauri_path else None

    checks: list[dict[str, str]] = []
    project_type = "unknown"
    versions: dict[str, str] = {}

    if package:
        project_type = "node"
        package_name = package.get("name")
        if isinstance(package_name, str) and package_name.strip():
            versions["package.json"] = str(package.get("version", "missing"))
        scripts = package.get("scripts") if isinstance(package.get("scripts"), dict) else {}
        build_scripts = [name for name in scripts if "build" in name.lower()]
        dev_scripts = [name for name in scripts if name == "dev" or name.startswith("dev:")]
        checks.append(
            check(
                "production-build-command",
                "pass" if build_scripts else "blocker",
                "Build scripts: " + ", ".join(sorted(build_scripts)) if build_scripts else "No build script found in package.json.",
            )
        )
        checks.append(
            check(
                "development-command",
                "pass" if dev_scripts else "warning",
                "Development scripts: " + ", ".join(sorted(dev_scripts)) if dev_scripts else "No explicit development script found.",
            )
        )

    if cargo_path.is_file():
        project_type = "tauri" if tauri_path else "rust"
        version = read_toml_version(cargo_path)
        if version:
            versions["Cargo.toml"] = version

    if tauri_path and tauri:
        product_name = tauri.get("productName")
        identifier = tauri.get("identifier")
        config_version = tauri.get("version")
        if isinstance(config_version, str) and config_version:
            versions[tauri_path.name] = config_version
        has_identity = isinstance(product_name, str) and isinstance(identifier, str) and bool(identifier)
        checks.append(
            check(
                "desktop-identity",
                "pass" if has_identity else "blocker",
                "Product name and bundle identifier are configured." if has_identity else "Tauri productName or identifier is missing.",
            )
        )
        build = tauri.get("build") if isinstance(tauri.get("build"), dict) else {}
        frontend_dist = build.get("frontendDist")
        checks.append(
            check(
                "packaged-frontend",
                "pass" if isinstance(frontend_dist, str) and frontend_dist else "blocker",
                "frontendDist is configured for a packaged frontend." if isinstance(frontend_dist, str) and frontend_dist else "frontendDist is missing from the Tauri build configuration.",
            )
        )
        plugins = tauri.get("plugins") if isinstance(tauri.get("plugins"), dict) else {}
        updater = plugins.get("updater") if isinstance(plugins.get("updater"), dict) else None
        if updater:
            public_key = updater.get("pubkey")
            endpoints = updater.get("endpoints")
            placeholder = isinstance(public_key, str) and "PLACEHOLDER" in public_key.upper()
            checks.append(
                check(
                    "updater-configuration",
                    "blocker" if placeholder else "pass",
                    "Updater public key contains a placeholder." if placeholder else "Updater configuration is present without an obvious public-key placeholder.",
                )
            )
            if not endpoints:
                checks.append(check("updater-endpoints", "warning", "Updater is configured without explicit endpoints."))

    if len(set(versions.values())) > 1:
        checks.append(
            check(
                "version-alignment",
                "warning",
                "Version sources differ: " + ", ".join(f"{name}={value}" for name, value in sorted(versions.items())),
            )
        )
    elif versions:
        checks.append(check("version-alignment", "pass", "Detected version sources agree."))
    else:
        checks.append(check("version-alignment", "warning", "No recognized version source was found."))

    lockfiles = [
        name
        for name in ("pnpm-lock.yaml", "package-lock.json", "yarn.lock", "bun.lock", "bun.lockb", "Cargo.lock")
        if (root / name).exists()
    ]
    checks.append(
        check(
            "dependency-lock",
            "pass" if lockfiles else "warning",
            "Detected lockfiles: " + ", ".join(lockfiles) if lockfiles else "No recognized dependency lockfile found.",
        )
    )

    return {
        "schema": "lov-dev-to-prod/production-audit/v1",
        "project": root.name,
        "project_type": project_type,
        "git_state": git_state(root),
        "versions": versions,
        "checks": checks,
        "summary": {
            "pass": sum(item["status"] == "pass" for item in checks),
            "warning": sum(item["status"] == "warning" for item in checks),
            "blocker": sum(item["status"] == "blocker" for item in checks),
        },
    }


def to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Production readiness baseline",
        "",
        f"- Project: `{report['project']}`",
        f"- Detected type: `{report['project_type']}`",
        f"- Git state: `{report['git_state']}`",
    ]
    versions = report["versions"]
    if versions:
        lines.append("- Version sources: " + ", ".join(f"`{name}` = `{value}`" for name, value in sorted(versions.items())))
    lines.extend(["", "| Check | Status | Detail |", "| --- | --- | --- |"])
    for item in report["checks"]:
        lines.append(f"| {item['id']} | {item['status']} | {item['detail']} |")
    summary = report["summary"]
    lines.extend(
        [
            "",
            f"Summary: {summary['pass']} pass, {summary['warning']} warning, {summary['blocker']} blocker.",
            "",
            "This is a read-only baseline. A passing audit is not production-artifact proof; run the target build and native verification next.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."), help="Target project root")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--output", type=Path, help="Optional report file")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when blockers are found")
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print("ERROR: project root is not a directory", file=sys.stderr)
        return 2

    report = project_report(root)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else to_markdown(report)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 1 if args.strict and report["summary"]["blocker"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
