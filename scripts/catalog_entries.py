"""Shared classification for `skills.yaml` entries.

The catalog drives four generated surfaces — the `./skills/` mirror, the
marketplace manifest, the README tables, and the runtime-name contract. Each one
needs the same answer to "does the public catalog carry this entry at all?".
Keeping that test inline in every script is what let the runtime-name check
demand a mirror that the sync step is designed never to produce.
"""
from __future__ import annotations


def is_internal(skill: dict) -> bool:
    """Lovstudio staff-only entry: listed for staff, never mirrored publicly."""
    return (skill.get("pricing") or {}).get("visibility") == "internal"


def is_installable(skill: dict) -> bool:
    """Whether the catalog owes this entry a payload under `./skills/<name>/`.

    Only free entries ship a mirror. Paid sources stay private and are handed
    out by lovstudio.ai to accounts that own them; internal entries are never
    published.
    """
    return not skill.get("paid") and not is_internal(skill)
