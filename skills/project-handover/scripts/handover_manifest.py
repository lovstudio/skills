#!/usr/bin/env python3
"""Integrity record for a handover package, and a check that the handover document points at real files.

  python3 handover_manifest.py build  <package_dir>                 # write MANIFEST.tsv (path, bytes, sha256)
  python3 handover_manifest.py verify <package_dir>                 # after unpacking: missing, changed, extra files
  python3 handover_manifest.py check-refs <package_dir> [doc.md ...]  # every relative path a document names exists

check-refs reads `backticked` tokens and Markdown link targets that look like package paths (a known file suffix, or a
first folder the package really has) and reports the ones that do not exist. Tokens with spaces, "…", "*", "<", "{"
or a URL scheme are skipped; --ignore PREFIX skips paths created later (an install's node_modules). A name that exists
elsewhere in the package counts as found, since documents often name a file relative to a subfolder.
Defaults to HANDOVER.md and AGENTS.md.
verify exits 1 on any problem, so it can gate an acceptance run."""
import argparse
import hashlib
import re
import sys
from pathlib import Path

NAME = "MANIFEST.tsv"
JUNK = {".DS_Store", "Thumbs.db"}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def files(pkg):
    for p in sorted(pkg.rglob("*")):
        if p.is_file() and p.name != NAME and p.name not in JUNK and "__MACOSX" not in p.parts and not p.name.startswith("._"):
            yield p


def build(pkg):
    rows = []
    total = 0
    for p in files(pkg):
        size = p.stat().st_size
        total += size
        rows.append(f"{p.relative_to(pkg).as_posix()}\t{size}\t{sha256(p)}")
    (pkg / NAME).write_text("path\tbytes\tsha256\n" + "\n".join(rows) + "\n", encoding="utf-8")
    print(f"{NAME}: {len(rows)} files, {total / 1e9:.2f} GB")


def verify(pkg):
    mf = pkg / NAME
    if not mf.exists():
        sys.exit(f"no {NAME} in {pkg}")
    listed = {}
    for line in mf.read_text(encoding="utf-8").splitlines()[1:]:
        if line.strip():
            path, size, digest = line.split("\t")
            listed[path] = (int(size), digest)
    missing, changed = [], []
    for path, (size, digest) in listed.items():
        p = pkg / path
        if not p.is_file():
            missing.append(path)
        elif p.stat().st_size != size or sha256(p) != digest:
            changed.append(path)
    extra = [p.relative_to(pkg).as_posix() for p in files(pkg) if p.relative_to(pkg).as_posix() not in listed]
    print(f"manifest: {len(listed)} files listed; {len(missing)} missing, {len(changed)} changed, {len(extra)} extra")
    for label, items in (("missing", missing), ("changed", changed), ("extra", extra)):
        for x in items[:30]:
            print(f"  {label}: {x}")
    if missing or changed or extra:
        sys.exit(1)


TOKEN = re.compile(r"`([^`\n]+)`|\]\(([^)\s]+)\)")
FILE_SUFFIX = re.compile(r"\.(md|txt|json|jsonl|tsv|csv|yaml|yml|toml|py|js|mjs|cjs|ts|tsx|jsx|sh|swift|html|css|mp4|mov|"
                         r"wav|mp3|png|jpg|jpeg|webp|svg|pdf|docx|xlsx|pptx|psd|zip|ttf|otf|srt|vtt|log)$", re.I)


def check_refs(pkg, docs, ignore):
    bad = 0
    checked = 0
    top = {p.name for p in pkg.iterdir()}
    for d in docs:
        doc = pkg / d
        if not doc.exists():
            print(f"skip (not in package): {d}")
            continue
        for m in TOKEN.finditer(doc.read_text(encoding="utf-8")):
            t = (m.group(1) or m.group(2) or "").strip()
            if not t or re.search(r"[\s…*<>{}]|^[a-z]+://|^#|^\$|^-", t) or t.startswith(("/", "~")):
                continue
            if "=" in t or "(" in t or t.startswith(("npx ", "python", "pnpm")):
                continue
            t = t.split(":")[0] if re.search(r":\d+$", t) else t
            first = t.split("/")[0]
            # a path only when it names a file type, or starts at a folder the package really has (model ids such as
            # vendor/model-1.2 and runtime folders such as node_modules/ are not package paths)
            if not FILE_SUFFIX.search(t.rstrip("/")) and first not in top and not (doc.parent / first).exists():
                continue
            if any(t.startswith(i.rstrip("*")) for i in ignore):
                continue
            checked += 1
            cands = [pkg / t, doc.parent / t]
            if not any(c.exists() for c in cands) and not list(pkg.rglob(Path(t).name))[:1]:
                bad += 1
                print(f"  not found: {t}   ({d})")
    print(f"check-refs: {checked} path references, {bad} not found")
    if bad:
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description="Build or verify MANIFEST.tsv; check paths named by handover docs.")
    ap.add_argument("command", choices=["build", "verify", "check-refs"])
    ap.add_argument("package_dir")
    ap.add_argument("docs", nargs="*", default=["HANDOVER.md", "AGENTS.md"])
    ap.add_argument("--ignore", action="append", default=[], help="path prefix check-refs should skip (created later, e.g. by an install)")
    args = ap.parse_args()
    pkg = Path(args.package_dir).resolve()
    {"build": lambda: build(pkg), "verify": lambda: verify(pkg), "check-refs": lambda: check_refs(pkg, args.docs, args.ignore)}[args.command]()


if __name__ == "__main__":
    main()
