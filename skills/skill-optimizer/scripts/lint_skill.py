#!/usr/bin/env python3
"""
Audit a lovstudio skill against repo conventions + official skill-creator best practices.

Usage:
    python lint_skill.py <skill-name>           # e.g. any2pdf or lovstudio-any2pdf
    python lint_skill.py <skill-name> --json
    python lint_skill.py --path /abs/path/to/skills/lovstudio-any2pdf

Outputs a list of findings with severity (error/warn/info) and a `fix_hint` field
to help the orchestrating skill prioritize automatic fixes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEVERITIES = ("error", "warn", "info")

FRONTMATTER_REQUIRED = ["name", "description", "license", "compatibility", "metadata"]
METADATA_REQUIRED = ["author", "version", "tags"]


def find_repo_root(start: Path) -> Path:
    for p in [start] + list(start.parents):
        if (p / "CLAUDE.md").exists() and (p / "skills").is_dir():
            return p
    return start


def resolve_skill_dir(name: str, path: str | None) -> Path:
    if path:
        return Path(path).resolve()
    name = name.removeprefix("lovstudio-").removeprefix("lovstudio:")
    root = find_repo_root(Path.cwd())
    return (root / "skills" / f"lovstudio-{name}").resolve()


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Naive YAML frontmatter parser — enough for lint purposes."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_block = text[3:end].strip("\n")
    body = text[end + 4 :].lstrip("\n")
    data: dict = {}
    current_key = None
    buf: list[str] = []
    for line in fm_block.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m and not line.startswith((" ", "\t")):
            if current_key is not None:
                data[current_key] = "\n".join(buf).strip() if buf else data.get(current_key, "")
            current_key = m.group(1)
            val = m.group(2).strip()
            buf = []
            if val in (">", "|", ">-", "|-"):
                data[current_key] = ""
            elif val == "":
                data[current_key] = {}  # likely nested
            else:
                data[current_key] = val.strip('"').strip("'")
                current_key = None
        elif current_key and line.startswith((" ", "\t")):
            stripped = line.strip()
            # nested key under metadata
            m2 = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", stripped)
            if m2 and isinstance(data.get(current_key), dict):
                data[current_key][m2.group(1)] = m2.group(2).strip().strip('"').strip("'")
            else:
                buf.append(stripped)
    if current_key is not None and buf:
        if isinstance(data.get(current_key), str) and data[current_key] == "":
            data[current_key] = "\n".join(buf).strip()
    return data, body


class Linter:
    def __init__(self, skill_dir: Path):
        self.dir = skill_dir
        self.name = skill_dir.name.removeprefix("lovstudio-")
        self.findings: list[dict] = []

    def add(self, severity: str, code: str, message: str, fix_hint: str = "", file: str = ""):
        self.findings.append(
            {
                "severity": severity,
                "code": code,
                "message": message,
                "fix_hint": fix_hint,
                "file": file,
            }
        )

    # --- Checks ---

    def check_structure(self):
        if not self.dir.exists():
            self.add("error", "DIR_MISSING", f"Skill directory not found: {self.dir}")
            return
        if not self.dir.name.startswith("lovstudio-"):
            self.add(
                "error",
                "DIR_PREFIX",
                f"Directory '{self.dir.name}' must start with 'lovstudio-'",
                "Rename directory to lovstudio-<name>",
            )
        for required in ("SKILL.md", "README.md"):
            f = self.dir / required
            if not f.exists():
                self.add(
                    "error",
                    f"MISSING_{required.split('.')[0]}",
                    f"{required} is missing",
                    f"Create {required} using the templates in skill-creator references",
                    file=required,
                )

    def check_skill_md(self):
        path = self.dir / "SKILL.md"
        if not path.exists():
            return
        text = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)

        for key in FRONTMATTER_REQUIRED:
            if key not in fm:
                self.add(
                    "error",
                    "FM_MISSING_FIELD",
                    f"SKILL.md frontmatter missing required field '{key}'",
                    f"Add '{key}:' to frontmatter",
                    file="SKILL.md",
                )

        name = fm.get("name", "")
        if name and name != f"lovstudio:{self.name}":
            self.add(
                "error",
                "FM_NAME_MISMATCH",
                f"frontmatter name '{name}' does not match directory (expected 'lovstudio:{self.name}')",
                f"Set name: lovstudio:{self.name}",
                file="SKILL.md",
            )

        desc = fm.get("description", "") or ""
        if isinstance(desc, str):
            if len(desc) < 80:
                self.add(
                    "warn",
                    "FM_DESC_TOO_SHORT",
                    "description is shorter than 80 chars — likely missing trigger info",
                    "Expand description to cover: what it does + when to trigger + specific user phrases",
                    file="SKILL.md",
                )
            if "trigger" not in desc.lower() and "mention" not in desc.lower() and "use when" not in desc.lower():
                self.add(
                    "warn",
                    "FM_DESC_NO_TRIGGER",
                    "description lacks explicit trigger cues (e.g. 'Use when...', 'trigger when user mentions...')",
                    "Add 'Use when ...' and 'Also trigger when the user mentions \"...\"' phrases",
                    file="SKILL.md",
                )

        meta = fm.get("metadata")
        if isinstance(meta, dict):
            for k in METADATA_REQUIRED:
                if k not in meta:
                    self.add(
                        "warn",
                        "FM_META_FIELD",
                        f"metadata.{k} missing",
                        f"Add metadata.{k}",
                        file="SKILL.md",
                    )
            version = meta.get("version", "")
            if version and not re.match(r"^\d+\.\d+\.\d+$", version):
                self.add(
                    "warn",
                    "FM_VERSION_FORMAT",
                    f"metadata.version '{version}' is not semver x.y.z",
                    "Use semver format like 0.1.0",
                    file="SKILL.md",
                )

        # Body checks
        if re.search(r"TODO:\s", body) or "TODO_CN" in body or "TODO_EN" in body:
            self.add(
                "error",
                "BODY_TODO",
                "SKILL.md body still contains TODO placeholders",
                "Replace all TODOs with real content",
                file="SKILL.md",
            )
        non_interactive = any(
            phrase in body.lower()
            for phrase in ("fully automatic", "no interactive", "non-interactive", "do not ask the user")
        )
        if (
            "AskUserQuestion" not in body
            and "## Workflow" in body
            and not non_interactive
        ):
            self.add(
                "info",
                "BODY_NO_ASKUSER",
                "Workflow does not mention AskUserQuestion — interactive skills should collect options before running",
                "Add an 'Ask the user' step using AskUserQuestion",
                file="SKILL.md",
            )
        if len(body.splitlines()) > 500:
            self.add(
                "warn",
                "BODY_TOO_LONG",
                "SKILL.md body exceeds 500 lines — consider progressive disclosure",
                "Split long sections to references/ and link from SKILL.md",
                file="SKILL.md",
            )

    def check_readme(self):
        path = self.dir / "README.md"
        if not path.exists():
            return
        text = path.read_text(encoding="utf-8")
        if re.search(r"TODO:\s", text) or "pip install TODO" in text or "--output TODO" in text:
            self.add(
                "error",
                "README_TODO",
                "README.md contains TODO placeholders",
                "Fill in install, usage, options",
                file="README.md",
            )
        if not re.search(r"!\[Version\]\(https://img\.shields\.io/badge/version-", text):
            self.add(
                "warn",
                "README_NO_BADGE",
                "README.md missing version badge",
                "Add ![Version](https://img.shields.io/badge/version-X.Y.Z-CC785C) near the top",
                file="README.md",
            )
        if "npx skills add lovstudio/skills" not in text:
            self.add(
                "warn",
                "README_NO_INSTALL",
                "README.md missing install command",
                "Add install block: `npx skills add lovstudio/skills --skill lovstudio:<name>`",
                file="README.md",
            )

    def check_changelog(self):
        path = self.dir / "CHANGELOG.md"
        if not path.exists():
            self.add(
                "warn",
                "NO_CHANGELOG",
                "CHANGELOG.md not found",
                "Run bump_version.py to create an initial entry",
                file="CHANGELOG.md",
            )

    def check_scripts(self):
        scripts_dir = self.dir / "scripts"
        if not scripts_dir.exists():
            return  # pure-instruction skills allowed
        for py in scripts_dir.glob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            rel = f"scripts/{py.name}"
            if "argparse" not in text and "if __name__" in text:
                self.add(
                    "warn",
                    "SCRIPT_NO_ARGPARSE",
                    f"{py.name} is a CLI but does not use argparse",
                    "Rewrite to use argparse for CLI parity with other skills",
                    file=rel,
                )
            if (
                re.search(r"pip install .*--break-system-packages", text)
                and re.search(r"(subprocess\.(run|call|Popen)|os\.system)", text)
            ):
                self.add(
                    "info",
                    "SCRIPT_PIP_FLAG",
                    f"{py.name} shells out pip install --break-system-packages (should be in docs, not code)",
                    "Move pip install guidance to SKILL.md/README.md",
                    file=rel,
                )
            if py.stat().st_size > 80_000:
                self.add(
                    "info",
                    "SCRIPT_LARGE",
                    f"{py.name} is large (>80KB) — verify it's still a single-file CLI",
                    "",
                    file=rel,
                )
            # CJK-relevant skills should handle mixed text
            if "pdf" in self.name or "docx" in self.name or "deck" in self.name:
                if "cjk" not in text.lower() and "chinese" not in text.lower() and "中文" not in text:
                    self.add(
                        "info",
                        "SCRIPT_NO_CJK_HINT",
                        f"{py.name}: document-skill script has no visible CJK handling code",
                        "Verify CJK/Latin mixed rendering works correctly",
                        file=rel,
                    )

    def run(self) -> list[dict]:
        self.check_structure()
        self.check_skill_md()
        self.check_readme()
        self.check_changelog()
        self.check_scripts()
        return self.findings


def format_text(findings: list[dict], skill_dir: Path) -> str:
    if not findings:
        return f"✓ {skill_dir.name}: no issues found\n"
    lines = [f"Lint report for {skill_dir.name}:", ""]
    by_sev = {s: [f for f in findings if f["severity"] == s] for s in SEVERITIES}
    marks = {"error": "✗", "warn": "!", "info": "·"}
    for sev in SEVERITIES:
        for f in by_sev[sev]:
            loc = f" [{f['file']}]" if f["file"] else ""
            lines.append(f"  {marks[sev]} {sev.upper():5} {f['code']:20}{loc}  {f['message']}")
            if f["fix_hint"]:
                lines.append(f"      → {f['fix_hint']}")
    lines.append("")
    lines.append(
        f"Summary: {len(by_sev['error'])} errors, {len(by_sev['warn'])} warnings, {len(by_sev['info'])} info"
    )
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Audit a lovstudio skill")
    ap.add_argument("name", nargs="?", help="Skill name (with or without lovstudio- prefix)")
    ap.add_argument("--path", help="Absolute path to skill directory (overrides name)")
    ap.add_argument("--json", action="store_true", help="Output findings as JSON")
    args = ap.parse_args()

    if not args.name and not args.path:
        ap.error("provide a skill name or --path")

    skill_dir = resolve_skill_dir(args.name or "", args.path)
    linter = Linter(skill_dir)
    findings = linter.run()

    if args.json:
        print(
            json.dumps(
                {"skill": skill_dir.name, "path": str(skill_dir), "findings": findings},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        sys.stdout.write(format_text(findings, skill_dir))

    # Exit non-zero if errors present
    if any(f["severity"] == "error" for f in findings):
        sys.exit(2)


if __name__ == "__main__":
    main()
