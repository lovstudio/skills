#!/usr/bin/env python3
"""Initialize and optionally install a portable local Skill Publisher Skill."""

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
  author: skill-publisher
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
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

{user_profile_section}{kit_section}{skill_composition_section}## Workflow (MANDATORY)

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

{user_profile_runtime}### Step 1: Understand the requested outcome

- Separate internal context from user-visible output.
- Confirm the input, intended audience, expected deliverable, and evidence gaps.
- Record one real user case before calling the Skill complete. The case must show
  the input, the prompt or minimum brief, and the output; do not invent results.

### Step 1.5: Analyze nearby Skills before implementation

- Inspect related local and installed Skills by routing contract and concrete
  input/output, not by filename alone.
- Record upstream, core, downstream, overlap, and not-composed decisions in
  `references/skill-composition.md`.
- Keep sibling Skills optional and artifact-based. When stages require hard
  coupling for one outcome, create a self-contained Kit instead.

### Step 2: Execute the workflow

TODO：写出可执行步骤。只有确定性操作需要自定义脚本。

### Step 3: Validate the deliverable

- Verify completeness, factual support, user-visible copy, and output paths.
- Report concrete files or results, plus any remaining evidence gaps.
- Validate `skill-card.yaml`, `cases/cases.json`, and `pricing-card.yaml` as the
  standard trust bundle for this Skill.

## Dependencies

TODO：列出运行依赖；没有额外依赖时明确写 `None`。
"""

USER_PROFILE_SKILL_SECTION = """## User Profile (cross-session)

Every generated Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and this
Skill's `skills.<skill_id>` namespace at the start of every run. Keep the source
portable: resolved personal values belong in the shared profile, never here.

When the user directly states a durable preference or brand fact, persist it
through `scripts/profile_store.py` and report the saved profile path. Put
Skill-specific values under `records.<field>`; use `brand.<field>` or
`user.<field>` for shared values. Do not persist inferred secrets or credentials.
See `references/user-profile.md` for the complete contract.

"""

USER_PROFILE_RUNTIME = """Resolve `context.profile` on every invocation. The precedence is current request,
project context, Skill-specific profile records, shared preferences, shared
brand/user profile, then safe defaults. A direct user statement about a durable
preference or brand fact should be saved with `scripts/profile_store.py record`
using `--confirm`, followed by a concise saved-path report.

"""

SKILL_COMPOSITION_SECTION = """## Skill Group Composition

