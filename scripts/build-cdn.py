#!/usr/bin/env python3
"""Build static CDN artifacts for Lovstudio skill distribution.

The CDN layer is deliberately independent from the target agent sandbox:
WorkBuddy can download these artifacts in its own process, verify sha256, and
then inject the unpacked skill into the target agent's local skill directory.

Output layout:
    dist/cdn/
      registry.json
      registry.min.json
      SHA256SUMS
      packages/<name>/<version>/<name>-<version>.skillpack.zip
      packages/<name>/latest/<name>.skillpack.zip

Run from this index repo:
    python3 scripts/build-cdn.py --base-url https://cdn.agentskills.cn/lovstudio/skills
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import yaml


DEFAULT_EXCLUDES = [
    ".DS_Store",
    ".git",
    ".github",
    ".next",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
    "*.pyc",
    "*.pyo",
]

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "dist" / "cdn"
ZIP_DATE_TIME = (1980, 1, 1, 0, 0, 0)


@dataclass(frozen=True)
class PackageFile:
    path: str
    size: int
    sha256: str


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def skill_id(name: str, namespace: str) -> str:
    return f"{namespace}-{name}"


def read_frontmatter(skill_md: Path) -> dict[str, Any]:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


def load_skills(root: Path, include_test: bool) -> list[dict[str, Any]]:
    with (root / "skills.yaml").open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    skills = data.get("skills") or []
    if include_test:
        return skills
    return [s for s in skills if not s.get("test")]


def is_installable(skill: dict[str, Any]) -> bool:
    return (not skill.get("paid")) or bool(skill.get("encrypted_bundle"))


def safe_segment(value: str) -> str:
    value = value.strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", value):
        raise ValueError(f"unsafe path segment: {value!r}")
    return value


def should_exclude(rel: Path, patterns: list[str]) -> bool:
    parts = rel.parts
    for part in parts:
        for pattern in patterns:
            if fnmatch.fnmatch(part, pattern):
                return True
    rel_posix = rel.as_posix()
    return any(fnmatch.fnmatch(rel_posix, pattern) for pattern in patterns)


def iter_skill_files(skill_dir: Path, excludes: list[str]) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    skipped_symlinks: list[str] = []
    for path in skill_dir.rglob("*"):
        rel = path.relative_to(skill_dir)
        if should_exclude(rel, excludes):
            continue
        if path.is_symlink():
            skipped_symlinks.append(rel.as_posix())
            continue
        if path.is_file():
            files.append(path)
    return (
        sorted(files, key=lambda p: p.relative_to(skill_dir).as_posix()),
        sorted(skipped_symlinks),
    )


def package_manifest(
    *,
    generated_at: str,
    namespace: str,
    skill: dict[str, Any],
    version: str,
    skill_dir: Path,
    files: list[Path],
    skipped_symlinks: list[str],
) -> tuple[dict[str, Any], list[PackageFile]]:
    package_files: list[PackageFile] = []
    for path in files:
        rel = path.relative_to(skill_dir).as_posix()
        package_files.append(
            PackageFile(path=rel, size=path.stat().st_size, sha256=sha256_file(path))
        )

    manifest = {
        "schema_version": 1,
        "format": "lovstudio.skillpack",
        "id": skill_id(str(skill["name"]), namespace),
        "namespace": namespace,
        "name": skill["name"],
        "version": version,
        "generated_at": generated_at,
        "entrypoint": "SKILL.md",
        "paid": bool(skill.get("paid")),
        "encrypted_bundle": bool(skill.get("encrypted_bundle")),
        "source": {
            "repo": skill.get("repo"),
            "skill_path": skill.get("skill_path", ""),
        },
        "files": [f.__dict__ for f in package_files],
    }
    if skipped_symlinks:
        manifest["skipped"] = {"symlinks": skipped_symlinks}
    return manifest, package_files


def zip_write_bytes(zf: zipfile.ZipFile, arcname: str, data: bytes) -> None:
    info = zipfile.ZipInfo(arcname)
    info.date_time = ZIP_DATE_TIME
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    zf.writestr(info, data)


def zip_write_file(zf: zipfile.ZipFile, src: Path, arcname: str) -> None:
    info = zipfile.ZipInfo(arcname)
    info.date_time = ZIP_DATE_TIME
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    zf.writestr(info, src.read_bytes())


def make_package(
    *,
    skill: dict[str, Any],
    version: str,
    skill_dir: Path,
    out_file: Path,
    generated_at: str,
    namespace: str,
    excludes: list[str],
) -> dict[str, Any]:
    files, skipped_symlinks = iter_skill_files(skill_dir, excludes)
    if not any(p.name == "SKILL.md" and p.parent == skill_dir for p in files):
        raise RuntimeError(f"{skill['name']}: SKILL.md missing from {skill_dir}")
    if skill.get("encrypted_bundle") and not (skill_dir / "MANIFEST.enc.json").exists():
        raise RuntimeError(f"{skill['name']}: encrypted_bundle=true but MANIFEST.enc.json is missing")

    manifest, package_files = package_manifest(
        generated_at=generated_at,
        namespace=namespace,
        skill=skill,
        version=version,
        skill_dir=skill_dir,
        files=files,
        skipped_symlinks=skipped_symlinks,
    )

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip", dir=str(out_file.parent)) as tmp:
        tmp_path = Path(tmp.name)
    try:
        with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            payload = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
            zip_write_bytes(zf, "skillpack.json", payload)
            for path in files:
                arcname = path.relative_to(skill_dir).as_posix()
                zip_write_file(zf, path, arcname)
        tmp_path.replace(out_file)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    return {
        "sha256": sha256_file(out_file),
        "size": out_file.stat().st_size,
        "file_count": len(package_files),
        "skipped_symlink_count": len(skipped_symlinks),
        "content_sha256": sha256_bytes(
            json.dumps([f.__dict__ for f in package_files], sort_keys=True).encode("utf-8")
        ),
    }


def url_for(base_url: str, rel: Path) -> str:
    rel_posix = rel.as_posix()
    if not base_url:
        return rel_posix
    quoted = "/".join(quote(part) for part in rel_posix.split("/"))
    return f"{base_url.rstrip('/')}/{quoted}"


def version_for(skill: dict[str, Any], skill_dir: Path) -> str:
    if skill.get("version"):
        return str(skill["version"])
    fm = read_frontmatter(skill_dir / "SKILL.md")
    return str(fm.get("version") or "0.1.0")


def git_value(root: Path, args: list[str]) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def write_json(path: Path, data: dict[str, Any], *, minify: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {"ensure_ascii": False, "sort_keys": True}
    if minify:
        text = json.dumps(data, separators=(",", ":"), **kwargs)
    else:
        text = json.dumps(data, indent=2, **kwargs)
    path.write_text(text + "\n", encoding="utf-8")


def build_registry(
    *,
    root: Path,
    out: Path,
    base_url: str,
    namespace: str,
    include_test: bool,
    allow_missing: bool,
    clean: bool,
    excludes: list[str],
) -> int:
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if clean and out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    skills = load_skills(root, include_test)
    installable = [s for s in skills if is_installable(s)]
    skipped = [s["name"] for s in skills if not is_installable(s)]
    registry_skills: list[dict[str, Any]] = []
    missing: list[str] = []
    sums: list[str] = []

    for skill in installable:
        name = safe_segment(str(skill["name"]))
        skill_dir = root / "skills" / name
        if not skill_dir.exists():
            missing.append(name)
            if allow_missing:
                continue
            continue

        version = safe_segment(version_for(skill, skill_dir))
        package_rel = Path("packages") / name / version / f"{name}-{version}.skillpack.zip"
        latest_rel = Path("packages") / name / "latest" / f"{name}.skillpack.zip"
        package_path = out / package_rel
        stats = make_package(
            skill=skill,
            version=version,
            skill_dir=skill_dir,
            out_file=package_path,
            generated_at=generated_at,
            namespace=namespace,
            excludes=excludes,
        )

        latest_path = out / latest_rel
        latest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(package_path, latest_path)

        sha_path = package_path.with_suffix(package_path.suffix + ".sha256")
        sha_text = f"{stats['sha256']}  {package_path.name}\n"
        sha_path.write_text(sha_text, encoding="utf-8")
        latest_path.with_suffix(latest_path.suffix + ".sha256").write_text(
            f"{stats['sha256']}  {latest_path.name}\n",
            encoding="utf-8",
        )
        sums.append(f"{stats['sha256']}  {package_rel.as_posix()}")

        package_url = url_for(base_url, package_rel)
        latest_url = url_for(base_url, latest_rel)
        registry_skills.append(
            {
                "id": skill_id(name, namespace),
                "name": name,
                "aliases": [name, skill_id(name, namespace)],
                "display_name": skill.get("display_name"),
                "name_zh": skill.get("name_zh"),
                "category": skill.get("category"),
                "version": version,
                "paid": bool(skill.get("paid")),
                "encrypted_bundle": bool(skill.get("encrypted_bundle")),
                "featured": bool(skill.get("featured")),
                "recommended_by": skill.get("recommended_by"),
                "description": skill.get("description"),
                "tagline_en": skill.get("tagline_en"),
                "tagline_zh": skill.get("tagline_zh"),
                "repo": skill.get("repo"),
                "skill_path": skill.get("skill_path", ""),
                "depends_on": skill.get("depends_on") or [],
                "related": skill.get("related") or [],
                "package": {
                    "format": "lovstudio.skillpack.zip",
                    "entrypoint": "SKILL.md",
                    "path": package_rel.as_posix(),
                    "url": package_url,
                    "latest_path": latest_rel.as_posix(),
                    "latest_url": latest_url,
                    "sha256": stats["sha256"],
                    "size": stats["size"],
                    "file_count": stats["file_count"],
                    "skipped_symlink_count": stats["skipped_symlink_count"],
                    "content_sha256": stats["content_sha256"],
                    "content_type": "application/zip",
                },
                "sources": [
                    {
                        "type": "cdn",
                        "url": latest_url,
                        "versioned_url": package_url,
                        "sha256": stats["sha256"],
                    },
                    {
                        "type": "github",
                        "repo": skill.get("repo"),
                        "skill_path": skill.get("skill_path", ""),
                    },
                ],
            }
        )

    if missing and not allow_missing:
        for name in missing:
            print(f"missing installable skill dir: skills/{name}", file=sys.stderr)
        return 2

    registry = {
        "schema_version": 1,
        "generated_at": generated_at,
        "namespace": namespace,
        "base_url": base_url,
        "index": {
            "name": root.name,
            "repo": git_value(root, ["config", "--get", "remote.origin.url"]),
            "commit": git_value(root, ["rev-parse", "HEAD"]),
        },
        "counts": {
            "total": len(skills),
            "installable": len(registry_skills),
            "skipped": len(skipped),
            "missing": len(missing),
        },
        "skipped": skipped,
        "missing": missing,
        "skills": registry_skills,
    }
    write_json(out / "registry.json", registry)
    write_json(out / "registry.min.json", registry, minify=True)
    (out / "SHA256SUMS").write_text("\n".join(sorted(sums)) + "\n", encoding="utf-8")

    print(f"built {len(registry_skills)} skill package(s) -> {out}")
    print(f"registry: {out / 'registry.json'}")
    if skipped:
        print(f"skipped non-installable: {', '.join(skipped)}")
    if missing:
        print(f"missing: {', '.join(missing)}")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Index repo root containing skills.yaml and skills/.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output directory for CDN artifacts.")
    parser.add_argument("--base-url", default=os.environ.get("LOVSTUDIO_SKILLS_CDN_BASE_URL", ""))
    parser.add_argument("--namespace", default="lov")
    parser.add_argument("--include-test", action="store_true", help="Include skills marked test:true.")
    parser.add_argument("--allow-missing", action="store_true", help="Build registry even if a skill dir is missing.")
    parser.add_argument("--no-clean", action="store_true", help="Do not delete the output directory before building.")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Additional exclude pattern. Can be passed multiple times.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = args.root.resolve()
    out = args.out.resolve()
    return build_registry(
        root=root,
        out=out,
        base_url=args.base_url,
        namespace=args.namespace,
        include_test=args.include_test,
        allow_missing=args.allow_missing,
        clean=not args.no_clean,
        excludes=[*DEFAULT_EXCLUDES, *args.exclude],
    )


if __name__ == "__main__":
    raise SystemExit(main())
