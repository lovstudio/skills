#!/usr/bin/env python3
"""Append a partner to the configured PARTNERS TSX file + add tagline keys to all 4 locale JSONs.

Idempotent: if the partner name or taglineKey already exists, exits with an error
rather than duplicating. Logo file must already exist (use normalize_logo.py first).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


LOCALES = ["zh-CN", "en", "ja", "th"]


def is_website_repo(repo: Path) -> bool:
    return (
        (repo / "app/(main)/(home)/PartnersGrid.tsx").exists()
        or (repo / "app/(main)/(home)/WorkshopDispatch.tsx").exists()
        or ((repo / "app").is_dir() and (repo / "public").is_dir())
    )


def _nested(data: dict, dotted: str) -> str | None:
    cur = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return str(cur) if cur else None


def _expand_path(value: str) -> Path:
    return Path(os.path.expandvars(value)).expanduser()


def resolve_repo(cli_repo: str | None) -> Path:
    candidates: list[str] = []
    if cli_repo:
        repo = _expand_path(cli_repo)
        if is_website_repo(repo):
            return repo
        sys.exit(f"Website repo not found at --repo: {repo}")
    for env_key in (
        "LOVSTUDIO_MAINTAIN_PARTNERS_SITE_ROOT",
        "LOVSTUDIO_WEB_ROOT",
        "PARTNERS_SITE_ROOT",
    ):
        if os.environ.get(env_key):
            candidates.append(os.environ[env_key])

    profile = Path(
        os.environ.get("LOVSTUDIO_SKILLS_PROFILE")
        or os.environ.get("AGENT_SKILL_PROFILE")
        or os.environ.get("LOVSTUDIO_SKILL_PROFILE")
        or str(Path.home() / ".lovstudio/skills/profile.json")
    ).expanduser()
    if profile.exists():
        try:
            data = json.loads(profile.read_text())
        except json.JSONDecodeError as exc:
            sys.exit(f"Invalid JSON in {profile}: {exc}")
        for key in (
            "sites.lovstudio_web",
            "lovstudio.web_root",
            "workspace.web_root",
            "workspace.website_root",
        ):
            value = _nested(data, key)
            if value:
                candidates.append(value)

    for candidate in candidates:
        repo = _expand_path(candidate)
        if is_website_repo(repo):
            return repo

    sys.exit(
        "Website repo not found. Pass --repo, set LOVSTUDIO_MAINTAIN_PARTNERS_SITE_ROOT, or add "
        "sites.lovstudio_web / lovstudio.web_root / workspace.web_root to "
        f"{profile}. LOVSTUDIO_WEB_ROOT and PARTNERS_SITE_ROOT are still accepted as legacy aliases."
    )


def resolve_partners_file(repo: Path, cli_partners_file: str | None) -> Path:
    def as_path(value: str) -> Path:
        p = _expand_path(value)
        return p if p.is_absolute() else repo / p

    if cli_partners_file:
        path = as_path(cli_partners_file)
        if path.exists():
            return path
        sys.exit(f"Partners file not found at --partners-file: {path}")

    candidates: list[str] = []
    for env_key in (
        "LOVSTUDIO_MAINTAIN_PARTNERS_FILE",
        "LOVSTUDIO_PARTNERS_FILE",
        "PARTNERS_FILE",
    ):
        if os.environ.get(env_key):
            candidates.append(os.environ[env_key])

    profile = Path(
        os.environ.get("LOVSTUDIO_SKILLS_PROFILE")
        or os.environ.get("AGENT_SKILL_PROFILE")
        or os.environ.get("LOVSTUDIO_SKILL_PROFILE")
        or str(Path.home() / ".lovstudio/skills/profile.json")
    ).expanduser()
    if profile.exists():
        try:
            data = json.loads(profile.read_text())
        except json.JSONDecodeError as exc:
            sys.exit(f"Invalid JSON in {profile}: {exc}")
        for key in (
            "sites.partners_file",
            "lovstudio.partners_file",
            "partners.file",
            "workspace.partners_file",
        ):
            value = _nested(data, key)
            if value:
                candidates.append(value)

    candidates.extend(
        [
            "app/(main)/(home)/PartnersGrid.tsx",
            "app/(main)/(home)/WorkshopDispatch.tsx",
        ]
    )

    for candidate in candidates:
        path = as_path(candidate)
        if path.exists() and "PARTNERS" in path.read_text():
            return path

    sys.exit(
        "Partners file not found. Pass --partners-file, set LOVSTUDIO_MAINTAIN_PARTNERS_FILE, "
        "or add sites.partners_file / lovstudio.partners_file to the shared profile. "
        "LOVSTUDIO_PARTNERS_FILE and PARTNERS_FILE are still accepted as legacy aliases."
    )


def insert_partner_entry(
    src: str,
    name: str,
    href: str,
    logo: str,
    key: str,
    category: str,
    show_name: bool,
) -> str:
    if f'name: "{name}"' in src:
        sys.exit(f"Partner '{name}' already exists in PARTNERS")

    show_suffix = ", showName: true" if show_name else ""
    line = (
        f'  {{ name: "{name}", '
        f'href: "{href}", '
        f'logo: "{logo}", '
        f'taglineKey: "{key}", '
        f'category: "{category}"{show_suffix} }},\n'
    )

    pattern = re.compile(r"(export const PARTNERS:\s*Partner\[\]\s*=\s*\[[\s\S]*?)(\n\]\n)", re.M)
    new_src, n = pattern.subn(lambda m: f"{m.group(1)}\n{line}{m.group(2)}", src, count=1)
    if n == 0:
        sys.exit("Could not find PARTNERS array closing bracket — manual edit required")
    return new_src


def insert_tagline(locale_path: Path, key: str, value: str):
    text = locale_path.read_text()
    if f'"{key}"' in text:
        return  # idempotent
    # Insert as the new last entry inside the dispatch block (before its closing "}").
    # Strategy: find the last `partner...Tagline` entry and append after it.
    matches = list(re.finditer(r'(\n\s*"partner\w+Tagline":\s*"[^"]*")(,?)\n', text))
    if not matches:
        sys.exit(f"Could not find any partner*Tagline entries in {locale_path.name}")
    last = matches[-1]
    insertion = f'{last.group(1)},\n    "{key}": "{value}"\n'
    new_text = text[: last.start()] + insertion + text[last.end():]
    locale_path.write_text(new_text)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--repo",
        default=None,
        help="Website repo root. Defaults to LOVSTUDIO_MAINTAIN_PARTNERS_SITE_ROOT, profile JSON, or legacy LOVSTUDIO_WEB_ROOT/PARTNERS_SITE_ROOT.",
    )
    ap.add_argument(
        "--partners-file",
        default=None,
        help="Partners TSX file. Defaults to LOVSTUDIO_MAINTAIN_PARTNERS_FILE, profile JSON, legacy LOVSTUDIO_PARTNERS_FILE/PARTNERS_FILE, PartnersGrid.tsx, or WorkshopDispatch.tsx.",
    )
    ap.add_argument("--name", required=True, help="Display name (CJK ok)")
    ap.add_argument("--href", required=True, help="Brand homepage URL")
    ap.add_argument(
        "--logo",
        required=True,
        help="Logo path under /public, e.g. /partners/foo/logo.png",
    )
    ap.add_argument(
        "--key",
        required=True,
        help="Tagline i18n key, e.g. partnerFooTagline",
    )
    ap.add_argument(
        "--category",
        choices=["compute", "peer", "invest", "media", "community"],
        default="community",
        help="Partner category used by the LovStudio PartnersGrid component",
    )
    ap.add_argument("--zh", required=True, help="Tagline in Simplified Chinese")
    ap.add_argument("--en", required=True, help="Tagline in English")
    ap.add_argument("--ja", required=True, help="Tagline in Japanese")
    ap.add_argument("--th", required=True, help="Tagline in Thai")
    ap.add_argument(
        "--show-name",
        action="store_true",
        help="Render the name next to the logo (use for icon-only logos < 32px wide)",
    )
    args = ap.parse_args()

    repo = resolve_repo(args.repo)
    partners_file = resolve_partners_file(repo, args.partners_file)
    public = repo / "public"
    locales_dir = repo / "src/i18n/messages"

    logo_file = public / args.logo.lstrip("/")
    if not logo_file.exists():
        sys.exit(f"Logo file missing: {logo_file}\nRun normalize_logo.py first.")

    src = partners_file.read_text()
    new_src = insert_partner_entry(
        src,
        args.name,
        args.href,
        args.logo,
        args.key,
        args.category,
        args.show_name,
    )
    partners_file.write_text(new_src)
    print(f"✓ Added '{args.name}' to PARTNERS")

    taglines = {"zh-CN": args.zh, "en": args.en, "ja": args.ja, "th": args.th}
    for loc, txt in taglines.items():
        insert_tagline(locales_dir / f"{loc}.json", args.key, txt)
        print(f"✓ Added {args.key} to {loc}.json")


if __name__ == "__main__":
    main()
