#!/usr/bin/env python3
"""Scan a web project for common mobile-adaptation issues.

Checks:
  - viewport meta tag presence and correctness
  - CSS overflow issues (fixed widths, horizontal overflow risks)
  - safe-area-inset usage
  - touch target sizes
  - responsive breakpoint coverage
  - 100vh pitfalls (mobile browser chrome)

Usage:
  python3 scan_mobile_issues.py /path/to/project [--format json|text]
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

HTML_EXTS = {".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte", ".astro"}
CSS_EXTS = {".css", ".scss", ".sass", ".less"}
CODE_EXTS = HTML_EXTS | CSS_EXTS | {".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte", ".astro"}
SKIP_DIRS = {
    "node_modules", ".git", ".next", "dist", "build", ".output",
    ".nuxt", ".svelte-kit", "__pycache__", ".turbo", ".vercel",
}
MAX_FILE_SIZE = 512 * 1024  # 512KB


@dataclass
class Issue:
    severity: str  # "error" | "warning" | "info"
    category: str
    file: str
    line: Optional[int]
    message: str
    fix_hint: str


@dataclass
class ScanResult:
    project_path: str
    files_scanned: int = 0
    issues: list = field(default_factory=list)
    summary: dict = field(default_factory=dict)


def collect_files(root: Path) -> list[Path]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            fp = Path(dirpath) / f
            if fp.suffix in CODE_EXTS and fp.stat().st_size < MAX_FILE_SIZE:
                files.append(fp)
    return files


def check_viewport_meta(content: str, filepath: str, issues: list):
    if filepath.endswith((".html", ".htm")):
        if "viewport" not in content.lower():
            issues.append(Issue(
                severity="error",
                category="viewport",
                file=filepath,
                line=None,
                message="Missing <meta name=\"viewport\"> tag",
                fix_hint='Add: <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">',
            ))
        elif "viewport-fit=cover" not in content.lower():
            for i, line in enumerate(content.splitlines(), 1):
                if "viewport" in line.lower() and "meta" in line.lower():
                    issues.append(Issue(
                        severity="warning",
                        category="viewport",
                        file=filepath,
                        line=i,
                        message="viewport meta missing viewport-fit=cover (needed for notch/island devices)",
                        fix_hint='Add viewport-fit=cover to the viewport meta content attribute',
                    ))
                    break


def check_overflow_risks(content: str, filepath: str, issues: list):
    for i, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("/*"):
            continue

        # Fixed pixel widths on containers
        match = re.search(r'width\s*:\s*(\d{4,})px', line)
        if match:
            px = match.group(1)
            issues.append(Issue(
                severity="warning",
                category="overflow",
                file=filepath,
                line=i,
                message=f"Fixed width {px}px may cause horizontal overflow on mobile",
                fix_hint="Use max-width, percentage, or clamp() instead of fixed px width",
            ))

        # overflow-x not handled on body/html
        if re.search(r'(html|body)\s*\{', line) or re.search(r'@apply', line):
            pass  # skip rule-level checks here

        # Horizontal scroll risk: min-width large values
        match = re.search(r'min-width\s*:\s*(\d+)px', line)
        if match and int(match.group(1)) > 768:
            issues.append(Issue(
                severity="warning",
                category="overflow",
                file=filepath,
                line=i,
                message=f"min-width: {match.group(1)}px forces minimum width larger than most phones",
                fix_hint="Consider using a responsive approach or media query instead",
            ))


def check_100vh_pitfall(content: str, filepath: str, issues: list):
    for i, line in enumerate(content.splitlines(), 1):
        if re.search(r'height\s*:\s*100vh\b', line) and "dvh" not in line:
            issues.append(Issue(
                severity="warning",
                category="viewport-units",
                file=filepath,
                line=i,
                message="100vh doesn't account for mobile browser chrome (address bar)",
                fix_hint="Use 100dvh (dynamic viewport height) or min-height: 100svh with fallback",
            ))

        if re.search(r'height\s*:\s*100svh\b', line):
            issues.append(Issue(
                severity="info",
                category="viewport-units",
                file=filepath,
                line=i,
                message="100svh (small viewport) is safe but may leave gap when browser chrome hides",
                fix_hint="Consider 100dvh for dynamic sizing, or use 100svh if fixed size is intended",
            ))


def check_safe_area(content: str, filepath: str, issues: list, all_contents: str):
    is_css = filepath.endswith(tuple(CSS_EXTS))
    if not is_css:
        return

    has_safe_area = "safe-area-inset" in all_contents or "env(safe-area" in all_contents

    if "position: fixed" in content or "position:fixed" in content:
        for i, line in enumerate(content.splitlines(), 1):
            if re.search(r'position\s*:\s*fixed', line):
                if "safe-area" not in content[max(0, content.rfind("{", 0, content.find(line))):content.find("}", content.find(line))]:
                    issues.append(Issue(
                        severity="warning",
                        category="safe-area",
                        file=filepath,
                        line=i,
                        message="Fixed-position element may overlap notch/home indicator without safe-area padding",
                        fix_hint="Add padding-bottom: env(safe-area-inset-bottom) or padding-top: env(safe-area-inset-top)",
                    ))

    if not has_safe_area:
        issues.append(Issue(
            severity="info",
            category="safe-area",
            file=filepath,
            line=None,
            message="No safe-area-inset usage found in project CSS",
            fix_hint="Add env(safe-area-inset-*) padding to fixed/sticky elements for notch devices",
        ))


def check_touch_targets(content: str, filepath: str, issues: list):
    for i, line in enumerate(content.splitlines(), 1):
        # Very small explicit heights/widths on interactive elements
        match = re.search(r'(?:height|width)\s*:\s*(\d+)px', line)
        if match:
            px = int(match.group(1))
            if 0 < px < 44:
                context_start = max(0, i - 10)
                context_lines = content.splitlines()[context_start:i]
                context_text = "\n".join(context_lines).lower()
                if any(kw in context_text for kw in ["button", "btn", "link", "a ", "input", "select", "tap", "click"]):
                    issues.append(Issue(
                        severity="warning",
                        category="touch-target",
                        file=filepath,
                        line=i,
                        message=f"Interactive element may be {px}px — below 44px minimum touch target",
                        fix_hint="Apple HIG recommends 44x44px minimum; Material Design recommends 48x48dp",
                    ))


def check_responsive_breakpoints(content: str, filepath: str, issues: list):
    if not filepath.endswith(tuple(CSS_EXTS)):
        return

    breakpoints = re.findall(r'@media[^{]*max-width\s*:\s*(\d+)', content)
    breakpoints += re.findall(r'@media[^{]*min-width\s*:\s*(\d+)', content)

    if not breakpoints and len(content) > 500:
        issues.append(Issue(
            severity="info",
            category="responsive",
            file=filepath,
            line=None,
            message="No media query breakpoints found in this stylesheet",
            fix_hint="Consider adding breakpoints for mobile (640px), tablet (768px), desktop (1024px)",
        ))


def check_text_overflow(content: str, filepath: str, issues: list):
    for i, line in enumerate(content.splitlines(), 1):
        if re.search(r'white-space\s*:\s*nowrap', line):
            block_start = max(0, content.rfind("{", 0, content.find(line)))
            block_end = content.find("}", content.find(line))
            block = content[block_start:block_end] if block_end > block_start else ""
            if "overflow" not in block and "text-overflow" not in block:
                issues.append(Issue(
                    severity="warning",
                    category="overflow",
                    file=filepath,
                    line=i,
                    message="white-space: nowrap without overflow handling may cause text overflow on mobile",
                    fix_hint="Add overflow: hidden; text-overflow: ellipsis; or use line-clamp",
                ))


def check_tailwind_issues(content: str, filepath: str, issues: list):
    if not filepath.endswith((".jsx", ".tsx", ".vue", ".svelte", ".astro")):
        return

    for i, line in enumerate(content.splitlines(), 1):
        # h-screen without dvh fallback
        if re.search(r'\bh-screen\b', line) and "h-dvh" not in line:
            issues.append(Issue(
                severity="warning",
                category="viewport-units",
                file=filepath,
                line=i,
                message="h-screen uses 100vh which has mobile browser chrome issues",
                fix_hint="Use h-dvh (Tailwind v3.4+) or h-[100dvh] instead",
            ))

        # Fixed width classes on containers
        match = re.search(r'\bw-\[(\d{4,})px\]', line)
        if match:
            issues.append(Issue(
                severity="warning",
                category="overflow",
                file=filepath,
                line=i,
                message=f"Fixed width w-[{match.group(1)}px] may overflow on mobile",
                fix_hint="Use max-w-* or responsive w-full md:w-[...] pattern",
            ))


def scan_project(root: Path) -> ScanResult:
    result = ScanResult(project_path=str(root))
    files = collect_files(root)
    result.files_scanned = len(files)

    all_css = ""
    for f in files:
        if f.suffix in CSS_EXTS:
            try:
                all_css += f.read_text(errors="replace")
            except Exception:
                pass

    safe_area_checked = False

    for f in files:
        try:
            content = f.read_text(errors="replace")
        except Exception:
            continue

        relpath = str(f.relative_to(root))

        check_viewport_meta(content, relpath, result.issues)
        check_overflow_risks(content, relpath, result.issues)
        check_100vh_pitfall(content, relpath, result.issues)
        check_text_overflow(content, relpath, result.issues)
        check_touch_targets(content, relpath, result.issues)
        check_responsive_breakpoints(content, relpath, result.issues)
        check_tailwind_issues(content, relpath, result.issues)

        if not safe_area_checked and f.suffix in CSS_EXTS:
            check_safe_area(content, relpath, result.issues, all_css)
            safe_area_checked = True

    # Deduplicate info-level safe-area warnings
    seen_cats = set()
    deduped = []
    for issue in result.issues:
        key = (issue.category, issue.message) if issue.severity == "info" and issue.line is None else id(issue)
        if key not in seen_cats:
            seen_cats.add(key)
            deduped.append(issue)
    result.issues = deduped

    # Summary
    result.summary = {
        "total": len(result.issues),
        "errors": sum(1 for i in result.issues if i.severity == "error"),
        "warnings": sum(1 for i in result.issues if i.severity == "warning"),
        "info": sum(1 for i in result.issues if i.severity == "info"),
        "categories": list(set(i.category for i in result.issues)),
    }

    return result


def format_text(result: ScanResult) -> str:
    lines = [
        f"Mobile Adaptation Scan: {result.project_path}",
        f"Files scanned: {result.files_scanned}",
        f"Issues found: {result.summary['total']} "
        f"({result.summary['errors']} errors, {result.summary['warnings']} warnings, {result.summary['info']} info)",
        "",
    ]

    if not result.issues:
        lines.append("No issues found.")
        return "\n".join(lines)

    for sev in ("error", "warning", "info"):
        sev_issues = [i for i in result.issues if i.severity == sev]
        if not sev_issues:
            continue
        icon = {"error": "[E]", "warning": "[W]", "info": "[I]"}[sev]
        lines.append(f"--- {sev.upper()} ({len(sev_issues)}) ---")
        for issue in sev_issues:
            loc = f"{issue.file}:{issue.line}" if issue.line else issue.file
            lines.append(f"  {icon} [{issue.category}] {loc}")
            lines.append(f"      {issue.message}")
            lines.append(f"      Fix: {issue.fix_hint}")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Scan web project for mobile adaptation issues")
    parser.add_argument("project", help="Path to the web project root")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory", file=sys.stderr)
        sys.exit(1)

    result = scan_project(root)

    if args.format == "json":
        data = {
            "project_path": result.project_path,
            "files_scanned": result.files_scanned,
            "summary": result.summary,
            "issues": [asdict(i) for i in result.issues],
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(format_text(result))


if __name__ == "__main__":
    main()
