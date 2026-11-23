#!/usr/bin/env python3
"""Inventory a project before handing it over: what is big, what can be regenerated, what must not travel.

  python3 handover_scan.py <project_dir> [--json report.json] [--top 15]

Reports, without changing anything:
  - total size, the largest directories (two levels) and the largest files;
  - directories that look regenerable (dependency trees, render and build caches, virtualenvs);
  - secrets: API-key shapes, bearer tokens, private-key blocks, .env and key files;
  - personal data: e-mail addresses, mainland China mobile numbers, ID-card numbers, WeChat ids and chatroom ids;
  - absolute home-directory paths in text files (the recipient's machine will not have them);
  - environment variables the code reads (the credentials the recipient must bring);
  - package managers and lockfiles, with version hints (pnpm 10 settings in pnpm-workspace.yaml);
  - whether the directory is a git repository and whether it is dirty.
Findings are candidates for a person to judge, not verdicts: an e-mail in a contract is private, the same e-mail in
a public docs URL is not. Text scans skip regenerable trees and files over --max-text-mb."""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REGEN_NAMES = {
    "node_modules", ".pnpm-store", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".mypy_cache", ".next",
    ".nuxt", ".turbo", ".parcel-cache", ".cache", "cache", "dist", "renders", "render", "tmp", "temp", ".tmp",
    "DerivedData", "Pods", "target", ".gradle", ".remotion",
}
REGEN_PREFIXES = ("build", "preview", "stills", "chunks")
TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env", ".py", ".js",
    ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".sh", ".zsh", ".bash", ".swift", ".html", ".css", ".csv", ".tsv",
    ".xml", ".srt", ".vtt", ".sql", ".rb", ".go", ".rs", ".java", ".kt", ".php", ".log", ".src", "",
}
SECRET_PATTERNS = [
    ("openai/openrouter-style key", re.compile(r"\bsk-(?:or-|proj-|ant-)?[A-Za-z0-9_-]{20,}")),
    ("aws access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("bearer token", re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{24,}")),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("assigned secret", re.compile(r"(?i)\b(?:api[_-]?key|secret|token|password|passwd|access[_-]?key)\b\s*[:=]\s*[\"'][^\"'\s]{12,}[\"']")),
]
PII_PATTERNS = [
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")),
    ("cn mobile", re.compile(r"(?<![0-9A-Za-z])1[3-9][0-9]{9}(?![0-9A-Za-z])")),
    ("cn id card", re.compile(r"(?<![0-9A-Za-z])[1-9][0-9]{5}(?:19|20)[0-9]{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01])[0-9]{3}[0-9Xx](?![0-9A-Za-z])")),
    ("wechat id", re.compile(r"\bwxid_[A-Za-z0-9_-]{6,}")),
    ("wechat chatroom", re.compile(r"\b[0-9]{6,}@chatroom\b")),
]
KEY_FILE_NAMES = re.compile(r"(?i)^(?:\.env(?:\..+)?|.*\.pem|.*\.p12|.*\.pfx|id_rsa.*|id_ed25519.*|.*credentials?.*\.json|.*secret.*)$")
ENV_PATTERNS = [
    re.compile(r"os\.environ(?:\.get)?\(\s*[\"']([A-Z][A-Z0-9_]{2,})[\"']"),
    re.compile(r"os\.environ\[\s*[\"']([A-Z][A-Z0-9_]{2,})[\"']\s*\]"),
    re.compile(r"os\.getenv\(\s*[\"']([A-Z][A-Z0-9_]{2,})[\"']"),
    re.compile(r"process\.env\.([A-Z][A-Z0-9_]{2,})"),
    re.compile(r"process\.env\[\s*[\"']([A-Z][A-Z0-9_]{2,})[\"']\s*\]"),
    re.compile(r"\$\{?([A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|_AK|_SK|APPID|APP_ID))\b"),
]
CREDENTIAL_HINT = re.compile(r"KEY|TOKEN|SECRET|PASSWORD|_AK$|_SK$|APPID|APP_ID|CREDENTIAL")


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} TB"


def is_regen(name):
    return name in REGEN_NAMES or name.startswith(REGEN_PREFIXES)


