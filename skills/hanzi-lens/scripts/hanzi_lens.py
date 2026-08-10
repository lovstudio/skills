#!/usr/bin/env python3
"""Inspect, scaffold, and audit evidence-led Chinese-character exhibits."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE = Path("~/.lovstudio/skills/profile.json")
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|FIXME)\b|请替换|占位|Lorem ipsum", re.I)
PERSON_INFERENCE = re.compile(r"姓名|性格|命理|姻缘|缘分|女生|男生|女孩|男孩")
FONT_SUFFIXES = {".ttf", ".otf", ".ttc", ".otc"}

CJK_RANGES: Tuple[Tuple[int, int, str], ...] = (
    (0x3400, 0x4DBF, "CJK Unified Ideographs Extension A"),
    (0x4E00, 0x9FFF, "CJK Unified Ideographs"),
    (0xF900, 0xFAFF, "CJK Compatibility Ideographs"),
    (0x20000, 0x2A6DF, "CJK Unified Ideographs Extension B"),
    (0x2A700, 0x2B73F, "CJK Unified Ideographs Extension C"),
    (0x2B740, 0x2B81F, "CJK Unified Ideographs Extension D"),
    (0x2B820, 0x2CEAF, "CJK Unified Ideographs Extension E"),
    (0x2CEB0, 0x2EBEF, "CJK Unified Ideographs Extension F"),
    (0x2EBF0, 0x2EE5F, "CJK Unified Ideographs Extension I"),
    (0x2F800, 0x2FA1F, "CJK Compatibility Ideographs Supplement"),
    (0x30000, 0x3134F, "CJK Unified Ideographs Extension G"),
    (0x31350, 0x323AF, "CJK Unified Ideographs Extension H"),
    (0x323B0, 0x3347F, "CJK Unified Ideographs Extension J"),
)


class CliError(RuntimeError):
    """Actionable CLI failure."""


def expand_path(value: str, base: Optional[Path] = None) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(value))
    path = Path(expanded)
    if not path.is_absolute() and base is not None:
        path = base / path
    return path.resolve()


def read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CliError(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CliError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CliError(f"Expected a JSON object in {path}")
    return value


def write_json(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def is_variation_selector(codepoint: int) -> bool:
    return 0xFE00 <= codepoint <= 0xFE0F or 0xE0100 <= codepoint <= 0xE01EF


def cjk_block(codepoint: int) -> Optional[str]:
    for start, end, label in CJK_RANGES:
        if start <= codepoint <= end:
            return label
    return None


def parse_character(raw: str) -> Tuple[str, int, List[int]]:
    value = unicodedata.normalize("NFC", raw.strip())
    if not value:
        raise CliError("Character input is empty.")
    points = [ord(char) for char in value]
    base = points[0]
    if cjk_block(base) is None:
        raise CliError(
            f"Expected one Han ideograph; got U+{base:04X} "
            f"({unicodedata.name(value[0], 'UNKNOWN')})."
        )
    if any(not is_variation_selector(point) for point in points[1:]):
        raise CliError(
            "Expected one Han ideograph, optionally followed by Unicode "
            "variation selectors."
        )
    return value, base, points


def inspect_data(raw: str) -> Dict[str, Any]:
    value, base, points = parse_character(raw)
    return {
        "schema_version": 1,
        "character": value,
        "base_character": chr(base),
        "base_codepoint": f"U+{base:04X}",
        "codepoints": [f"U+{point:04X}" for point in points],
        "unicode_name": unicodedata.name(chr(base), "UNKNOWN"),
        "unicode_block": cjk_block(base),
        "unicode_category": unicodedata.category(chr(base)),
        "east_asian_width": unicodedata.east_asian_width(chr(base)),
        "normalized_nfc": unicodedata.normalize("NFC", value),
        "normalized_nfkc": unicodedata.normalize("NFKC", value),
        "variation_selectors": [
            f"U+{point:04X}" for point in points[1:] if is_variation_selector(point)
        ],
        "runtime_unicode_version": unicodedata.unidata_version,
        "is_han": True,
    }


def shared_profile_path() -> Path:
    return expand_path(os.environ.get("LOVSTUDIO_SKILLS_PROFILE", str(DEFAULT_PROFILE)))


def load_profile() -> Dict[str, Any]:
    path = shared_profile_path()
    if not path.is_file():
        return {}
    return read_json(path)


def configured_output_root() -> Path:
    for raw in (
        os.environ.get("LOVSTUDIO_HANZI_LENS_OUTPUT_DIR"),
        os.environ.get("LOVSTUDIO_SKILLS_OUTPUT_DIR"),
    ):
        if raw:
            return expand_path(raw) / "hanzi-lens"
    profile = load_profile()
    workspace = profile.get("workspace")
    if isinstance(workspace, dict) and workspace.get("output_dir"):
        return (
            expand_path(
                str(workspace["output_dir"]),
                shared_profile_path().parent,
            )
            / "hanzi-lens"
        )
    return (Path.home() / "Documents" / "hanzi-lens").resolve()


def resolve_infographic_cli(explicit: Optional[str]) -> Path:
    candidates: List[Path] = []
    if explicit:
        configured = expand_path(explicit)
        candidates.append(
            configured / "scripts" / "infographic_cli.py"
            if configured.is_dir()
            else configured
        )
    env_dir = os.environ.get("LOVSTUDIO_HANZI_LENS_INFOGRAPHIC_SKILL_DIR")
    if env_dir:
        candidates.append(
            expand_path(env_dir) / "scripts" / "infographic_cli.py"
        )
    install_dir = os.environ.get("LOVSTUDIO_SKILLS_INSTALL_DIR")
    if install_dir:
        candidates.append(
            expand_path(install_dir)
            / "sgc-professional-infographic"
            / "scripts"
            / "infographic_cli.py"
        )
    candidates.extend(
        [
            SKILL_ROOT.parent
            / "sgc-professional-infographic"
            / "scripts"
            / "infographic_cli.py",
            SKILL_ROOT.parent
            / "professional-infographic-skill"
            / "scripts"
            / "infographic_cli.py",
        ]
    )
    for path in candidates:
        if path.is_file():
            return path.resolve()
    checked = "\n".join(f"- {path}" for path in candidates)
    raise CliError(
        "Could not locate sgc-professional-infographic. Pass "
        "--infographic-skill-dir or set "
        "LOVSTUDIO_HANZI_LENS_INFOGRAPHIC_SKILL_DIR.\n"
        f"Checked:\n{checked}"
    )


def command_inspect(args: argparse.Namespace) -> int:
    payload = inspect_data(args.character)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        output = expand_path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
        print(f"Character metadata: {output}")
    else:
        print(text)
    return 0


def empty_research(character: str) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "character": character,
        "pronunciations": [],
        "structure": {
            "radical": "",
            "strokes": None,
            "form_analysis": "",
            "source_ids": [],
        },
        "etymology": {
            "claim": "",
            "source_ids": [],
            "caveat": "",
        },
        "semantic_model": {
            "governing_message": "",
            "relationship": "",
            "branches": [],
        },
        "classical_examples": [],
        "sources": [],
        "interpretation_boundary": "",
        "omissions": [],
    }


def scaffold_source(character: str, request: str, locale: str, focus: str) -> str:
    return f"""# Source

