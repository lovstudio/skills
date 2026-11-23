#!/usr/bin/env python3
"""Replace the sender's absolute paths in a staged handover package with neutral placeholders.

  python3 handover_sanitize.py <package_dir>                       # dry run: which files would change, by folder
  python3 handover_sanitize.py <package_dir> --apply               # rewrite them
  python3 handover_sanitize.py <package_dir> --root "$(pwd)=<项目根>" --protect "app/src/**" --apply   # run from the project root

Only text files with the listed suffixes are touched (logs, reports, job records, manifests of generated takes).
Every --root PREFIX=PLACEHOLDER is replaced first (longest first); any other path under the home directory becomes
--home-placeholder. Files matching --protect are never changed, and a changed file whose name looks functional
(package.json, *.config.*, lockfiles, source code) is listed separately: a path the program reads at run time must be
made relative in the source project instead, not masked here. Review the dry run before --apply."""
import argparse
import fnmatch
import os
import re
from pathlib import Path

DEFAULT_SUFFIXES = ".json,.jsonl,.txt,.md,.tsv,.csv,.log,.src,.yaml,.yml"
FUNCTIONAL = ["package.json", "*.config.*", "*.lock", "*-lock.*", "pnpm-workspace.yaml", "tsconfig*.json",
              "*.py", "*.js", "*.mjs", "*.cjs", "*.ts", "*.tsx", "*.sh", "*.swift", "Makefile", "Dockerfile"]


def main():
    ap = argparse.ArgumentParser(description="Mask the sender's absolute paths inside a staged handover package.")
    ap.add_argument("package_dir")
    ap.add_argument("--root", action="append", default=[], help="PREFIX=PLACEHOLDER, e.g. the project root; repeatable")
    ap.add_argument("--home", default=os.path.expanduser("~"), help="home directory whose other paths are masked")
    ap.add_argument("--home-placeholder", default="<原作者本机路径>")
    ap.add_argument("--suffixes", default=DEFAULT_SUFFIXES, help="comma-separated text suffixes to rewrite")
    ap.add_argument("--protect", action="append", default=[], help="glob (relative to the package) never to change")
    ap.add_argument("--apply", action="store_true", help="write the changes (default is a dry run)")
    args = ap.parse_args()

    pkg = Path(args.package_dir).resolve()
    roots = []
    for r in args.root:
        if "=" not in r:
            raise SystemExit(f"--root needs PREFIX=PLACEHOLDER: {r}")
        a, b = r.split("=", 1)
        roots.append((a.rstrip("/"), b))
    roots.sort(key=lambda x: -len(x[0]))
    home = args.home.rstrip("/")
    home_re = re.compile(re.escape(home) + r"/[^\s\"'<>,;)\]}]*")
    suffixes = {s.strip().lower() for s in args.suffixes.split(",") if s.strip()}

    changed, functional, protected_hits = {}, [], []
    for p in sorted(pkg.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in suffixes:
            continue
        rel = p.relative_to(pkg).as_posix()
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if home + "/" not in text:
            continue
        if any(fnmatch.fnmatch(rel, g) for g in args.protect):
            protected_hits.append(rel)
            continue
        new = text
        for a, b in roots:
            new = new.replace(a, b)
        new = home_re.sub(args.home_placeholder, new)
        if new == text:
            continue
        folder = str(Path(rel).parent)
        changed.setdefault(folder, []).append(rel)
        if any(fnmatch.fnmatch(p.name, g) for g in FUNCTIONAL):
            functional.append(rel)
        if args.apply:
            p.write_text(new, encoding="utf-8")

    n = sum(len(v) for v in changed.values())
    print(f"{'rewrote' if args.apply else 'would rewrite'} {n} files in {len(changed)} folders" + ("" if args.apply else " (dry run)"))
    for folder, files in sorted(changed.items(), key=lambda x: (-len(x[1]), x[0])):
        print(f"  {len(files):>4}  {folder}/")
    if functional:
        print("FUNCTIONAL-LOOKING files among them (fix the path in the source project instead, or --protect them):")
        for f in functional:
            print("   ", f)
    if protected_hits:
        print(f"protected files that still contain {home}/ (left as they are):")
        for f in protected_hits:
            print("   ", f)
    remaining = []
    if args.apply:
        for p in pkg.rglob("*"):
            if p.is_file() and p.suffix.lower() in suffixes:
                try:
                    if home + "/" in p.read_text(encoding="utf-8"):
                        remaining.append(p.relative_to(pkg).as_posix())
                except (UnicodeDecodeError, OSError):
                    pass
        print(f"text files still containing {home}/: {len(remaining)}")
        for f in remaining[:20]:
            print("   ", f)


if __name__ == "__main__":
    main()
