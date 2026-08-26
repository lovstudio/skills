#!/usr/bin/env python3
"""Audit a project against the Skill Publisher app baseline."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


TEXT_EXTENSIONS = {
    ".json",
    ".json5",
    ".toml",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".css",
    ".md",
    ".pbxproj",
    ".plist",
    ".swift",
    ".yml",
    ".yaml",
}

LEGACY_INSPECTOR_DEPENDENCIES = {
    "code-inspector-plugin",
    "@aspect/code-inspector-plugin",
}

VITE_FRAMEWORK_PLUGIN_PATTERN = re.compile(
    r"\b(?:react|vue|svelte|solid|preact|qwik|astro)\s*\(",
    re.IGNORECASE,
)


@dataclass
class Check:
    id: str
    title: str
    status: str
    detail: str
    recommendation: str


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def load_json_file(path: Path) -> dict:
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError:
        return {}


def load_package_json(root: Path) -> dict:
    package_path = root / "package.json"
    if not package_path.exists():
        return {}
    try:
        return json.loads(read_text(package_path))
    except json.JSONDecodeError:
        return {}


def dependencies(package: dict) -> dict:
    merged = {}
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        value = package.get(key)
        if isinstance(value, dict):
            merged.update(value)
    return merged


def file_exists(root: Path, patterns: Iterable[str]) -> bool:
    for pattern in patterns:
        if any(root.glob(pattern)):
            return True
    return False


def find_files(root: Path, patterns: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        files.extend(root.glob(pattern))
    return sorted({p.resolve() for p in files if p.is_file()})


def contains_text(paths: Iterable[Path], needles: Iterable[str]) -> bool:
    lower_needles = [needle.lower() for needle in needles]
    for path in paths:
        text = read_text(path).lower()
        if any(needle in text for needle in lower_needles):
            return True
    return False


def has_truthy_setting(paths: Iterable[Path], key: str) -> bool:
    """Recognize a true plist/xcconfig-style boolean without treating false as present."""
    escaped_key = re.escape(key)
    xml_pattern = re.compile(
        rf"<key>\s*{escaped_key}\s*</key>\s*<true\s*/>",
        re.IGNORECASE | re.DOTALL,
    )
    assignment_pattern = re.compile(
        rf"\b(?:INFOPLIST_KEY_)?{escaped_key}\b\s*=\s*(?:YES|true|1)\s*;?",
        re.IGNORECASE,
    )
    for path in paths:
        text = read_text(path)
        if xml_pattern.search(text) or assignment_pattern.search(text):
            return True
    return False


def has_narrow_activation_rule(paths: Iterable[Path]) -> bool:
    """Require a typed/count-limited activation rule rather than TRUEPREDICATE."""
    for path in paths:
        text = read_text(path)
        if "NSExtensionActivationRule" not in text or "TRUEPREDICATE" in text.upper():
            continue
        if re.search(r"NSExtensionActivationSupports\w+WithMaxCount", text) or any(
            marker in text
            for marker in ("UTI-CONFORMS-TO", "registeredTypeIdentifiers", "contentType")
        ):
            return True
    return False


def has_embedded_app_extension(paths: Iterable[Path]) -> bool:
    """Detect an Xcode app-extension product in an extension embedding build phase."""
    for path in paths:
        text = read_text(path)
        has_appex = ".appex" in text
        has_embed_phase = bool(
            re.search(r"Embed (?:App|Foundation) Extensions", text, re.IGNORECASE)
            or re.search(r"dstSubfolderSpec\s*=\s*13\s*;", text)
        )
        if has_appex and has_embed_phase:
            return True
    return False


def search_text(root: Path, needles: Iterable[str], max_files: int = 300) -> bool:
    lower_needles = [needle.lower() for needle in needles]
    count = 0
    for path in root.rglob("*"):
        if count >= max_files:
            break
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        parts = set(path.parts)
        if {"node_modules", "target", "dist", "build"} & parts:
            continue
        count += 1
        text = read_text(path).lower()
        if any(needle in text for needle in lower_needles):
            return True
    return False


def vite_lovinsp_order(paths: Iterable[Path]) -> tuple[bool, bool]:
    """Return (lovinsp_call_found, order_valid) for Vite plugin arrays."""
    found = False
    for path in paths:
        if not path.name.startswith("vite.config"):
            continue
        text = read_text(path)
        plugins_match = re.search(r"\bplugins\s*:\s*\[", text)
        if not plugins_match:
            continue
        plugin_section = text[plugins_match.end() :]
        lovinsp_match = re.search(r"\blovinspPlugin\s*\(", plugin_section)
        if not lovinsp_match:
            continue
        found = True
        framework_match = VITE_FRAMEWORK_PLUGIN_PATTERN.search(plugin_section)
        if framework_match and lovinsp_match.start() > framework_match.start():
            return True, False
    return found, found


def status(ok: bool) -> str:
    return "ok" if ok else "missing"


def audit(root: Path, app_type: str = "auto", native_integration: str = "auto") -> dict:
    root = root.resolve()
    package = load_package_json(root)
    deps = dependencies(package)
    src_tauri = root / "src-tauri"

    tauri_conf = find_files(
        root,
        [
            "src-tauri/tauri.conf.json",
            "src-tauri/tauri.conf.json5",
            "src-tauri/Tauri.toml",
        ],
    )
    workflows = find_files(root, [".github/workflows/*.yml", ".github/workflows/*.yaml"])
    xcode_project_files = find_files(root, ["*.xcodeproj/project.pbxproj", "**/*.xcodeproj/project.pbxproj"])
    plist_files = find_files(root, ["Info.plist", "**/Info.plist"])
    native_config_files = sorted({*xcode_project_files, *plist_files})
    css_files = find_files(
        root,
        [
            "src/index.css",
            "src/App.css",
            "app/globals.css",
            "src/app/globals.css",
            "styles/globals.css",
            "src/styles/*.css",
        ],
    )
    build_config_files = find_files(
        root,
        [
            "vite.config.ts",
            "vite.config.js",
            "vite.config.mts",
            "webpack.config.ts",
            "webpack.config.js",
            "next.config.ts",
            "next.config.js",
            "next.config.mjs",
            "nuxt.config.ts",
            "nuxt.config.js",
        ],
    )
    local_instruction_files = find_files(root, ["AGENTS.md", "CLAUDE.md", "tailwind.config.ts", "tailwind.config.js"])

    has_tauri = src_tauri.exists() or "@tauri-apps/api" in deps or "@tauri-apps/cli" in deps
    has_native_macos_project = bool(xcode_project_files)
    has_action_extension_target = contains_text(
        xcode_project_files,
        ["com.apple.product-type.app-extension"],
    )
    has_finder_preview_flag = has_truthy_setting(
        native_config_files,
        "NSExtensionServiceAllowsFinderPreviewItem",
    )
    has_activation_rule = has_narrow_activation_rule(native_config_files)
    has_action_extension_point = contains_text(
        native_config_files,
        ["com.apple.services", "com.apple.ui-services"],
    )
    has_finder_label = contains_text(native_config_files, ["NSExtensionServiceFinderPreviewLabel"])
    has_finder_icon = contains_text(native_config_files, ["NSExtensionServiceFinderPreviewIconName"])
    has_embedded_extension = has_embedded_app_extension(xcode_project_files)
    has_nsservices = contains_text(plist_files, ["<key>NSServices</key>", "NSServices ="])
    has_finder_quick_action = (
        has_action_extension_target
        and has_finder_preview_flag
        and has_activation_rule
        and has_action_extension_point
    )
    has_react = "react" in deps
    has_vite = file_exists(root, ["vite.config.ts", "vite.config.js", "vite.config.mts"]) or "vite" in deps
    has_next = file_exists(root, ["next.config.ts", "next.config.js", "next.config.mjs"]) or "next" in deps
    target_app_type = app_type
    if target_app_type == "auto":
        if has_tauri:
            target_app_type = "tauri"
        elif has_native_macos_project:
            target_app_type = "macos"
        else:
            target_app_type = "web"
    include_tauri = target_app_type == "tauri"
    include_frontend = target_app_type in {"web", "tauri"}
    include_macos = target_app_type == "macos"
    target_native_integration = native_integration
    if target_native_integration == "auto":
        target_native_integration = "finder-quick-action" if (
            has_action_extension_target or has_finder_preview_flag
        ) else "none"
    include_finder_quick_action = target_native_integration == "finder-quick-action"
    has_shadcn = (root / "components.json").exists()
    has_tanstack = "@tanstack/react-query" in deps
    has_lucide = "lucide-react" in deps
    has_lovinsp_dependency = "lovinsp" in deps
    lovinsp_configured = contains_text(build_config_files, ["lovinspplugin", "@lovinsp/", "lovinsp"])
    vite_lovinsp_found, vite_lovinsp_order_ok = vite_lovinsp_order(build_config_files)
    if has_vite:
        lovinsp_configured = lovinsp_configured and vite_lovinsp_found
    legacy_lovinsp_dependencies = sorted(LEGACY_INSPECTOR_DEPENDENCIES & set(deps))
    legacy_lovinsp_config = contains_text(
        build_config_files,
        ["codeinspectorplugin", "code-inspector-plugin", "@aspect/code-inspector-plugin"],
    )
    legacy_lovinsp_remains = bool(legacy_lovinsp_dependencies or legacy_lovinsp_config)
    lovinsp_order_ok = vite_lovinsp_order_ok if has_vite else True
    has_lovinsp = (
        has_lovinsp_dependency
        and lovinsp_configured
        and lovinsp_order_ok
        and not legacy_lovinsp_remains
    )
    has_logo = file_exists(root, ["assets/logo.png", "assets/logo.svg", "public/logo.png", "public/logo.svg"])
    has_icons = file_exists(root, ["src-tauri/icons/icon.icns", "src-tauri/icons/icon.ico"])
    has_macos_app_icon = file_exists(
        root,
        ["**/Assets.xcassets/AppIcon.appiconset/Contents.json", "**/*.icns"],
    )
    has_ci = any(re.search(r"(check|ci|test|build)", p.name, re.I) for p in workflows)
    has_release = any(re.search(r"(release|tauri)", p.name, re.I) for p in workflows)
    has_web_deploy = (
        any(re.search(r"(deploy|vercel|netlify|pages|cloudflare|wrangler)", p.name, re.I) for p in workflows)
        or file_exists(
            root,
            [
                "vercel.json",
                "netlify.toml",
                "wrangler.toml",
                ".github/workflows/deploy*.yml",
                ".github/workflows/deploy*.yaml",
            ],
        )
    )
    has_updater = (
        "@tauri-apps/plugin-updater" in deps
        or (src_tauri.exists() and search_text(src_tauri, ["plugin-updater", "tauri_plugin_updater", "updater"]))
    )
    updater_pubkey = False
    for conf in tauri_conf:
        if conf.suffix.lower() == ".json":
            config = load_json_file(conf)
            pubkey = (
                config.get("plugins", {})
                .get("updater", {})
                .get("pubkey", "")
            )
            updater_pubkey = updater_pubkey or bool(str(pubkey).strip())
        else:
            text = read_text(conf)
            updater_pubkey = updater_pubkey or bool(re.search(r"pubkey\s*[:=]\s*['\"][^'\"]+", text))
    frontend_roots = [path for path in (root / "src", root / "app", root / "pages") if path.exists()]
    has_query_provider = has_tanstack and any(search_text(path, ["queryclientprovider"]) for path in frontend_roots)
    has_warm_academic = any(
        "--primary" in read_text(path)
        and ("--background" in read_text(path) or "bg-background" in read_text(path))
        for path in css_files
    ) or contains_text(local_instruction_files, ["warm academic", "cc785c", "skill-publisher"])

    checks: list[Check] = []
    if include_frontend:
        checks.extend(
            [
                Check(
                    "package",
                    "Package manifest",
                    status(bool(package)),
                    "package.json found" if package else "package.json not found",
                    (
                        "Create a React web package before app-layer setup, using Vite, "
                        "Next.js, or Tauri based on the selected app type."
                    ),
                ),
                Check(
                    "react-vite",
                    "React web baseline",
                    status(has_react and (has_vite or has_next)),
                    f"react={has_react}, vite={has_vite}, next={has_next}",
                    (
                        "Use Vite React for app-like workflows or Next.js for "
                        "SEO/SSR/content routing unless the target project already has "
                        "a stronger local convention."
                    ),
                ),
                Check(
                    "shadcn",
                    "shadcn/ui",
                    status(has_shadcn),
                    "components.json found" if has_shadcn else "components.json missing",
                    (
                        "Initialize shadcn/ui and map tokens to the Skill Publisher "
                        "Configurable Academic theme."
                    ),
                ),
                Check(
                    "warm-academic",
                    "Skill Publisher Configurable Academic UI",
                    status(has_warm_academic),
                    (
                        "theme tokens or Skill Publisher references detected"
                        if has_warm_academic
                        else "theme tokens not detected"
                    ),
                    (
                        "Read the Configurable Academic design guide from local workspace "
                        "config and use semantic Tailwind classes."
                    ),
                ),
                Check(
                    "tanstack-query",
                    "TanStack Query",
                    status(has_tanstack and has_query_provider),
                    f"dependency={has_tanstack}, provider={has_query_provider}",
                    (
                        "Add QueryClientProvider, stable query keys, and invoke/query "
                        "wrappers for server state."
                    ),
                ),
                Check(
                    "icons",
                    "Target-specific app logo and icons",
                    status(has_logo and (has_icons or not include_tauri)),
                    f"source_logo={has_logo}, tauri_icons={has_icons}, app_type={target_app_type}",
                    (
                        "For new apps, run lov-gen-logo to create assets/logo* and "
                        "public/logo*, then generate favicons/PWA icons or Tauri icons "
                        "based on app type."
                    ),
                ),
                Check(
                    "lucide",
                    "Lucide icons",
                    status(has_lucide),
                    "lucide-react dependency found" if has_lucide else "lucide-react missing",
                    "Use lucide-react for toolbar and action icons.",
                ),
                Check(
                    "lovinsp",
                    "Lovinsp default integration",
                    status(has_lovinsp),
                    (
                        f"dependency={has_lovinsp_dependency}, configured={lovinsp_configured}, "
                        f"order_ok={lovinsp_order_ok}, legacy_remains={legacy_lovinsp_remains}"
                    ),
                    (
                        "Run the lov-integrate-lovinsp skill to install or update Lovinsp, "
                        "migrate supported code-inspector integrations, and register "
                        "lovinspPlugin before the framework plugin."
                    ),
                ),
                Check(
                    "ci",
                    "CI workflow",
                    status(has_ci),
                    f"workflow_files={len(workflows)}",
                    (
                        "Add a GitHub Actions check workflow for install, typecheck, "
                        "lint/build where available."
                    ),
                ),
            ]
        )
    elif include_macos:
        checks.extend(
            [
                Check(
                    "macos-project",
                    "Native macOS project",
                    status(has_native_macos_project),
                    f"xcode_project_files={len(xcode_project_files)}",
                    "Create a signed macOS containing-app target in Xcode for the native extension.",
                ),
                Check(
                    "icons",
                    "Target-specific macOS app icon",
                    status(has_logo or has_macos_app_icon),
                    f"source_logo={has_logo}, app_icon={has_macos_app_icon}",
                    "Run lov-gen-logo and publish the selected asset into the macOS AppIcon set.",
                ),
                Check(
                    "ci",
                    "CI workflow",
                    status(has_ci),
                    f"workflow_files={len(workflows)}",
                    "Add a CI workflow that builds the containing app and Action Extension.",
                ),
            ]
        )
    if include_tauri:
        checks.extend(
            [
                Check(
                    "tauri",
                    "Tauri baseline",
                    status(has_tauri and bool(tauri_conf)),
                    f"src-tauri={src_tauri.exists()}, config_files={len(tauri_conf)}",
                    "Run Tauri init and configure title, identifier, windows, bundle metadata, and capabilities.",
                ),
                Check(
                    "release",
                    "Tauri release workflow",
                    status(has_release),
                    f"workflow_files={len(workflows)}",
                    "Add a Tauri release workflow that builds artifacts and attaches them to GitHub Releases.",
                ),
                Check(
                    "updater",
                    "Auto update",
                    status(has_updater and updater_pubkey),
                    f"updater={has_updater}, pubkey={updater_pubkey}",
                    "Wire @tauri-apps/plugin-updater / tauri_plugin_updater and include plugins.updater.pubkey, using a placeholder until the real signer public key exists.",
                ),
            ]
        )
    elif target_app_type == "web":
        checks.append(
            Check(
                "web-deploy",
                "Web deploy surface",
                status(has_web_deploy),
                f"workflow_files={len(workflows)}, deploy_config={has_web_deploy}",
                "Add a deploy workflow or config for the selected target, such as Vercel, Netlify, Cloudflare Pages, GitHub Pages, or documented static hosting.",
            )
        )

    if include_finder_quick_action:
        checks.extend(
            [
                Check(
                    "finder-action-extension-target",
                    "Finder Action Extension target",
                    status(has_action_extension_target),
                    f"xcode_project_files={len(xcode_project_files)}, action_extension_target={has_action_extension_target}",
                    "Add a macOS Action Extension target; an NSServices entry or Automator workflow is not a substitute.",
                ),
                Check(
                    "finder-quick-action-surface",
                    "Finder Quick Actions surface",
                    status(has_finder_quick_action),
                    (
                        f"finder_preview={has_finder_preview_flag}, activation_rule={has_activation_rule}, "
                        f"extension_point={has_action_extension_point}"
                    ),
                    (
                        "Set NSExtensionServiceAllowsFinderPreviewItem=YES, declare a narrow "
                        "NSExtensionActivationRule, and use com.apple.services or com.apple.ui-services."
                    ),
                ),
                Check(
                    "finder-quick-action-presentation",
                    "Finder Quick Action label and icon",
                    status(has_finder_label and has_finder_icon),
                    f"label={has_finder_label}, icon={has_finder_icon}",
                    "Provide a localized Finder preview label and template icon for the Quick Action.",
                ),
                Check(
                    "finder-quick-action-embedding",
                    "Embedded Action Extension",
                    status(has_embedded_extension),
                    f"embed_phase={has_embedded_extension}",
                    "Embed the signed .appex in the containing app's Contents/PlugIns build phase.",
                ),
                Check(
                    "finder-quick-action-not-service-only",
                    "Not a Service-only substitute",
                    status(has_finder_quick_action),
                    f"finder_quick_action={has_finder_quick_action}, nsservices={has_nsservices}",
                    "A traditional NSServices registration does not satisfy a Finder Quick Action request.",
                ),
            ]
        )

    return {
        "root": str(root),
        "app_type": target_app_type,
        "requested_app_type": app_type,
        "native_integration": target_native_integration,
        "requested_native_integration": native_integration,
        "summary": {
            "ok": sum(1 for check in checks if check.status == "ok"),
            "missing": sum(1 for check in checks if check.status != "ok"),
        },
        "checks": [asdict(check) for check in checks],
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Skill Publisher App Audit",
        "",
        f"Root: `{report['root']}`",
        f"App type: `{report['app_type']}` (requested: `{report['requested_app_type']}`)",
        (
            f"Native integration: `{report['native_integration']}` "
            f"(requested: `{report['requested_native_integration']}`)"
        ),
        "",
        f"Checks: {report['summary']['ok']} ok, {report['summary']['missing']} missing",
        "",
        "| Status | Area | Detail | Recommendation |",
        "|---|---|---|---|",
    ]
    marker = {"ok": "OK", "missing": "MISSING"}
    for check in report["checks"]:
        lines.append(
            "| {status} | {title} | {detail} | {recommendation} |".format(
                status=marker.get(check["status"], check["status"].upper()),
                title=check["title"].replace("|", "\\|"),
                detail=check["detail"].replace("|", "\\|"),
                recommendation=check["recommendation"].replace("|", "\\|"),
            )
        )
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit a project against the Skill Publisher app baseline.")
    parser.add_argument("--root", default=".", help="Target app root to inspect.")
    parser.add_argument(
        "--app-type",
        choices=("auto", "web", "tauri", "macos"),
        default="auto",
        help="Audit profile to apply.",
    )
    parser.add_argument(
        "--native-integration",
        choices=("auto", "none", "finder-quick-action"),
        default="auto",
        help="Native surface contract to enforce.",
    )
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format.")
    parser.add_argument("--output", help="Optional path to write the report.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root)
    if not root.exists():
        print(f"error: root does not exist: {root}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"error: root is not a directory: {root}", file=sys.stderr)
        return 2

    report = audit(root, args.app_type, args.native_integration)
    if args.format == "json":
        output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    else:
        output = render_markdown(report)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
