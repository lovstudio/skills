#!/usr/bin/env python3
"""Zip a handover package so it unpacks cleanly on macOS, Windows and Linux.

  python3 handover_pack.py <package_dir> [--out <zip>]     # default: <package_dir>.zip next to the folder
  python3 handover_pack.py --check <zip>                   # list macOS/Windows junk inside an existing zip

The archive keeps the package folder as its top level, stores UTF-8 names, uses ZIP64 for large packages, and never
contains __MACOSX/, ._* resource forks, .DS_Store or Thumbs.db (Finder's "Compress" and `ditto --sequesterRsrc` add
them). Already-compressed media are stored, everything else is deflated. Prints the entry count, size and SHA-256 to
quote to the recipient."""
import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

STORE = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".mp3", ".m4a", ".aac", ".ogg", ".opus", ".flac", ".jpg", ".jpeg",
         ".png", ".webp", ".gif", ".avif", ".heic", ".zip", ".gz", ".tgz", ".xz", ".7z", ".rar", ".woff", ".woff2",
         ".pdf", ".docx", ".xlsx", ".pptx", ".psd"}


def junk(name):
    parts = name.split("/")
    return any(p == "__MACOSX" or p.startswith("._") or p in (".DS_Store", "Thumbs.db") for p in parts)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def check(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
    bad = [n for n in names if junk(n)]
    print(f"{zip_path}: {len(names)} entries, {len(bad)} junk")
    for n in bad[:30]:
        print("  ", n)
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description="Zip a handover package without platform junk.")
    ap.add_argument("package_dir", nargs="?")
    ap.add_argument("--out", help="zip path (default: <package_dir>.zip)")
    ap.add_argument("--check", metavar="ZIP", help="only inspect an existing zip for junk entries")
    args = ap.parse_args()
    if args.check:
        sys.exit(check(args.check))
    if not args.package_dir:
        ap.error("package_dir is required unless --check is given")

    pkg = Path(args.package_dir).resolve()
    out = Path(args.out).resolve() if args.out else pkg.with_suffix(".zip") if pkg.suffix == "" else Path(str(pkg) + ".zip")
    if out.exists():
        out.unlink()
    top = pkg.name
    n = skipped = 0
    with zipfile.ZipFile(out, "w", allowZip64=True) as z:
        for p in sorted(pkg.rglob("*")):
            rel = p.relative_to(pkg).as_posix()
            if junk(rel):
                skipped += 1
                continue
            arc = f"{top}/{rel}"
            if p.is_dir():
                continue
            method = zipfile.ZIP_STORED if p.suffix.lower() in STORE else zipfile.ZIP_DEFLATED
            z.write(p, arc, compress_type=method, compresslevel=6 if method == zipfile.ZIP_DEFLATED else None)
            n += 1
    size = out.stat().st_size
    print(f"{out.name}: {n} files, {size / 1e9:.2f} GB, skipped {skipped} junk entries")
    print(f"sha256 {sha256(out)}")
    sys.exit(check(out))


if __name__ == "__main__":
    main()