## Exact request

{request.strip() or f"解释「{character}」这个汉字。"}

## Scope

- Character: {character}
- Locale: {locale}
- Focus: {focus.strip() or "读音、字形、字源、古义、经典用例与核心语义关系"}
- Default boundary: explain the character itself; avoid person-specific inference.

## Evidence

Record verified source excerpts here before authoring the Exhibit. Separate:

1. modern pronunciation and glyph standards;
2. historical lexicography;
3. classical usage in context;
4. interpretation and visual metaphor.
"""


def scaffold_brief(character: str) -> str:
    return f"""# Hanzi Lens brief

## Audience and decision

- Audience:
- Use moment:
- What should change after reading:

## Governing message

Write one source-supported conclusion about 「{character}」.

## Evidence graph

| ID | Claim | Exact evidence | Source ID | Encoding | Annotation |
|---|---|---|---|---|---|

## Fact and interpretation boundary

- Dictionary fact:
- Historical commentary:
- Contemporary interpretation:
- Visual metaphor:

## Visual job

- Primary relationship:
- Recommended professional-infographic template:
- Required encodings:
- Decision marker:

## Deliberate omissions

- Omit anything that does not strengthen the single visual argument.

## Human review

- [ ] The Exhibit explains the character rather than a person.
- [ ] The main visual proves the action title in five seconds.
- [ ] Regional readings and disputed analyses are labeled.
- [ ] Rare-glyph font coverage was checked before rendering.
"""


def command_scaffold(args: argparse.Namespace) -> int:
    metadata = inspect_data(args.character)
    character = str(metadata["character"])
    if args.output_dir:
        project = expand_path(args.output_dir)
    else:
        project = configured_output_root() / str(metadata["base_codepoint"]).lower()
    if project.exists() and any(project.iterdir()):
        raise CliError(f"Refusing to write into non-empty directory: {project}")
    project.mkdir(parents=True, exist_ok=True)
    write_json(project / "hanzi.json", metadata)
    write_json(project / "research.json", empty_research(character))
    write_json(
        project / "project.json",
        {
            "schema_version": 1,
            "character": character,
            "scope": "character-only",
            "locale": args.locale,
            "focus": args.focus,
            "dependency": "sgc-professional-infographic",
            "research": "research.json",
            "source": "source.md",
            "brief": "brief.md",
            "exhibit_dir": "exhibit",
        },
    )
    (project / "source.md").write_text(
        scaffold_source(character, args.request, args.locale, args.focus),
        encoding="utf-8",
    )
    (project / "brief.md").write_text(
        scaffold_brief(character),
        encoding="utf-8",
    )
    print(f"Hanzi project scaffolded: {project}")
    print(f"Research ledger: {project / 'research.json'}")
    return 0


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def source_ids(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def validate_research(
    research: Dict[str, Any],
    expected_character: str,
) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []

    def error(code: str, message: str) -> None:
        issues.append({"level": "error", "code": code, "message": message})

    if research.get("character") != expected_character:
        error("character-mismatch", "research.json character does not match project.")

    sources = research.get("sources")
    if not isinstance(sources, list) or len(sources) < 2:
        error("source-count", "At least two distinct sources are required.")
        sources = []
    known_ids: Set[str] = set()
    for index, item in enumerate(sources):
        if not isinstance(item, dict):
            error("source-shape", f"sources[{index}] must be an object.")
            continue
        source_id = str(item.get("id", "")).strip()
        if not source_id:
            error("source-id", f"sources[{index}] is missing id.")
        elif source_id in known_ids:
            error("source-id", f"Duplicate source id: {source_id}")
        else:
            known_ids.add(source_id)
        if not nonempty_text(item.get("title")):
            error("source-title", f"sources[{index}] is missing title.")
        url = str(item.get("url", "")).strip()
        if not re.match(r"^https?://", url):
            error("source-url", f"sources[{index}] needs an http(s) URL.")
        if not nonempty_text(item.get("type")):
            error("source-type", f"sources[{index}] is missing source type.")

    def check_refs(refs: Any, location: str) -> None:
        values = source_ids(refs)
        if not values:
            error("source-linkage", f"{location} needs source_ids.")
        for source_id in values:
            if source_id not in known_ids:
                error(
                    "unknown-source",
                    f"{location} references unknown source id {source_id}.",
                )

    pronunciations = research.get("pronunciations")
    if not isinstance(pronunciations, list) or not pronunciations:
        error("pronunciation", "At least one sourced pronunciation is required.")
    else:
        for index, item in enumerate(pronunciations):
            if not isinstance(item, dict) or not nonempty_text(item.get("reading")):
                error("pronunciation", f"pronunciations[{index}] needs a reading.")
                continue
            check_refs(item.get("source_ids"), f"pronunciations[{index}]")

    structure = research.get("structure")
    if not isinstance(structure, dict):
        error("structure", "structure must be an object.")
    else:
        for field in ("radical", "form_analysis"):
            if not nonempty_text(structure.get(field)):
                error("structure", f"structure.{field} is required.")
        strokes = structure.get("strokes")
        if not isinstance(strokes, int) or strokes <= 0:
            error("structure", "structure.strokes must be a positive integer.")
        check_refs(structure.get("source_ids"), "structure")

    etymology = research.get("etymology")
    if not isinstance(etymology, dict):
        error("etymology", "etymology must be an object.")
    else:
        if not nonempty_text(etymology.get("claim")):
            error("etymology", "etymology.claim is required.")
        if not nonempty_text(etymology.get("caveat")):
            error("etymology-caveat", "etymology.caveat is required.")
        check_refs(etymology.get("source_ids"), "etymology")

    model = research.get("semantic_model")
    if not isinstance(model, dict):
        error("semantic-model", "semantic_model must be an object.")
    else:
        for field in ("governing_message", "relationship"):
            if not nonempty_text(model.get(field)):
                error("semantic-model", f"semantic_model.{field} is required.")
        branches = model.get("branches")
        if not isinstance(branches, list) or len(branches) < 2:
            error("semantic-branches", "At least two semantic branches are required.")
        else:
            for index, branch in enumerate(branches):
                if not isinstance(branch, dict):
                    error("semantic-branches", f"branches[{index}] must be an object.")
                    continue
                if not nonempty_text(branch.get("label")):
                    error("semantic-branches", f"branches[{index}] needs label.")
                if not nonempty_text(branch.get("claim")):
                    error("semantic-branches", f"branches[{index}] needs claim.")
                check_refs(branch.get("source_ids"), f"branches[{index}]")

    examples = research.get("classical_examples")
    if not isinstance(examples, list) or len(examples) < 2:
        error("classical-examples", "At least two classical examples are required.")
    else:
        for index, item in enumerate(examples):
            if not isinstance(item, dict):
                error("classical-examples", f"classical_examples[{index}] must be an object.")
                continue
            for field in ("quote", "work", "gloss"):
                if not nonempty_text(item.get(field)):
                    error(
                        "classical-examples",
                        f"classical_examples[{index}].{field} is required.",
                    )
            check_refs(item.get("source_ids"), f"classical_examples[{index}]")

    if not nonempty_text(research.get("interpretation_boundary")):
        error(
            "interpretation-boundary",
            "interpretation_boundary must separate fact from interpretation.",
        )
    omissions = research.get("omissions")
    if not isinstance(omissions, list) or not omissions:
        error("omissions", "Record at least one deliberate omission.")

    return issues


def require_research(project: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    project_meta = read_json(project / "project.json")
    research = read_json(project / "research.json")
    character = str(project_meta.get("character", ""))
    issues = validate_research(research, character)
    if issues:
        lines = "\n".join(f"- {item['code']}: {item['message']}" for item in issues)
        raise CliError(f"Research ledger is not release-ready:\n{lines}")
    return project_meta, research


def command_exhibit(args: argparse.Namespace) -> int:
    project = expand_path(args.project)
    project_meta, _ = require_research(project)
    source = project / "source.md"
    if not source.is_file() or not source.read_text(encoding="utf-8").strip():
        raise CliError(f"Source file is empty or missing: {source}")
    output = project / "exhibit"
    if output.exists() and any(output.iterdir()):
        raise CliError(f"Refusing to overwrite non-empty exhibit directory: {output}")
    cli = resolve_infographic_cli(args.infographic_skill_dir)
    command = [
        sys.executable,
        str(cli),
        "scaffold",
        "--title",
        args.title,
        "--source",
        str(source),
        "--template",
        args.template,
        "--mode",
        "qualitative",
        "--aspect",
        args.aspect,
        "--output-dir",
        str(output),
    ]
    if args.brand_profile:
        command.extend(["--brand-profile", str(expand_path(args.brand_profile))])
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode:
        raise CliError(
            f"professional-infographic scaffold failed:\n"
            f"{result.stdout}{result.stderr}"
        )
    project_meta["exhibit"] = {
        "title": args.title,
        "template": args.template,
        "aspect": args.aspect,
        "path": "exhibit",
    }
    write_json(project / "project.json", project_meta)
    print(result.stdout.strip())
    print(f"Hanzi exhibit scaffolded: {output}")
    return 0


def discover_font_paths(font_dirs: Sequence[str], limit: int) -> List[Path]:
    paths: List[Path] = []
    if shutil.which("fc-list"):
        result = subprocess.run(
            ["fc-list", "-f", "%{file}\n"],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            paths.extend(Path(line.strip()) for line in result.stdout.splitlines() if line.strip())
    roots = [expand_path(value) for value in font_dirs]
    if not roots and not paths:
        roots = [
            Path("/System/Library/Fonts"),
            Path("/Library/Fonts"),
            Path.home() / "Library" / "Fonts",
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            Path.home() / ".fonts",
        ]
        windows = os.environ.get("WINDIR")
        if windows:
            roots.append(Path(windows) / "Fonts")
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.suffix.lower() in FONT_SUFFIXES:
                paths.append(path)
    unique: List[Path] = []
    seen: Set[str] = set()
    for path in paths:
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen or path.suffix.lower() not in FONT_SUFFIXES:
            continue
        seen.add(key)
        unique.append(path)
        if len(unique) >= limit:
            break
    return unique


def font_faces_supporting(path: Path, codepoint: int) -> List[str]:
    try:
        from fontTools.ttLib import TTCollection, TTFont
    except ImportError as exc:
        raise CliError(
            'font-check requires fontTools. Install with: '
            'python3 -m pip install "fonttools>=4.53,<5"'
        ) from exc

    def font_name(font: Any, fallback: str) -> str:
        names = font["name"].names if "name" in font else []
        family = ""
        style = ""
        for record in names:
            if record.nameID not in (1, 2):
                continue
            try:
                text = record.toUnicode().strip()
            except Exception:
                continue
            if record.nameID == 1 and not family:
                family = text
            elif record.nameID == 2 and not style:
                style = text
        return " ".join(part for part in (family, style) if part) or fallback

    matches: List[str] = []
    suffix = path.suffix.lower()
    try:
        if suffix in {".ttc", ".otc"}:
            collection = TTCollection(str(path), lazy=True)
            try:
                for index, font in enumerate(collection.fonts):
                    if codepoint in (font.getBestCmap() or {}):
                        matches.append(font_name(font, f"{path.name}#{index}"))
            finally:
                collection.close()
        else:
            font = TTFont(str(path), lazy=True)
            try:
                if codepoint in (font.getBestCmap() or {}):
                    matches.append(font_name(font, path.name))
            finally:
                font.close()
    except Exception:
        return []
    return matches


def command_font_check(args: argparse.Namespace) -> int:
    metadata = inspect_data(args.character)
    codepoint = int(str(metadata["base_codepoint"])[2:], 16)
    explicit = [expand_path(value) for value in args.font]
    fonts = explicit or discover_font_paths(args.font_dir, args.limit)
    matches: List[Dict[str, str]] = []
    for path in fonts:
        if not path.is_file():
            continue
        for face in font_faces_supporting(path, codepoint):
            matches.append(
                {
                    "font": face,
                    "file": path.name if args.portable else str(path.resolve()),
                }
            )
    report = {
        "schema_version": 1,
        "character": metadata["character"],
        "base_codepoint": metadata["base_codepoint"],
        "checked_fonts": len(fonts),
        "matching_faces": matches,
        "status": "pass" if matches else "fail",
        "portable_paths": bool(args.portable),
    }
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        output = expand_path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
        print(f"Font report: {output}")
    else:
        print(text)
    return 0 if matches else 1


def command_render(args: argparse.Namespace) -> int:
    project = expand_path(args.project)
    poster = project / "exhibit" / "poster.html"
    if not poster.is_file():
        raise CliError(f"Exhibit source is missing: {poster}")
    cli = resolve_infographic_cli(args.infographic_skill_dir)
    output = project / "exhibit" / "poster.png"
    command = [
        sys.executable,
        str(cli),
        "render",
        "--input",
        str(poster),
        "--output",
        str(output),
        "--scale",
        str(args.scale),
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode:
        raise CliError(
            f"professional-infographic render failed:\n"
            f"{result.stdout}{result.stderr}"
        )
    print(result.stdout.strip())
    return 0


def command_audit(args: argparse.Namespace) -> int:
    project = expand_path(args.project)
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    def add(target: List[Dict[str, str]], code: str, message: str) -> None:
        target.append({"code": code, "message": message})

    required = ("project.json", "hanzi.json", "research.json", "source.md", "brief.md")
    for name in required:
        if not (project / name).is_file():
            add(errors, "missing-file", f"Missing required file: {name}")

    project_meta: Dict[str, Any] = {}
    character = ""
    if not errors:
        project_meta = read_json(project / "project.json")
        character = str(project_meta.get("character", ""))
        research = read_json(project / "research.json")
        for issue in validate_research(research, character):
            add(errors, str(issue["code"]), str(issue["message"]))

    exhibit = project / "exhibit"
    poster_html = exhibit / "poster.html"
    poster_png = exhibit / "poster.png"
    if poster_html.is_file():
        markup = poster_html.read_text(encoding="utf-8")
        if character and character not in markup:
            add(errors, "character-visibility", "Target character is missing from poster.html.")
        if project_meta.get("scope") == "character-only" and PERSON_INFERENCE.search(markup):
            add(
                errors,
                "scope-leak",
                "Character-only poster contains person/name inference language.",
            )
        if PLACEHOLDER.search(markup):
            add(errors, "placeholder", "poster.html still contains placeholder copy.")
    elif args.strict:
        add(errors, "missing-exhibit", "Strict audit requires exhibit/poster.html.")
    else:
        add(warnings, "missing-exhibit", "Exhibit has not been authored yet.")

    font_report = project / "font-report.json"
    if font_report.is_file():
        report = read_json(font_report)
        if report.get("character") != character or report.get("status") != "pass":
            add(errors, "font-coverage", "font-report.json does not pass for this character.")
    elif args.strict:
        add(errors, "font-coverage", "Strict audit requires a passing font-report.json.")
    else:
        add(warnings, "font-coverage", "Font coverage has not been recorded.")

    infographic_result: Optional[Dict[str, Any]] = None
    infographic_output = ""
    if poster_html.is_file():
        try:
            cli = resolve_infographic_cli(args.infographic_skill_dir)
        except CliError as exc:
            add(errors, "dependency", str(exc))
        else:
            command = [
                sys.executable,
                str(cli),
                "audit",
                "--input",
                str(poster_html),
                "--report",
                str(exhibit / "audit.json"),
                "--human-review",
                args.human_review,
            ]
            if poster_png.is_file():
                command.extend(["--image", str(poster_png)])
            if args.review_note:
                command.extend(["--review-note", args.review_note])
            if args.strict:
                command.append("--strict")
            result = subprocess.run(command, text=True, capture_output=True, check=False)
            infographic_output = (result.stdout + result.stderr).strip()
            if (exhibit / "audit.json").is_file():
                infographic_result = read_json(exhibit / "audit.json")
            if result.returncode:
                add(
                    errors,
                    "infographic-audit",
                    infographic_output or "professional-infographic audit failed.",
                )

    if args.strict and not poster_png.is_file():
        add(errors, "missing-image", "Strict audit requires exhibit/poster.png.")

    output = expand_path(args.report) if args.report else project / "hanzi-audit.json"
    project_reference = (
        "."
        if output.parent.resolve() == project.resolve()
        else project.name
    )
    result_payload = {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "project": project_reference,
        "character": character,
        "strict": bool(args.strict),
        "status": "pass" if not errors and (not args.strict or not warnings) else "fail",
        "errors": errors,
        "warnings": warnings,
        "professional_infographic": infographic_result,
        "professional_infographic_output": infographic_output,
    }
    write_json(output, result_payload)
    status = result_payload["status"].upper()
    print(
        f"Hanzi audit {status}: {len(errors)} error(s), "
        f"{len(warnings)} warning(s)"
    )
    for item in errors:
        print(f"ERROR {item['code']}: {item['message']}")
    for item in warnings:
        print(f"WARN {item['code']}: {item['message']}")
    return 0 if result_payload["status"] == "pass" else 1


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Inspect, scaffold, and audit evidence-led Hanzi Lens projects."
    )
    subparsers = root.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Validate one Han ideograph and print Unicode metadata.",
    )
    inspect_parser.add_argument("character")
    inspect_parser.add_argument("--output", help="Optional JSON output path.")
    inspect_parser.set_defaults(handler=command_inspect)

    scaffold_parser = subparsers.add_parser(
        "scaffold",
        help="Create a non-destructive Hanzi research project.",
    )
    scaffold_parser.add_argument("character")
    scaffold_parser.add_argument("--output-dir")
    scaffold_parser.add_argument("--request", default="")
    scaffold_parser.add_argument("--focus", default="")
    scaffold_parser.add_argument(
        "--locale",
        choices=("zh-CN", "zh-TW", "both"),
        default="both",
    )
    scaffold_parser.set_defaults(handler=command_scaffold)

    exhibit_parser = subparsers.add_parser(
        "exhibit",
        help="Scaffold the dependent professional-infographic Exhibit.",
    )
    exhibit_parser.add_argument("--project", required=True)
    exhibit_parser.add_argument("--title", required=True)
    exhibit_parser.add_argument(
        "--template",
        choices=(
            "comparison-matrix",
            "decision-tree",
            "driver-tree",
            "positioning-map",
            "waterfall",
            "roadmap",
            "operating-model",
            "small-multiples",
        ),
        default="driver-tree",
    )
    exhibit_parser.add_argument(
        "--aspect",
        choices=("16:9", "4:5", "1:1", "A4"),
        default="16:9",
    )
    exhibit_parser.add_argument("--brand-profile")
    exhibit_parser.add_argument("--infographic-skill-dir")
    exhibit_parser.set_defaults(handler=command_exhibit)

    font_parser = subparsers.add_parser(
        "font-check",
        help="Find installed font faces that contain the ideograph.",
    )
    font_parser.add_argument("character")
    font_parser.add_argument("--font", action="append", default=[])
    font_parser.add_argument("--font-dir", action="append", default=[])
    font_parser.add_argument("--limit", type=int, default=1500)
    font_parser.add_argument("--portable", action="store_true")
    font_parser.add_argument("--output")
    font_parser.set_defaults(handler=command_font_check)

    render_parser = subparsers.add_parser(
        "render",
        help="Render exhibit/poster.html through professional-infographic.",
    )
    render_parser.add_argument("--project", required=True)
    render_parser.add_argument("--scale", type=int, choices=(1, 2, 3), default=2)
    render_parser.add_argument("--infographic-skill-dir")
    render_parser.set_defaults(handler=command_render)

    audit_parser = subparsers.add_parser(
        "audit",
        help="Audit Hanzi research, scope, font coverage, and the dependent Exhibit.",
    )
    audit_parser.add_argument("--project", required=True)
    audit_parser.add_argument("--report")
    audit_parser.add_argument("--infographic-skill-dir")
    audit_parser.add_argument("--strict", action="store_true")
    audit_parser.add_argument(
        "--human-review",
        choices=("pending", "passed", "failed"),
        default="pending",
    )
    audit_parser.add_argument("--review-note")
    audit_parser.set_defaults(handler=command_audit)
    return root


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except CliError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