def walk(root):
    """Yield (path, size) for every file; does not follow symlinks."""
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for f in filenames:
            p = Path(dirpath) / f
            try:
                st = p.lstat()
            except OSError:
                continue
            if p.is_symlink():
                continue
            yield p, st.st_size


def main():
    ap = argparse.ArgumentParser(description="Inventory a project before a handover (read-only).")
    ap.add_argument("project_dir")
    ap.add_argument("--json", help="also write the full report as JSON here")
    ap.add_argument("--top", type=int, default=15, help="how many largest directories and files to list")
    ap.add_argument("--max-text-mb", type=float, default=5.0, help="skip text scans of files larger than this")
    ap.add_argument("--home", default=os.path.expanduser("~"), help="home directory whose absolute paths are flagged")
    ap.add_argument("--exclude", action="append", default=["output/handover"],
                    help="path prefix (relative to the project) left out of the scan, e.g. earlier handover packages; repeatable")
    args = ap.parse_args()

    root = Path(args.project_dir).expanduser().resolve()
    if not root.is_dir():
        sys.exit(f"not a directory: {root}")
    home = args.home.rstrip("/")

    total = 0
    dir_sizes = {}
    files = []
    regen = {}
    secrets, pii, abs_paths, key_files = [], [], {}, []
    env_vars = {}
    max_text = args.max_text_mb * 1024 * 1024

    skip = [e.strip("/") for e in args.exclude if e.strip("/")]
    for p, size in walk(root):
        rel = p.relative_to(root)
        if any(rel.as_posix() == s or rel.as_posix().startswith(s + "/") for s in skip):
            continue
        parts = rel.parts
        total += size
        for depth in (1, 2):
            if len(parts) > depth:
                k = "/".join(parts[:depth])
                dir_sizes[k] = dir_sizes.get(k, 0) + size
        files.append((size, rel.as_posix()))
        regen_part = next((i for i, part in enumerate(parts[:-1]) if is_regen(part)), None)
        if regen_part is not None:
            k = "/".join(parts[: regen_part + 1])
            regen[k] = regen.get(k, 0) + size
            continue  # regenerable trees are not text-scanned
        if KEY_FILE_NAMES.match(p.name) and p.name not in (".env.example", ".env.sample"):
            key_files.append(rel.as_posix())
        if p.suffix.lower() not in TEXT_SUFFIXES or size > max_text:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, pat in SECRET_PATTERNS:
            for m in pat.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                shown = m.group(0)
                secrets.append({"file": rel.as_posix(), "line": line, "kind": label, "match": shown[:8] + "…" if len(shown) > 8 else shown})
        for label, pat in PII_PATTERNS:
            for m in pat.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                pii.append({"file": rel.as_posix(), "line": line, "kind": label, "match": m.group(0)})
        n_abs = text.count(home + "/")
        if n_abs:
            abs_paths[rel.as_posix()] = n_abs
        if p.suffix.lower() in {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".sh", ".zsh", ".bash", ""}:
            for pat in ENV_PATTERNS:
                for m in pat.finditer(text):
                    env_vars.setdefault(m.group(1), set()).add(rel.as_posix())

    lockfiles = []
    for name in ("package.json", "pnpm-lock.yaml", "pnpm-workspace.yaml", "package-lock.json", "yarn.lock", "bun.lockb",
                 "requirements.txt", "pyproject.toml", "uv.lock", "poetry.lock", "Pipfile.lock", "Gemfile.lock", "go.mod",
                 "Cargo.lock"):
        for p in root.rglob(name):
            rel = p.relative_to(root)
            if any(is_regen(part) for part in rel.parts[:-1]) or any(rel.as_posix().startswith(s + "/") for s in skip):
                continue
            hint = ""
            if name == "pnpm-workspace.yaml":
                t = p.read_text(encoding="utf-8", errors="replace")
                if "packages:" not in t and re.search(r"^(allowBuilds|onlyBuiltDependencies|catalog)", t, re.M):
                    hint = "settings-only workspace file: needs pnpm 10 (pnpm 9 fails with 'packages field missing or empty')"
            if name == "pnpm-lock.yaml":
                m = re.search(r"lockfileVersion:\s*'?([0-9.]+)", p.read_text(encoding="utf-8", errors="replace")[:200])
                hint = f"lockfileVersion {m.group(1)}" if m else ""
            if name == "package.json":
                try:
                    pj = json.loads(p.read_text(encoding="utf-8"))
                    pm = pj.get("packageManager") or ""
                    eng = (pj.get("engines") or {}).get("node", "")
                    hint = "; ".join(x for x in (f"packageManager {pm}" if pm else "", f"node {eng}" if eng else "") if x)
                except (ValueError, OSError):
                    pass
            lockfiles.append({"file": rel.as_posix(), "hint": hint})

    git = {"is_repo": False}
    try:
        top = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if top.returncode == 0:
            git["is_repo"] = True
            git["toplevel_is_project"] = Path(top.stdout.strip()).resolve() == root
            st = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], capture_output=True, text=True)
            git["dirty_entries"] = len([l for l in st.stdout.splitlines() if l.strip()])
    except FileNotFoundError:
        git["error"] = "git not installed"

    report = {
        "project": root.name,
        "total_bytes": total,
        "largest_dirs": sorted(({"dir": k, "bytes": v} for k, v in dir_sizes.items()), key=lambda x: -x["bytes"])[: args.top * 2],
        "largest_files": [{"file": f, "bytes": s} for s, f in sorted(files, reverse=True)[: args.top]],
        "regenerable_candidates": sorted(({"dir": k, "bytes": v} for k, v in regen.items()), key=lambda x: -x["bytes"]),
        "secrets": secrets,
        "key_files": key_files,
        "personal_data": pii,
        "absolute_home_paths": [{"file": f, "count": c} for f, c in sorted(abs_paths.items(), key=lambda x: -x[1])],
        "env_vars": [{"name": k, "credential_like": bool(CREDENTIAL_HINT.search(k)), "files": sorted(v)[:5]} for k, v in sorted(env_vars.items())],
        "lockfiles": lockfiles,
        "git": git,
    }
    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    out = [f"# 交接盘点：{root.name}", "", f"- 总大小：{human(total)}，{len(files)} 个文件"]
    out.append(f"- Git：{'是仓库' if git.get('is_repo') else '不是 git 仓库'}" + (f"，未提交改动 {git.get('dirty_entries')} 项" if git.get("is_repo") else ""))
    out += ["", "## 最大的目录", ""] + [f"- {human(d['bytes'])}  {d['dir']}" for d in report["largest_dirs"][: args.top]]
    out += ["", "## 可重新生成的候选目录（按名称判断，需人工确认）", ""] + ([f"- {human(d['bytes'])}  {d['dir']}" for d in report["regenerable_candidates"][: args.top * 2]] or ["- 无"])
    out += ["", "## 最大的文件", ""] + [f"- {human(f['bytes'])}  {f['file']}" for f in report["largest_files"]]
    out += ["", f"## 疑似密钥（{len(secrets)}）与密钥类文件（{len(key_files)}）", ""]
    out += ([f"- {s['file']}:{s['line']}  {s['kind']}  {s['match']}" for s in secrets[:40]] + [f"- 文件：{k}" for k in key_files[:20]]) or ["- 无"]
    out += ["", f"## 个人信息候选（{len(pii)}，可能含误报，如链接里的哈希）", ""]
    out += [f"- {x['file']}:{x['line']}  {x['kind']}  {x['match']}" for x in pii[:60]] or ["- 无"]
    out += ["", f"## 含本机路径 {home}/ 的文本文件（{len(abs_paths)}）", ""]
    out += [f"- {x['file']}  ×{x['count']}" for x in report["absolute_home_paths"][:40]] or ["- 无"]
    out += ["", "## 代码读取的环境变量（接手方要自备的凭据看 credential_like）", ""]
    out += [f"- {e['name']}{'  ← 凭据' if e['credential_like'] else ''}  ({', '.join(e['files'][:2])})" for e in report["env_vars"]] or ["- 无"]
    out += ["", "## 依赖与锁文件", ""] + ([f"- {l['file']}" + (f"  — {l['hint']}" if l["hint"] else "") for l in lockfiles] or ["- 无"])
    print("\n".join(out))


if __name__ == "__main__":
    main()
