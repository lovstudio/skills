#!/usr/bin/env python3
"""Initialize and optionally install a portable local LovStudio Skill."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Optional, Tuple


SKILL_MD = """---
name: lov-{name}
description: >
  TODO：用 50–200 个字符说明这个 Skill 能完成什么、适用于哪些输入或任务，
  并自然包含用户会说出的中文与 English 触发语句。
license: MIT
metadata:
  author: lovstudio
  version: "0.1.0"
  tags:
    - TODO
  compatibility: "Portable Agent Skills format. TODO: list runtime requirements."
  dependencies: []
---

# {title}

TODO：用一到两句话说明用户得到的结果，不要把内部背景或实现细节写进用户制品。

## Triggers

### Activate when

- TODO：列出明确中文触发语，例如“帮我……”
- TODO: list an explicit English trigger phrase.

### Do not activate when

- TODO：列出相邻但不属于本 Skill 的任务，并说明应交给什么能力。

{user_config_section}{kit_section}## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and runtime context

- Use `SKILL_DIR` if the environment provides it.
- Otherwise infer the installed skill directory from the current skill context.
- Verify every required local module, reference, script, and asset before work.
- If a required resource is missing, name its expected relative path and stop
  before producing a partial result.

When running scripts manually:

```bash
export SKILL_DIR="/path/to/lov-{name}"
```

{user_config_runtime}### Step 1: Understand the requested outcome

- Separate internal context from user-visible output.
- Confirm the input, intended audience, expected deliverable, and evidence gaps.

### Step 2: Execute the workflow

TODO：写出可执行步骤。只有确定性操作需要自定义脚本。

### Step 3: Validate the deliverable

- Verify completeness, factual support, user-visible copy, and output paths.
- Report concrete files or results, plus any remaining evidence gaps.

## Dependencies

TODO：列出运行依赖；没有额外依赖时明确写 `None`。
"""

USER_CONFIG_SKILL_SECTION = """## User Configuration

This Skill needs persistent user-specific settings. Resolve and initialize them
through `references/user-config.md`; never hard-code one user's paths or brand.

"""

USER_CONFIG_RUNTIME = """Resolve user settings from the current request, environment, or shared profile.
On first run, infer safe values, ask once only for required fields that remain
unknown, and persist them with the user's knowledge.

"""

KIT_SECTION = """## Skill Kit Modules

This repository is a self-contained Skill Kit. At Step 0, load and verify:

{module_lines}

`kit.yaml` is the machine-readable module and pipeline manifest. Every module
listed there must ship inside this repository.

"""

README_MD = """# lov-{name}

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

TODO：用一句话说明用户获得的结果。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${{LOVSTUDIO_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}}"
ln -s "$SKILL_SOURCE_DIR" \
  "$LOVSTUDIO_SKILLS_INSTALL_DIR/lov-{name}"
