#!/usr/bin/env python3
"""Append a zsh function alias to a zsh rc file, idempotently.

Use case: turn a trigger word (English or 中文) into a one-liner that runs
any command. zsh supports CJK function names, so 中文 trigger works.

Examples:
  add_alias.py --name zxsd --cmd 'claude "说一句开心的话"' --comment '中信书店'
  add_alias.py --name 中信书店 --cmd 'claude "说一句开心的话"' --also-as zxsd
  add_alias.py --name gs --cmd 'git status' --simple   # use `alias` instead of function
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

MARKER_BEGIN = "# >>> lov-zsh-alias >>>"
MARKER_END = "# <<< lov-zsh-alias <<<"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Append a zsh alias/function to ~/.zshrc idempotently.",
    )
    p.add_argument("--name", required=True, help="Trigger word (English or 中文)")
    p.add_argument("--cmd", required=True, help="Shell command to run when triggered")
    p.add_argument(
        "--also-as",
        action="append",
        default=[],
        metavar="ALIAS",
        help="Additional name(s) that resolve to the same command (repeatable)",
    )
    p.add_argument("--comment", default="", help="Human-readable comment shown above the entry")
    p.add_argument(
        "--simple",
        action="store_true",
        help="Use `alias name='cmd'` instead of a function (only for ASCII names without args)",
    )
    p.add_argument(
        "--rcfile",
        default=os.environ.get("SKILL_ZSH_ALIAS_RCFILE") or str(Path.home() / ".zshrc"),
        help="Target rc file (default: SKILL_ZSH_ALIAS_RCFILE or ~/.zshrc)",
    )
    p.add_argument("--dry-run", action="store_true", help="Print the entry, don't write")
    p.add_argument("--remove", action="store_true", help="Remove the entry for --name instead of adding")
    return p.parse_args()


def is_ascii_identifier(s: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", s))


def render_entry(name: str, cmd: str, also_as: list[str], comment: str, simple: bool) -> str:
    lines: list[str] = []
    if comment:
        lines.append(f"# {comment}")

    cmd_escaped = cmd.replace("\\", "\\\\").replace('"', '\\"')

    if simple:
        if not is_ascii_identifier(name):
            print(
                f"error: --simple requires ASCII identifier name, got {name!r}",
                file=sys.stderr,
            )
            sys.exit(2)
        lines.append(f'alias {name}="{cmd_escaped}"')
        for a in also_as:
            if not is_ascii_identifier(a):
                print(f"error: --simple requires ASCII --also-as, got {a!r}", file=sys.stderr)
                sys.exit(2)
            lines.append(f'alias {a}="{cmd_escaped}"')
    else:
        lines.append(f'{name}() {{ {cmd} }}')
        for a in also_as:
            lines.append(f'{a}() {{ {name} "$@" }}')

    return "\n".join(lines) + "\n"


def block_pattern(name: str) -> re.Pattern[str]:
    name_escaped = re.escape(name)
    return re.compile(
        rf"{re.escape(MARKER_BEGIN)} {name_escaped}\n.*?{re.escape(MARKER_END)} {name_escaped}\n",
        re.DOTALL,
    )


def main() -> int:
    args = parse_args()
    rcfile = Path(args.rcfile).expanduser()

    entry_body = render_entry(
        args.name,
        args.cmd,
        args.also_as,
        args.comment,
        args.simple,
    )
    block = (
        f"{MARKER_BEGIN} {args.name}\n"
        f"{entry_body}"
        f"{MARKER_END} {args.name}\n"
    )

    if args.remove:
        if not rcfile.exists():
            print(f"no rcfile at {rcfile} — nothing to remove")
            return 0
        content = rcfile.read_text(encoding="utf-8")
        pattern = block_pattern(args.name)
        if not pattern.search(content):
            print(f"no entry for {args.name!r} — nothing to remove")
            return 0
        if args.dry_run:
            print(f"[dry-run] would remove entry for {args.name!r} from {rcfile}")
            return 0
        rcfile.write_text(pattern.sub("", content), encoding="utf-8")
        print(f"removed entry for {args.name!r} from {rcfile}")
        return 0

    if args.dry_run:
        sys.stdout.write(block)
        return 0

    if not rcfile.exists():
        rcfile.touch()

    content = rcfile.read_text(encoding="utf-8")
    pattern = block_pattern(args.name)
    existed = bool(pattern.search(content))

    if existed:
        new_content = pattern.sub(block, content)
        action = "updated"
    else:
        sep = "" if content.endswith("\n") or content == "" else "\n"
        new_content = content + sep + "\n" + block
        action = "added"
    rcfile.write_text(new_content, encoding="utf-8")

    names = [args.name, *args.also_as]
    print(f"✓ {action} alias for {', '.join(repr(n) for n in names)} in {rcfile}")
    print(f"  run: source {rcfile}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
