#!/usr/bin/env python3
"""
Inventory a source folder for the incremental docs build.

Walks a folder (a code repo, an article collection, a mixed knowledge dump —
they're all just "a folder of source material"), classifies each file, and emits
a JSON manifest the agent uses to drive the incremental authoring loop.

It does NOT read file *contents* into the manifest (the agent does that, one unit
at a time). It only enumerates, classifies, guesses titles cheaply, and orders
files so overview material comes first.

Usage:
    python3 inventory.py --src ./my-folder
    python3 inventory.py --src ./my-folder --out manifest.json
    python3 inventory.py --src ./my-folder --max-bytes 2000000

Output (JSON):
    {
      "root": "/abs/path",
      "counts": {"article": 12, "code": 30, "image": 40, ...},
      "units": [
        {"path": "README.md", "kind": "article", "title": "...", "bytes": 1234,
         "order": 0, "images": []},
        ...
      ]
    }
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Extension → kind
TEXT_DOC = {".md", ".mdx", ".markdown", ".rst", ".txt", ".adoc", ".org"}
IMAGE = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif", ".bmp",
         ".heic", ".heif", ".tiff"}
DATA = {".json", ".yaml", ".yml", ".toml", ".csv", ".tsv", ".xml", ".ini"}
CODE = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".kt",
        ".rb", ".php", ".c", ".h", ".cpp", ".hpp", ".cs", ".swift", ".sh",
        ".lua", ".sql", ".vue", ".svelte", ".scala", ".clj", ".ex", ".dart"}
PDF = {".pdf"}
OFFICE = {".docx", ".pptx", ".xlsx", ".doc", ".ppt", ".xls"}

# Directories never worth walking.
SKIP_DIRS = {
    ".git", "node_modules", ".next", "dist", "build", "out", "target",
    "__pycache__", ".venv", "venv", ".idea", ".vscode", "coverage",
    ".turbo", ".cache", "vendor", ".pnpm-store", ".obsidian",
}

# Overview-ish names float to the front of the reading order.
OVERVIEW_HINTS = ("readme", "index", "intro", "introduction", "overview",
                  "start", "getting-started", "about", "_index", "home")


def classify(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in IMAGE:
        return "image"
    if ext in TEXT_DOC:
        return "article"
    if ext in CODE:
        return "code"
    if ext in PDF:
        return "pdf"
    if ext in OFFICE:
        return "office"
    if ext in DATA:
        return "data"
    return "other"


def guess_title(path: Path, kind: str, max_read: int = 4096) -> str:
    """Cheap title guess: markdown frontmatter title, first ATX heading, or
    a humanized filename."""
    stem = path.stem.replace("-", " ").replace("_", " ").strip()
    if kind != "article":
        return stem
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:max_read]
    except OSError:
        return stem
    # YAML frontmatter title
    m = re.search(r"^---\s*\n(.*?)\n---", head, re.DOTALL)
    if m:
        t = re.search(r"^title:\s*(.+)$", m.group(1), re.MULTILINE)
        if t:
            return t.group(1).strip().strip('"\'')
    # First ATX heading
    h = re.search(r"^#\s+(.+)$", head, re.MULTILINE)
    if h:
        return h.group(1).strip()
    return stem


def order_key(rel: str, kind: str):
    """Overview material first, then articles, then code, then the rest;
    shallower paths before deeper ones; alpha within a level."""
    name = rel.lower()
    overview = 0 if any(h in os.path.basename(name) for h in OVERVIEW_HINTS) else 1
    kind_rank = {"article": 0, "pdf": 1, "office": 1, "code": 2,
                 "data": 3, "image": 4, "other": 5}.get(kind, 5)
    depth = name.count("/")
    return (overview, kind_rank, depth, name)


def walk(root: Path, max_bytes: int):
    units = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if fn.startswith("."):
                continue
            p = Path(dirpath) / fn
            try:
                size = p.stat().st_size
            except OSError:
                continue
            kind = classify(p)
            rel = str(p.relative_to(root))
            unit = {
                "path": rel,
                "kind": kind,
                "bytes": size,
                "title": guess_title(p, kind) if size <= max_bytes else p.stem,
            }
            units.append(unit)
    units.sort(key=lambda u: order_key(u["path"], u["kind"]))
    for i, u in enumerate(units):
        u["order"] = i
    return units


def main():
    ap = argparse.ArgumentParser(description="Inventory a source folder for incremental docs")
    ap.add_argument("--src", required=True, help="Source folder to inventory")
    ap.add_argument("--out", default="", help="Write manifest JSON here (default: stdout)")
    ap.add_argument("--max-bytes", type=int, default=2_000_000,
                    help="Skip title-reading files larger than this (default 2MB)")
    args = ap.parse_args()

    root = Path(os.path.expanduser(args.src)).resolve()
    if not root.is_dir():
        sys.exit(f"ERROR: not a directory: {root}")

    units = walk(root, args.max_bytes)
    counts = {}
    for u in units:
        counts[u["kind"]] = counts.get(u["kind"], 0) + 1

    manifest = {"root": str(root), "counts": counts, "units": units}
    text = json.dumps(manifest, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"✓ {len(units)} units → {args.out}", file=sys.stderr)
        print("  " + ", ".join(f"{k}:{v}" for k, v in sorted(counts.items())), file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
