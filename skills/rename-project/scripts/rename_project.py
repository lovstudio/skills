#!/usr/bin/env python3
"""Plan or apply a project rename without a blind repository-wide replace.

The default mode is a read-only plan. Applying changes is explicit with
``--apply``. Git operations stage only files changed by this run, and
compatibility-sensitive files are left for review unless ``--include-compat``
is supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


SKIP_DIRS = {
    ".git",
    ".worktrees",
    ".codex-upstream",
    ".runtime",
    ".cache",
    ".output",
    ".turbo",
    "node_modules",
    "dist",
    "build",
    ".next",
    "vendor",
    "target",
    "coverage",
    ".venv",
    "__pycache__",
}
LOCK_NAMES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "Cargo.lock"}
TEXT_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".css",
    ".env",
    ".go",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".plist",
    ".py",
    ".rs",
    ".scss",
    ".sh",
    ".sql",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".vue",
    ".xml",
    ".yaml",
    ".yml",
    ".zsh",
}
TEXT_FILENAMES = {
    "Dockerfile",
    "Makefile",
    "Procfile",
    ".env",
    ".env.example",
    ".gitignore",
    ".npmrc",
    ".prettierignore",
}
COMPAT_PATH_RE = re.compile(
    r"(?:^|/)(?:legacy|compat(?:ibility)?|migration(?:s)?|storage|schema(?:s)?|data)(?:/|$)", re.I
)
COMPAT_LINE_RE = re.compile(
    r"\b(?:legacy|compat(?:ibility)?|migration|namespace|storage|data[_ -]?dir|alias|backward)\b",
    re.I,
)
PROJECT_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def run_git(root: Path, *args: str, check: bool = False) -> str | None:
    result: dict = {}
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=check,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def detect_old_name(root: Path) -> str:
    remote = run_git(root, "remote", "get-url", "origin")
    if remote:
        candidate = remote.rstrip("/").rsplit("/", 1)[-1]
        if ":" in candidate and "/" in candidate:
            candidate = candidate.rsplit("/", 1)[-1]
        if candidate.endswith(".git"):
            candidate = candidate[:-4]
        if candidate:
            return candidate

    package_json = root / "package.json"
    if package_json.exists():
        match = re.search(r'"name"\s*:\s*"([^"/]+)"', package_json.read_text(encoding="utf-8", errors="ignore"))
        if match:
            return match.group(1)
    return root.name


def name_variants(old_name: str, new_name: str) -> dict[str, str]:
    variants = {
        old_name: new_name,
        old_name.lower(): new_name.lower(),
        old_name.upper(): new_name.upper(),
        old_name.title(): new_name.title(),
    }
    return {source: target for source, target in variants.items() if source}


def is_text_candidate(path: Path, include_locks: bool) -> bool:
    if path.name in LOCK_NAMES and not include_locks:
        return False
    return path.name in TEXT_FILENAMES or path.suffix.lower() in TEXT_EXTENSIONS


def read_text(path: Path) -> tuple[str | None, str | None]:
    try:
        data = path.read_bytes()
    except OSError as error:
        return None, f"read-error: {error}"
    if len(data) > 2_000_000:
        return None, "file-too-large"
    if b"\0" in data:
        return None, "binary"
    try:
        return data.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, "non-utf8"


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_root(root: Path) -> Path | None:
    value = run_git(root, "rev-parse", "--show-toplevel")
    return Path(value).resolve() if value else None


def project_prefix(root: Path) -> tuple[Path, str] | None:
    repository = git_root(root)
    if repository is None:
        return None
    relative = root.resolve().relative_to(repository).as_posix()
    return repository, relative or "."


def parse_status_paths(output: str, prefix: str) -> set[str]:
    paths: set[str] = set()
    for line in output.splitlines():
        if len(line) < 4:
            continue
        value = line[3:]
        if " -> " in value:
            value = value.rsplit(" -> ", 1)[-1]
        if prefix != ".":
            if value == prefix:
                value = "."
            elif value.startswith(prefix + "/"):
                value = value[len(prefix) + 1 :]
            else:
                continue
        paths.add(value)
    return paths


def git_dirty_paths(root: Path) -> set[str]:
    context = project_prefix(root)
    if context is None:
        output = run_git(root, "status", "--porcelain=v1", "--untracked-files=all")
        return parse_status_paths(output or "", ".")
    repository, prefix = context
    output = run_git(
        repository,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        prefix,
    )
    return parse_status_paths(output or "", prefix)


def git_staged_paths(root: Path) -> set[str]:
    repository = git_root(root)
    if repository is None:
        return set()
    output = run_git(repository, "diff", "--cached", "--name-only")
    return {line.strip() for line in (output or "").splitlines() if line.strip()}


def repository_path(root: Path, relative: str) -> str:
    repository = git_root(root)
    if repository is None:
        return relative
    return (root / relative).resolve().relative_to(repository).as_posix()


def compile_patterns(patterns: list[str], option: str) -> list[re.Pattern[str]]:
    try:
        return [re.compile(pattern) for pattern in patterns]
    except re.error as error:
        raise ValueError(f"invalid {option} regex: {error}") from error


def normalize_skip_dirs(values: list[str]) -> set[str]:
    skip_dirs: set[str] = set()
    for value in values:
        if not value or value in {".", ".."} or Path(value).name != value:
            raise ValueError(f"invalid --skip-dir value: {value!r}; pass a directory name, not a path")
        skip_dirs.add(value)
    return skip_dirs


def compatibility_reasons(relative: str, hit_lines: list[str], old_name: str) -> list[str]:
    reasons: list[str] = []
    if COMPAT_PATH_RE.search(relative):
        reasons.append("compatibility-like path")
    if any(COMPAT_LINE_RE.search(line) for line in hit_lines):
        reasons.append("compatibility keyword")
    old = re.escape(old_name)
    path_or_namespace = re.compile(
        rf"(?:\.lovstudio|Application Support|search[-_]index|join\s*\(\s*['\"]|[\\/])[^\n]*{old}",
        re.I,
    )
    if any(path_or_namespace.search(line) for line in hit_lines):
        reasons.append("path or namespace reference")
    return list(dict.fromkeys(reasons))


def scan(
    root: Path,
    old_name: str,
    new_name: str,
    include_compat: bool,
    include_compat_paths: list[str],
    include_locks: bool,
    preserve_patterns: list[str],
    skip_dirs: list[str] | None = None,
) -> dict:
    mapping = name_variants(old_name, new_name)
    preserves = compile_patterns(preserve_patterns, "--preserve")
    compatibility_paths = compile_patterns(include_compat_paths, "--include-compat-path")
    effective_skip_dirs = SKIP_DIRS | normalize_skip_dirs(skip_dirs or [])
    candidates: list[dict] = []
    skipped: list[dict] = []
    for directory, subdirectories, filenames in os.walk(root, topdown=True, followlinks=False):
        subdirectories[:] = [name for name in subdirectories if name not in effective_skip_dirs]
        for filename in filenames:
            path = Path(directory) / filename
            relative = path.relative_to(root).as_posix()
            if not is_text_candidate(path, include_locks):
                continue
            text, reason = read_text(path)
            if text is None:
                skipped.append({"path": relative, "reason": reason})
                continue
            matches = {source: text.count(source) for source in mapping if source in text}
            if not matches:
                continue
            hit_lines = [line for line in text.splitlines() if any(source in line for source in matches)]
            reasons = compatibility_reasons(relative, hit_lines, old_name)
            compatibility_review = bool(reasons)
            preserved = any(pattern.search(relative) for pattern in preserves)
            if preserved:
                status = "preserved"
            elif compatibility_review and not include_compat and not any(
                pattern.search(relative) for pattern in compatibility_paths
            ):
                status = "compatibility_review"
            else:
                status = "would_change"
            candidates.append(
                {
                    "path": relative,
                    "status": status,
                    "matches": matches,
                    "sha256_before": file_digest(path),
                    "replacement_count": sum(matches.values()),
                    "compatibility_reasons": reasons,
                }
            )
    return {
        "mapping": mapping,
        "candidates": candidates,
        "skipped": skipped,
        "skip_dirs": sorted(effective_skip_dirs),
    }


def apply_changes(root: Path, plan: dict, allow_dirty: bool) -> list[str]:
    dirty = git_dirty_paths(root)
    changed = [item for item in plan["candidates"] if item["status"] == "would_change"]
    blocked = [item["path"] for item in changed if item["path"] in dirty]
    if blocked and not allow_dirty:
        raise RuntimeError(
            "target files already have local changes; inspect them or rerun with --allow-dirty: "
            + ", ".join(blocked)
        )
    mapping = plan["mapping"]
    changed_paths: list[str] = []
    for item in changed:
        path = root / item["path"]
        text, reason = read_text(path)
        if text is None:
            raise RuntimeError(f"cannot apply {item['path']}: {reason}")
        updated = text
        for source in sorted(mapping, key=len, reverse=True):
            updated = updated.replace(source, mapping[source])
        if updated == text:
            continue
        path.write_text(updated, encoding="utf-8")
        item["sha256_after"] = file_digest(path)
        item["status"] = "changed"
        changed_paths.append(item["path"])
    return changed_paths


def commit_exact(root: Path, paths: list[str], old_name: str, new_name: str) -> None:
    if not paths:
        raise RuntimeError("no files changed; nothing to commit")
    repository = git_root(root)
    if repository is None:
        raise RuntimeError("Git repository is not configured for the project root")
    expected = {repository_path(root, path) for path in paths}
    existing_staged = git_staged_paths(root)
    unexpected = existing_staged.difference(expected)
    if unexpected:
        raise RuntimeError("staging area already contains unrelated files: " + ", ".join(sorted(unexpected)))
    result = subprocess.run(
        ["git", "-C", str(repository), "add", "--", *sorted(expected)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git add failed")
    staged = git_staged_paths(root)
    if staged != expected:
        raise RuntimeError("staged file set differs from rename plan")
    message = f"chore: rename project from {old_name} to {new_name}"
    result = subprocess.run(
        ["git", "-C", str(repository), "commit", "-m", message],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "git commit failed")


def push(root: Path) -> None:
    if not run_git(root, "remote", "get-url", "origin"):
        raise RuntimeError("origin remote is not configured")
    branch = run_git(root, "branch", "--show-current")
    if not branch:
        raise RuntimeError("cannot push from a detached HEAD")
    result = subprocess.run(["git", "-C", str(root), "push", "origin", "HEAD"], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git push failed")


def rename_github(root: Path, new_name: str) -> None:
    if not run_git(root, "remote", "get-url", "origin"):
        raise RuntimeError("origin remote is not configured")
    result = subprocess.run(["gh", "repo", "rename", new_name, "--yes"], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "gh repo rename failed")
    verified = subprocess.run(
        ["gh", "repo", "view", "--json", "name", "-q", ".name"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if verified.returncode != 0 or verified.stdout.strip().lower() != new_name.lower():
        raise RuntimeError("GitHub rename completed but repository name verification did not match")


def write_report(path: str | None, root: Path, result: dict) -> None:
    if not path:
        return
    report_path = Path(path).expanduser()
    if not report_path.is_absolute():
        report_path = root / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan or apply a guarded project rename")
    parser.add_argument("new_name", help="New project name")
    parser.add_argument("--root", default=".", help="Project root; defaults to the current directory")
    parser.add_argument("--old-name", help="Current project name; otherwise detect from origin/package.json/directory")
    parser.add_argument("--apply", action="store_true", help="Apply product-name replacements")
    parser.add_argument("--include-compat", action="store_true", help="Also replace compatibility-sensitive files")
    parser.add_argument(
        "--include-compat-path",
        action="append",
        default=[],
        help="Regex of compatibility-sensitive paths to include; repeatable",
    )
    parser.add_argument("--include-locks", action="store_true", help="Include package and cargo lock files")
    parser.add_argument(
        "--skip-dir",
        action="append",
        default=[],
        help="Additional generated directory name to skip; repeatable",
    )
    parser.add_argument("--preserve", action="append", default=[], help="Regex of relative paths to leave unchanged")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow replacement inside already modified files")
    parser.add_argument("--report", help="Write the JSON plan/result to this path")
    parser.add_argument("--commit", action="store_true", help="Commit only files changed by this run")
    parser.add_argument("--push", action="store_true", help="Push the rename commit to origin")
    parser.add_argument("--github", action="store_true", help="Rename and verify the GitHub repository with gh")
    args = parser.parse_args()

    if args.push and not args.commit:
        parser.error("--push requires --commit")
    if args.github and not args.push:
        parser.error("--github requires --push")
    if not PROJECT_NAME_RE.match(args.new_name):
        parser.error("new_name must be a simple project/repository name")

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        parser.error(f"project root not found: {root}")
    old_name = args.old_name or detect_old_name(root)
    if not old_name:
        parser.error("current project name could not be detected; pass --old-name")
    if old_name == args.new_name:
        parser.error("new_name is already the current project name")

    result = {
        "root": str(root),
        "old_name": old_name,
        "new_name": args.new_name,
        "mode": "apply" if args.apply else "plan",
        "include_compat": args.include_compat,
        "include_compat_paths": args.include_compat_path,
        "include_locks": args.include_locks,
        "requested_skip_dirs": args.skip_dir,
        "git_worktree": "dirty" if git_dirty_paths(root) else "clean",
    }
    try:
        plan = scan(
            root,
            old_name,
            args.new_name,
            args.include_compat,
            args.include_compat_path,
            args.include_locks,
            args.preserve,
            args.skip_dir,
        )
        result.update(plan)
        if args.apply:
            if args.commit and git_staged_paths(root):
                raise RuntimeError("staging area already contains files; review or clear it before --commit")
            changed_paths = apply_changes(root, result, args.allow_dirty)
            result["changed_paths"] = changed_paths
            if args.commit:
                commit_exact(root, changed_paths, old_name, args.new_name)
                result["commit"] = "created"
            if args.push:
                push(root)
                result["push"] = "complete"
            if args.github:
                rename_github(root, args.new_name)
                result["github"] = "verified"
        else:
            result["changed_paths"] = [
                item["path"] for item in result["candidates"] if item["status"] == "would_change"
            ]
        write_report(args.report, root, result)
    except (RuntimeError, ValueError, OSError) as error:
        failure = dict(result)
        failure["status"] = "error"
        failure["error"] = str(error)
        write_report(args.report, root, failure)
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error

    counts = {}
    for item in result["candidates"]:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    print(json.dumps({"old_name": old_name, "new_name": args.new_name, "counts": counts}, ensure_ascii=False))
    if result.get("changed_paths"):
        print("files: " + ", ".join(result["changed_paths"]))


if __name__ == "__main__":
    main()
