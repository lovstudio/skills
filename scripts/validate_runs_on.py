#!/usr/bin/env python3
"""Validate the `runs_on` record on `skills.yaml` entries.

`runs_on` answers "can I run this on my machine with the tools I have". The rule it
exists to enforce: a claim that something works needs a real run behind it, and
anything nobody ran stays `unverified`. Prose reviews drift, so that rule lives here,
in CI, where a record that breaks it fails the render.

Usage: python3 scripts/validate_runs_on.py [path/to/skills.yaml]
"""
from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_URL_PREFIX = "https://github.com/lovstudio/skills/blob/main/"

SYSTEMS = ("macos-arm64", "macos-intel", "windows", "linux")
STATUSES = ("verified", "partial", "blocked", "unverified")
RESULTS = ("passed", "partial", "failed")
KINDS = ("run", "source")

RECORD_KEYS = {
    "checked_at", "skill_version", "verdict_zh", "verdict_en",
    "systems", "agents", "requires", "alternatives", "evidence",
}
EVIDENCE_KEYS = {"id", "date", "env", "kind", "result", "skill_version", "scope_zh", "scope_en", "url"}
SYSTEM_KEYS = {"id", "status", "evidence", "note_zh", "note_en"}
AGENT_KEYS = {"label", "model", "domestic", "status", "evidence", "gap_zh", "gap_en"}
REQUIRE_KEYS = {"name", "required", "for_zh", "for_en"}
ALTERNATIVE_KEYS = {"replaces_zh", "replaces_en", "with_zh", "with_en", "status", "evidence", "gap_zh", "gap_en"}

# The catalog is public: evidence has to stay readable there without exposing the machine it ran on.
PRIVATE_TEXT = re.compile(r"/Users/|/home/|~/|\bsk-[A-Za-z0-9]{8,}|_API_KEY=\S")


