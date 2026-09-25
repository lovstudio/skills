#!/usr/bin/env python3
"""Read-only structural audit of a bilingual skill-naming-review/v1 plan."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import unicodedata


FIELDS = {"name_zh", "display_name"}
ROW_FIELDS = {"id", "before", "after", "decision", "approval", "approved", "evidence", "reason"}
ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("invalid JSON constant: " + value)


def normalized(value):
    return "".join(unicodedata.normalize("NFKC", value).casefold().split())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def validate_shape(plan):
    require(isinstance(plan, dict), "root must be an object")
    required = {"schema", "scope_ids", "rows"}
    require(required <= set(plan) <= required | {"author_prefixes"}, "invalid root fields")
    require(plan["schema"] == "skill-naming-review/v1", "unsupported schema")
    scope = plan["scope_ids"]
    require(isinstance(scope, list) and bool(scope), "scope_ids must be a non-empty list")
    require(all(isinstance(item, str) and ID.fullmatch(item) for item in scope), "invalid scope id")
    require(isinstance(plan["rows"], list), "rows must be a list")
    prefixes = plan.get("author_prefixes", [])
    require(isinstance(prefixes, list) and all(text(p) for p in prefixes), "invalid author_prefixes")
    for i, row in enumerate(plan["rows"]):
        at = "rows[{}]".format(i)
        require(isinstance(row, dict) and set(row) == ROW_FIELDS, at + ": invalid fields")
        require(isinstance(row["id"], str) and ID.fullmatch(row["id"]), at + ": invalid id")
        for side in ("before", "after"):
            names = row[side]
            require(isinstance(names, dict) and set(names) == FIELDS, at + ": invalid " + side)
            require(all(isinstance(v, str) for v in names.values()), at + ": names must be strings")
            if side == "after":
                require(all(text(v) for v in names.values()), at + ": empty proposed name")
        approval = row["approval"]
        require(isinstance(approval, dict) and set(approval) == FIELDS, at + ": invalid approval")
        require(all(isinstance(v, str) and v in {"user", "editorial", "unresolved"}
                    for v in approval.values()), at + ": invalid approval state")
        approved = row["approved"]
        require(isinstance(approved, dict) and set(approved) <= FIELDS
                and all(text(v) for v in approved.values()), at + ": invalid approved names")
        decision = row["decision"]
        require(isinstance(decision, str) and decision in {"rename", "retain", "review"}, at + ": invalid decision")
        evidence = row["evidence"]
        require(isinstance(evidence, list) and bool(evidence) and all(text(v) for v in evidence), at + ": missing evidence")
        require(text(row["reason"]), at + ": missing reason")


def audit(plan):
    validate_shape(plan)
    errors, warnings = [], []

    def issue(target, code, location, message):
        target.append({"code": code, "location": location, "message": message})

    scope, rows = plan["scope_ids"], plan["rows"]
    ids = [row["id"] for row in rows]
    for label, values in (("scope_ids", scope), ("rows", ids)):
        for identity, count in Counter(values).items():
            if count > 1:
                issue(errors, "duplicate_id", label, identity)
    missing, extra = set(scope) - set(ids), set(ids) - set(scope)
    if missing:
        issue(errors, "missing_rows", "rows", ", ".join(sorted(missing)))
    if extra:
        issue(errors, "out_of_scope", "rows", ", ".join(sorted(extra)))

    seen = {field: {} for field in FIELDS}
    counts = {"scope": len(scope), "reviewed": len(rows), "rename": 0, "retain": 0, "review": 0}
    for row in rows:
        identity = row["id"]
        counts[row["decision"]] += 1
        changed = row["before"] != row["after"]
        if row["decision"] == "review":
            issue(errors, "pending_review", identity, "editorial decision remains unresolved")
        elif changed != (row["decision"] == "rename"):
            issue(errors, "decision_mismatch", identity, "rename/retain disagrees with before/after")
        for field in sorted(FIELDS):
            value = row["after"][field]
            location = identity + "." + field
            state = row["approval"][field]
            locked = row["approved"].get(field)
            if locked is not None and value != locked:
                issue(errors, "approved_name_changed", location, "proposed name differs from the approved spelling")
            if state == "user" and locked is None:
                issue(errors, "missing_approval_evidence", location, "user approval requires an exact approved value")
            if locked is not None and state != "user":
                issue(errors, "approval_mismatch", location, "approved value must retain user approval status")
            if state == "unresolved":
                issue(errors, "unresolved_approval", location, "approval is unresolved")
            if value != value.strip():
                issue(errors, "outer_whitespace", location, "remove accidental outer whitespace explicitly")
            key = normalized(value)
            if key in seen[field]:
                issue(errors, "duplicate_name", location, "conflicts with " + seen[field][key])
            else:
                seen[field][key] = identity
            for prefix in plan.get("author_prefixes", []):
                if key.startswith(normalized(prefix)):
                    issue(warnings, "author_prefix", location, "review declared author/studio prefix")
                    break
    return {"ok": not errors, "counts": counts, "errors": errors, "warnings": warnings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="UTF-8 naming review JSON; never modified")
    args = parser.parse_args()
    try:
        plan = json.loads(args.input.read_text(encoding="utf-8"), object_pairs_hook=unique_object,
                          parse_constant=reject_constant)
        report = audit(plan)
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