```

{configuration_section}## 使用

TODO：提供两个真实示例，并说明输入与输出。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+
- PyYAML

## License

MIT
"""

README_CONFIGURATION = """## 用户配置

首次使用时按 `references/user-config.md` 初始化工作区、品牌、输出目录或
供应商偏好。显式输入始终覆盖已保存配置。

默认共享配置：

```bash
${LOVSTUDIO_SKILLS_PROFILE:-$HOME/.lovstudio/skills/profile.json}
```

"""

KIT_YAML = """name: {name}
display_name: "TODO"
version: "0.1.0"
entrypoint: lov-{name}
modules:
{module_entries}
pipelines:
  full:
{pipeline_entries}
"""

GITIGNORE = """__pycache__/
*.pyc
*.pyo
.DS_Store
.venv/
venv/
node_modules/
.env
.env.local
dist/
"""

LICENSE_MD = """MIT License

Copyright (c) 2026 LovStudio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

CHANGELOG_MD = """# Changelog

## 0.1.0

- Initial local Skill source.
"""

USER_CONFIG_MD = """# User Configuration

This Skill needs persistent settings but remains portable across users and
brands. Never store a personal absolute path in committed Skill source.

## First-run initialization

1. Prefill from the current request and project.
2. Resolve environment overrides.
3. Read the shared profile when present.
4. Infer safe defaults from the current directory and locale.
5. Ask once only for required user-facing values still missing.
6. Show the values being persisted and update the profile with the user's
   knowledge.

## Resolution order

1. Explicit CLI flags or current request.
2. Skill-specific environment variables.
3. Shared profile JSON.
4. Safe defaults.
5. One focused question for a remaining required field.

## Shared profile

```bash
${{LOVSTUDIO_SKILLS_PROFILE:-$HOME/.lovstudio/skills/profile.json}}
```

```json
{
  "user": {
    "name": "Your Name",
    "language": "zh-CN",
    "timezone": "Asia/Shanghai"
  },
  "workspace": {
    "root": "$HOME/projects",
    "output_dir": "$HOME/Documents/lov-skill-output"
  },
  "brand": {
    "name": "Your Brand",
    "site": "https://example.com",
    "profile": "$HOME/.lovstudio/skills/brand.json",
    "design_guide": "$HOME/.lovstudio/skills/design-guide.md"
  }
}
```

LovStudio uses these same fields with LovStudio values. Other users provide
their own values; there is no separate internal mode.
"""


def _expand_path(value: str) -> Path:
    return Path(os.path.expandvars(value)).expanduser()


def _nested(data: dict, dotted: str) -> Optional[str]:
    current = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return str(current) if current else None


def _load_profile() -> Tuple[Path, dict]:
    profile = _expand_path(
        os.environ.get("LOVSTUDIO_SKILLS_PROFILE")
        or str(Path.home() / ".lovstudio/skills/profile.json")
    )
    if not profile.exists():
        return profile, {}
    try:
        return profile, json.loads(profile.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON in {profile}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def _profile_first(data: dict, keys: Tuple[str, ...]) -> Optional[str]:
    for key in keys:
        value = _nested(data, key)
        if value:
            return value
    return None


def resolve_base(cli_path: str) -> Path:
    if cli_path:
        return _expand_path(cli_path)
    _, profile = _load_profile()
    if os.environ.get("LOVSTUDIO_SKILL_CREATOR_REPOS_ROOT"):
        return _expand_path(os.environ["LOVSTUDIO_SKILL_CREATOR_REPOS_ROOT"])
    profile_value = _profile_first(
        profile,
        (
            "lovstudio.skill_repos_root",
            "skills.repos_root",
            "workspace.skill_repos_root",
            "workspace.skills_root",
        ),
    )
    return _expand_path(profile_value) if profile_value else Path.cwd()


def resolve_install_dir(cli_path: str) -> Optional[Path]:
    if cli_path:
        return _expand_path(cli_path)
    if os.environ.get("LOVSTUDIO_SKILLS_INSTALL_DIR"):
        return _expand_path(os.environ["LOVSTUDIO_SKILLS_INSTALL_DIR"])
    _, profile = _load_profile()
    profile_value = _profile_first(
        profile,
        (
            "skills.install_dir",
            "lovstudio.skills_install_dir",
            "workspace.skills_install_dir",
        ),
    )
    return _expand_path(profile_value) if profile_value else None


def normalize_name(value: str) -> str:
    name = value
    if name.startswith("lov-"):
        name = name[len("lov-") :]
    if name.endswith("-skill"):
        name = name[: -len("-skill")]
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError(
            "skill name must use lowercase letters, numbers, and single hyphens only"
        )
    return name


def write_skill(path: Path, name: str, kit_section: str, user_config: bool) -> None:
    path.write_text(
        SKILL_MD.format(
            name=name,
            title=f"lov-{name} — TODO",
            kit_section=kit_section,
            user_config_section=USER_CONFIG_SKILL_SECTION if user_config else "",
            user_config_runtime=USER_CONFIG_RUNTIME if user_config else "",
        ),
        encoding="utf-8",
    )


def render_kit(name: str, modules: list[str]) -> tuple[str, str]:
    module_lines = "\n".join(
        f"- `$SKILL_DIR/skills/{module}/SKILL.md` — `lov-{module}`"
        for module in modules
    )
    module_entries = "\n".join(
        "  - id: {module}\n"
        "    skill: lov-{module}\n"
        "    path: skills/{module}".format(module=module)
        for module in modules
    )
    pipeline_entries = "\n".join(f"    - {module}" for module in modules)
    return (
        KIT_SECTION.format(module_lines=module_lines),
        KIT_YAML.format(
            name=name,
            module_entries=module_entries,
            pipeline_entries=pipeline_entries,
        ),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="Short name without lov- or -skill")
    parser.add_argument("--path", default="", help="Custom local source parent")
    parser.add_argument(
        "--install-dir",
        default="",
        help="Local agent skills directory; also resolves from env/profile",
    )
    parser.add_argument(
        "--user-config",
        action="store_true",
        help="Scaffold portable first-run user profile initialization",
    )
    parser.add_argument(
        "--kit",
        action="store_true",
        help="Create a Skill Kit controller and embedded child modules",
    )
    parser.add_argument(
        "--module",
        action="append",
        default=[],
        help="Embedded module short name; repeat for each module (requires --kit)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        name = normalize_name(args.name)
        modules = [normalize_name(module) for module in args.module]
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.module and not args.kit:
        print("ERROR: --module requires --kit", file=sys.stderr)
        return 1
    if args.kit and not modules:
        print("ERROR: --kit requires at least one --module", file=sys.stderr)
        return 1
    if len(set(modules)) != len(modules):
        print("ERROR: module names must be unique", file=sys.stderr)
        return 1
    if name in modules:
        print("ERROR: a module name must differ from the controller name", file=sys.stderr)
        return 1

    base = resolve_base(args.path)
    skill_dir = base / f"{name}-skill"
    install_dir = resolve_install_dir(args.install_dir)
    install_path = install_dir / f"lov-{name}" if install_dir else None

    if skill_dir.exists() or skill_dir.is_symlink():
        print(f"ERROR: source already exists: {skill_dir}", file=sys.stderr)
        return 1
    if install_path and (install_path.exists() or install_path.is_symlink()):
        print(f"ERROR: install target already exists: {install_path}", file=sys.stderr)
        return 1

    base.mkdir(parents=True, exist_ok=True)
    skill_dir.mkdir()
    (skill_dir / "scripts").mkdir()

    kit_section = ""
    if args.kit:
        kit_section, kit_text = render_kit(name, modules)
        (skill_dir / "kit.yaml").write_text(kit_text, encoding="utf-8")
        for module in modules:
            module_dir = skill_dir / "skills" / module
            module_dir.mkdir(parents=True)
            write_skill(module_dir / "SKILL.md", module, "", args.user_config)
            if args.user_config:
                (module_dir / "references").mkdir()
                (module_dir / "references" / "user-config.md").write_text(
                    USER_CONFIG_MD, encoding="utf-8"
                )

    write_skill(skill_dir / "SKILL.md", name, kit_section, args.user_config)
    (skill_dir / "README.md").write_text(
        README_MD.format(
            name=name,
            configuration_section=(
                README_CONFIGURATION if args.user_config else ""
            ),
        ),
        encoding="utf-8",
    )
    if args.user_config:
        (skill_dir / "references").mkdir(exist_ok=True)
        (skill_dir / "references" / "user-config.md").write_text(
            USER_CONFIG_MD, encoding="utf-8"
        )
    (skill_dir / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
    (skill_dir / "LICENSE").write_text(LICENSE_MD, encoding="utf-8")
    (skill_dir / "CHANGELOG.md").write_text(CHANGELOG_MD, encoding="utf-8")

    script_root = Path(__file__).resolve().parent
    shutil.copy2(script_root / "validate_skill.py", skill_dir / "scripts")

    if install_path:
        install_dir.mkdir(parents=True, exist_ok=True)
        install_path.symlink_to(skill_dir.resolve(), target_is_directory=True)

    kind = "Skill Kit" if args.kit else "Skill"
    print(f"created={skill_dir.resolve()}")
    print(f"kind={kind}")
    print(f"user_config={'enabled' if args.user_config else 'none'}")
    print(f"installed={install_path if install_path else 'pending'}")
    if install_path:
        print(f"install_target={install_path.resolve()}")
    print("validation=python3 scripts/validate_skill.py .")
    if not install_path:
        print("next=resolve a local agent skills directory and install the source")
    else:
        print("next=replace placeholders, validate, and exercise trigger routing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
