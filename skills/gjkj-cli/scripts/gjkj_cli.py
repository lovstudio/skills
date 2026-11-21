#!/usr/bin/env python3
"""Run the bundled 共绩算力 (suanli.cn) CLI with the Skill's safety rules applied.

usage:
  gjkj_cli.py ops [--group TEXT] [--read-only] [--json]     list commands: method, path, group, read/write, billed, encrypted, live-verified
  gjkj_cli.py doctor                                        Node, CLI, operation count, credentials present (lengths only, never values)
  gjkj_cli.py run [--approved "user's words"] -- CMD [ARGS]  call one command through assets/cli/bin/lov-suanli-cli.mjs
  gjkj_cli.py swagger [--port 4790] [--allow-write]          start the local Swagger proxy (127.0.0.1 only)

`run` refuses, before anything is sent:
  - a write operation (x-write-operation) or a billed call (llm-chat-completions) without --approved quoting the user's own approval
    for this exact call; with it, --confirm-write is added for write operations;
  - an unknown command (not in the bundled openapi.json).
--dry-run is always allowed and sends nothing. Credentials are read by the CLI from env or the macOS Keychain; this script never
prints them.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
CLI = SKILL / "assets" / "cli"
BIN = CLI / "bin" / "lov-suanli-cli.mjs"
BILLED = {"llm-chat-completions"}  # consumes account balance even though it creates no platform resource
KEYCHAIN = {"suanli-token": "SUANLI_TOKEN", "suanli-llm-key": "SUANLI_LLM_API_KEY"}


def kebab(op_id):
    return re.sub(r"(?<!^)(?=[A-Z])", "-", op_id).replace("_", "-").lower()


def operations():
    spec = json.loads((CLI / "openapi.json").read_text())
    rows = []
    for path, item in spec["paths"].items():
        for method, op in item.items():
            if not isinstance(op, dict) or "operationId" not in op:
                continue
            cmd = kebab(op["operationId"])
            rows.append({
                "command": cmd, "method": method.upper(), "path": path, "group": (op.get("tags") or [""])[0],
                "summary": op.get("summary", ""), "write": bool(op.get("x-write-operation")), "billed": cmd in BILLED,
                "encrypted": bool((op.get("x-suanli-auth") or {}).get("encryption")),
                "live": op.get("x-observation") == "live-verified-token-mode" or bool((op.get("x-evidence") or {}).get("liveCheck")),
            })
    return rows


def cmd_ops(a):
    rows = operations()
    if a.group:
        rows = [r for r in rows if a.group in r["group"]]
    if a.read_only:
        rows = [r for r in rows if not r["write"] and not r["billed"]]
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return
    for r in rows:
        flags = "".join(["W" if r["write"] else "-", "$" if r["billed"] else "-", "E" if r["encrypted"] else "-", "V" if r["live"] else "-"])
        print(f"{flags}  {r['command']:<58} {r['method']:<6} {r['path']}  [{r['group']}] {r['summary']}")
    print(f"\n{len(rows)} commands · flags: W write  $ billed  E encrypted body  V live-verified read-only", file=sys.stderr)


def keychain_len(service):
    if sys.platform != "darwin" or os.environ.get("SUANLI_KEYCHAIN") == "0":
        return None
    r = subprocess.run(["security", "find-generic-password", "-s", service, "-w"], capture_output=True, text=True)
    return len(r.stdout.strip()) if r.returncode == 0 else 0


def cmd_doctor(_a):
    node = shutil.which("node")
    out = {"node": None, "cli": str(BIN.relative_to(SKILL)), "operations": None, "manifest_operations": None, "credentials": {}}
    if node:
        out["node"] = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip()
    out["operations"] = len(operations())
    out["manifest_operations"] = json.loads((CLI / "manifest.json").read_text()).get("operationCount")
    for service, env in KEYCHAIN.items():
        out["credentials"][env] = {"env_set": bool(os.environ.get(env)), "keychain_length": keychain_len(service)}
    out["rsa_private_key_file"] = bool(os.environ.get("SUANLI_PRIVATE_KEY_FILE"))
    out["platform_public_key_file"] = bool(os.environ.get("SUANLI_PLATFORM_PUBLIC_KEY_FILE"))
    ok = bool(node) and out["operations"] == out["manifest_operations"]
    out["ok"] = ok
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(0 if ok else 1)


def cmd_run(a):
    args = list(a.args)
    if args and args[0] == "--":
        args = args[1:]
    if not args:
        sys.exit("run needs a command, e.g. gjkj_cli.py run -- storage-get-regions")
    cmd = args[0]
    known = {r["command"]: r for r in operations()}
    if cmd not in ("help", "--help") and cmd not in known:
        sys.exit(f"unknown command {cmd!r}; list them with: gjkj_cli.py ops")
    row = known.get(cmd)
    dry = "--dry-run" in args
    if row and (row["write"] or row["billed"]) and not dry:
        if not (a.approved or "").strip():
            kind = "write operation" if row["write"] else "billed call"
            sys.exit(f"{cmd} is a {kind}. Ask the user first, then pass --approved with their words for this exact call "
                     f"(or use --dry-run to show the request).")
        if row["write"] and "--confirm-write" not in args:
            args.append("--confirm-write")
    node = shutil.which("node") or sys.exit("Node.js 20+ is required")
    sys.exit(subprocess.call([node, str(BIN), *args]))


def cmd_swagger(a):
    node = shutil.which("node") or sys.exit("Node.js 20+ is required")
    extra = ["--allow-write"] if a.allow_write else []
    sys.exit(subprocess.call([node, str(CLI / "swagger" / "server.mjs"), "--port", str(a.port), *extra]))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("ops"); s.add_argument("--group"); s.add_argument("--read-only", action="store_true"); s.add_argument("--json", action="store_true")
    sub.add_parser("doctor")
    s = sub.add_parser("run"); s.add_argument("--approved", default=None); s.add_argument("args", nargs=argparse.REMAINDER)
    s = sub.add_parser("swagger"); s.add_argument("--port", type=int, default=4790); s.add_argument("--allow-write", action="store_true")
    a = ap.parse_args()
    {"ops": cmd_ops, "doctor": cmd_doctor, "run": cmd_run, "swagger": cmd_swagger}[a.cmd](a)


if __name__ == "__main__":
    main()