Read `references/skill-composition.md` before deciding whether to invoke or
extend any adjacent capability. The record distinguishes optional upstream and
downstream handoffs from embedded Kit modules. Do not silently depend on a
sibling Skill that is not shipped with this source.

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
mkdir -p "${{SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILL_SKILLS_INSTALL_DIR/lov-{name}"
```

{configuration_section}## 使用

TODO：提供两个真实示例，并说明输入与输出。

## 原子组合

每个新 Skill 都带有 `references/skill-composition.md`。它记录已检查的相邻
Skills、可选的上游/下游交接、重叠处理，以及为何选择 Single Skill 或自包含
Skill Kit；外部 sibling Skill 不作为隐藏依赖。

## 可信度卡与用户案例

每个新 Skill 都必须随源代码提供：

- `skill-card.yaml` / `skill-card.md`：用途、负责人、依赖、风险、输出与维度地图。
- `cases/cases.json`：至少一个真实的 Input → Prompt → Output 案例。
- `pricing-card.yaml`：免费或付费都要写清价值锚点、交付边界和复评条件。

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

SKILL_CARD_YAML = """schema: lovstudio/skill-card/v1
version: "0.1.0"
description: "TODO: describe the user-visible outcome in one concise paragraph."
owner:
  team: "TODO"
  contact: "TODO"
license:
  name: MIT
  terms: "TODO: state the terms users should know."
  url: "../LICENSE"
use_case:
  audience: "TODO"
  scenario: "TODO"
  tasks:
    - "TODO"
deployment:
  geography: global
  environments:
    - "TODO"
requirements:
  credentials: "none"
  dependencies: []
  runtime:
    - "TODO"
risks:
  - risk: "TODO"
    mitigation: "TODO"
references:
  - title: "Primary Skill instructions"
    path: "SKILL.md"
output:
  types:
    - "TODO"
  formats:
    - "TODO"
  parameters:
    - "TODO"
  validation:
    - "TODO"
  description: "TODO"
ethical_considerations: "TODO: describe privacy, copyright, safety, or misuse boundaries."
dimensions:
  - id: correctness
    label: "TODO"
    description: "TODO"
    evidence: "TODO"
    score: null
  - id: effectiveness
    label: "TODO"
    description: "TODO"
    evidence: "TODO"
    score: null
  - id: efficiency
    label: "TODO"
    description: "TODO"
    evidence: "TODO"
    score: null
pricing:
  model: free
  currency: CNY
  list_price_cny: 0
  basis: "TODO"
  boundary: "TODO"
  review_trigger: "TODO"
  confidence: internal
distribution:
  paid: []
  free:
    - github
    - lovstudio
"""

SKILL_CARD_MD = """# Skill Card — lov-{name}

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

TODO: state the user-visible outcome.

## Owner

TODO: state the maintaining team and contact.

## License / Terms

TODO: state the license and material usage terms.

## Use Case

TODO: state the audience, supported input, and expected task.

## Deployment Geography

TODO: state where the Skill is intended to run.

## Requirements / Dependencies

TODO: list credentials, runtime, files, APIs, and dependencies.

## Known Risks and Mitigations

TODO: list the meaningful failure or misuse modes and their mitigations.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)

## Skill Output

TODO: name the output type, format, parameters, and validation checks.

## Skill Version

0.1.0

## Ethical Considerations

TODO: state privacy, copyright, safety, and attribution boundaries.

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json). Every case must show Input → Prompt → Output.

### Dimension Map

The machine-readable card contains the dimensions, evidence, and score status.

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). Free Skills still explain their value,
boundary, and review trigger.

### Distribution

Keep paid channels (`workbuddy`, `skillpay`) and free channels (`github`, `lovstudio`)
explicit. A planned or unavailable channel must not be described as live.
"""

PRICING_CARD_YAML = """schema: lovstudio/pricing-card/v1
version: "0.1.0"
model: free
currency: CNY
list_price_cny: 0
value_anchor: "TODO"
basis: "TODO: explain the pricing or why this Skill is free."
boundary: "TODO: state what is included and excluded."
review_trigger: "TODO: state when the price or access should be revisited."
confidence: internal
"""

CASES_JSON = """[
  {
    "type": "case",
    "title": "TODO: name one real user case",
    "description": "TODO: explain the task and why the result mattered.",
    "input": {
      "items": ["TODO: name the real input file, request, or starting state"]
    },
    "prompt": "TODO: record the minimum prompt or brief used.",
    "output": {
      "items": ["TODO: name the real output file, result, or decision"]
    }
  }
]
"""

CARD_STANDARD_REFERENCE_MD = """# LovStudio Skill Card standard

`skill-card.yaml` follows the minimum release-record idea of NVIDIA Skill Cards:
description, owner, license/terms, use case, deployment, requirements,
risks/mitigations, references, output contract, version, and ethical
considerations. LovStudio adds evidence that helps a user decide whether the
Skill is credible:

1. A real user case with Input → Prompt → Output.
2. A dimension map with named evidence, not an unexplained score.
3. A pricing basis, including the free boundary and review trigger.
4. Explicit paid and free distribution states.

Never claim a case, score, channel, or price that has not been verified.
"""

README_CONFIGURATION = """## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享
Profile 读取用户、品牌、工作区和本 Skill 的长期记录。用户直接说出的持久
偏好或品牌事实由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

"""

SKILL_MANIFEST_YAML = """schema: skill-manifest/v1
id: lov-{name}
version: "0.1.0"
runtime: skill-runtime/v1
context:
  profile:
    schema: user-profile/v1
    source: shared-profile
    read:
      - user
      - brand
      - workspace
      - preferences
      - skills.lov-{name}
    persist:
      enabled: true
      namespace: skills.lov-{name}
      records_path: skills.lov-{name}.records
      write_policy: direct-user-statement
      atomic: true
    fields:
      - path: user.name
        aliases:
          - identity.name
        required: false
        question: 如果本次输出需要用户身份，请提供名称。
      - path: user.language
        required: false
        question: 希望使用哪种语言输出？
      - path: user.timezone
        required: false
        question: 需要使用哪个时区处理日期和时间？
      - path: brand.name
        aliases:
          - identity.name
        required: false
        question: 如果本次输出需要品牌身份，请提供品牌名称。
      - path: brand.site
        required: false
        question: 如果需要品牌官网，请提供地址。
      - path: brand.tone
        required: false
        question: 如果已有品牌语气或审美关键词，请提供它们。
  preferences:
    namespace: sgc_{namespace}
    fields:
      - path: user.language
        required: false
        question: 希望使用哪种语言输出？
      - path: user.timezone
        required: false
        question: 需要使用哪个时区处理日期和时间？
  interaction:
    ask_missing: true
    max_questions: 1
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

Copyright (c) 2026 Skill Publisher

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

USER_PROFILE_MD = """# User Profile contract

Every Skill created by Skill Creator declares `user-profile/v1` in `skill.yaml`.
The contract connects independent sessions to one user-owned JSON Profile while
keeping the Skill source portable across users and brands.

## Shared shape

The host supplies the Profile through `SKILL_PROFILE_PATH` (or the runtime's
configured profile path). The stable shared scopes are:

- `user`: user identity, language, timezone, and other personal working defaults.
- `brand`: public brand facts, site, logo, tone, profile, and design guidance.
- `workspace`: project roots and output locations.
- `preferences`: shared preference values when the host stores them in the Profile.
- `skills.<skill_id>.profile`: Skill-specific defaults.
- `skills.<skill_id>.records`: durable decisions and preferences learned from
  direct user statements for this Skill.

The Profile may also use the runtime's canonical `identity` fields. Manifest
field aliases bridge `identity.*` and the portable `user.*` / `brand.*` names.

## Read on every run

1. Read the current request and project context.
2. Read the shared Profile and the `skills.<skill_id>` namespace.
3. Resolve values in this order: current request, project context, Skill records,
   shared preferences, shared user/brand Profile, safe defaults.
4. Keep `profile_scope` and field provenance available for the final result.

Do not copy resolved personal paths, brand values, or private records into the
committed Skill source.

## Persist directly stated values

When the user explicitly gives a value meant to survive later sessions, save it
immediately after the user statement and report the canonical path:

```bash
python3 scripts/profile_store.py record \\
  --skill-id lov-example \\
  --path records.subtitle_level \\
  --value '\"cet4\"' \\
  --confirm
