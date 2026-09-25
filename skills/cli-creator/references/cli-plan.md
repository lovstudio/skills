# `lov-cli-plan/v1` Schema

The plan is a UTF-8 JSON object written after project analysis and before
scaffolding. It is both the generation input and an auditable command design.

## Top-level fields

| Field | Required | Meaning |
|---|---:|---|
| `schema` | yes | Exact value `lov-cli-plan/v1` |
| `name` | yes | Human-readable project name |
| `command` | no | Kebab-case console name; default `lov-cli-` plus project slug |
| `package` | no | Python import name; derived safely when absent |
| `version` | no | Initial SemVer, default `0.1.0` |
| `description` | yes | Concrete user-visible CLI outcome |
| `python_dependencies` | no | Python requirement strings needed by the harness/backend |
| `backend` | yes | Real backend dependency and invocation policy |
| `commands` | yes | One or more project-specific command definitions |

Built-in `doctor`, `info`, and `capabilities` commands are generated and must not
be redefined in `commands`.

## Backend object

```json
{
  "kind": "subprocess",
  "name": "Project runtime",
  "executable": "python3",
  "install": "Install the project runtime described by the target README.",
  "timeout_seconds": 120
}
```

`kind` is `subprocess` for a fixed argv bridge or `custom` when generated source
will be completed with an in-process/protocol adapter. `doctor` checks the named
executable when supplied. The subprocess runner never uses a shell.

Within a command's fixed `argv`, `$PYTHON` resolves to the interpreter running
the harness and `$PROJECT_ROOT` resolves to the configured real project root.

## Command object

```json
{
  "name": "validate",
  "description": "Validate a Skill source directory.",
  "mutates": false,
  "argv": ["$PYTHON", "scripts/validate_skill.py"],
  "parameters": [
    {
      "name": "path",
      "kind": "positional",
      "type": "path",
      "required": false,
      "default": "."
    }
  ],
  "postconditions": ["Backend exits zero", "Validation reports PASSED"]
}
```

Command names are unique kebab-case values. `argv` is a fixed array, not a shell
string. `mutates` documents whether the command changes project state.

## Parameter object

| Field | Values | Notes |
|---|---|---|
| `name` | kebab-case or snake_case | Stable JSON/input key |
| `kind` | `positional`, `option`, `flag` | Parsing and backend behavior |
| `flags` | list of option strings | Required for option/flag; long flag preferred |
| `type` | `string`, `path`, `int`, `float` | Flags omit `type` |
| `required` | boolean | Optional when a default exists |
| `default` | JSON scalar | Used when the caller omits the value |
| `choices` | list of JSON scalars | Optional closed set |
| `repeatable` | boolean | Repeats the backend flag for each value |
| `backend_flag` | option string or null | Null appends a positional value |

For `kind: flag`, a true value appends `backend_flag`. For options, each supplied
value is appended after `backend_flag`; a repeatable option repeats the pair.

## Example plan

```json
{
  "schema": "lov-cli-plan/v1",
  "name": "Example Project",
  "command": "lov-cli-example",
  "description": "Inspect and validate Example Project through its real scripts.",
  "python_dependencies": [],
  "backend": {
    "kind": "subprocess",
    "name": "Python",
    "executable": "python3",
    "install": "Install Python 3.9 or newer.",
    "timeout_seconds": 120
  },
  "commands": [
    {
      "name": "validate",
      "description": "Run the project's source validator.",
      "mutates": false,
      "argv": ["$PYTHON", "scripts/validate.py"],
      "parameters": [
        {
          "name": "path",
          "kind": "positional",
          "type": "path",
          "required": false,
          "default": "."
        }
      ],
      "postconditions": ["Validator returns zero"]
    }
  ]
}
```

The scaffold validates names, types, flags, duplicate commands, reserved names,
and fixed argv arrays before writing anything.
