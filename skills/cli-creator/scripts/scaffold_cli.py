#!/usr/bin/env python3
"""Create a safe, installable CLI harness from a validated lov-cli plan."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


PLAN_SCHEMA = "lov-cli-plan/v1"
CLI_SCHEMA = "lov-cli/v1"
RESERVED_COMMANDS = {"doctor", "info", "capabilities"}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PARAM_RE = re.compile(r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$")
PACKAGE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
PARAMETER_TYPES = {"string", "path", "int", "float"}
PARAMETER_KINDS = {"positional", "option", "flag"}


class PlanError(ValueError):
    pass


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    if not value:
        raise PlanError("project name cannot be converted to a safe slug")
    return value


def package_name(slug: str) -> str:
    return "lov_cli_" + slug.replace("-", "_")


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PlanError(f"{label} must be a non-empty string")
    return value.strip()


def validate_parameter(raw: Any, command_name: str, index: int) -> Dict[str, Any]:
    label = f"commands[{command_name}].parameters[{index}]"
    if not isinstance(raw, dict):
        raise PlanError(f"{label} must be an object")
    parameter = dict(raw)
    name = require_text(parameter.get("name"), f"{label}.name")
    if not PARAM_RE.fullmatch(name):
        raise PlanError(f"{label}.name must be lower kebab-case or snake_case")
    kind = require_text(parameter.get("kind"), f"{label}.kind")
    if kind not in PARAMETER_KINDS:
        raise PlanError(f"{label}.kind must be positional, option, or flag")
    parameter["name"] = name
    parameter["kind"] = kind
    parameter["required"] = bool(parameter.get("required", False))
    parameter["repeatable"] = bool(parameter.get("repeatable", False))
    if kind == "flag":
        parameter.pop("type", None)
        parameter["repeatable"] = False
    else:
        value_type = parameter.get("type", "string")
        if value_type not in PARAMETER_TYPES:
            raise PlanError(f"{label}.type must be one of: {', '.join(sorted(PARAMETER_TYPES))}")
        parameter["type"] = value_type
    if kind == "positional":
        if parameter.get("repeatable"):
            raise PlanError(f"{label}: repeatable positional parameters are not supported")
        parameter.pop("flags", None)
        parameter.setdefault("backend_flag", None)
    else:
        flags = parameter.get("flags")
        if not isinstance(flags, list) or not flags or not all(
            isinstance(flag, str) and flag.startswith("-") and " " not in flag
            for flag in flags
        ):
            raise PlanError(f"{label}.flags must be a non-empty list of option flags")
        if len(set(flags)) != len(flags):
            raise PlanError(f"{label}.flags contains duplicates")
        parameter["backend_flag"] = parameter.get("backend_flag") or flags[0]
        if not isinstance(parameter["backend_flag"], str) or not parameter["backend_flag"].startswith("-"):
            raise PlanError(f"{label}.backend_flag must be an option flag")
    if "choices" in parameter:
        choices = parameter["choices"]
        if not isinstance(choices, list) or not choices:
            raise PlanError(f"{label}.choices must be a non-empty list")
    return parameter


def validate_command(raw: Any, index: int, backend_kind: str) -> Dict[str, Any]:
    label = f"commands[{index}]"
    if not isinstance(raw, dict):
        raise PlanError(f"{label} must be an object")
    command = dict(raw)
    name = require_text(command.get("name"), f"{label}.name")
    if not NAME_RE.fullmatch(name):
        raise PlanError(f"{label}.name must be kebab-case")
    if name in RESERVED_COMMANDS:
        raise PlanError(f"{label}.name is reserved: {name}")
    command["name"] = name
    command["description"] = require_text(command.get("description"), f"{label}.description")
    command["mutates"] = bool(command.get("mutates", False))
    raw_parameters = command.get("parameters", [])
    if not isinstance(raw_parameters, list):
        raise PlanError(f"{label}.parameters must be a list")
    command["parameters"] = [
        validate_parameter(parameter, name, parameter_index)
        for parameter_index, parameter in enumerate(raw_parameters)
    ]
    parameter_names = [parameter["name"] for parameter in command["parameters"]]
    if len(parameter_names) != len(set(parameter_names)):
        raise PlanError(f"{label}.parameters contains duplicate names")
    flags = [
        flag
        for parameter in command["parameters"]
        for flag in parameter.get("flags", [])
    ]
    if len(flags) != len(set(flags)):
        raise PlanError(f"{label}.parameters contains duplicate flags")
    argv = command.get("argv", [])
    if backend_kind == "subprocess":
        if not isinstance(argv, list) or not argv or not all(
            isinstance(item, str) and item for item in argv
        ):
            raise PlanError(f"{label}.argv must be a non-empty string array for subprocess backends")
    elif argv and (not isinstance(argv, list) or not all(isinstance(item, str) for item in argv)):
        raise PlanError(f"{label}.argv must be a string array")
    command["argv"] = argv
    postconditions = command.get("postconditions", [])
    if not isinstance(postconditions, list) or not all(
        isinstance(item, str) and item.strip() for item in postconditions
    ):
        raise PlanError(f"{label}.postconditions must be a list of non-empty strings")
    command["postconditions"] = postconditions
    return command


def normalize_plan(raw: Any, project: Path, output: Path) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise PlanError("plan root must be an object")
    if raw.get("schema") != PLAN_SCHEMA:
        raise PlanError(f"plan.schema must be {PLAN_SCHEMA}")
    name = require_text(raw.get("name"), "plan.name")
    slug = slugify(name if name else project.name)
    command = raw.get("command") or f"lov-cli-{slug}"
    if not isinstance(command, str) or not NAME_RE.fullmatch(command):
        raise PlanError("plan.command must be kebab-case")
    package = raw.get("package") or package_name(slug)
    if not isinstance(package, str) or not PACKAGE_RE.fullmatch(package):
        raise PlanError("plan.package must be a safe snake_case Python package name")
    version = raw.get("version", "0.1.0")
    if not isinstance(version, str) or not SEMVER_RE.fullmatch(version):
        raise PlanError("plan.version must use SemVer")
    description = require_text(raw.get("description"), "plan.description")
    python_dependencies = raw.get("python_dependencies", [])
    if not isinstance(python_dependencies, list) or not all(
        isinstance(item, str) and item.strip() for item in python_dependencies
    ):
        raise PlanError("plan.python_dependencies must be a list of requirement strings")
    backend = raw.get("backend")
    if not isinstance(backend, dict):
        raise PlanError("plan.backend must be an object")
    backend = dict(backend)
    kind = backend.get("kind")
    if kind not in {"subprocess", "custom"}:
        raise PlanError("plan.backend.kind must be subprocess or custom")
    backend["kind"] = kind
    backend["name"] = require_text(backend.get("name"), "plan.backend.name")
    executable = backend.get("executable")
    if executable is not None and (not isinstance(executable, str) or not executable.strip()):
        raise PlanError("plan.backend.executable must be a non-empty string when supplied")
    backend["install"] = require_text(
        backend.get("install", "Install the target project's required runtime."),
        "plan.backend.install",
    )
    timeout = backend.get("timeout_seconds", 120)
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
        raise PlanError("plan.backend.timeout_seconds must be a positive integer")
    backend["timeout_seconds"] = timeout
    raw_commands = raw.get("commands")
    if not isinstance(raw_commands, list) or not raw_commands:
        raise PlanError("plan.commands must contain at least one project-specific command")
    commands = [
        validate_command(item, index, kind) for index, item in enumerate(raw_commands)
    ]
    names = [item["name"] for item in commands]
    if len(names) != len(set(names)):
        raise PlanError("plan.commands contains duplicate names")
    root_relative = Path(os.path.relpath(project, output)).as_posix()
    return {
        "schema": CLI_SCHEMA,
        "status": "scaffold",
        "name": name,
        "slug": slug,
        "command": command,
        "package": package,
        "version": version,
        "description": description,
        "python_dependencies": python_dependencies,
        "project": {"name": project.name, "root_relative": root_relative},
        "backend": backend,
        "commands": commands,
        "generated_by": "lov-cli-creator/0.1.0",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def command_table(commands: Iterable[Dict[str, Any]]) -> str:
    lines = ["| Command | Mutates | Description |", "|---|---:|---|"]
    for command in commands:
        description = command["description"].replace("|", "\\|")
        lines.append(
            f"| `{command['name']}` | {'yes' if command['mutates'] else 'no'} | {description} |"
        )
    return "\n".join(lines)


def render(template: str, replacements: Dict[str, str]) -> str:
    result = template
    for token, value in replacements.items():
        result = result.replace(token, value)
    unresolved = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]+__", result)))
    if unresolved:
        raise PlanError(f"template has unresolved tokens: {', '.join(unresolved)}")
    return result


def write_from_templates(destination: Path, spec: Dict[str, Any]) -> None:
    template_root = Path(__file__).resolve().parents[1] / "assets" / "cli-template"
    package = spec["package"]
    replacements = {
        "__PROJECT_NAME__": spec["name"],
        "__PROJECT_SLUG__": spec["slug"],
        "__COMMAND_NAME__": spec["command"],
        "__PACKAGE_NAME__": package,
        "__DISTRIBUTION_NAME__": spec["command"],
        "__VERSION__": spec["version"],
        "__DESCRIPTION__": spec["description"],
        "__DESCRIPTION_TOML__": toml_escape(spec["description"]),
        "__DESCRIPTION_PYTHON__": repr(spec["description"]),
        "__DEPENDENCIES_TOML__": json.dumps(spec["python_dependencies"]),
        "__DEPENDENCIES_PYTHON__": repr(spec["python_dependencies"]),
        "__DEPENDENCIES_LINES__": "\n".join(spec["python_dependencies"]),
        "__BACKEND_NAME__": spec["backend"]["name"],
        "__COMMAND_TABLE__": command_table(spec["commands"]),
        "__YEAR__": str(datetime.now(timezone.utc).year),
    }
    mapping = {
        "pyproject.toml.tmpl": destination / "pyproject.toml",
        "setup.py.tmpl": destination / "setup.py",
        "requirements.txt.tmpl": destination / "requirements.txt",
        "README.md.tmpl": destination / "README.md",
        "CLI_SPEC.md.tmpl": destination / "CLI_SPEC.md",
        "TEST.md.tmpl": destination / "TEST.md",
        "LICENSE.tmpl": destination / "LICENSE",
        "package/__init__.py.tmpl": destination / "src" / package / "__init__.py",
        "package/__main__.py.tmpl": destination / "src" / package / "__main__.py",
        "package/backend.py.tmpl": destination / "src" / package / "backend.py",
        "package/cli.py.tmpl": destination / "src" / package / "cli.py",
        "tests/test_core.py.tmpl": destination / "tests" / "test_core.py",
        "tests/test_e2e.py.tmpl": destination / "tests" / "test_e2e.py",
    }
    for source_name, target in mapping.items():
        source = template_root / source_name
        if not source.is_file():
            raise PlanError(f"required template is missing: {source_name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            render(source.read_text(encoding="utf-8"), replacements),
            encoding="utf-8",
        )
    serialized = json.dumps(spec, ensure_ascii=False, indent=2) + "\n"
    (destination / "lov-cli.json").write_text(serialized, encoding="utf-8")
    (destination / "src" / package / "cli_spec.json").write_text(serialized, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--plan", type=Path, required=True, help="lov-cli-plan/v1 JSON file")
    parser.add_argument("--output", type=Path, help="Harness directory; defaults to PROJECT/agent-harness")
    parser.add_argument("--json", dest="json_output", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project = args.project.expanduser().resolve()
    if not project.is_dir():
        print("ERROR: project path is not a directory", file=sys.stderr)
        return 2
    plan_path = args.plan.expanduser().resolve()
    if not plan_path.is_file():
        print("ERROR: plan file does not exist", file=sys.stderr)
        return 2
    output = (args.output.expanduser() if args.output else project / "agent-harness").resolve()
    if output.exists():
        print(f"ERROR: output target already exists: {output}", file=sys.stderr)
        return 5
    try:
        raw = json.loads(plan_path.read_text(encoding="utf-8"))
        spec = normalize_plan(raw, project, output)
    except (OSError, json.JSONDecodeError, PlanError) as exc:
        print(f"ERROR: invalid CLI plan: {exc}", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    try:
        write_from_templates(temporary, spec)
        os.replace(temporary, output)
    except (OSError, PlanError) as exc:
        shutil.rmtree(temporary, ignore_errors=True)
        print(f"ERROR: failed to create harness: {exc}", file=sys.stderr)
        return 4
    result = {
        "ok": True,
        "status": "scaffold",
        "project": str(project),
        "output": str(output),
        "command": spec["command"],
        "package": spec["package"],
        "next": [
            "Complete or verify the real backend adapter.",
            "Finish TEST.md and real installed-command E2E coverage.",
            "Set lov-cli.json status to ready only after tests pass.",
        ],
    }
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False))
    else:
        for key in ("project", "output", "command", "package", "status"):
            print(f"{key}={result[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
