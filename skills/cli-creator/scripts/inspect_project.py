#!/usr/bin/env python3
"""Inspect a local project for real CLI/backend integration surfaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "lov-cli-project-analysis/v1"
IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "node_modules",
    "target",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".next",
    ".turbo",
}
MANIFESTS = {
    "package.json": "node",
    "pyproject.toml": "python",
    "setup.py": "python",
    "setup.cfg": "python",
    "requirements.txt": "python",
    "Cargo.toml": "rust",
    "go.mod": "go",
    "pom.xml": "java",
    "build.gradle": "java",
    "build.gradle.kts": "kotlin",
    "Package.swift": "swift",
    "CMakeLists.txt": "native",
    "Makefile": "native",
    "Dockerfile": "container",
    "docker-compose.yml": "container",
    "docker-compose.yaml": "container",
    "tauri.conf.json": "tauri",
    "tauri.conf.json5": "tauri",
    "skill.yaml": "agent-skill",
    "SKILL.md": "agent-skill",
}
LANGUAGE_BY_SUFFIX = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".rs": "Rust",
    ".go": "Go",
    ".swift": "Swift",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".c": "C",
    ".h": "C/C++",
    ".cc": "C/C++",
    ".cpp": "C/C++",
    ".hpp": "C/C++",
    ".rb": "Ruby",
    ".php": "PHP",
    ".sh": "Shell",
    ".zsh": "Shell",
    ".fish": "Shell",
}
CLI_CONTENT_PATTERNS = {
    "argparse": re.compile(r"\bargparse\b|ArgumentParser\s*\("),
    "click": re.compile(r"\bclick\.(?:group|command|option|argument)\b"),
    "typer": re.compile(r"\btyper\.(?:Typer|Option|Argument)\b"),
    "commander": re.compile(r"\bcommander\b|\.command\s*\("),
    "yargs": re.compile(r"\byargs\b"),
    "clap": re.compile(r"\bclap::|derive\s*\(.*Parser"),
    "cobra": re.compile(r"\bcobra\.Command\b"),
    "swift-argument-parser": re.compile(r"\bParsableCommand\b"),
}
BACKEND_CONTENT_PATTERNS = {
    "subprocess": re.compile(r"\bsubprocess\.(?:run|Popen|check_output)\b|\bexecFile\s*\("),
    "http-api": re.compile(r"\bFastAPI\s*\(|\bFlask\s*\(|\bexpress\s*\(|\bRouter\s*\("),
    "rpc-or-mcp": re.compile(r"\bMCP\b|ModelContextProtocol|\bgrpc\b|JSON-RPC"),
    "database": re.compile(r"\bsqlite3\b|\bSQLAlchemy\b|\bprisma\b|\bsqlx\b"),
}


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def walk_files(root: Path, max_files: int) -> tuple[list[Path], bool]:
    files: list[Path] = []
    truncated = False
    for current, directories, names in os.walk(root, followlinks=False):
        directories[:] = sorted(
            name for name in directories if name not in IGNORED_DIRS
        )
        for name in sorted(names):
            files.append(Path(current) / name)
            if len(files) >= max_files:
                truncated = True
                return files, truncated
    return files, truncated


def small_text(path: Path, max_bytes: int = 512_000) -> str:
    try:
        if path.stat().st_size > max_bytes:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def manifest_records(root: Path, files: Iterable[Path]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for path in files:
        kind = MANIFESTS.get(path.name)
        if kind:
            records.append({"path": relative(path, root), "ecosystem": kind})
    return records


def package_json_signals(root: Path, files: Iterable[Path]) -> dict[str, Any]:
    bins: dict[str, str] = {}
    scripts: dict[str, str] = {}
    for path in files:
        if path.name != "package.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        raw_bin = data.get("bin", {})
        if isinstance(raw_bin, str) and isinstance(data.get("name"), str):
            bins[data["name"]] = f"{relative(path.parent, root)}/{raw_bin}".lstrip("./")
        elif isinstance(raw_bin, dict):
            for key, value in raw_bin.items():
                if isinstance(key, str) and isinstance(value, str):
                    prefix = relative(path.parent, root)
                    bins[key] = f"{prefix}/{value}".lstrip("./")
        raw_scripts = data.get("scripts", {})
        if isinstance(raw_scripts, dict):
            for key, value in raw_scripts.items():
                if isinstance(key, str) and isinstance(value, str):
                    scripts[f"{relative(path.parent, root) or '.'}:{key}"] = value
    return {"bin": bins, "scripts": scripts}


def scan_source_signals(root: Path, files: Iterable[Path]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    cli_hits: list[dict[str, str]] = []
    backend_hits: list[dict[str, str]] = []
    source_suffixes = set(LANGUAGE_BY_SUFFIX)
    for path in files:
        lowered = path.name.casefold()
        rel = relative(path, root)
        name_signal = any(
            token in lowered
            for token in ("cli", "command", "console", "main", "server", "api")
        )
        if name_signal and path.suffix.lower() in source_suffixes:
            cli_hits.append({"path": rel, "signal": "filename"})
        if path.suffix.lower() not in source_suffixes:
            continue
        text = small_text(path)
        if not text:
            continue
        for signal, pattern in CLI_CONTENT_PATTERNS.items():
            if pattern.search(text):
                cli_hits.append({"path": rel, "signal": signal})
                break
        for signal, pattern in BACKEND_CONTENT_PATTERNS.items():
            if pattern.search(text):
                backend_hits.append({"path": rel, "signal": signal})
                break
    return deduplicate(cli_hits), deduplicate(backend_hits)


def deduplicate(records: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    output: list[dict[str, str]] = []
    for record in records:
        key = (record["path"], record["signal"])
        if key not in seen:
            seen.add(key)
            output.append(record)
    return output


def classify_project(manifests: list[dict[str, str]], files: list[Path]) -> list[str]:
    ecosystems = {record["ecosystem"] for record in manifests}
    names = {path.name for path in files}
    kinds: list[str] = []
    if "agent-skill" in ecosystems:
        kinds.append("agent-skill")
    if "tauri" in ecosystems:
        kinds.append("desktop-application")
    if "package.json" in names and any(name in names for name in ("vite.config.ts", "next.config.js", "next.config.mjs", "next.config.ts")):
        kinds.append("web-application")
    if any(name in names for name in ("Dockerfile", "docker-compose.yml", "docker-compose.yaml")):
        kinds.append("service-or-container")
    if any(path.name in {"pyproject.toml", "Cargo.toml", "go.mod", "Package.swift"} for path in files):
        kinds.append("library-or-application")
    if len({record["path"].split("/", 1)[0] for record in manifests}) >= 3:
        kinds.append("multi-package")
    return kinds or ["unclassified-project"]


def inspect(root: Path, max_files: int, portable: bool = False) -> dict[str, Any]:
    files, truncated = walk_files(root, max_files)
    manifests = manifest_records(root, files)
    languages = Counter(
        LANGUAGE_BY_SUFFIX[path.suffix.lower()]
        for path in files
        if path.suffix.lower() in LANGUAGE_BY_SUFFIX
    )
    cli_hits, backend_hits = scan_source_signals(root, files)
    package_signals = package_json_signals(root, files)
    instruction_files = [
        relative(path, root)
        for path in files
        if path.name in {"AGENTS.md", "CLAUDE.md"}
    ]
    readmes = [
        relative(path, root)
        for path in files
        if path.name.casefold().startswith("readme")
    ][:20]
    digest_input = "|".join(
        [root.name, str(len(files)), *sorted(record["path"] for record in manifests)]
    )
    context_id = "cli-" + hashlib.sha256(digest_input.encode("utf-8")).hexdigest()[:8]
    return {
        "schema": SCHEMA,
        "status": "inspected",
        "context_id": context_id,
        "project": {
            "name": root.name,
            "root": "." if portable else str(root),
            "kinds": classify_project(manifests, files),
        },
        "inventory": {
            "file_count": len(files),
            "truncated": truncated,
            "max_files": max_files,
            "languages": dict(languages.most_common()),
            "manifests": manifests,
            "instruction_files": instruction_files,
            "readmes": readmes,
        },
        "callable_surfaces": {
            "package_bins": package_signals["bin"],
            "package_scripts": package_signals["scripts"],
            "cli_candidates": cli_hits[:100],
            "backend_candidates": backend_hits[:100],
        },
        "next_checks": [
            "Read project instructions and primary README files.",
            "Trace one real user workflow from entry point to verified postcondition.",
            "Choose the narrowest real backend boundary; do not reimplement the product.",
            "Design doctor, info, capabilities, and at least one domain command.",
        ],
    }


def markdown(data: dict[str, Any]) -> str:
    project = data["project"]
    inventory = data["inventory"]
    surfaces = data["callable_surfaces"]
    lines = [
        f"# CLI Project Analysis — {project['name']}",
        "",
        f"- Context: `{data['context_id']}`",
        f"- Root: `{project['root']}`",
        f"- Kinds: {', '.join(project['kinds'])}",
        f"- Files scanned: {inventory['file_count']}"
        + (" (truncated)" if inventory["truncated"] else ""),
        "",
        "## Languages",
        "",
    ]
    if inventory["languages"]:
        lines.extend(
            f"- {name}: {count}" for name, count in inventory["languages"].items()
        )
    else:
        lines.append("- No recognized source files")
    lines.extend(["", "## Manifests", ""])
    lines.extend(
        f"- `{item['path']}` ({item['ecosystem']})"
        for item in inventory["manifests"]
    )
    if not inventory["manifests"]:
        lines.append("- None detected")
    lines.extend(["", "## Callable surfaces", ""])
    for name, path in surfaces["package_bins"].items():
        lines.append(f"- Package bin `{name}` → `{path}`")
    for item in surfaces["cli_candidates"][:30]:
        lines.append(f"- CLI candidate `{item['path']}` ({item['signal']})")
    for item in surfaces["backend_candidates"][:30]:
        lines.append(f"- Backend candidate `{item['path']}` ({item['signal']})")
    if not any(
        (surfaces["package_bins"], surfaces["cli_candidates"], surfaces["backend_candidates"])
    ):
        lines.append("- No callable surface detected automatically; inspect source manually")
    lines.extend(["", "## Required next checks", ""])
    lines.extend(f"- {item}" for item in data["next_checks"])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-files", type=int, default=20_000)
    parser.add_argument(
        "--portable",
        action="store_true",
        help="Write the project root as '.' for reusable evidence",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.project.expanduser().resolve()
    if not root.is_dir():
        context_id = "cli-" + hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:8]
        error = {
            "ok": False,
            "error": {
                "code": "project_not_found",
                "message": "Project path is not a directory.",
                "context_id": context_id,
                "path": str(root),
            },
        }
        print(json.dumps(error, ensure_ascii=False), file=sys.stderr)
        return 2
    if args.max_files < 1:
        print("--max-files must be positive", file=sys.stderr)
        return 2
    data = inspect(root, args.max_files, portable=args.portable)
    rendered = (
        json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        if args.format == "json"
        else markdown(data)
    )
    if args.output:
        output = args.output.expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        print(str(output.resolve()))
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
