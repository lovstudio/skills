#!/usr/bin/env python3
"""Create a portable investor-BP workspace without overwriting existing work."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def expand_path(value: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(value))).resolve()


def slugify(value: str) -> str:
    normalized = re.sub(r"[^\w\u4e00-\u9fff]+", "-", value.strip().lower(), flags=re.UNICODE)
    return normalized.strip("-_") or "project"


def load_profile(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read profile {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Profile must be a JSON object: {path}")
    return data


def nested(data: Dict[str, Any], *keys: str) -> Optional[str]:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current if isinstance(current, str) and current.strip() else None


def resolve_output(args: argparse.Namespace, profile: Dict[str, Any]) -> Path:
    if args.output:
        return expand_path(args.output)
    skill_output = os.environ.get("LOVSTUDIO_BP_OUTPUT_DIR")
    if skill_output:
        return expand_path(skill_output) / f"{slugify(args.name)}-business-plan"
    shared_output = os.environ.get("LOVSTUDIO_SKILLS_OUTPUT_DIR")
    if shared_output:
        return expand_path(shared_output) / f"{slugify(args.name)}-business-plan"
    profile_output = nested(profile, "workspace", "output_dir")
    if profile_output:
        return expand_path(profile_output) / f"{slugify(args.name)}-business-plan"
    return (Path.cwd() / "business-plan").resolve()


def resolve_optional(explicit: Optional[str], env_name: str, profile: Dict[str, Any], key: str) -> str:
    value = explicit or os.environ.get(env_name) or nested(profile, "brand", key)
    return str(expand_path(value)) if value else "not configured"


def render_template(template: Path, destination: Path, values: Dict[str, str]) -> None:
    text = template.read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    destination.write_text(text, encoding="utf-8")


def ensure_safe_destination(output: Path) -> None:
    home = Path.home().resolve()
    if output in {Path("/").resolve(), home}:
        raise SystemExit(f"Refusing to use broad destination: {output}")
    if output.exists() and any(output.iterdir()):
        raise SystemExit(
            f"Destination already contains files: {output}\n"
            "Continue in that workspace manually or choose a new --output path."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a source-backed 12–15 slide investor-BP workspace."
    )
    parser.add_argument("--name", required=True, help="Project or company name")
    parser.add_argument(
        "--stage",
        default="seed",
        choices=("pre-seed", "seed", "angel", "pre-a", "series-a", "growth", "other"),
        help="Financing stage (default: seed)",
    )
    parser.add_argument("--output", help="Exact workspace directory")
    parser.add_argument("--profile", help="Shared LovStudio skills profile JSON")
    parser.add_argument("--brand-profile", help="Brand profile file")
    parser.add_argument("--design-guide", help="Design guide file")
    parser.add_argument("--json", action="store_true", help="Print machine-readable result")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile_path = expand_path(
        args.profile
        or os.environ.get("LOVSTUDIO_SKILLS_PROFILE")
        or "$HOME/.lovstudio/skills/profile.json"
    )
    profile = load_profile(profile_path)
    output = resolve_output(args, profile)
    ensure_safe_destination(output)

    skill_root = Path(__file__).resolve().parent.parent
    template_root = skill_root / "assets" / "templates"
    required_templates = {
        "brief.md": template_root / "brief.md",
        "evidence-ledger.md": template_root / "evidence-ledger.md",
        "outline.md": template_root / "outline.md",
    }
    missing = [str(path) for path in required_templates.values() if not path.exists()]
    if missing:
        raise SystemExit("Missing templates:\n- " + "\n- ".join(missing))

    output.mkdir(parents=True, exist_ok=True)
    (output / "assets").mkdir(exist_ok=True)
    (output / "assets" / ".gitkeep").touch()

    today = dt.date.today().isoformat()
    values = {
        "PROJECT_NAME": args.name.strip(),
        "STAGE": args.stage,
        "DATE": today,
        "VERSION": "draft-0.1",
    }
    created = []
    for relative, template in required_templates.items():
        destination = output / relative
        render_template(template, destination, values)
        created.append(str(destination))

    brand_profile = resolve_optional(
        args.brand_profile, "LOVSTUDIO_BP_BRAND_PROFILE", profile, "profile"
    )
    design_guide = resolve_optional(
        args.design_guide, "LOVSTUDIO_BP_DESIGN_GUIDE", profile, "design_guide"
    )
    source_note = output / "source-config.md"
    source_note.write_text(
        "# BP Source Configuration\n\n"
        f"- Project: {args.name.strip()}\n"
        f"- Stage: {args.stage}\n"
        f"- Created: {today}\n"
        f"- Brand profile: {brand_profile}\n"
        f"- Design guide: {design_guide}\n\n"
        "Do not store credentials or private customer data in this file.\n",
        encoding="utf-8",
    )
    created.append(str(source_note))

    result = {
        "project": args.name.strip(),
        "stage": args.stage,
        "workspace": str(output),
        "created": created,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Created investor-BP workspace: {output}")
        for path in created:
            print(f"  - {path}")
        print("Next: replace missing/TODO items, pass the evidence gate, then use bp-deck.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
