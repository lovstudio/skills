#!/usr/bin/env python3
"""Run the bundled cli2anything++ project without shell evaluation."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    cli = project_root / "bin" / "cli2anything.mjs"
    package = project_root / "package.json"

    if not cli.is_file() or not package.is_file():
        print(
            "ERROR: cli2anything++ project runtime is incomplete; expected "
            "bin/cli2anything.mjs and package.json beside the internal Skill.",
            file=sys.stderr,
        )
        return 2
    if shutil.which("node") is None:
        print("ERROR: Node.js 20+ is required but node was not found in PATH.", file=sys.stderr)
        return 2

    if sys.argv[1:] == ["--project-test"]:
        return subprocess.run(["npm", "test"], cwd=project_root, check=False).returncode

    return subprocess.run(
        ["node", str(cli), *sys.argv[1:]],
        cwd=project_root,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