```

For shared facts, use `--path brand.<field>` or `--path user.<field>`. The
script writes JSON atomically, preserves unrelated Profile data, increments a
numeric Profile revision when present, and never echoes the stored value.

Inferred information, credentials, tokens, cookies, and secret-like fields stay
out of durable records. If the user has not stated that a value should persist,
keep it in the current request context.

## Read the connected context

```bash
python3 scripts/profile_store.py read \\
  --skill-id lov-example \\
  --pretty
```

The result contains `user`, `brand`, `workspace`, `preferences`, `skill`, and
`records` scopes. A host using `skill-runtime/v1` also returns the same binding
as `profile_scope` and `profile_contract`.

## Compatibility

`--user-config` remains accepted by the Creator as a compatibility flag for old
invocations. The Profile contract is now always generated; users do not choose
an initialization mode.
"""

SKILL_COMPOSITION_MD = """# Skill Group Composition

This record is required for every generated Skill. It prevents adjacent Skills
from becoming accidental duplicates or hidden dependencies.

## Nearby Skills Inspected

TODO: list each related local or installed Skill, its routing contract, and why
it is relevant or not relevant.

## Atomic Handoffs

TODO: record each upstream/core/downstream handoff as input artifact, owner,
output artifact, and acceptance boundary. State explicitly when there is no
handoff.

## Overlap Decisions

TODO: explain any overlap that should be reused, extended, or intentionally
kept separate.

## Composition Decision

TODO: state whether this source is a Single Skill or a self-contained Skill Kit
and why. External sibling Skills remain optional unless their module is embedded
inside this source.
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
    configured = (
        os.environ.get("SKILL_PROFILE_PATH")
        or os.environ.get("SKILLS_PROFILE_PATH")
        or os.environ.get("LOVSTUDIO_SKILLS_PROFILE")
    )
    if configured:
        profile = _expand_path(configured)
    else:
        candidates = (
            Path.home() / ".lovstudio" / "skills" / "profile.json",
            Path.home() / ".skill-publisher" / "skills" / "profile.json",
        )
        profile = next(
            (candidate for candidate in candidates if candidate.exists()),
            candidates[-1],
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
    if os.environ.get("SKILL_SKILL_CREATOR_REPOS_ROOT"):
        return _expand_path(os.environ["SKILL_SKILL_CREATOR_REPOS_ROOT"])
    profile_value = _profile_first(
        profile,
        (
            "skill-publisher.skill_repos_root",
            "skills.repos_root",
            "workspace.skill_repos_root",
            "workspace.skills_root",
        ),
    )
    return _expand_path(profile_value) if profile_value else Path.cwd()


def resolve_install_dir(cli_path: str) -> Optional[Path]:
    if cli_path:
        return _expand_path(cli_path)
    if os.environ.get("SKILL_SKILLS_INSTALL_DIR"):
        return _expand_path(os.environ["SKILL_SKILLS_INSTALL_DIR"])
    _, profile = _load_profile()
    profile_value = _profile_first(
        profile,
        (
            "skills.install_dir",
            "skill-publisher.skills_install_dir",
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


def write_skill(path: Path, name: str, kit_section: str, user_config: bool = False) -> None:
    """Write a Skill instruction file with the always-on profile contract."""

    path.write_text(
        SKILL_MD.format(
            name=name,
            title=f"lov-{name} — TODO",
            kit_section=kit_section,
            user_profile_section=USER_PROFILE_SKILL_SECTION,
            user_profile_runtime=USER_PROFILE_RUNTIME,
            skill_composition_section=SKILL_COMPOSITION_SECTION,
        ),
        encoding="utf-8",
    )


def write_manifest(path: Path, name: str) -> None:
    (path / "skill.yaml").write_text(
        SKILL_MANIFEST_YAML.format(name=name, namespace=name.replace("-", "_")),
        encoding="utf-8",
    )


def write_profile_reference(path: Path) -> None:
    (path / "references").mkdir(exist_ok=True)
    (path / "references" / "user-profile.md").write_text(
        USER_PROFILE_MD, encoding="utf-8"
    )


def write_composition_reference(path: Path) -> None:
    (path / "references").mkdir(exist_ok=True)
    (path / "references" / "skill-composition.md").write_text(
        SKILL_COMPOSITION_MD, encoding="utf-8"
    )


def copy_runtime_scripts(path: Path, script_root: Path) -> None:
    scripts_dir = path / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    for script_name in ("validate_skill.py", "profile_store.py"):
        shutil.copy2(script_root / script_name, scripts_dir / script_name)


def write_card_bundle(path: Path, name: str) -> None:
    """Create the evidence and pricing records required for a new Skill."""
    (path / "cases").mkdir(exist_ok=True)
    (path / "references").mkdir(exist_ok=True)
    (path / "skill-card.yaml").write_text(
        SKILL_CARD_YAML, encoding="utf-8"
    )
    (path / "skill-card.md").write_text(
        SKILL_CARD_MD.format(name=name), encoding="utf-8"
    )
    (path / "pricing-card.yaml").write_text(
        PRICING_CARD_YAML, encoding="utf-8"
    )
    (path / "cases" / "cases.json").write_text(
        CASES_JSON, encoding="utf-8"
    )
    (path / "references" / "skill-card-standard.md").write_text(
        CARD_STANDARD_REFERENCE_MD, encoding="utf-8"
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
        help="Compatibility flag; the user-profile contract is always generated",
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
            write_card_bundle(module_dir, module)
            write_manifest(module_dir, module)
            write_profile_reference(module_dir)
            write_composition_reference(module_dir)

    write_skill(skill_dir / "SKILL.md", name, kit_section, args.user_config)
    write_card_bundle(skill_dir, name)
    write_manifest(skill_dir, name)
    write_profile_reference(skill_dir)
    write_composition_reference(skill_dir)
    (skill_dir / "README.md").write_text(
        README_MD.format(
            name=name,
            configuration_section=README_CONFIGURATION,
        ),
        encoding="utf-8",
    )
    (skill_dir / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
    (skill_dir / "LICENSE").write_text(LICENSE_MD, encoding="utf-8")
    (skill_dir / "CHANGELOG.md").write_text(CHANGELOG_MD, encoding="utf-8")

    script_root = Path(__file__).resolve().parent
    copy_runtime_scripts(skill_dir, script_root)
    for module in modules:
        copy_runtime_scripts(skill_dir / "skills" / module, script_root)

    if install_path:
        install_dir.mkdir(parents=True, exist_ok=True)
        install_path.symlink_to(skill_dir.resolve(), target_is_directory=True)

    kind = "Skill Kit" if args.kit else "Skill"
    print(f"created={skill_dir.resolve()}")
    print(f"kind={kind}")
    print("profile_contract=user-profile/v1")
    print("composition_record=references/skill-composition.md")
    print(f"user_config={'compatibility-flag' if args.user_config else 'always-on'}")
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
