#!/usr/bin/env python3
"""Build a validated WorkBuddy skill-only Connector distribution."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKBUDDY_DIR = ROOT / "workbuddy"

SKILLS = {
    "lovstudio-bp": {
        "source": ROOT,
        "version": "0.2.0",
        "description": (
            "根据用户目标按需编排商业计划书大纲、融资演示文稿和专业审校流程。"
        ),
    },
    "lovstudio-bp-outline": {
        "source": ROOT / "skills" / "bp-outline",
        "version": "0.1.0",
        "description": (
            "从项目材料提取事实和证据，形成投资人叙事、证据账本与商业计划书大纲。"
        ),
    },
    "lovstudio-bp-deck": {
        "source": ROOT / "skills" / "bp-deck",
        "version": "0.1.0",
        "description": (
            "将已确认的商业计划书大纲制作成结构清晰、证据可信的专业融资演示文稿。"
        ),
    },
    "lovstudio-bp-polish": {
        "source": ROOT / "skills" / "bp-polish",
        "version": "0.1.0",
        "description": (
            "审查并润色已有商业计划书大纲、PPT 或 PDF，输出逐页修改与定向重做建议。"
        ),
    },
}

ROOT_RESOURCE_FILES = ("kit.yaml",)
ROOT_RESOURCE_DIRS = ("assets", "references", "scripts")
SKILL_RESOURCES = ("assets", "references", "scripts")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the LovStudio BP WorkBuddy Connector package."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="New directory to create. It must not already exist.",
    )
    parser.add_argument(
        "--zip-path",
        type=Path,
        help="Optional ZIP path. Defaults to <output-dir>.zip.",
    )
    return parser.parse_args()


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md is missing YAML frontmatter")
    marker = text.find("\n---\n", 4)
    if marker < 0:
        raise ValueError("SKILL.md frontmatter is not closed")
    return text[4:marker], text[marker + 5 :]


def workbuddy_skill_text(
    name: str, description: str, version: str, source_text: str
) -> str:
    _, body = split_frontmatter(source_text)
    if name == "lovstudio-bp":
        body = body.replace(
            "$KIT_DIR/skills/bp-outline/SKILL.md",
            "$KIT_DIR/../lovstudio-bp-outline/SKILL.md",
        )
        body = body.replace(
            "$KIT_DIR/skills/bp-deck/SKILL.md",
            "$KIT_DIR/../lovstudio-bp-deck/SKILL.md",
        )
        body = body.replace(
            "$KIT_DIR/skills/bp-polish/SKILL.md",
            "$KIT_DIR/../lovstudio-bp-polish/SKILL.md",
        )
    if name == "lovstudio-bp-deck":
        body = body.replace(
            "### Step 0: Resolve input and dependency",
            "### Step 0: Resolve input and WorkBuddy capabilities",
        )
        body = body.replace(
            "Resolve `lovstudio-any2deck` through the active Agent Skills environment; do not\n"
            "assume an author's private installation path.",
            "Use WorkBuddy's available presentation and document-generation capabilities. "
            "Do not\nassume an author's private installation path or require a separate "
            "LovStudio Skill.",
        )
        body = body.replace(
            "### Step 4: Generate with `lovstudio-any2deck`",
            "### Step 4: Generate with WorkBuddy",
        )
        body = body.replace(
            "Invoke `lovstudio-any2deck` using the approved outline and chosen style. Preserve the\n"
            "BP page order and evidence notes.",
            "Use WorkBuddy's presentation-generation capability with the approved outline and "
            "chosen\nstyle. Preserve the BP page order and evidence notes.",
        )

    frontmatter = (
        "---\n"
        f"name: {name}\n"
        f'description: "{description}"\n'
        f'version: "{version}"\n'
        'author: "LovStudio"\n'
        "---\n"
    )
    return frontmatter + body


def copy_skill(name: str, config: dict[str, object], skills_dir: Path) -> None:
    source_dir = Path(config["source"])
    target_dir = skills_dir / name
    target_dir.mkdir(parents=True)

    source_text = (source_dir / "SKILL.md").read_text(encoding="utf-8")
    target_text = workbuddy_skill_text(
        name=name,
        description=str(config["description"]),
        version=str(config["version"]),
        source_text=source_text,
    )
    (target_dir / "SKILL.md").write_text(target_text, encoding="utf-8")

    if name == "lovstudio-bp":
        for relative in ROOT_RESOURCE_FILES:
            source = ROOT / relative
            target = target_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        for relative in ROOT_RESOURCE_DIRS:
            ignored = ["__pycache__", "*.pyc", ".DS_Store"]
            if relative == "scripts":
                ignored.append("build_workbuddy_connector.py")
            shutil.copytree(
                ROOT / relative,
                target_dir / relative,
                ignore=shutil.ignore_patterns(*ignored),
            )
        return

    for relative in SKILL_RESOURCES:
        source = source_dir / relative
        if source.exists():
            shutil.copytree(
                source,
                target_dir / relative,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
            )


def write_zip(output_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        raise FileExistsError(f"ZIP already exists: {zip_path}")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output_dir.rglob("*")):
            if path.is_file():
                archive.write(path, Path(output_dir.name) / path.relative_to(output_dir))


def write_individual_zips(output_dir: Path, individual_dir: Path) -> None:
    if individual_dir.exists():
        raise FileExistsError(f"individual ZIP directory already exists: {individual_dir}")
    individual_dir.mkdir(parents=True)
    for skill_dir in sorted((output_dir / "skills").iterdir()):
        zip_path = individual_dir / f"{skill_dir.name}.zip"
        with zipfile.ZipFile(
            zip_path, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            for path in sorted(skill_dir.rglob("*")):
                if path.is_file():
                    archive.write(
                        path, Path(skill_dir.name) / path.relative_to(skill_dir)
                    )


def validate_frontmatter(skill_file: Path) -> list[str]:
    errors: list[str] = []
    frontmatter, body = split_frontmatter(skill_file.read_text(encoding="utf-8"))
    for field in ("name", "description", "version", "author"):
        if not re.search(rf"(?m)^{re.escape(field)}:\s*.+$", frontmatter):
            errors.append(f"{skill_file}: missing {field}")
    if not body.strip():
        errors.append(f"{skill_file}: empty body")
    return errors


def validate_package(output_dir: Path) -> None:
    errors: list[str] = []
    meta_path = output_dir / "connector-meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    required = (
        "name",
        "name_en",
        "description",
        "description_zh",
        "description_en",
        "source",
        "type",
        "version",
        "examples_zh",
        "examples_en",
    )
    for field in required:
        if field not in meta:
            errors.append(f"connector-meta.json: missing {field}")
    if meta.get("type") != "skill-only":
        errors.append('connector-meta.json: type must be "skill-only"')
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(meta.get("source", ""))):
        errors.append("connector-meta.json: source must be kebab-case")
    for field in ("examples_zh", "examples_en"):
        value = meta.get(field)
        if not isinstance(value, list) or not 2 <= len(value) <= 5:
            errors.append(f"connector-meta.json: {field} must contain 2-5 examples")

    skill_files = sorted((output_dir / "skills").glob("*/SKILL.md"))
    if len(skill_files) != len(SKILLS):
        errors.append(f"expected {len(SKILLS)} SKILL.md files, found {len(skill_files)}")
    for skill_file in skill_files:
        errors.extend(validate_frontmatter(skill_file))

    all_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in output_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".json", ".yaml", ".yml", ".svg"}
    )
    if "/Users/mark" in all_text:
        errors.append("package contains a private absolute path")
    deck_text = (
        output_dir / "skills" / "lovstudio-bp-deck" / "SKILL.md"
    ).read_text(encoding="utf-8")
    if "Requires lovstudio-any2deck" in deck_text or "Invoke `lovstudio-any2deck`" in deck_text:
        errors.append("WorkBuddy deck Skill still has a hard any2deck runtime dependency")
    root_text = (
        output_dir / "skills" / "lovstudio-bp" / "SKILL.md"
    ).read_text(encoding="utf-8")
    if "$KIT_DIR/skills/bp-" in root_text:
        errors.append("WorkBuddy controller still points at the source-repo module layout")

    if errors:
        raise ValueError("WorkBuddy package validation failed:\n- " + "\n- ".join(errors))


def build(output_dir: Path, zip_path: Path, individual_dir: Path) -> None:
    if output_dir.exists():
        raise FileExistsError(f"output directory already exists: {output_dir}")
    output_dir.mkdir(parents=True)

    for filename in ("connector-meta.json", "icon.svg", "README.md", "SUBMISSION.md"):
        shutil.copy2(WORKBUDDY_DIR / filename, output_dir / filename)

    skills_dir = output_dir / "skills"
    skills_dir.mkdir()
    for name, config in SKILLS.items():
        copy_skill(name, config, skills_dir)

    validate_package(output_dir)
    write_zip(output_dir, zip_path)
    write_individual_zips(output_dir, individual_dir)

    print(f"connector_dir={output_dir}")
    print(f"connector_zip={zip_path}")
    print(f"individual_zips={individual_dir}")
    print(f"skills={len(SKILLS)}")
    print("validation=passed")


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    zip_path = (
        args.zip_path.expanduser().resolve()
        if args.zip_path
        else Path(f"{output_dir}.zip")
    )
    individual_dir = output_dir.parent / f"{output_dir.name}-individual"
    try:
        build(output_dir, zip_path, individual_dir)
    except (FileExistsError, ValueError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
