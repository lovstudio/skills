#!/usr/bin/env python3
"""Copy the parts of a project that travel into a handover package, from an explicit plan.

  python3 handover_stage.py plan.json --dry-run    # what would be copied, item by item, with sizes
  python3 handover_stage.py plan.json              # copy (refuses a non-empty destination unless --update)

plan.json (relative paths resolve from the plan file's directory):
  {
    "source": "../..",                                   # the project root
    "dest": "output/handover/<package-name>",            # relative to source unless absolute
    "exclude_everywhere": [".DS_Store", "__pycache__", "*.pyc", "Thumbs.db"],
    "items": [
      {"path": "docs/requirements.md"},                  # one file
      {"path": "materials"},                             # a whole directory
      {"path": "app", "exclude": ["node_modules", "tools/.bin"]},
      {"path": "qc", "only": ["*.md", "*.json"]},        # only these file names, anywhere below
      {"path": "releases", "only": ["*.md", "*-2.5.0.apk"]}
    ]
  }
An exclude pattern without "/" matches any path component (like rsync); one with "/" matches the path relative to the
item, or anything below it. "only" filters file names. Nothing under the destination is ever copied, so the package
may live inside the project. Symbolic links are copied as the file or directory they point to, with a warning."""
import argparse
import fnmatch
import json
import shutil
import sys
from pathlib import Path


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024


def excluded(rel_parts, patterns):
    rel = "/".join(rel_parts)
    for pat in patterns:
        if "/" in pat:
            p = pat.rstrip("/")
            if fnmatch.fnmatch(rel, p) or rel.startswith(p + "/"):
                return True
        elif any(fnmatch.fnmatch(part, pat) for part in rel_parts):
            return True
    return False


def collect(src_root, dest, item, everywhere):
    base = (src_root / item["path"]).resolve()
    if not base.exists():
        raise SystemExit(f"missing in source: {item['path']}")
    excl = list(everywhere) + list(item.get("exclude", []))
    only = item.get("only")
    out, warnings = [], []
    if base.is_file():
        cands = [base]
    else:
        cands = [p for p in base.rglob("*") if p.is_file()]
    for p in sorted(cands):
        try:
            if dest == p.resolve() or dest in p.resolve().parents:
                continue
        except OSError:
            continue
        rel_in_item = p.relative_to(base).parts if p != base else (p.name,)
        if excluded(rel_in_item, excl):
            continue
        if only and not any(fnmatch.fnmatch(p.name, o) for o in only):
            continue
        if p.is_symlink():
            warnings.append(f"symlink copied as its target: {p.relative_to(src_root)}")
        out.append(p)
    return out, warnings


def main():
    ap = argparse.ArgumentParser(description="Stage a handover package from an explicit include plan.")
    ap.add_argument("plan")
    ap.add_argument("--dry-run", action="store_true", help="list what would be copied; copy nothing")
    ap.add_argument("--update", action="store_true", help="copy into an existing destination, overwriting same paths")
    args = ap.parse_args()

    plan_path = Path(args.plan).resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    src_root = (plan_path.parent / plan["source"]).resolve() if not Path(plan["source"]).is_absolute() else Path(plan["source"]).resolve()
    dest = Path(plan["dest"])
    dest = (dest if dest.is_absolute() else src_root / dest).resolve()
    everywhere = plan.get("exclude_everywhere", [".DS_Store", "__pycache__", "*.pyc", "Thumbs.db"])

    if not args.dry_run and dest.exists() and any(dest.iterdir()) and not args.update:
        sys.exit(f"destination is not empty: {dest} (use --update to copy over it, or choose a new version folder)")

    grand_n = grand_b = 0
    all_warnings = []
    seen = set()
    for item in plan["items"]:
        found, warnings = collect(src_root, dest, item, everywhere)
        all_warnings += warnings
        files = [f for f in found if f not in seen]  # items may overlap: count and copy each file once
        seen.update(files)
        size = sum(f.stat().st_size for f in files)
        grand_n += len(files)
        grand_b += size
        dup = len(found) - len(files)
        print(f"{human(size):>10}  {len(files):>6} files  {item['path']}" + (f"  ({dup} already in an earlier item)" if dup else ""))
        if args.dry_run:
            continue
        for f in files:
            rel = f.relative_to(src_root)
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target, follow_symlinks=True)
    print(f"{human(grand_b):>10}  {grand_n:>6} files  total -> {dest}" + ("  (dry run, nothing copied)" if args.dry_run else ""))
    for w in all_warnings[:20]:
        print("warning:", w)


if __name__ == "__main__":
    main()
