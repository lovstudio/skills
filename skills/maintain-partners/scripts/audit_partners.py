#!/usr/bin/env python3
"""Audit the partners section: dead URLs, missing logos, missing i18n keys.

Walks PARTNERS in the configured partners TSX file, then for each entry verifies:
  1. logo file exists at the referenced public path
  2. taglineKey exists in all 4 locale JSONs (zh-CN, en, ja, th)
  3. href returns a non-error HTTP status (skipped unless --probe)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


LOCALES = ["zh-CN", "en", "ja", "th"]

PROXY_ENV = {
    "https_proxy": "http://127.0.0.1:7890",
    "http_proxy": "http://127.0.0.1:7890",
    "all_proxy": "socks5://127.0.0.1:7891",
}

PARTNER_RE = re.compile(
    r'\{\s*name:\s*"([^"]+)"\s*,\s*href:\s*"([^"]+)"\s*,\s*logo:\s*"([^"]+)"\s*,\s*taglineKey:\s*"([^"]+)"',
    re.M,
)


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


def parse_partners(src: str) -> list[dict]:
    return [
        {"name": m[0], "href": m[1], "logo": m[2], "taglineKey": m[3]}
        for m in PARTNER_RE.findall(src)
    ]


def load_tagline_keys(repo: Path, locale: str) -> set[str]:
    p = repo / "src/i18n/messages" / f"{locale}.json"
    data = json.loads(p.read_text())
    # Tagline keys live under dispatch.partner*Tagline
    dispatch = data.get("dispatch", {})
    return {k for k in dispatch if k.startswith("partner") and k.endswith("Tagline")}


def probe(url: str, timeout: int = 8) -> int:
    cmd = ["curl", "-sL", "-m", str(timeout), "-o", "/dev/null", "-w", "%{http_code}", url]
    r = subprocess.run(cmd, env={**__import__("os").environ, **PROXY_ENV}, capture_output=True)
    try:
        return int(r.stdout.decode().strip() or 0)
    except ValueError:
        return 0


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
    ap.add_argument("--probe", action="store_true", help="HTTP-probe each href (slow)")
    args = ap.parse_args()

    repo = resolve_repo(args.repo)
    partners_file = resolve_partners_file(repo, args.partners_file)
    public = repo / "public"

    if not partners_file.exists():
        sys.exit(f"Not found: {partners_file}")

    partners = parse_partners(partners_file.read_text())
    if not partners:
        sys.exit("PARTNERS array empty or unparseable")

    print(f"Parsed {len(partners)} partners")

    locale_keys = {loc: load_tagline_keys(repo, loc) for loc in LOCALES}

    issues: list[str] = []
    for p in partners:
        logo_path = public / p["logo"].lstrip("/")
        if not logo_path.exists():
            issues.append(f"  [missing-logo] {p['name']}: {logo_path}")

        for loc in LOCALES:
            if p["taglineKey"] not in locale_keys[loc]:
                issues.append(f"  [missing-i18n:{loc}] {p['name']}: {p['taglineKey']}")

        if args.probe:
            code = probe(p["href"])
            if code == 0 or code >= 400:
                issues.append(f"  [dead-url:{code}] {p['name']}: {p['href']}")

    if issues:
        print(f"\n{len(issues)} issue(s):")
        print("\n".join(issues))
        sys.exit(1)
    print("\n✓ All partners healthy")


if __name__ == "__main__":
    main()
