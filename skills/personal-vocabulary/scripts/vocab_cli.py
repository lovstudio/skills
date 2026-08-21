#!/usr/bin/env python3
"""Deterministic local CLI for the canonical personal vocabulary.

Pure text, idempotent, standard library only. It never touches the network,
never writes a target app, and never reads or prints credentials.

Subcommands:
  init       create an empty canonical vocabulary.json
  validate   check a canonical vocabulary.json for schema errors
  merge      import terms from an app file into the canonical store (dedupe by phrase)
  render     convert the canonical store into one app's file format
  diff       compare the canonical store against an app's terms and emit a plan
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
LANG_RE = re.compile(r"^[a-z]{2,3}(-[A-Za-z]{2,4})?$")
CATEGORIES = {"general", "company", "person", "product", "place", "other"}
APP_PHRASE_KEY = {
    "openless": "phrase",
    "typeless": "term",
    "canonical": "phrase",
}
# Key fields that define a "same" entry for diff purposes.
KEY_FIELDS = ("note", "category", "lang", "enabled")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "+00:00")


def _load(path: Path):
    data = json.loads(path.read_text())
    if isinstance(data, list):
        # Bare array => treat as app-style entries, not canonical wrapper.
        return {"entries": data}
    return data


def _save(path: Path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def canonical_entries(canonical: Path) -> list:
    data = _load(canonical)
    return data.get("entries", [])


def normalize_phrase(text: str) -> str:
    return " ".join(str(text).strip().split())


def validate(canonical: Path) -> int:
    errors = []
    data = _load(canonical)
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        errors.append("entries must be a list")
        entries = []
    seen = {}
    for idx, e in enumerate(entries):
        phrase = normalize_phrase(e.get("phrase", ""))
        if not phrase:
            errors.append(f"entries[{idx}]: empty phrase")
            continue
        if phrase in seen:
            errors.append(f"entries[{idx}]: duplicate phrase '{phrase}' (first at {seen[phrase]})")
        seen[phrase] = idx
        cat = e.get("category", "general")
        if cat not in CATEGORIES:
            errors.append(f"entries[{idx}]: invalid category '{cat}'")
        lang = e.get("lang", "")
        if lang and not LANG_RE.match(lang):
            errors.append(f"entries[{idx}]: invalid lang '{lang}'")
        if "enabled" in e and not isinstance(e["enabled"], bool):
            errors.append(f"entries[{idx}]: enabled must be boolean")
    for msg in errors:
        print(f"ERROR: {msg}")
    return 1 if errors else 0


def init(canonical: Path, args) -> int:
    if canonical.exists():
        print(f"refused: {canonical} already exists")
        return 1
    obj = {"version": SCHEMA_VERSION, "updated_at": _now(), "entries": []}
    canonical.parent.mkdir(parents=True, exist_ok=True)
    _save(canonical, obj)
    print(f"created={canonical}")
    return 0


def _entry_from_app(raw: dict, from_app: str) -> dict:
    phrase = raw.get(APP_PHRASE_KEY.get(from_app, "phrase"), "") if from_app != "canonical" else raw.get("phrase", "")
    phrase = normalize_phrase(phrase)
    if not phrase:
        return None
    note = raw.get("note")
    category = raw.get("category", "general")
    lang = raw.get("lang", "zh-CN")
    enabled = raw.get("enabled", True)
    hits = raw.get("hits", 0)
    created_at = raw.get("created_at") or raw.get("createdAt") or _now()
    updated_at = raw.get("updated_at") or raw.get("updatedAt") or created_at
    return {
        "phrase": phrase,
        "note": note,
        "category": category,
        "lang": lang,
        "enabled": enabled,
        "hits": hits,
        "source": from_app,
        "created_at": created_at,
        "updated_at": updated_at,
    }


def merge(canonical: Path, import_file: Path, from_app: str) -> int:
    data = _load(canonical)
    entries = data.get("entries", [])
    existing = {normalize_phrase(e["phrase"]) for e in entries}
    imported = _load(import_file)
    raw_entries = imported.get("entries", imported) if isinstance(imported, dict) else imported
    added = 0
    skipped = 0
    now = _now()
    for raw in raw_entries:
        ent = _entry_from_app(raw, from_app)
        if ent is None:
            continue
        if ent["phrase"] in existing:
            skipped += 1
            continue
        ent.setdefault("created_at", now)
        ent.setdefault("updated_at", now)
        entries.append(ent)
        existing.add(ent["phrase"])
        added += 1
    data["entries"] = entries
    data["updated_at"] = now
    _save(canonical, data)
    print(f"added={added} skipped={skipped} total={len(entries)}")
    return 0


def render(canonical: Path, app: str, output: Path) -> int:
    entries = canonical_entries(canonical)
    if app == "openless":
        rows = [
            {
                "id": f"vocab-{normalize_phrase(e['phrase']) or 'x'}",
                "phrase": e["phrase"],
                "note": e.get("note"),
                "enabled": e.get("enabled", True),
                "hits": e.get("hits", 0),
                "createdAt": e.get("created_at", _now()),
            }
            for e in entries
        ]
    elif app == "typeless":
        rows = [
            {
                "term": e["phrase"],
                "lang": e.get("lang", "zh-CN"),
                "category": e.get("category", "general"),
                "auto": False,
                "replace": False,
                "replace_targets": [],
            }
            for e in entries
        ]
    else:
        print(f"unsupported app: {app}")
        return 1
    _save(output, rows)
    print(f"rendered={output} rows={len(rows)}")
    return 0


def _app_terms(app: str, app_file: Path) -> list:
    if not app_file or not app_file.exists():
        return []
    data = _load(app_file)
    return data.get("entries", data) if isinstance(data, dict) else data


def diff(canonical: Path, app: str, app_file: Path) -> int:
    canon = canonical_entries(canonical)
    app_terms = _app_terms(app, app_file)
    app_by_phrase = {normalize_phrase(t.get(APP_PHRASE_KEY.get(app, "term"), "")): t for t in app_terms}
    classes = {"add": [], "skip": [], "conflict": [], "app_only": []}
    for e in canon:
        phrase = normalize_phrase(e["phrase"])
        if phrase not in app_by_phrase:
            classes["add"].append(phrase)
            continue
        other = app_by_phrase[phrase]
        # Only compare fields the app actually carries. Lossy app formats (e.g.
        # openless carries no category/lang) must not surface as conflicts.
        same = True
        for k in KEY_FIELDS:
            if k not in other:
                continue
            canon_val = bool(e.get(k, True)) if k == "enabled" else e.get(k)
            app_val = bool(other.get(k, True)) if k == "enabled" else other.get(k)
            if canon_val != app_val:
                same = False
                break
        classes["skip" if same else "conflict"].append(phrase)
    for phrase in app_by_phrase:
        if phrase not in {normalize_phrase(e["phrase"]) for e in canon}:
            classes["app_only"].append(phrase)
    for k in ("add", "skip", "conflict", "app_only"):
        print(f"{k}={len(classes[k])}")
        for phrase in classes[k]:
            print(f"  - {phrase}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="vocab_cli", description="Canonical personal vocabulary CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init")
    s.add_argument("--canonical", required=True, type=Path)
    s.set_defaults(fn=init)

    s = sub.add_parser("validate")
    s.add_argument("--canonical", required=True, type=Path)
    s.set_defaults(fn=validate)

    s = sub.add_parser("merge")
    s.add_argument("--canonical", required=True, type=Path)
    s.add_argument("--import", dest="import_file", required=True, type=Path)
    s.add_argument("--from-app", required=True, choices=["openless", "typeless", "canonical"])
    s.set_defaults(fn=merge)

    s = sub.add_parser("render")
    s.add_argument("--canonical", required=True, type=Path)
    s.add_argument("--app", required=True, choices=["openless", "typeless"])
    s.add_argument("--output", required=True, type=Path)
    s.set_defaults(fn=render)

    s = sub.add_parser("diff")
    s.add_argument("--canonical", required=True, type=Path)
    s.add_argument("--app", required=True, choices=["openless", "typeless"])
    s.add_argument("--app-file", type=Path)
    s.set_defaults(fn=diff)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "init":
            return init(args.canonical, args)
        if args.cmd == "validate":
            return validate(args.canonical)
        return _dispatch(args)
    except FileNotFoundError as e:
        print(f"ERROR: file not found: {e}")
        return 2
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}")
        return 2


def _dispatch(args):
    if args.cmd == "merge":
        return merge(args.canonical, args.import_file, args.from_app)
    if args.cmd == "render":
        return render(args.canonical, args.app, args.output)
    if args.cmd == "diff":
        return diff(args.canonical, args.app, args.app_file)
    return 1


if __name__ == "__main__":
    sys.exit(main())
