#!/usr/bin/env python3
"""Collect a compact, reviewable source summary for Skill distillation."""

from __future__ import annotations

import argparse
import subprocess
from collections import Counter
from pathlib import Path


KEYWORDS = (
    "fix",
    "bug",
    "update",
    "restart",
    "release",
    "publish",
    "verify",
    "test",
    "skill",
    "自动更新",
    "重启",
    "发布",
    "验收",
    "修复",
    "技能",
)


def run_git(project: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(project), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def is_git_repository(project: Path) -> bool:
    return run_git(project, "rev-parse", "--is-inside-work-tree") == "true"


def markdown_files(project: Path) -> list[Path]:
    excluded = {".git", "node_modules", "dist", "build", ".next", ".venv"}
    return [
        path
        for path in project.rglob("*.md")
        if not any(part in excluded for part in path.relative_to(project).parts)
    ][:80]


def matching_lines(project: Path) -> list[str]:
    matches: list[str] = []
    for path in markdown_files(project):
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, start=1):
            lowered = line.lower()
            if any(keyword.lower() in lowered for keyword in KEYWORDS):
                compact = " ".join(line.split())
                matches.append(f"- `{path.relative_to(project)}:{number}` {compact[:220]}")
                if len(matches) >= 40:
                    return matches
    return matches


def commit_topics(project: Path) -> tuple[list[str], list[tuple[str, int]]]:
    raw = run_git(project, "log", "--format=%s", "-n", "100")
    if not raw:
        return [], []
    subjects = [line for line in raw.splitlines() if line.strip()]
    counts: Counter[str] = Counter()
    for subject in subjects:
        lowered = subject.lower()
        for keyword in KEYWORDS:
            if keyword.lower() in lowered:
                counts[keyword] += 1
    return subjects[:30], counts.most_common()


def render(project: Path) -> str:
    git_enabled = is_git_repository(project)
    subjects, topic_counts = commit_topics(project) if git_enabled else ([], [])
    lines = [
        f"# Skill Distillation Evidence: {project.name}",
        "",
        "这是一份源材料摘要，不是 Skill 蓝图。请先蒸馏稳定流程、边界与验收。",
        "",
        "## Scope",
        "",
        f"- Project: `{project}`",
        f"- Git history available: {'yes' if git_enabled else 'no'}",
        "",
    ]
    if topic_counts:
        lines.extend(["## Repeated Git Topics", ""])
        lines.extend(f"- `{topic}`: {count}" for topic, count in topic_counts)
        lines.append("")
    if subjects:
        lines.extend(["## Recent Commit Evidence", ""])
        lines.extend(f"- {subject}" for subject in subjects)
        lines.append("")
    docs = matching_lines(project)
    if docs:
        lines.extend(["## Documentation Evidence", "", *docs, ""])
    if not subjects and not docs:
        lines.extend([
            "## Source Gap",
            "",
            "- 未找到足够的 Git 或 Markdown 证据；请补充事故记录、重复需求或真实验收材料。",
            "",
        ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Project directory to scan")
    parser.add_argument("--output", type=Path, required=True, help="Markdown output path")
    args = parser.parse_args()

    project = args.project.expanduser().resolve()
    if not project.is_dir():
        parser.error(f"project directory does not exist: {project}")
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(project), encoding="utf-8")
    print(f"wrote={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
