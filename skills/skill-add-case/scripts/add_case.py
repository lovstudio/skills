#!/usr/bin/env python3
"""Validate and atomically add one accepted case to a Skill's case registry."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


CASE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL_RE = re.compile(r"^https?://", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"\bTODO\b|\{[^}]+\}", re.IGNORECASE)
PRIVATE_PATH_RE = re.compile(
    r"(?:/" r"Users/[^/\s]+|/home/[^/\s]+|[A-Za-z]:\\Users\\[^\\\s]+)"
)
SECRET_PATTERNS = (
    re.compile(r"\bgh[opusr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b(?:Bearer|Authorization:)\s+[A-Za-z0-9._~+/-]{12,}", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


class CaseError(ValueError):
    """A copyable, user-fixable case contract error."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def has_content(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(has_content(item) for item in value.values())
    if isinstance(value, list):
        return any(has_content(item) for item in value)
    return value is not None


def string_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from string_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from string_values(item)


def load_json(path_value: str) -> Any:
    if path_value == "-":
        text = sys.stdin.read()
        label = "stdin"
    else:
        path = Path(path_value).expanduser()
        label = str(path)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise CaseError(f"cannot read case input {label}: {exc}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise CaseError(f"invalid JSON in {label}: {exc}") from exc


def safe_relative_asset(root: Path, value: str, field: str) -> None:
    if URL_RE.match(value) or value.startswith("data:"):
        return
    if value.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", value):
        raise CaseError(f"{field} must not expose an absolute filesystem path")
    candidate = (root / value).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise CaseError(f"{field} escapes the target Skill root: {value}") from exc
    if not candidate.is_file():
        raise CaseError(f"{field} asset does not exist: {value}")


def validate_case(root: Path, raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise CaseError("case input must be one JSON object, not an array")
    case = dict(raw)
    if case.get("type", "case") != "case":
        raise CaseError("type must be 'case'")
    case["type"] = "case"

    for key in ("title", "description", "input", "prompt", "output"):
        if not has_content(case.get(key)):
            raise CaseError(f"required field is missing or empty: {key}")

    evidence = case.get("evidence")
    if not isinstance(evidence, dict):
        raise CaseError("evidence must be an object")
    if evidence.get("acceptance") != "user-confirmed":
        raise CaseError("evidence.acceptance must be 'user-confirmed'")
    for key in ("verified_at", "method", "privacy"):
        if not has_content(evidence.get(key)):
            raise CaseError(f"evidence.{key} is required")
    if not DATE_RE.fullmatch(str(evidence["verified_at"]).strip()):
        raise CaseError("evidence.verified_at must use YYYY-MM-DD")

    case_id = str(case.get("id", "")).strip()
    if not case_id:
        seed = {
            "title": case["title"],
            "input": case["input"],
            "prompt": case["prompt"],
            "output": case["output"],
        }
        case_id = f"case-{fingerprint(seed)[:12]}"
        case["id"] = case_id
    if not CASE_ID_RE.fullmatch(case_id):
        raise CaseError("id must use lowercase kebab-case")

    public_text = json.dumps(case, ensure_ascii=False, sort_keys=True)
    if any(PLACEHOLDER_RE.search(value) for value in string_values(case)):
        raise CaseError("case contains an unresolved placeholder")
    private_path = PRIVATE_PATH_RE.search(public_text)
    if private_path:
        raise CaseError(f"case contains a private absolute path: {private_path.group(0)}")
    for pattern in SECRET_PATTERNS:
        if pattern.search(public_text):
            raise CaseError("case contains a secret-like value; redact it before publication")

    cover = case.get("cover")
    if cover is not None:
        if not isinstance(cover, str) or not cover.strip():
            raise CaseError("cover must be a non-empty string")
        safe_relative_asset(root, cover.strip(), "cover")
    gallery = case.get("gallery", [])
    if not isinstance(gallery, list):
        raise CaseError("gallery must be a list")
    for index, value in enumerate(gallery):
        if not isinstance(value, str) or not value.strip():
            raise CaseError(f"gallery[{index}] must be a non-empty string")
        safe_relative_asset(root, value.strip(), f"gallery[{index}]")
    return case


def read_registry(path: Path) -> list[Any]:
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CaseError(f"cannot read existing case registry {path}: {exc}") from exc
    if not isinstance(value, list):
        raise CaseError(f"existing case registry must be a JSON array: {path}")
    return value


def atomic_write(path: Path, cases: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            json.dump(cases, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_name, mode)
        os.replace(temporary_name, path)
    finally:
        if temporary_name and Path(temporary_name).exists():
            Path(temporary_name).unlink()


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = args.target.expanduser().resolve()
    if not (root / "SKILL.md").is_file():
        raise CaseError(f"target is not a Skill source: missing {root / 'SKILL.md'}")
    registry_path = root / "cases" / "cases.json"
    case = validate_case(root, load_json(args.case))
    case_id = case["id"]
    case_fingerprint = fingerprint(case)
    cases = read_registry(registry_path)

    duplicate_id = next(
        (index for index, item in enumerate(cases) if isinstance(item, dict) and item.get("id") == case_id),
        None,
    )
    duplicate_fingerprint = next(
        (index for index, item in enumerate(cases) if isinstance(item, dict) and fingerprint(item) == case_fingerprint),
        None,
    )
    action = "added"
    if duplicate_id is not None:
        if not args.replace_existing:
            raise CaseError(f"duplicate case id at cases[{duplicate_id}]: {case_id}")
        cases[duplicate_id] = case
        action = "replaced"
    elif duplicate_fingerprint is not None:
        raise CaseError(f"duplicate evidence fingerprint at cases[{duplicate_fingerprint}]: {case_fingerprint}")
    else:
        cases.append(case)

    if not args.dry_run:
        atomic_write(registry_path, cases)
    return {
        "status": "prepared" if args.dry_run else action,
        "target": str(root),
        "cases_path": str(registry_path),
        "case_id": case_id,
        "fingerprint": case_fingerprint,
        "total_cases": len(cases),
        "dry_run": bool(args.dry_run),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="Target Skill source root")
    parser.add_argument("--case", required=True, help="Case JSON object path, or '-' for stdin")
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing")
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Replace the same stable case ID after explicit correction approval",
    )
    args = parser.parse_args()
    try:
        result = run(args)
    except (CaseError, OSError) as exc:
        print(f"context_id=skill-add-case error={exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
