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

    Free entries ship a plaintext mirror and paid entries ship an encrypted
    bundle. Internal entries ship neither, and a public-source paid entry
    installs straight from its own repository, so neither has a mirror to read.
    """
    if is_internal(skill):
        return False
    return not skill.get("paid") or bool(skill.get("encrypted_bundle"))