def _date(value: Any) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _walk_text(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_text(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_text(item)


class _Checker:
    def __init__(self, name: str, root: Path):
        self.name = name
        self.root = root
        self.errors: list[str] = []
        self.evidence: dict[str, dict] = {}
        self.cited: set[str] = set()

    def error(self, where: str, message: str) -> None:
        self.errors.append(f"{self.name}.runs_on.{where}: {message}")

    def unknown_keys(self, where: str, item: dict, allowed: set[str]) -> None:
        for key in sorted(set(item) - allowed):
            self.error(where, f"unknown field {key!r}")

    def check_evidence(self, items: Any, checked_at: dt.date | None) -> None:
        if not isinstance(items, list):
            self.error("evidence", "must be a list")
            return
        for index, item in enumerate(items):
            where = f"evidence[{index}]"
            if not isinstance(item, dict):
                self.error(where, "must be a mapping")
                continue
            self.unknown_keys(where, item, EVIDENCE_KEYS)
            evidence_id = item.get("id")
            if not _text(evidence_id):
                self.error(where, "needs an id")
                continue
            where = f"evidence[{evidence_id}]"
            if evidence_id in self.evidence:
                self.error(where, "duplicate id")
            self.evidence[evidence_id] = item
            date = _date(item.get("date"))
            if date is None:
                self.error(where, "date must be YYYY-MM-DD")
            elif checked_at and date > checked_at:
                self.error(where, f"dated after checked_at ({date} > {checked_at})")
            for field in ("env", "scope_zh", "scope_en"):
                if not _text(item.get(field)):
                    self.error(where, f"{field} is required: say where it ran and what actually ran")
            if item.get("result") not in RESULTS:
                self.error(where, f"result must be one of {RESULTS}")
            kind = item.get("kind", "run")
            if kind not in KINDS:
                self.error(where, f"kind must be one of {KINDS}")
            if kind == "source" and item.get("result") != "failed":
                self.error(where, "a source declaration can only record that something does not run")
            url = item.get("url")
            if url is not None:
                if not (_text(url) and url.startswith("https://")):
                    self.error(where, "url must be https")
                elif url.startswith(EVIDENCE_URL_PREFIX):
                    target = self.root / url[len(EVIDENCE_URL_PREFIX):]
                    if not target.is_file():
                        self.error(where, f"url points at a file not in this repo: {target.relative_to(self.root)}")

    def check_claim(self, where: str, item: dict, gap_fields: tuple[str, str]) -> None:
        """The one rule that matters: a status is only as good as the evidence it cites."""
        status = item.get("status")
        if status not in STATUSES:
            self.error(where, f"status must be one of {STATUSES}")
            return
        ids = item.get("evidence", [])
        if not isinstance(ids, list):
            self.error(where, "evidence must be a list of ids")
            return
        cited = []
        for evidence_id in ids:
            self.cited.add(evidence_id)
            if evidence_id not in self.evidence:
                self.error(where, f"cites unknown evidence {evidence_id!r}")
            else:
                cited.append(self.evidence[evidence_id])
        runs = [entry for entry in cited if entry.get("kind", "run") == "run"]
        if status == "verified" and not any(entry.get("result") == "passed" for entry in runs):
            self.error(where, "verified needs a cited run that passed")
        if status == "partial" and not any(entry.get("result") in ("passed", "partial") for entry in runs):
            self.error(where, "partial needs a cited run that at least partly passed")
        if status == "blocked" and not any(entry.get("result") == "failed" for entry in cited):
            self.error(where, "blocked needs cited evidence that it failed")
        if status == "unverified" and ids:
            self.error(where, "unverified must not cite evidence: use partial or blocked instead")
        if status in ("partial", "blocked") and not all(_text(item.get(field)) for field in gap_fields):
            self.error(where, f"{status} must say what is missing in {gap_fields[0]} and {gap_fields[1]}")

    def check_systems(self, items: Any) -> None:
        if not isinstance(items, list):
            self.error("systems", "must be a list")
            return
        seen = []
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                self.error(f"systems[{index}]", "must be a mapping")
                continue
            where = f"systems[{item.get('id', index)}]"
            self.unknown_keys(where, item, SYSTEM_KEYS)
            if item.get("id") not in SYSTEMS:
                self.error(where, f"id must be one of {SYSTEMS}")
                continue
            seen.append(item["id"])
            self.check_claim(where, item, ("note_zh", "note_en"))
        for system in SYSTEMS:
            if seen.count(system) != 1:
                self.error("systems", f"must list {system} exactly once, so the page answers every reader")

    def check_agents(self, items: Any) -> None:
        if not isinstance(items, list):
            self.error("agents", "must be a list")
            return
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                self.error(f"agents[{index}]", "must be a mapping")
                continue
            where = f"agents[{item.get('label', index)}/{item.get('model', '')}]"
            self.unknown_keys(where, item, AGENT_KEYS)
            if not _text(item.get("label")):
                self.error(where, "needs a label")
            if not isinstance(item.get("domestic"), bool):
                self.error(where, "domestic must be true or false")
            if item.get("status") != "unverified" and not _text(item.get("model")):
                self.error(where, "a tested agent must name the model it ran with")
            self.check_claim(where, item, ("gap_zh", "gap_en"))

    def check_requires(self, items: Any) -> None:
        if not isinstance(items, list):
            self.error("requires", "must be a list; use [] when no account or key is needed")
            return
        for index, item in enumerate(items):
            where = f"requires[{index}]"
            if not isinstance(item, dict):
                self.error(where, "must be a mapping")
                continue
            self.unknown_keys(where, item, REQUIRE_KEYS)
            if not _text(item.get("name")):
                self.error(where, "needs a name")
            if not isinstance(item.get("required"), bool):
                self.error(where, "required must be true or false")
            if not (_text(item.get("for_zh")) and _text(item.get("for_en"))):
                self.error(where, "for_zh and for_en must say what it is for")

    def check_alternatives(self, items: Any) -> None:
        if not isinstance(items, list):
            self.error("alternatives", "must be a list")
            return
        for index, item in enumerate(items):
            where = f"alternatives[{index}]"
            if not isinstance(item, dict):
                self.error(where, "must be a mapping")
                continue
            self.unknown_keys(where, item, ALTERNATIVE_KEYS)
            for field in ("replaces_zh", "replaces_en", "with_zh", "with_en"):
                if not _text(item.get(field)):
                    self.error(where, f"{field} is required")
            self.check_claim(where, item, ("gap_zh", "gap_en"))


def validate_record(name: str, record: Any, root: Path = ROOT, version: str | None = None) -> list[str]:
    checker = _Checker(name, root)
    if not isinstance(record, dict):
        checker.error("", "must be a mapping")
        return checker.errors
    checker.unknown_keys("", record, RECORD_KEYS)

    checked_at = _date(record.get("checked_at"))
    if checked_at is None:
        checker.error("checked_at", "must be YYYY-MM-DD")
    if not _text(record.get("skill_version")):
        checker.error("skill_version", "must name the version this record was checked against")
    for field in ("verdict_zh", "verdict_en"):
        if not _text(record.get(field)):
            checker.error(field, "is required: this is the per-Skill answer the page leads with")

    # Evidence first: the claim checks below resolve ids against it.
    checker.check_evidence(record.get("evidence", []), checked_at)
    checker.check_systems(record.get("systems"))
    checker.check_agents(record.get("agents"))
    checker.check_requires(record.get("requires"))
    checker.check_alternatives(record.get("alternatives", []))

    for evidence_id in sorted(set(checker.evidence) - checker.cited):
        checker.error(f"evidence[{evidence_id}]", "is not cited by anything")
    for text in _walk_text(record):
        match = PRIVATE_TEXT.search(text)
        if match:
            checker.error("", f"public text contains a private path or secret: {match.group(0)!r}")
    return checker.errors


def validate_catalog(data: dict, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for skill in data.get("skills", []):
        if "runs_on" in skill:
            errors.extend(validate_record(skill.get("name", "?"), skill["runs_on"], root))
    return errors


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else ROOT / "skills.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    errors = validate_catalog(data)
    for error in errors:
        print(f"::error::{error}")
    records = sum(1 for skill in data.get("skills", []) if "runs_on" in skill)
    print(f"runs_on: {records} records, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
