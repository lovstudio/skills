#!/usr/bin/env python3
"""Build a self-contained WorkBuddy Connector ZIP from local Skill source."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any

try:
    from validate_skill import (
        ValidationFailure,
        compact_text,
        split_frontmatter,
        validate_connector_meta,
        validate_source,
        validate_workbuddy_package,
    )
except ImportError as exc:
    print(
        "ERROR: scripts/validate_skill.py must be present next to this builder",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


RESOURCE_DIRS = ("assets", "cases", "prompts", "references", "scripts", "skills")
RESOURCE_FILES = ("kit.yaml",)
SKIP_DIRS = {".git", "dist", ".venv", "venv", "node_modules", "__pycache__"}
SKIP_FILES = {
    ".DS_Store",
    "build_workbuddy.py",
    "validate_skill.py",
}
SKIP_SUFFIXES = {".pyc", ".pyo"}
PUBLISHER_SOURCE = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="Skill source repository (default: current directory)",
    )
    parser.add_argument(
        "--meta",
        type=Path,
        required=True,
        help="External WorkBuddy connector-meta.json",
    )
    parser.add_argument(
        "--icon",
        type=Path,
        required=True,
        help="External market icon (.svg, .png, .jpg, or .jpeg)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="New staging directory to create",
    )
    parser.add_argument(
        "--zip-path",
        type=Path,
        help="ZIP destination (default: OUTPUT_DIR.zip)",
    )
    parser.add_argument(
        "--individual-dir",
        type=Path,
        help="Directory for independently installable Skill ZIPs",
    )
    return parser.parse_args()


def fail_on_errors(errors: list[str], label: str) -> None:
    if errors:
        raise ValueError(f"{label} failed:\n- " + "\n- ".join(errors))


def ignore_resources(_directory: str, names: list[str]) -> set[str]:
    ignored = set()
    for name in names:
        path = Path(name)
        if (
            name in SKIP_DIRS
            or name in SKIP_FILES
            or path.suffix.lower() in SKIP_SUFFIXES
        ):
            ignored.add(name)
    return ignored


def copy_source_resources(source: Path, target: Path) -> None:
    shutil.copy2(source / "SKILL.md", target / "SKILL.md")
    for filename in RESOURCE_FILES:
        candidate = source / filename
        if candidate.is_file():
            shutil.copy2(candidate, target / filename)
    for dirname in RESOURCE_DIRS:
        candidate = source / dirname
        if candidate.is_dir():
            # The publisher is itself a distributable Skill. Its validation and
            # WorkBuddy-builder scripts are runtime dependencies, while those
            # same files remain distribution tooling for every other Skill.
            ignore = None if source.resolve() == PUBLISHER_SOURCE else ignore_resources
            shutil.copytree(
                candidate,
                target / dirname,
                ignore=ignore,
            )


def make_module_self_contained(source: Path, target: Path) -> None:
    """Copy shared kit resources into a standalone module package.

    The combined entrypoint keeps `$KIT_DIR` semantics. WorkBuddy also emits
    every module as an independently installable Skill, so those siblings need
    their own copy of shared references/assets/scripts and local `$SKILL_DIR`
    references.
    """
    for dirname in ("assets", "cases", "prompts", "references", "scripts"):
        candidate = source / dirname
        if candidate.is_dir():
            shutil.copytree(
                candidate,
                target / dirname,
                dirs_exist_ok=True,
                ignore=ignore_resources,
            )
    for path in target.rglob("*.md"):
        original = path.read_text(encoding="utf-8")
        updated = original.replace("$KIT_DIR/", "$SKILL_DIR/")
        if updated != original:
            path.write_text(updated, encoding="utf-8")


def workbuddy_frontmatter(
    source_skill: Path,
    connector: dict[str, Any],
    root_source_name: str,
) -> tuple[str, str]:
    data, body = split_frontmatter(source_skill)
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        raise ValidationFailure(f"{source_skill}: metadata must be a mapping")
    source_name = compact_text(data.get("name"))
    raw_name = compact_text(connector.get("raw_name"))
    package_name = (
        raw_name
        if raw_name and source_name == root_source_name
        else source_name
    )
    fields: list[tuple[str, str]] = [
        ("name", package_name),
        ("description", compact_text(data.get("description"))),
        ("version", compact_text(metadata.get("version"))),
        ("author", compact_text(metadata.get("author"))),
        ("source_type", compact_text(connector.get("source_type"))),
    ]
    for locator in ("clawhub_slug", "skillhub_slug", "git_url"):
        value = compact_text(connector.get(locator))
        if value:
            fields.append((locator, value))
    lines = ["---"]
    for key, value in fields:
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.extend(("---", ""))
    return "\n".join(lines), body


def transform_skills(
    target: Path,
    connector: dict[str, Any],
    root_source_name: str,
) -> None:
    for skill_file in sorted(target.rglob("SKILL.md")):
        frontmatter, body = workbuddy_frontmatter(
            skill_file,
            connector,
            root_source_name,
        )
        skill_file.write_text(frontmatter + body, encoding="utf-8")


def write_zip(output_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        raise FileExistsError(f"ZIP already exists: {zip_path}")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output_dir.rglob("*")):
            if path.is_file():
                archive.write(
                    path,
                    Path(output_dir.name) / path.relative_to(output_dir),
                )


def write_individual_zips(skills_dir: Path, individual_dir: Path) -> None:
    if individual_dir.exists():
        raise FileExistsError(
            f"individual ZIP directory already exists: {individual_dir}"
        )
    individual_dir.mkdir(parents=True)
    for skill_dir in sorted(skills_dir.iterdir()):
        if not (skill_dir / "SKILL.md").is_file():
            continue
        zip_path = individual_dir / f"{skill_dir.name}.zip"
        with zipfile.ZipFile(
            zip_path, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            for path in sorted(skill_dir.rglob("*")):
                if path.is_file():
                    archive.write(
                        path,
                        Path(skill_dir.name) / path.relative_to(skill_dir),
                    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(
    source: Path,
    meta_path: Path,
    icon_path: Path,
    output_dir: Path,
    zip_path: Path,
    individual_dir: Path,
) -> None:
    source_errors: list[str] = []
    validate_source(source, source_errors, require_self_contained=True)
    validate_connector_meta(meta_path, source_errors)
    if not icon_path.is_file():
        source_errors.append(f"{icon_path}: market icon is required")
    elif icon_path.suffix.lower() not in {".svg", ".png", ".jpg", ".jpeg"}:
        source_errors.append(f"{icon_path}: unsupported market icon format")
    fail_on_errors(source_errors, "WorkBuddy input validation")

    if output_dir.exists():
        raise FileExistsError(f"output directory already exists: {output_dir}")
    if zip_path.exists():
        raise FileExistsError(f"ZIP already exists: {zip_path}")
    if individual_dir.exists():
        raise FileExistsError(
            f"individual ZIP directory already exists: {individual_dir}"
        )

    connector = json.loads(meta_path.read_text(encoding="utf-8"))
    source_data, _ = split_frontmatter(source / "SKILL.md")
    root_source_name = compact_text(source_data.get("name"))
    root_skill_name = compact_text(connector.get("raw_name")) or root_source_name

    output_dir.mkdir(parents=True)
    shutil.copy2(meta_path, output_dir / "connector-meta.json")
    shutil.copy2(icon_path, output_dir / f"icon{icon_path.suffix.lower()}")

    skills_target = output_dir / "skills"
    skill_target = skills_target / root_skill_name
    skill_target.mkdir(parents=True)
    copy_source_resources(source, skill_target)

    source_modules = source / "skills"
    if source_modules.is_dir():
        for module_source in sorted(source_modules.iterdir()):
            module_skill = module_source / "SKILL.md"
            if not module_skill.is_file():
                continue
            module_data, _ = split_frontmatter(module_skill)
            module_name = compact_text(module_data.get("name"))
            module_target = skills_target / module_name
            module_target.mkdir(parents=True)
            copy_source_resources(module_source, module_target)
            make_module_self_contained(source, module_target)

    transform_skills(skills_target, connector, root_source_name)

    package_errors: list[str] = []
    validate_workbuddy_package(output_dir, package_errors)
    fail_on_errors(package_errors, "WorkBuddy package validation")
    write_zip(output_dir, zip_path)
    write_individual_zips(skills_target, individual_dir)

    print(f"connector_dir={output_dir}")
    print(f"connector_zip={zip_path}")
    print(f"connector_sha256={sha256(zip_path)}")
    print(f"individual_zips={individual_dir}")
    print(f"entrypoint={root_skill_name}")
    print(
        "top_level_skills="
        f"{len(list(skills_target.glob('*/SKILL.md')))}"
    )
    print("validation=passed")


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    meta_path = args.meta.expanduser().resolve()
    icon_path = args.icon.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    zip_path = (
        args.zip_path.expanduser().resolve()
        if args.zip_path
        else output_dir.parent / f"{output_dir.name}.zip"
    )
    individual_dir = (
        args.individual_dir.expanduser().resolve()
        if args.individual_dir
        else output_dir.parent / f"{output_dir.name}-individual"
    )
    if not source.is_dir():
        print(f"ERROR: source directory does not exist: {source}", file=sys.stderr)
        return 2
    try:
        build(source, meta_path, icon_path, output_dir, zip_path, individual_dir)
    except (FileExistsError, ValidationFailure, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
