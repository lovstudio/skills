#!/usr/bin/env python3
"""Scan, show and tidy a local agent harness.

One snapshot covers three areas: the shared system prompt and how each host is
bound to it, the Skills installed across hosts, and the Skill source repos a
studio maintains. The same snapshot feeds a terminal report, a local dashboard
and a guarded tidy engine (dry run by default, journaled, undoable).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
import webbrowser
from collections import Counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

try:
    import yaml
except ImportError:  # PyYAML is optional; without it the catalog view is skipped.
    yaml = None

SKILL_ID = "lov-harness"
SNAPSHOT_SCHEMA = "lov-harness/snapshot/v1"
JOURNAL_SCHEMA = "lov-harness/journal/v1"
DEFAULT_PORT = 8737
MAX_TEXT_BYTES = 512 * 1024
MAX_REQUEST_BYTES = 64 * 1024
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
ASSET_ROOT = SKILL_ROOT / "assets" / "dashboard"
STATIC_TYPES = {
    "dashboard.css": "text/css; charset=utf-8",
    "dashboard.js": "text/javascript; charset=utf-8",
}

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)")
BATCH_RE = re.compile(r"^\d{8}-\d{6}-[0-9a-f]{4}$")
FRONT_END_RE = re.compile(r"\n---[ \t]*(?:\n|$)")
RULE_RE = re.compile(
    r"^\s*[-*]\s+`(?P<id>(?:[A-Z][A-Z0-9]*-)?\d+)`\s+\*\*(?P<title>[^*]+)\*\*\s*[:：]?\s*(?P<body>.*)$"
)
PATH_REF_RE = re.compile(r"`((?:~|/)[^`\n]+)`")
DIGEST_RE = re.compile(r"sha256:\s*([0-9a-f]{64})")
SEVERITIES = ("error", "warn", "info")
SEVERITY_LABELS = {"error": "错误", "warn": "警告", "info": "提示"}
AREA_LABELS = {"prompt": "System Prompt", "skills": "Skills", "studio": "工作室"}

# Host instruction files whose location is documented by the host itself.
KNOWN_PROMPT_ENTRIES = (
    ("claude", ".claude/CLAUDE.md"),
    ("codex", ".codex/AGENTS.md"),
    ("gemini", ".gemini/GEMINI.md"),
    ("qwen", ".qwen/QWEN.md"),
    ("opencode", ".config/opencode/AGENTS.md"),
    ("copilot", ".copilot/copilot-instructions.md"),
    ("qoder", ".qoder/AGENTS.md"),
    ("codebuddy", ".codebuddy/CODEBUDDY.md"),
)
PROMPT_ENTRY_NAMES = {Path(relative).name for _, relative in KNOWN_PROMPT_ENTRIES}
HOST_LABELS = {
    "shared": "共享目录",
    "claude": "Claude Code",
    "codex": "Codex",
    "gemini": "Gemini CLI",
    "qwen": "Qwen Code",
    "opencode": "OpenCode",
    "copilot": "GitHub Copilot",
    "qoder": "Qoder",
    "codebuddy": "CodeBuddy",
    "workbuddy": "WorkBuddy",
    "cursor": "Cursor",
    "openclaw": "OpenClaw",
}
GIT_ENV = dict(os.environ, GIT_OPTIONAL_LOCKS="0", LC_ALL="C")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def now_iso() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def tool_version() -> str:
    try:
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    except OSError:
        return "unknown"
    match = re.search(r"(?m)^\s+version:\s*[\"']?([0-9][^\"'\s]*)", text)
    return match.group(1) if match else "unknown"


def read_text(path: Any, limit: int = MAX_TEXT_BYTES) -> str:
    with open(path, "rb") as handle:
        return handle.read(limit).decode("utf-8", errors="replace")


def read_bytes(path: Any) -> Optional[bytes]:
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError:
        return None


def safe_scandir(path: Any) -> List[os.DirEntry]:
    try:
        with os.scandir(path) as iterator:
            return sorted(iterator, key=lambda entry: entry.name.lower())
    except OSError:
        return []


def entry_is_dir(item: os.DirEntry) -> bool:
    try:
        return item.is_dir(follow_symlinks=False)
    except OSError:
        return False


def clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def yaml_load(text: str) -> Any:
    # The C loader is an order of magnitude faster on a large catalog and equally safe.
    return yaml.load(text, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))


def scalar(value: Any) -> str:
    if value is None or isinstance(value, (dict, list)):
        return ""
    return str(value).strip()


def compact(value: Any) -> str:
    return " ".join(scalar(value).split())


def nested(data: Any, dotted: str) -> Any:
    current = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def is_inside(path: str, parent: str) -> bool:
    return path == parent or path.startswith(parent.rstrip(os.sep) + os.sep)


def semver_tuple(value: str) -> Optional[Tuple[int, int, int]]:
    match = SEMVER_RE.match(value or "")
    return (int(match.group(1)), int(match.group(2)), int(match.group(3))) if match else None


def version_relation(source: str, other: str) -> str:
    left, right = semver_tuple(source), semver_tuple(other)
    if left is None or right is None:
        return "unknown"
    if left == right:
        return "same"
    return "source-ahead" if left > right else "source-behind"


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


# ---------------------------------------------------------------------------
# Frontmatter and rule parsing
# ---------------------------------------------------------------------------


def split_frontmatter(text: str) -> Tuple[Optional[str], str]:
    text = text.lstrip("﻿").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return None, "缺少 YAML frontmatter"
    match = FRONT_END_RE.search(text, 3)
    if not match:
        return None, "frontmatter 没有闭合"
    return text[4 : match.start()], ""


def loose_map(raw: str) -> Dict[str, Any]:
    """Recover top-level keys when a strict YAML parser is missing or rejects the block."""
    data: Dict[str, Any] = {}
    lines = raw.split("\n")
    index = 0
    while index < len(lines):
        top = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", lines[index])
        if not top:
            index += 1
            continue
        key, value = top.group(1), top.group(2).strip()
        if value in ("", ">", "|", ">-", "|-", ">+", "|+"):
            block = []
            index += 1
            while index < len(lines) and (not lines[index].strip() or lines[index][:1] in (" ", "\t")):
                block.append(lines[index].strip())
                index += 1
            joined = " ".join(part for part in block if part)
            if key == "metadata":
                inner = re.search(r"(?:^|\s)version:\s*[\"']?([^\"'\s]+)", joined)
                data.setdefault(key, {"version": inner.group(1)} if inner else {})
            else:
                data.setdefault(key, joined)
            continue
        data.setdefault(key, value.strip("\"'"))
        index += 1
    return data


def frontmatter_map(raw: str) -> Tuple[Dict[str, Any], str]:
    if yaml is None:
        return loose_map(raw), ""
    try:
        data = yaml_load(raw) if raw.strip() else {}
    except yaml.YAMLError as exc:
        return loose_map(raw), "frontmatter 不是合法 YAML：" + clip(" ".join(str(exc).split()), 160)
    if isinstance(data, dict):
        return data, ""
    return loose_map(raw), "frontmatter 不是键值映射"


def parse_skill_frontmatter(text: str) -> Dict[str, Any]:
    raw, error = split_frontmatter(text)
    if raw is None:
        return {"present": False, "error": error, "name": "", "description": "", "version": ""}
    data, error = frontmatter_map(raw)
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    return {
        "present": True,
        "error": error,
        "name": scalar(data.get("name")),
        "description": compact(data.get("description")),
        "version": scalar(metadata.get("version", data.get("version"))),
    }


def parse_rules(text: str, home: str = "") -> List[Dict[str, Any]]:
    """Collect numbered rules written as ``- `ID` **Title**: body``."""
    if home:
        text = text.replace(home, "~")
    rules: List[Dict[str, Any]] = []
    section = ""
    fenced = False
    for number, line in enumerate(text.split("\n"), 1):
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        heading = re.match(r"^#{2,6}\s+(.+?)\s*$", line)
        if heading:
            section = heading.group(1)
            continue
        match = RULE_RE.match(line)
        if match:
            rules.append(
                {
                    "id": match.group("id"),
                    "title": match.group("title").strip(),
                    "body": clip(match.group("body").strip(), 320),
                    "section": section,
                    "line": number,
                }
            )
    return rules


# ---------------------------------------------------------------------------
# Environment resolution: flags > environment > shared Profile > inference
# ---------------------------------------------------------------------------


class Env:
    """Resolved locations for one scan. Paths shown to people use ``~``."""

    def __init__(self, home: Path, agents_home: Path) -> None:
        self.home = home
        self.agents_home = agents_home
        self.source_root: Optional[Path] = None
        self.catalog: Optional[Path] = None
        self.state_dir = agents_home / "backups" / "harness"
        self.provenance: Dict[str, str] = {}
        self.profile: Dict[str, Any] = {}
        self.notes: List[str] = []

    @property
    def hub(self) -> Path:
        return self.agents_home / "skills"

    @property
    def disabled(self) -> Path:
        return self.agents_home / "skills-disabled"

    @property
    def root_prompt(self) -> Path:
        return self.agents_home / "AGENTS.md"

    def show(self, path: Any) -> str:
        text, home = str(path), str(self.home)
        if text == home:
            return "~"
        return "~" + text[len(home) :] if text.startswith(home + os.sep) else text

    def real(self, shown: str) -> str:
        if shown == "~":
            return str(self.home)
        return str(self.home) + shown[1:] if shown.startswith("~/") else shown


def expand_path(value: str) -> Path:
    return Path(os.path.realpath(os.path.expanduser(os.path.expandvars(value))))


def load_profile(home: Path, explicit: Optional[str]) -> Dict[str, Any]:
    configured = explicit or os.environ.get("SKILL_PROFILE_PATH") or os.environ.get("SKILLS_PROFILE_PATH")
    if configured:
        candidates = [expand_path(configured)]
    else:
        config_dir = os.environ.get("SKILLS_CONFIG_DIR")
        candidates = [
            home / ".lovstudio" / "skills" / "profile.json",
            home / ".skill-publisher" / "skills" / "profile.json",
            (expand_path(config_dir) if config_dir else home / ".config" / "agent-skills") / "profile.json",
        ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return {}
            return data if isinstance(data, dict) else {}
    return {}


def infer_source_root(hub: Path) -> Optional[Path]:
    """The folder most shared entries link into is where the Skill sources live."""
    parents: Counter = Counter()
    for item in safe_scandir(hub):
        if item.is_symlink():
            real = os.path.realpath(item.path)
            if real.endswith("-skill") and os.path.isdir(real):
                parents[os.path.dirname(real)] += 1
    if not parents:
        return None
    parent, count = parents.most_common(1)[0]
    return Path(parent) if count >= 3 else None


_CATALOG_CACHE: Dict[Tuple[str, float, int], Tuple[List[Dict[str, Any]], str]] = {}


def load_catalog(path: Path) -> Tuple[List[Dict[str, Any]], str]:
    if yaml is None:
        return [], "未安装 PyYAML，已跳过目录对照（python3 -m pip install PyYAML）"
    try:
        stat = os.stat(path)
        key = (os.path.realpath(path), stat.st_mtime, stat.st_size)
        if key not in _CATALOG_CACHE:
            _CATALOG_CACHE.clear()
            _CATALOG_CACHE[key] = parse_catalog(read_text(path, 8 * 1024 * 1024))
        return _CATALOG_CACHE[key]
    except OSError as exc:
        return [], "目录无法读取：" + (exc.strerror or str(exc))


def parse_catalog(text: str) -> Tuple[List[Dict[str, Any]], str]:
    try:
        data = yaml_load(text)
    except yaml.YAMLError as exc:
        return [], "目录无法解析：" + clip(" ".join(str(exc).split()), 160)
    skills = data.get("skills") if isinstance(data, dict) else None
    if not isinstance(skills, list):
        return [], "目录文件缺少 skills 列表"
    entries = []
    for item in skills:
        if not isinstance(item, dict) or not scalar(item.get("name")):
            continue
        pricing = item.get("pricing") if isinstance(item.get("pricing"), dict) else {}
        updated = item.get("updated_at")
        entries.append(
            {
                "name": scalar(item.get("name")),
                "runtime_name": scalar(item.get("runtime_name")),
                "repo": scalar(item.get("repo")),
                "paid": bool(item.get("paid")),
                "category": scalar(item.get("category")),
                "version": scalar(item.get("version")),
                "updated_at": updated.isoformat() if hasattr(updated, "isoformat") else scalar(updated),
                "name_zh": scalar(item.get("name_zh")),
                "display_name": scalar(item.get("display_name")),
                "skill_path": scalar(item.get("skill_path")),
                "visibility": scalar(pricing.get("visibility")) or "public",
            }
        )
    return entries, ""


def infer_catalog(source_root: Optional[Path]) -> Optional[Path]:
    """Pick the skills.yaml whose repos best match the local source folders."""
    cwd = Path.cwd()
    candidates = [base / "skills.yaml" for base in [cwd, *list(cwd.parents)[:2]]]
    if source_root is not None:
        candidates += sorted(source_root.parent.glob("*/skills.yaml"))
    best: Optional[Path] = None
    best_score = 0
    seen = set()
    for candidate in candidates:
        key = os.path.realpath(candidate)
        if key in seen or not os.path.isfile(candidate):
            continue
        seen.add(key)
        try:
            repos = re.findall(r"(?m)^\s*-?\s*repo:\s*[\"']?[\w.-]+/([\w.-]+)", read_text(candidate, 8 * 1024 * 1024))
        except OSError:
            continue
        score = len(repos) if source_root is None else sum(1 for repo in repos if os.path.isdir(source_root / repo))
        if score > best_score:
            best, best_score = Path(key), score
    return best


def resolve_env(args: argparse.Namespace) -> Env:
    home = Path(os.path.realpath(os.path.expanduser(getattr(args, "home", None) or "~")))
    profile = load_profile(home, getattr(args, "profile", None))

    def pick(label: str, flag: Optional[str], variables: Tuple[str, ...], keys: Tuple[str, ...]) -> Optional[Path]:
        if flag:
            provenance[label] = "flag"
            return expand_path(flag)
        for name in variables:
            if os.environ.get(name):
                provenance[label] = "env:" + name
                return expand_path(os.environ[name])
        for key in keys:
            value = nested(profile, key)
            if isinstance(value, str) and value.strip():
                provenance[label] = "profile:" + key
                return expand_path(value)
        return None

    provenance: Dict[str, str] = {}
    records = "skills." + SKILL_ID + ".records."
    agents_home = pick(
        "agents_home", getattr(args, "agents_home", None), ("LOV_HARNESS_AGENTS_HOME",), (records + "agents_home",)
    )
    if agents_home is None:
        agents_home = home / ".agents"
        provenance["agents_home"] = "default"
    env = Env(home, agents_home)
    env.profile = profile
    env.provenance = provenance

    env.source_root = pick(
        "source_root",
        getattr(args, "source_root", None),
        ("LOV_HARNESS_SOURCE_ROOT", "LOVSTUDIO_SKILL_CREATOR_REPOS_ROOT"),
        (
            records + "source_root",
            "workspace.skill_repos_root",
            "lovstudio.skill_repos_root",
            "skills.repos_root",
            "workspace.skills_root",
        ),
    )
    if env.source_root is None:
        env.source_root = infer_source_root(env.hub)
        if env.source_root is not None:
            provenance["source_root"] = "inferred:shared-links"
    if env.source_root is not None and not os.path.isdir(env.source_root):
        env.notes.append("源码根目录不存在：" + env.show(env.source_root))
        env.source_root = None

    env.catalog = pick("catalog", getattr(args, "catalog", None), ("LOV_HARNESS_CATALOG",), (records + "catalog_path",))
    if env.catalog is None:
        env.catalog = infer_catalog(env.source_root)
        if env.catalog is not None:
            provenance["catalog"] = "inferred:repo-match"
    if env.catalog is not None and not os.path.isfile(env.catalog):
        env.notes.append("目录文件不存在：" + env.show(env.catalog))
        env.catalog = None

    state_dir = pick("state_dir", getattr(args, "state_dir", None), ("LOV_HARNESS_STATE_DIR",), ())
    if state_dir is not None:
        env.state_dir = state_dir
    else:
        provenance["state_dir"] = "default"
    return env


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


class Findings:
    def __init__(self) -> None:
        self.items: List[Dict[str, Any]] = []
        self._seen: set = set()

    def add(
        self,
        area: str,
        code: str,
        severity: str,
        title: str,
        path: str,
        detail: str = "",
        subject: str = "",
        fix: Optional[Dict[str, Any]] = None,
    ) -> str:
        identifier = hashlib.sha1("|".join((code, path, subject)).encode("utf-8")).hexdigest()[:10]
        if identifier not in self._seen:
            self._seen.add(identifier)
            self.items.append(
                {
                    "id": identifier,
                    "area": area,
                    "code": code,
                    "severity": severity,
                    "title": title,
                    "path": path,
                    "subject": subject,
                    "detail": detail,
                    "fix": fix,
                }
            )
        return identifier


# ---------------------------------------------------------------------------
# Area 1: system prompt
# ---------------------------------------------------------------------------


def local_refs(text: str, env: Env) -> List[Tuple[int, str]]:
    """Backticked paths under the home directory, with the line they appear on."""
    refs = []
    home = str(env.home)
    for number, line in enumerate(text.split("\n"), 1):
        for raw in PATH_REF_RE.findall(line):
            candidate = raw.strip().rstrip(".,;:")
            if any(mark in candidate for mark in "{}<>*$|"):
                continue
            expanded = env.real(candidate)
            if is_inside(expanded, home) and expanded != home:
                refs.append((number, expanded))
    return refs


def ref_exists(path: str) -> bool:
    """A reference may be a command line; then only its first word is the path."""
    return os.path.exists(path) or (" " in path and os.path.exists(path.split(" ", 1)[0]))


def text_file_record(env: Env, path: Path, kind: str, data: bytes) -> Dict[str, Any]:
    return {
        "kind": kind,
        "path": env.show(path),
        "name": path.name,
        "bytes": len(data),
        "lines": data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0),
        "sha": hashlib.sha256(data).hexdigest()[:12],
        "link_target": env.show(os.readlink(path)) if os.path.islink(path) else "",
    }


def classify_prompt_entry(env: Env, path: Path, root_real: str, root_sha: str) -> Dict[str, Any]:
    record: Dict[str, Any] = {"path": env.show(path), "state": "missing", "link_target": "", "detail": ""}
    if os.path.islink(path):
        record["link_target"] = env.show(os.readlink(path))
        if not os.path.exists(path):
            record["state"] = "broken"
        elif root_real and os.path.realpath(path) == root_real:
            record["state"] = "linked"
        else:
            record["state"] = "independent"
            record["detail"] = "链接到其他文件"
        return record
    if not os.path.isfile(path):
        return record
    data = read_bytes(path)
    if data is None:
        record["state"] = "independent"
        record["detail"] = "无法读取"
        return record
    record["bytes"] = len(data)
    if root_sha and hashlib.sha256(data).hexdigest() == root_sha:
        record["state"] = "copy"
        return record
    text = data[:MAX_TEXT_BYTES].decode("utf-8", errors="replace")
    digests = DIGEST_RE.findall(text)
    mentions_root = bool(root_real) and (root_real in text or env.show(root_real) in text)
    if root_sha and root_sha in digests:
        record["state"] = "embedded"
    elif digests and mentions_root:
        record["state"] = "embedded-stale"
    else:
        record["state"] = "independent"
    return record


def discover_prompt_entries(env: Env, root_real: str) -> List[Tuple[str, Path, bool, bool]]:
    """Known host entry files, plus any shallow file that links to or mirrors the root."""
    found: Dict[str, Tuple[str, Path, bool, bool]] = {}
    for host, relative in KNOWN_PROMPT_ENTRIES:
        path = env.home / relative
        if os.path.isdir(path.parent):
            found[str(path)] = (host, path, True, True)

    def consider(item: os.DirEntry, host: str, direct: bool) -> None:
        if item.path in found:
            return
        try:
            if item.is_symlink():
                if root_real and os.path.realpath(item.path) == root_real:
                    found[item.path] = (host, Path(item.path), False, direct)
            elif item.name in PROMPT_ENTRY_NAMES and item.is_file():
                found[item.path] = (host, Path(item.path), False, direct)
        except OSError:
            return

    agents_real = os.path.realpath(env.agents_home)
    for top in safe_scandir(env.home):
        if not top.name.startswith(".") or not entry_is_dir(top):
            continue
        if os.path.realpath(top.path) == agents_real:
            continue
        nested_hosts = top.name == ".config"
        for child in safe_scandir(top.path):
            if not nested_hosts:
                consider(child, top.name[1:], True)
            if entry_is_dir(child):
                for grand in safe_scandir(child.path):
                    consider(grand, child.name if nested_hosts else top.name[1:], nested_hosts)
    return sorted(found.values(), key=lambda item: (not item[2], str(item[1])))


def scan_prompt(env: Env, findings: Findings) -> Dict[str, Any]:
    section: Dict[str, Any] = {"root": None, "files": [], "hosts": [], "changelog": None, "refs": []}
    root = env.root_prompt
    root_text, root_sha, root_real, root_version = "", "", "", ""
    home = str(env.home)
    data = read_bytes(root)

    if data is not None:
        root_sha = hashlib.sha256(data).hexdigest()
        root_real = os.path.realpath(root)
        root_text = data[:MAX_TEXT_BYTES].decode("utf-8", errors="replace")
        raw, _ = split_frontmatter(root_text)
        front = frontmatter_map(raw)[0] if raw is not None else {}
        root_version = scalar(front.get("version"))
        rules = parse_rules(root_text, home)
        record = text_file_record(env, root, "root", data)
        record.update(rules=rules, version=root_version, updated_at=scalar(front.get("updated_at")))
        section["files"].append(record)
        section["root"] = {
            "path": record["path"],
            "version": root_version,
            "updated_at": record["updated_at"],
            "rules": len(rules),
            "sha": record["sha"],
            "bytes": record["bytes"],
        }
        numbers = [int(rule["id"]) for rule in rules if rule["id"].isdigit()]
        for value, count in sorted(Counter(numbers).items()):
            if count > 1:
                findings.add(
                    "prompt", "PRM-RULE-DUP", "error", "根 Prompt 编号重复", record["path"],
                    "编号 %02d 出现 %d 次，后来的引用无法确定指向哪一条。" % (value, count), "%02d" % value,
                )
        if len(numbers) >= 3:
            missing = sorted(set(range(min(numbers), max(numbers) + 1)) - set(numbers))
            if missing and len(missing) <= 20:
                findings.add(
                    "prompt", "PRM-RULE-GAP", "warn", "根 Prompt 编号不连续", record["path"],
                    "缺少编号：" + "、".join("%02d" % value for value in missing), "gap",
                )
        by_line = {rule["line"]: rule for rule in rules}
        for line, target in local_refs(root_text, env):
            exists = ref_exists(target)
            rule = by_line.get(line, {})
            section["refs"].append(
                {"rule": rule.get("id", ""), "title": rule.get("title", ""), "target": env.show(target),
                 "exists": exists, "line": line}
            )
            if not exists:
                findings.add(
                    "prompt", "PRM-PATH-MISSING", "error", "根 Prompt 引用的路径不存在", record["path"],
                    "%s（第 %d 行%s）" % (env.show(target), line, "，规则 " + rule["id"] if rule else ""),
                    env.show(target),
                )
    else:
        findings.add(
            "prompt", "PRM-ROOT-MISSING", "info", "未找到共享根 Prompt", env.show(root),
            "各宿主的指令文件按独立文件列出；建立共享根 Prompt 后可在这里看到绑定关系。",
        )

    namespaces: Dict[str, List[str]] = {}
    for item in safe_scandir(env.agents_home / "references"):
        if not item.name.endswith(".md"):
            continue
        path = Path(item.path)
        shown = env.show(path)
        if not os.path.exists(path):
            target = env.show(os.readlink(path)) if item.is_symlink() else ""
            section["files"].append({"kind": "reference", "path": shown, "name": item.name, "state": "broken",
                                     "link_target": target, "rules": []})
            findings.add("prompt", "PRM-REF-BROKEN", "error", "reference 是断开的链接", shown,
                         "指向 " + (target or "未知目标"))
            continue
        data = read_bytes(path)
        if data is None:
            continue
        text = data[:MAX_TEXT_BYTES].decode("utf-8", errors="replace")
        rules = parse_rules(text, home)
        identifiers = [rule["id"] for rule in rules]
        spaces = sorted({identifier.split("-")[0] for identifier in identifiers if "-" in identifier})
        for space in spaces:
            namespaces.setdefault(space, []).append(shown)
        routed = bool(root_text) and item.name in root_text
        record = text_file_record(env, path, "reference", data)
        record.update(rules=rules, namespaces=spaces, routed=routed)
        section["files"].append(record)
        for identifier, count in sorted(Counter(identifiers).items()):
            if count > 1:
                findings.add("prompt", "PRM-RULE-DUP", "error", "reference 规则编号重复", shown,
                             "%s 出现 %d 次。" % (identifier, count), identifier)
        if root_text and not routed:
            findings.add("prompt", "PRM-REF-UNROUTED", "info", "reference 没有被根 Prompt 路由", shown,
                         "根 Prompt 里找不到这个文件名，Agent 不会按需加载它。")
        by_line = {rule["line"]: rule for rule in rules}
        for line, target in local_refs(text, env):
            if not ref_exists(target):
                rule = by_line.get(line, {})
                findings.add(
                    "prompt", "PRM-PATH-MISSING", "warn", "reference 引用的路径不存在", shown,
                    "%s（第 %d 行%s）" % (env.show(target), line, "，规则 " + rule["id"] if rule else ""),
                    env.show(target),
                )
    for space, owners in sorted(namespaces.items()):
        if len(owners) > 1:
            findings.add("prompt", "PRM-NS-COLLISION", "warn", "多个 reference 共用同一编号命名空间",
                         owners[0], "%s 同时出现在：%s" % (space, "、".join(owners)), space)

    changelog = env.agents_home / "CHANGELOG.md"
    data = read_bytes(changelog)
    if data is not None:
        record = text_file_record(env, changelog, "changelog", data)
        match = re.search(
            r"(?m)^##\s+\[?v?(\d+\.\d+\.\d+)\]?(?:\s*[—–-]+\s*(\d{4}-\d{2}-\d{2}))?",
            data[:MAX_TEXT_BYTES].decode("utf-8", errors="replace"),
        )
        latest = match.group(1) if match else ""
        record["version"] = latest
        section["files"].append(record)
        section["changelog"] = {
            "path": record["path"], "latest": latest, "date": (match.group(2) or "") if match else "",
            "matches_root": bool(latest) and latest == root_version,
        }
        if latest and root_version and latest != root_version:
            findings.add("prompt", "PRM-VERSION-DRIFT", "warn", "根 Prompt 版本与 CHANGELOG 不一致",
                         record["path"], "根 Prompt 是 %s，CHANGELOG 最新条目是 %s。" % (root_version, latest))

    for host, path, known, direct in discover_prompt_entries(env, root_real):
        record = classify_prompt_entry(env, path, root_real, root_sha)
        if not direct and record["state"] == "independent":
            continue  # an AGENTS.md inside some app or project folder, not a host entry
        record.update(host=host, label=HOST_LABELS.get(host, host), known=known)
        section["hosts"].append(record)
        shown, state = record["path"], record["state"]
        if state in ("copy", "embedded", "embedded-stale", "independent"):
            data = read_bytes(path)
            if data is not None:
                section["files"].append(text_file_record(env, path, "host", data))
        if state == "broken":
            findings.add("prompt", "PRM-HOST-BROKEN", "error", "宿主指令文件是断开的链接", shown,
                         "指向 " + record["link_target"],
                         fix={"action": "remove-broken-link", "path": shown, "label": "移除断链"})
        elif state == "embedded-stale":
            findings.add("prompt", "PRM-HOST-STALE", "warn", "宿主里嵌入的规则副本落后于根 Prompt", shown,
                         "文件记录的 sha256 与当前根 Prompt 不同，需要重新生成这一段。")
        elif state == "copy":
            findings.add("prompt", "PRM-HOST-COPY", "info", "宿主使用的是根 Prompt 的实体副本", shown,
                         "内容目前相同，但根 Prompt 更新后它不会跟随。")
        elif state == "missing" and known and root_real:
            findings.add(
                "prompt", "PRM-HOST-UNBOUND", "info", "宿主还没有绑定根 Prompt", shown,
                "%s 的指令文件不存在。" % record["label"],
                fix={"action": "link-prompt", "path": shown, "label": "链接到根 Prompt",
                     "target": os.path.relpath(root_real, os.path.realpath(path.parent))},
            )
        elif state == "independent" and known and root_real:
            findings.add("prompt", "PRM-HOST-INDEPENDENT", "info", "宿主指令文件独立维护，未接入根 Prompt",
                         shown, record["detail"] or "它与根 Prompt 的内容各自演进。")
    return section


# ---------------------------------------------------------------------------
# Area 2: installed skills
# ---------------------------------------------------------------------------


def discover_skill_dirs(env: Env) -> List[Tuple[str, Path]]:
    """The shared directory first, then every ``~/.<host>/skills`` that holds entries."""
    result: List[Tuple[str, Path]] = []
    taken = set()
    hub_real = os.path.realpath(env.hub)
    if os.path.isdir(env.hub):
        result.append(("shared", env.hub))
        taken.add("shared")
    candidates: List[Tuple[str, Path]] = []
    for top in safe_scandir(env.home):
        if not top.name.startswith("."):
            continue
        if top.name == ".config":
            candidates += [(child.name, Path(child.path) / "skills") for child in safe_scandir(top.path)]
        else:
            candidates.append((top.name[1:], Path(top.path) / "skills"))
    for host, path in candidates:
        if not os.path.isdir(path) or os.path.realpath(path) == hub_real:
            continue
        # A folder that only holds plain files (a Profile store, a lock file) is not a host.
        if not any(item.is_symlink() or entry_is_dir(item)
                   for item in safe_scandir(path) if not item.name.startswith(".")):
            continue
        identifier = host if host not in taken else "config-" + host
        taken.add(identifier)
        result.append((identifier, path))
    return result


def load_skill(real: str) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "has_skill_md": False, "collection": 0, "present": False, "error": "",
        "name": "", "description": "", "desc_len": 0, "version": "",
    }
    skill_md = os.path.join(real, "SKILL.md")
    if not os.path.isfile(skill_md):
        record["collection"] = sum(
            1 for child in safe_scandir(real) if os.path.isfile(os.path.join(child.path, "SKILL.md"))
        )
        return record
    record["has_skill_md"] = True
    try:
        record.update(parse_skill_frontmatter(read_text(skill_md, 256 * 1024)))
    except OSError as exc:
        record["error"] = "无法读取 SKILL.md：" + (exc.strerror or str(exc))
    record["desc_len"] = len(record["description"])
    return record


def scan_skills(env: Env, findings: Findings) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    dirs = discover_skill_dirs(env)
    hub_real = os.path.realpath(env.hub)
    host_reals = {host: os.path.realpath(path) for host, path in dirs}
    skills: Dict[str, Dict[str, Any]] = {}
    entries_by_real: Dict[str, List[Dict[str, Any]]] = {}
    raw_targets: Dict[str, str] = {}  # entry path -> link target exactly as stored on disk
    chains: Dict[str, List[Dict[str, str]]] = {}
    hosts: List[Dict[str, Any]] = []
    loose: List[Dict[str, Any]] = []

    lock: Dict[str, Any] = {}
    lock_path = env.agents_home / ".skill-lock.json"
    if os.path.isfile(lock_path):
        try:
            parsed = json.loads(read_text(lock_path, 8 * 1024 * 1024))
            lock = parsed.get("skills", {}) if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            lock = {}
        if not isinstance(lock, dict):
            lock = {}

    for host, directory in dirs:
        host_record = {
            "id": host, "label": HOST_LABELS.get(host, host), "path": env.show(directory),
            "entries": 0, "skills": 0, "desc_chars": 0,
        }
        hosts.append(host_record)
        for item in safe_scandir(directory):
            if item.name.startswith("."):
                continue
            path = Path(item.path)
            shown = env.show(path)
            entry: Dict[str, Any] = {"host": host, "entry": item.name, "path": shown, "link_target": ""}
            real = ""
            if item.is_symlink():
                entry["kind"] = "link"
                raw_targets[shown] = os.readlink(path)
                entry["link_target"] = env.show(raw_targets[shown])
                real = os.path.realpath(path)
                if not os.path.exists(real):
                    host_record["entries"] += 1
                    entry["state"] = "broken"
                    loose.append(entry)
                    findings.add("skills", "SKL-BROKEN-LINK", "error", "断开的 Skill 链接", shown,
                                 "指向 " + entry["link_target"],
                                 fix={"action": "remove-broken-link", "path": shown, "label": "移除断链"})
                    continue
                if not os.path.isdir(real):
                    real = ""
            elif entry_is_dir(item):
                entry["kind"] = "dir"
                real = os.path.realpath(path)
            if not real:
                if host == "shared":
                    entry.update(kind=entry.get("kind", "file"), state="stray")
                    loose.append(entry)
                    findings.add("skills", "SKL-STRAY", "info", "共享目录里的非 Skill 文件", shown,
                                 "Skill 目录只应包含 Skill 文件夹或链接。",
                                 fix={"action": "quarantine", "path": shown, "label": "移入整理备份"})
                continue
            host_record["entries"] += 1
            if real not in skills:
                info = load_skill(real)
                info.update(key=env.show(real), entries=[], hosts=[], findings=[], origin="", source="")
                skills[real] = info
            info = skills[real]
            if not info["has_skill_md"]:
                if info["collection"]:
                    continue
                entry["state"] = "no-skill-md"
                loose.append(entry)
                fix = {"action": "quarantine", "path": shown, "label": "移入整理备份"} if host == "shared" else None
                findings.add("skills", "SKL-NO-SKILL-MD", "warn" if host == "shared" else "info",
                             "目录里没有 SKILL.md", shown, "宿主不会把它识别为 Skill。", fix=fix)
                continue
            entry["state"] = "ok"
            info["entries"].append(entry)
            entries_by_real.setdefault(real, []).append(entry)
            host_record["skills"] += 1
            host_record["desc_chars"] += info["desc_len"]

    # Content checks, once per distinct Skill.
    for real, info in skills.items():
        if not info["has_skill_md"]:
            continue
        info["hosts"] = sorted({entry["host"] for entry in info["entries"]})
        shown = info["key"]

        def note(code: str, severity: str, title: str, detail: str) -> None:
            info["findings"].append(findings.add("skills", code, severity, title, shown, detail))

        if not info["present"]:
            note("SKL-FRONTMATTER", "error", "SKILL.md 没有可用的 frontmatter", info["error"])
            continue
        if info["error"]:
            note("SKL-FRONTMATTER-YAML", "warn", "frontmatter 不是合法 YAML", info["error"])
        if not info["name"]:
            note("SKL-NO-NAME", "error", "frontmatter 缺少 name", "宿主无法为它生成稳定的调用名。")
        elif not NAME_RE.match(info["name"]) or len(info["name"]) > 64:
            note("SKL-NAME-INVALID", "warn", "name 不是 kebab-case",
                 "“%s” 含有空格、大写或符号，部分宿主会改写或拒绝它。" % clip(info["name"], 60))
        if not info["description"]:
            note("SKL-NO-DESC", "error", "frontmatter 缺少 description", "没有描述就没有触发依据。")
        elif info["desc_len"] > 1024:
            note("SKL-DESC-OVER-SPEC", "warn", "description 超过 1024 字符",
                 "当前 %d 字符，会被宿主截断并挤占其他 Skill 的路由预算。" % info["desc_len"])

    hub_entries = {
        entry["entry"]: real
        for real, entries in entries_by_real.items() for entry in entries if entry["host"] == "shared"
    }
    hub_by_real: Dict[str, List[str]] = {}
    for name, real in hub_entries.items():
        hub_by_real.setdefault(real, []).append(name)

    for host, directory in dirs:
        directory_real = host_reals[host]
        names: Dict[str, set] = {}
        for real, entries in entries_by_real.items():
            own = [entry for entry in entries if entry["host"] == host]
            if not own:
                continue
            info = skills[real]
            if info["name"]:
                names.setdefault(info["name"], set()).add(real)
            if len(own) > 1:
                keep = [entry for entry in own if entry["entry"] == info["name"]]
                extra = [entry for entry in own if entry["entry"] != info["name"] and entry["kind"] == "link"]
                fix = None
                if host != "shared" and len(keep) == 1 and extra:
                    fix = {"action": "unlink-alias", "paths": [entry["path"] for entry in extra],
                           "label": "移除别名链接"}
                info["findings"].append(findings.add(
                    "skills", "SKL-ALIAS", "info", "同一个 Skill 在宿主里有多个入口", env.show(directory),
                    "%s 都指向 %s" % ("、".join(entry["entry"] for entry in own), info["key"]),
                    "|".join(sorted(entry["entry"] for entry in own)), fix,
                ))
            if host == "shared":
                continue
            for entry in own:
                if entry["kind"] == "dir":
                    info["findings"].append(findings.add(
                        "skills", "SKL-HOST-COPY", "info", "宿主目录里的实体副本", entry["path"],
                        "没有经过共享目录，其他宿主无法复用，也不会随真源更新。"))
                    continue
                raw = raw_targets[entry["path"]]
                lexical = raw if os.path.isabs(raw) else os.path.normpath(os.path.join(directory_real, raw))
                if is_inside(lexical, hub_real) or is_inside(lexical, str(env.hub)):
                    continue
                if is_inside(lexical, directory_real) or is_inside(lexical, str(directory)):
                    continue  # a sibling alias; reported by SKL-ALIAS
                via_host = any(
                    other != host and other != "shared"
                    and (is_inside(lexical, other_real) or is_inside(lexical, str(other_path)))
                    for (other, other_path), other_real in zip(dirs, host_reals.values())
                )
                if not via_host and not os.path.isabs(raw):
                    continue
                shared_names = hub_by_real.get(real, [])
                fix = None
                if shared_names:
                    chosen = entry["entry"] if entry["entry"] in shared_names else (
                        info["name"] if info["name"] in shared_names else sorted(shared_names)[0])
                    fix = {"action": "relink-relative", "path": entry["path"], "label": "改为经共享目录的相对链接",
                           "target": os.path.relpath(os.path.join(hub_real, chosen), directory_real)}
                if via_host:
                    chains.setdefault(real, []).append(
                        {"host": host, "path": entry["path"], "target": fix["target"] if fix else ""})
                    continue
                if fix is None and os.path.isdir(env.hub) and not os.path.lexists(env.hub / entry["entry"]):
                    fix = {"action": "adopt-into-hub", "path": entry["path"], "label": "登记到共享目录并改为相对链接",
                           "hub_path": env.show(env.hub / entry["entry"]), "real": info["key"],
                           "target": os.path.relpath(os.path.join(hub_real, entry["entry"]), directory_real)}
                if shared_names:
                    code, severity, title = "SKL-LINK-ABS", "info", "绝对路径链接，没有经过共享目录"
                    detail = "指向 %s；共享目录里已有同一个 Skill。" % entry["link_target"]
                else:
                    code, severity, title = "SKL-NOT-SHARED", "info", "直接链接到源码，没有登记到共享目录"
                    detail = "指向 %s；其他宿主无法通过共享目录复用它。" % entry["link_target"]
                info["findings"].append(findings.add("skills", code, severity, title, entry["path"], detail, fix=fix))
        for name, reals in sorted(names.items()):
            if len(reals) > 1:
                identifier = findings.add(
                    "skills", "SKL-DUP-NAME", "warn", "多个目录声明了同一个 Skill 名", env.show(directory),
                    "%s 来自：%s。宿主只会采用其中一个。" % (name, "、".join(sorted(skills[real]["key"] for real in reals))),
                    name,
                )
                for real in reals:
                    skills[real]["findings"].append(identifier)

    # Dozens of hosts often relay through one host's copy; report that once per Skill.
    for real, links in chains.items():
        info = skills[real]
        involved = sorted({link["host"] for link in links})
        relinkable = [{"path": link["path"], "target": link["target"]} for link in links if link["target"]]
        detail = "%d 个宿主的链接经过另一个宿主的目录（%s%s），那个入口变动时它们会一起失效。" % (
            len(involved), "、".join(involved[:6]), " 等" if len(involved) > 6 else "")
        if not relinkable:
            detail += "共享目录里还没有这个 Skill，需要先把实体目录放进共享目录。"
        info["findings"].append(findings.add(
            "skills", "SKL-LINK-CHAIN", "warn", "宿主链接绕经另一个宿主的目录", info["key"], detail,
            fix={"action": "relink-many", "links": relinkable, "label": "改为经共享目录的相对链接"}
            if relinkable else None))

    for real, names_in_hub in hub_by_real.items():
        info = skills[real]
        if not any(host != "shared" for host in info["hosts"]):
            info["findings"].append(findings.add(
                "skills", "SKL-HUB-UNLINKED", "info", "共享目录里的 Skill 没有宿主链接到它",
                env.show(env.hub / sorted(names_in_hub)[0]), "它不会出现在只扫描自己目录的宿主里。"))

    for real, info in skills.items():
        shared_names = hub_by_real.get(real, [])
        locked = next((lock[name] for name in shared_names if isinstance(lock.get(name), dict)), None)
        if env.source_root is not None and is_inside(real, str(env.source_root)):
            info["origin"] = "studio"
        elif locked:
            info["origin"] = "registry"
            info["source"] = scalar(locked.get("source"))
        elif is_inside(real, hub_real):
            info["origin"] = "shared-copy"
        elif any(is_inside(real, host_real) for host_real in host_reals.values()):
            info["origin"] = "host-copy"
        else:
            info["origin"] = "external"

    disabled = []
    for item in safe_scandir(env.disabled):
        if item.name.startswith("."):
            continue
        info = load_skill(os.path.realpath(item.path)) if os.path.isdir(item.path) else {}
        disabled.append({"entry": item.name, "path": env.show(item.path), "name": info.get("name", ""),
                         "description": clip(info.get("description", ""), 200)})

    public = [
        {key: value for key, value in info.items() if key not in ("present", "collection", "has_skill_md")}
        for info in skills.values() if info["has_skill_md"]
    ]
    public.sort(key=lambda item: (item["name"] or item["key"]).lower())
    section = {
        "hosts": hosts, "skills": public, "loose": loose, "disabled": disabled,
        "shared": env.show(env.hub) if os.path.isdir(env.hub) else "",
        "lock": {"path": env.show(lock_path), "count": len(lock)} if lock else None,
    }
    return section, {"skills": skills, "entries_by_real": entries_by_real, "hub_by_real": hub_by_real}


# ---------------------------------------------------------------------------
# Area 3: studio skill sources
# ---------------------------------------------------------------------------


def git(cwd: str, *arguments: str) -> Tuple[int, str]:
    try:
        process = subprocess.run(
            ["git", "-C", cwd, *arguments], capture_output=True, text=True, timeout=20, env=GIT_ENV
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, str(exc)
    return process.returncode, process.stdout.strip()


def normalize_remote(url: str) -> str:
    """Reduce a remote URL to ``owner/repo`` so embedded credentials never leave git."""
    match = re.search(r"[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", url.strip())
    return "%s/%s" % (match.group(1), match.group(2)) if match else ""


def git_state(directory: str) -> Dict[str, Any]:
    state: Dict[str, Any] = {"repo": False}
    marker = os.path.join(directory, ".git")
    if not os.path.lexists(marker):
        return state
    config = None
    if os.path.isdir(marker):
        # Without HEAD git ignores this folder and answers for the enclosing repository.
        if not os.path.isfile(os.path.join(marker, "HEAD")):
            state["broken"] = True
            return state
        try:
            config = read_text(os.path.join(marker, "config"), 64 * 1024)
        except OSError:
            config = None
    else:
        code, top = git(directory, "rev-parse", "--show-toplevel")
        if code != 0 or os.path.realpath(top) != os.path.realpath(directory):
            state["broken"] = True
            return state
    code, output = git(directory, "status", "--porcelain=v2", "--branch")
    if code != 0:
        state["broken"] = True
        return state
    state.update(repo=True, branch="", upstream="", ahead=0, behind=0, dirty=0, remote="", last_commit="")
    for line in output.split("\n"):
        if line.startswith("# branch.head "):
            state["branch"] = line.split(" ", 2)[2]
        elif line.startswith("# branch.upstream "):
            state["upstream"] = line.split(" ", 2)[2]
        elif line.startswith("# branch.ab "):
            match = re.match(r"# branch\.ab \+(\d+) -(\d+)", line)
            if match:
                state["ahead"], state["behind"] = int(match.group(1)), int(match.group(2))
        elif line and not line.startswith("#"):
            state["dirty"] += 1
    if config is None:
        code, url = git(directory, "config", "--get", "remote.origin.url")
        state["remote"] = normalize_remote(url) if code == 0 else ""
    else:
        origin = re.search(r'\[remote "origin"\]([^\[]*)', config)
        url_match = re.search(r"(?m)^\s*url\s*=\s*(\S+)", origin.group(1)) if origin else None
        state["remote"] = normalize_remote(url_match.group(1)) if url_match else ""
    code, log = git(directory, "log", "-1", "--format=%cI")
    state["last_commit"] = log if code == 0 else ""
    return state


def locate_skill_md(directory: str, hint: str) -> str:
    if os.path.isfile(os.path.join(directory, "SKILL.md")):
        return "SKILL.md"
    hint = hint[: -len("SKILL.md")].rstrip("/") if hint.endswith("SKILL.md") else hint.strip("/")
    if hint and os.path.isfile(os.path.join(directory, hint, "SKILL.md")):
        return hint + "/SKILL.md"
    children = [
        child for child in safe_scandir(directory)
        if os.path.isdir(child.path) and not child.name.startswith(".") and child.name not in ("node_modules", "dist")
    ]
    for child in children:
        if os.path.isfile(os.path.join(child.path, "SKILL.md")):
            return child.name + "/SKILL.md"
    for child in children:
        for grand in safe_scandir(child.path):
            if os.path.isfile(os.path.join(grand.path, "SKILL.md")):
                return "%s/%s/SKILL.md" % (child.name, grand.name)
    return ""


def version_surfaces(skill_dir: str, repo_dir: str, version: str) -> Dict[str, str]:
    surfaces: Dict[str, str] = {}
    if version:
        surfaces["SKILL.md"] = version

    def first_match(name: str, pattern: str) -> None:
        for base in (skill_dir, repo_dir):
            path = os.path.join(base, name)
            if os.path.isfile(path):
                try:
                    match = re.search(pattern, read_text(path, 128 * 1024))
                except OSError:
                    match = None
                if match:
                    surfaces[name] = match.group(1)
                return

    for name in ("skill.yaml", "skill-card.yaml", "pricing-card.yaml"):
        first_match(name, r"(?m)^version:\s*[\"']?([^\"'\s#]+)")
    first_match("README.md", r"badge/version-(\d+\.\d+\.\d+[^-\s)]*)-")
    first_match("CHANGELOG.md", r"(?m)^##\s+\[?v?(\d+\.\d+\.\d+[^\]\s]*)\]?")
    return surfaces


def scan_studio(env: Env, findings: Findings, index: Dict[str, Any], no_git: bool) -> Dict[str, Any]:
    section: Dict[str, Any] = {
        "configured": env.source_root is not None,
        "source_root": env.show(env.source_root) if env.source_root else "",
        "catalog": None, "sources": [], "stray": [],
    }
    catalog_entries: List[Dict[str, Any]] = []
    catalog_dir = ""
    if env.catalog is not None:
        catalog_entries, error = load_catalog(env.catalog)
        catalog_dir = str(env.catalog.parent)
        if error:
            env.notes.append(error)
        section["catalog"] = {
            "path": env.show(env.catalog), "total": len(catalog_entries),
            "paid": sum(1 for entry in catalog_entries if entry["paid"]), "error": error,
        }
    if env.source_root is None:
        return section

    by_repo: Dict[str, List[Dict[str, Any]]] = {}
    by_dir: Dict[str, List[Dict[str, Any]]] = {}
    by_runtime: Dict[str, Dict[str, Any]] = {}
    for entry in catalog_entries:
        by_repo.setdefault(entry["repo"].lower(), []).append(entry)
        by_dir.setdefault(entry["repo"].split("/")[-1].lower(), []).append(entry)
        if entry["runtime_name"]:
            by_runtime.setdefault(entry["runtime_name"], entry)

    directories = []
    for item in safe_scandir(env.source_root):
        if item.name.startswith("."):
            continue
        if os.path.isdir(item.path):
            directories.append(item.path)
        else:
            section["stray"].append(item.name)

    states: Dict[str, Dict[str, Any]] = {}
    if not no_git:
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
            for directory, state in zip(directories, pool.map(git_state, directories)):
                states[directory] = state

    skills = index["skills"]
    entries_by_real = index["entries_by_real"]
    matched = set()
    mirror_root = os.path.join(catalog_dir, "skills") if catalog_dir else ""

    for directory in directories:
        name = os.path.basename(directory)
        shown = env.show(directory)
        state = states.get(directory)
        candidates = by_dir.get(name.lower(), [])
        if state and state.get("remote"):
            candidates = by_repo.get(state["remote"].lower(), []) or candidates
        hint = candidates[0]["skill_path"] if candidates else ""
        relative = locate_skill_md(directory, hint)
        record: Dict[str, Any] = {
            "dir": name, "path": shown, "skill_md": relative, "name": "", "version": "", "desc_len": 0,
            "surfaces": {}, "drift": False, "bundle": {}, "modules": 0, "git": state, "catalog": None,
            "mirror": None, "installed": {"shared": [], "hosts": []}, "findings": [],
        }
        section["sources"].append(record)

        def note(code: str, severity: str, title: str, detail: str = "") -> None:
            record["findings"].append(findings.add("studio", code, severity, title, shown, detail))

        if state is not None:
            if not state.get("repo"):
                note("STU-NOT-REPO", "warn", "不是独立的 Git 仓库",
                     "目录内的 .git 不完整，git 命令会落到上层仓库。" if state.get("broken")
                     else "没有 .git；改动既没有版本记录，也无法推送。")
            else:
                if state["dirty"]:
                    note("STU-DIRTY", "warn", "有未提交的改动", "%d 个文件有改动。" % state["dirty"])
                if state["ahead"]:
                    note("STU-UNPUSHED", "warn", "有未推送的提交", "领先上游 %d 个提交。" % state["ahead"])
                if state["behind"]:
                    note("STU-BEHIND", "info", "落后于上游", "落后 %d 个提交（以上次 fetch 为准）。" % state["behind"])
                if not state["remote"]:
                    note("STU-NO-REMOTE", "info", "还没有远端仓库", "只存在于本机。")
        if not relative:
            note("STU-NO-SKILL-MD", "info", "源码目录里没有 SKILL.md")
            continue

        skill_dir = os.path.dirname(os.path.join(directory, relative))
        info = load_skill(skill_dir)
        record.update(name=info["name"], version=info["version"], desc_len=info["desc_len"])
        record["modules"] = sum(
            1 for child in safe_scandir(os.path.join(skill_dir, "skills"))
            if os.path.isfile(os.path.join(child.path, "SKILL.md"))
        )
        record["surfaces"] = version_surfaces(skill_dir, directory, info["version"])
        core = {key: value for key, value in record["surfaces"].items() if key != "CHANGELOG.md"}
        listing = "，".join("%s=%s" % pair for pair in record["surfaces"].items())
        if len(set(core.values())) > 1:
            record["drift"] = True
            note("STU-VERSION-DRIFT", "warn", "版本号在不同文件里不一致", listing)
        elif info["version"] and record["surfaces"].get("CHANGELOG.md", info["version"]) != info["version"]:
            note("STU-CHANGELOG-STALE", "info", "CHANGELOG 最新条目不是当前版本", listing)
        for filename in ("README.md", "CHANGELOG.md", "LICENSE", "skill.yaml", "skill-card.yaml",
                         "cases/cases.json", "pricing-card.yaml"):
            record["bundle"][filename] = any(
                os.path.isfile(os.path.join(base, filename)) for base in (skill_dir, directory))
        if not record["bundle"]["README.md"]:
            note("STU-NO-README", "warn", "缺少 README.md", "使用者看不到安装方式与示例。")

        match = next((entry for entry in candidates if entry["runtime_name"] == info["name"]), None)
        match = match or (candidates[0] if candidates else by_runtime.get(info["name"]))
        if match:
            matched.add(match["name"])
            relation = version_relation(info["version"], match["version"])
            record["catalog"] = dict(match, relation=relation)
            if relation == "source-ahead":
                note("STU-CATALOG-BEHIND", "info", "目录版本落后于源码",
                     "源码 %s，目录 %s；尚未发布或目录未同步。" % (info["version"], match["version"]))
            elif relation == "source-behind":
                note("STU-CATALOG-AHEAD", "warn", "本地源码落后于目录",
                     "源码 %s，目录 %s；本地 clone 可能没有拉取最新提交。" % (info["version"], match["version"]))
            if match["runtime_name"] and info["name"] and match["runtime_name"] != info["name"]:
                note("STU-RUNTIME-NAME", "warn", "目录的 runtime_name 与 SKILL.md 的 name 不一致",
                     "目录 %s，源码 %s。" % (match["runtime_name"], info["name"]))
            if mirror_root and os.path.isdir(mirror_root) and not match["paid"] and match["visibility"] != "internal":
                mirror_md = os.path.join(mirror_root, match["name"], "SKILL.md")
                if os.path.isfile(mirror_md):
                    mirror_version = parse_skill_frontmatter(read_text(mirror_md, 256 * 1024))["version"]
                    mirror_relation = version_relation(info["version"], mirror_version)
                    record["mirror"] = {"version": mirror_version, "relation": mirror_relation}
                    if mirror_relation in ("source-ahead", "source-behind"):
                        note("STU-MIRROR-STALE", "info", "目录镜像与源码版本不同",
                             "源码 %s，镜像 %s（以本地目录仓库为准）。" % (info["version"], mirror_version))
                else:
                    record["mirror"] = {"version": "", "relation": "missing"}
                    note("STU-MIRROR-MISSING", "warn", "免费条目在目录仓库里没有镜像",
                         "skills/%s/ 不存在，安装与官网详情页会缺内容。" % match["name"])
        elif catalog_entries:
            note("STU-UNLISTED", "info", "还没有登记到目录", "草稿或尚未发布。")

        reals = {os.path.realpath(directory), os.path.realpath(skill_dir)}
        linked = [entry for real in reals for entry in entries_by_real.get(real, [])]
        record["installed"] = {
            "shared": sorted({entry["entry"] for entry in linked if entry["host"] == "shared"}),
            "hosts": sorted({entry["host"] for entry in linked if entry["host"] != "shared"}),
        }
        if not linked:
            note("STU-NOT-INSTALLED", "info", "没有安装到本机任何宿主")

    installed_names = {info["name"]: info for info in skills.values() if info.get("has_skill_md") and info["name"]}
    missing = 0
    for entry in catalog_entries:
        if entry["name"] in matched:
            continue
        elsewhere = installed_names.get(entry["runtime_name"])
        record = {
            "dir": "", "path": elsewhere["key"] if elsewhere else "", "skill_md": "",
            "name": entry["runtime_name"] or entry["name"], "version": elsewhere["version"] if elsewhere else "",
            "desc_len": 0, "surfaces": {}, "drift": False, "bundle": {}, "modules": 0, "git": None,
            "catalog": dict(entry, relation=version_relation(elsewhere["version"], entry["version"])
                            if elsewhere else "unknown"),
            "mirror": None, "installed": {"shared": [], "hosts": elsewhere["hosts"] if elsewhere else []},
            "findings": [], "external": bool(elsewhere), "missing_source": not elsewhere,
        }
        section["sources"].append(record)
        missing += 0 if elsewhere else 1
    if missing:
        findings.add("studio", "STU-CATALOG-NO-SOURCE", "info", "目录里有条目在本机找不到源码",
                     section["source_root"], "%d 个条目既不在源码根目录，也没有安装到本机。" % missing)
    return section


# ---------------------------------------------------------------------------
# Snapshot and report
# ---------------------------------------------------------------------------


def severity_counts(items: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = Counter(item["severity"] for item in items)
    return {severity: counts.get(severity, 0) for severity in SEVERITIES}


def build_snapshot(env: Env, no_git: bool = False) -> Dict[str, Any]:
    findings = Findings()
    if not no_git and shutil.which("git") is None:
        no_git = True
        env.notes.append("没有找到 git，已跳过源码仓库的 Git 状态。")
    prompt = scan_prompt(env, findings)
    skills, index = scan_skills(env, findings)
    studio = scan_studio(env, findings, index, no_git)
    items = findings.items
    items.sort(key=lambda item: (SEVERITIES.index(item["severity"]), item["area"], item["code"], item["path"]))

    sources = [record for record in studio["sources"] if record["dir"]]
    states = [record["git"] for record in sources if record["git"] and record["git"].get("repo")]
    bound = [host for host in prompt["hosts"] if host["state"] in ("linked", "copy", "embedded")]
    summary = {
        "findings": dict(severity_counts(items), fixable=sum(1 for item in items if item["fix"])),
        "areas": {area: severity_counts([item for item in items if item["area"] == area]) for area in AREA_LABELS},
        "prompt": {
            "version": prompt["root"]["version"] if prompt["root"] else "",
            "rules": sum(len(record.get("rules", [])) for record in prompt["files"]),
            "references": sum(1 for record in prompt["files"] if record["kind"] == "reference"),
            "hosts_bound": len(bound),
            "hosts_total": sum(1 for host in prompt["hosts"] if host["state"] != "missing" or host["known"]),
        },
        "skills": {
            "hosts": len([host for host in skills["hosts"] if host["id"] != "shared"]),
            "unique": len(skills["skills"]),
            "shared_entries": next((host["entries"] for host in skills["hosts"] if host["id"] == "shared"), 0),
            "entries": sum(host["entries"] for host in skills["hosts"]),
            "disabled": len(skills["disabled"]),
        },
        "studio": {
            "sources": len(sources),
            "listed": sum(1 for record in sources if record["catalog"]),
            "dirty": sum(1 for state in states if state["dirty"]),
            "unpushed": sum(1 for state in states if state["ahead"]),
            "drift": sum(1 for record in sources if record["drift"]),
            "catalog_total": studio["catalog"]["total"] if studio["catalog"] else 0,
            "catalog_paid": studio["catalog"]["paid"] if studio["catalog"] else 0,
        },
    }
    return {
        "schema": SNAPSHOT_SCHEMA,
        "meta": {
            "generated_at": now_iso(), "tool_version": tool_version(), "write_enabled": False, "static": False,
            "brand": scalar(nested(env.profile, "brand.name")), "git_checked": not no_git, "notes": env.notes,
            "yaml": yaml is not None,
        },
        "roots": {
            "home": "~", "agents_home": env.show(env.agents_home),
            "source_root": env.show(env.source_root) if env.source_root else "",
            "catalog": env.show(env.catalog) if env.catalog else "",
            "state_dir": env.show(env.state_dir), "provenance": env.provenance,
        },
        "summary": summary, "prompt": prompt, "skills": skills, "studio": studio, "findings": items,
    }


def render_report(snapshot: Dict[str, Any], area: Optional[str], severity: Optional[str], limit: int) -> str:
    summary, roots = snapshot["summary"], snapshot["roots"]
    prompt, skills, studio = summary["prompt"], summary["skills"], summary["studio"]
    lines = [
        "# Harness 报告",
        "",
        "- 生成时间：%s" % snapshot["meta"]["generated_at"],
        "- 根 Prompt：%s%s，%d 条规则，%d 个 reference，%d/%d 个宿主已绑定" % (
            roots["agents_home"] + "/AGENTS.md", " v" + prompt["version"] if prompt["version"] else "",
            prompt["rules"], prompt["references"], prompt["hosts_bound"], prompt["hosts_total"]),
        "- Skills：%d 个宿主目录，%d 个入口，%d 个不同的 Skill，%d 个已停用" % (
            skills["hosts"], skills["entries"], skills["unique"], skills["disabled"]),
    ]
    if roots["source_root"]:
        lines.append("- 工作室：%s，%d 个源码目录（%d 个有未提交改动，%d 个未推送，%d 个版本不一致）" % (
            roots["source_root"], studio["sources"], studio["dirty"], studio["unpushed"], studio["drift"]))
    else:
        lines.append("- 工作室：未配置源码根目录（--source-root 或 Profile 的 workspace.skill_repos_root）")
    if roots["catalog"]:
        lines.append("- 目录：%s，%d 条（%d 条付费）" % (roots["catalog"], studio["catalog_total"], studio["catalog_paid"]))
    for note in snapshot["meta"]["notes"]:
        lines.append("- 注意：" + note)
    counts = summary["findings"]
    lines += ["", "## 待处理：错误 %d · 警告 %d · 提示 %d · 可自动整理 %d" % (
        counts["error"], counts["warn"], counts["info"], counts["fixable"])]
    for key, label in AREA_LABELS.items():
        if area and key != area:
            continue
        items = [item for item in snapshot["findings"] if item["area"] == key
                 and (not severity or SEVERITIES.index(item["severity"]) <= SEVERITIES.index(severity))]
        if not items:
            continue
        lines += ["", "### %s（%d）" % (label, len(items))]
        for item in items[:limit]:
            lines.append("- [%s] `%s` %s %s — %s%s%s" % (
                SEVERITY_LABELS[item["severity"]], item["id"], item["code"], item["title"], item["path"],
                "：" + item["detail"] if item["detail"] else "",
                "（可整理：%s）" % item["fix"]["label"] if item["fix"] else ""))
        if len(items) > limit:
            lines.append("- …另有 %d 项，用 --limit 调整或在 dashboard 里查看" % (len(items) - limit))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Tidy engine: plan -> apply (journaled) -> undo
# ---------------------------------------------------------------------------


class TidyError(Exception):
    """A requested operation cannot be planned or applied safely."""


def unlink_step(env: Env, path: str) -> Dict[str, Any]:
    if not os.path.islink(path):
        raise TidyError("%s 不是符号链接，不会删除实体文件" % env.show(path))
    target = os.readlink(path)
    return {"do": "unlink", "path": env.show(path), "expect": target,
            "text": "移除链接 %s（原指向 %s）" % (env.show(path), env.show(target))}


def symlink_step(env: Env, path: str, target: str) -> Dict[str, Any]:
    return {"do": "symlink", "path": env.show(path), "target": target,
            "text": "创建链接 %s → %s" % (env.show(path), env.show(target))}


def move_step(env: Env, source: str, destination: str) -> Dict[str, Any]:
    return {"do": "move", "src": env.show(source), "dst": env.show(destination),
            "text": "移动 %s → %s" % (env.show(source), env.show(destination))}


def detach_steps(env: Env, path: str, dirs: Dict[str, Path]) -> List[Dict[str, Any]]:
    """Links that would dangle once ``path`` leaves the shared directory."""
    if not os.path.exists(path):
        return []
    real = os.path.realpath(path)
    steps = []
    for host, directory in dirs.items():
        for item in safe_scandir(directory):
            if not item.is_symlink() or os.path.normpath(item.path) == os.path.normpath(path):
                continue
            if os.path.realpath(item.path) != real:
                continue
            if host == "shared":
                lexical = os.path.normpath(os.path.join(os.path.dirname(item.path), os.readlink(item.path)))
                if lexical != os.path.normpath(path):
                    continue
            steps.append(unlink_step(env, item.path))
    return steps


def recorded_links(env: Env, entry: str) -> List[Dict[str, Any]]:
    """Host links removed when ``entry`` was last disabled, taken from the journal."""
    source, destination = env.show(env.hub / entry), env.show(env.disabled / entry)
    for batch in list_batches(env, full=True):
        steps = [step for step in batch["steps"] if step.get("status") == "done"]
        if batch.get("undone_at") or not any(
            step["do"] == "move" and step["src"] == source and step["dst"] == destination for step in steps
        ):
            continue
        return [step for step in steps if step["do"] == "unlink"]
    return []


def fix_steps(env: Env, fix: Dict[str, Any], batch: str, dirs: Dict[str, Path]) -> List[Dict[str, Any]]:
    action = fix.get("action")
    path = env.real(scalar(fix.get("path")))
    if action == "remove-broken-link":
        if not os.path.islink(path):
            raise TidyError("%s 已不是链接" % fix["path"])
        if os.path.exists(path):
            raise TidyError("%s 已恢复可用，不再移除" % fix["path"])
        return [unlink_step(env, path)]
    if action == "relink-relative":
        return [unlink_step(env, path), symlink_step(env, path, fix["target"])]
    if action == "relink-many":
        steps = []
        for link in fix.get("links", []):
            target_path = env.real(link["path"])
            steps += [unlink_step(env, target_path), symlink_step(env, target_path, link["target"])]
        return steps
    if action == "adopt-into-hub":
        hub_path = env.real(fix["hub_path"])
        if os.path.lexists(hub_path):
            raise TidyError("%s 已被占用" % fix["hub_path"])
        return [symlink_step(env, hub_path, env.real(fix["real"])), unlink_step(env, path),
                symlink_step(env, path, fix["target"])]
    if action == "quarantine":
        if not os.path.lexists(path):
            raise TidyError("%s 已不存在" % fix["path"])
        destination = env.state_dir / batch / "quarantine" / os.path.basename(path)
        return detach_steps(env, path, dirs) + [move_step(env, path, str(destination))]
    if action == "link-prompt":
        if os.path.lexists(path):
            raise TidyError("%s 已存在" % fix["path"])
        return [symlink_step(env, path, fix["target"])]
    if action == "unlink-alias":
        return [unlink_step(env, env.real(item)) for item in fix.get("paths", [])]
    raise TidyError("未知的整理动作：%s" % action)


def op_steps(
    env: Env, op: Dict[str, Any], by_id: Dict[str, Dict[str, Any]], batch: str, dirs: Dict[str, Path]
) -> List[Dict[str, Any]]:
    kind = op.get("op")
    entry = scalar(op.get("entry"))
    if kind in ("disable", "enable", "link", "unlink") and (not entry or "/" in entry or entry.startswith(".")):
        raise TidyError("入口名无效：%r" % entry)
    if kind == "fix":
        item = by_id.get(scalar(op.get("id")))
        if item is None:
            raise TidyError("找不到问题 %s，请先重新扫描" % op.get("id"))
        if not item["fix"]:
            raise TidyError("%s 没有自动整理动作，需要手动处理" % item["code"])
        return fix_steps(env, item["fix"], batch, dirs)
    if kind == "disable":
        source = env.hub / entry
        if not os.path.lexists(source):
            raise TidyError("共享目录里没有 %s" % entry)
        if os.path.lexists(env.disabled / entry):
            raise TidyError("停用目录里已有 %s" % entry)
        return detach_steps(env, str(source), dirs) + [move_step(env, str(source), str(env.disabled / entry))]
    if kind == "enable":
        source = env.disabled / entry
        if not os.path.lexists(source):
            raise TidyError("停用目录里没有 %s" % entry)
        if os.path.lexists(env.hub / entry):
            raise TidyError("共享目录里已有 %s" % entry)
        steps = [move_step(env, str(source), str(env.hub / entry))]
        for link in recorded_links(env, entry):
            if not os.path.lexists(env.real(link["path"])):
                steps.append(symlink_step(env, env.real(link["path"]), link["expect"]))
        return steps
    if kind in ("link", "unlink"):
        host = scalar(op.get("host"))
        directory = dirs.get(host)
        if directory is None or host == "shared":
            raise TidyError("未知宿主：%s" % host)
        if kind == "unlink":
            return [unlink_step(env, str(directory / entry))]
        source = env.hub / entry
        if not os.path.isdir(source):
            raise TidyError("共享目录里没有 %s" % entry)
        declared = load_skill(os.path.realpath(source))["name"]
        name = declared if NAME_RE.match(declared) and len(declared) <= 64 else entry
        if os.path.lexists(directory / name):
            raise TidyError("%s 里已有 %s" % (host, name))
        target = os.path.relpath(os.path.join(os.path.realpath(env.hub), entry), os.path.realpath(directory))
        return [symlink_step(env, str(directory / name), target)]
    raise TidyError("未知操作：%s" % kind)


def plan_ops(env: Env, snapshot: Dict[str, Any], ops: List[Dict[str, Any]]) -> Dict[str, Any]:
    batch = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(2)
    dirs = dict(discover_skill_dirs(env))
    by_id = {item["id"]: item for item in snapshot.get("findings", [])}
    accepted: List[Dict[str, Any]] = []
    steps: List[Dict[str, Any]] = []
    owners: Dict[str, int] = {}
    for op in ops:
        if op in accepted:
            continue
        accepted.append(op)
        # Steps are planned against the current filesystem, so two operations that
        # touch the same path would invalidate each other's expectations.
        for step in op_steps(env, op, by_id, batch, dirs):
            for key in ("path", "src", "dst"):
                if key in step and owners.setdefault(step[key], len(accepted)) != len(accepted):
                    raise TidyError("%s 同时被多个整理项改动，请分两次执行" % step[key])
            steps.append(step)
    return {"batch": batch, "ops": accepted, "steps": steps}


def in_managed_area(env: Env, path: str) -> bool:
    normalized = os.path.normpath(path)
    if is_inside(normalized, str(env.agents_home)) or is_inside(normalized, str(env.state_dir)):
        return True
    relative = os.path.relpath(normalized, str(env.home))
    return not relative.startswith("..") and relative.split(os.sep)[0].startswith(".")


def movable(env: Env, path: str) -> bool:
    parent = os.path.realpath(os.path.dirname(path))
    return parent in (os.path.realpath(env.hub), os.path.realpath(env.disabled)) or is_inside(
        parent, os.path.realpath(env.state_dir))


def check_step(env: Env, step: Dict[str, Any]) -> str:
    """Re-validate one step against the filesystem right before it runs."""
    action = step.get("do")
    if action == "unlink":
        path = env.real(step["path"])
        if not in_managed_area(env, path):
            return "路径不在 Agent 配置目录内"
        if not os.path.islink(path):
            return "不是符号链接，不删除实体文件"
        if step.get("expect") is not None and os.readlink(path) != step["expect"]:
            return "链接目标已变化"
        return ""
    if action == "symlink":
        path = env.real(step["path"])
        if not in_managed_area(env, path):
            return "路径不在 Agent 配置目录内"
        if os.path.lexists(path):
            return "目标位置已被占用"
        if not os.path.isdir(os.path.dirname(path)):
            return "上级目录不存在"
        target = step["target"]
        resolved = target if os.path.isabs(target) else os.path.normpath(os.path.join(os.path.dirname(path), target))
        if not step.get("dangling_ok") and not os.path.exists(resolved):
            return "链接目标不存在"
        return ""
    if action == "move":
        source, destination = env.real(step["src"]), env.real(step["dst"])
        if not os.path.lexists(source):
            return "源已不存在"
        if os.path.lexists(destination):
            return "目标位置已被占用"
        if not movable(env, source) or not movable(env, destination):
            return "只允许在共享目录、停用目录与整理备份之间移动"
        return ""
    return "未知步骤"


def run_steps(env: Env, steps: List[Dict[str, Any]], save: Any) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    healthy = True
    for step in steps:
        record = dict(step)
        results.append(record)
        if not healthy:
            record["status"] = "skipped"
            continue
        error = check_step(env, step)
        if not error:
            try:
                if step["do"] == "unlink":
                    os.unlink(env.real(step["path"]))
                elif step["do"] == "symlink":
                    os.symlink(step["target"], env.real(step["path"]))
                else:
                    destination = env.real(step["dst"])
                    os.makedirs(os.path.dirname(destination), exist_ok=True)
                    os.rename(env.real(step["src"]), destination)
            except OSError as exc:
                error = exc.strerror or str(exc)
        record["status"] = "failed" if error else "done"
        if error:
            record["error"] = error
            healthy = False
        save(results)
    return results


def apply_plan(env: Env, plan: Dict[str, Any]) -> Dict[str, Any]:
    journal = {"schema": JOURNAL_SCHEMA, "batch": plan["batch"], "created_at": now_iso(),
               "ops": plan["ops"], "steps": [], "undone_at": None}
    path = env.state_dir / plan["batch"] / "journal.json"

    def save(results: List[Dict[str, Any]]) -> None:
        journal["steps"] = results
        write_json_atomic(path, journal)

    save([])
    save(run_steps(env, plan["steps"], save))
    return journal


def list_batches(env: Env, full: bool = False) -> List[Dict[str, Any]]:
    batches = []
    for item in sorted(safe_scandir(env.state_dir), key=lambda entry: entry.name, reverse=True):
        if not BATCH_RE.match(item.name):
            continue
        try:
            journal = json.loads(read_text(os.path.join(item.path, "journal.json")))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(journal, dict) or not isinstance(journal.get("steps"), list):
            continue
        if full:
            batches.append(journal)
            continue
        steps = journal["steps"]
        batches.append({
            "batch": journal.get("batch", item.name), "created_at": journal.get("created_at", ""),
            "undone_at": journal.get("undone_at"),
            "done": sum(1 for step in steps if step.get("status") == "done"),
            "failed": sum(1 for step in steps if step.get("status") == "failed"),
            "steps": [{"text": step.get("text", ""), "status": step.get("status", ""),
                       "error": step.get("error", "")} for step in steps],
        })
    return batches


def undo_batch(env: Env, batch: str, apply: bool) -> Dict[str, Any]:
    if not BATCH_RE.match(batch):
        raise TidyError("批次号无效：%s" % batch)
    path = env.state_dir / batch / "journal.json"
    try:
        journal = json.loads(read_text(path))
    except (OSError, json.JSONDecodeError):
        raise TidyError("找不到整理记录 %s" % batch)
    if journal.get("undone_at"):
        raise TidyError("批次 %s 已经撤销过" % batch)
    inverse: List[Dict[str, Any]] = []
    for step in reversed([step for step in journal["steps"] if step.get("status") == "done"]):
        if step["do"] == "unlink":
            restored = symlink_step(env, env.real(step["path"]), step["expect"])
            restored["dangling_ok"] = True
            inverse.append(restored)
        elif step["do"] == "symlink":
            inverse.append({"do": "unlink", "path": step["path"], "expect": step["target"],
                            "text": "移除链接 %s" % step["path"]})
        else:
            inverse.append(move_step(env, env.real(step["dst"]), env.real(step["src"])))
    if not apply:
        return {"batch": batch, "steps": inverse, "applied": False}

    def save(results: List[Dict[str, Any]]) -> None:
        journal["undo_steps"] = results

    results = run_steps(env, inverse, save)
    if all(step["status"] == "done" for step in results):
        journal["undone_at"] = now_iso()
    write_json_atomic(path, journal)
    return {"batch": batch, "steps": results, "applied": True, "undone": bool(journal["undone_at"])}


# ---------------------------------------------------------------------------
# Dashboard server and static export
# ---------------------------------------------------------------------------


class Dashboard:
    def __init__(self, args: argparse.Namespace, allow_write: bool) -> None:
        self.args = args
        self.allow_write = allow_write
        self.token = secrets.token_urlsafe(24)
        self.lock = threading.Lock()
        self.env: Optional[Env] = None
        self.snapshot: Optional[Dict[str, Any]] = None
        self.plans: Dict[str, Dict[str, Any]] = {}

    def state(self, refresh: bool = False) -> Tuple[Env, Dict[str, Any]]:
        with self.lock:
            if refresh or self.snapshot is None or self.env is None:
                self.env = resolve_env(self.args)
                self.snapshot = build_snapshot(self.env, getattr(self.args, "no_git", False))
                self.snapshot["meta"]["write_enabled"] = self.allow_write
                self.plans.clear()
            return self.env, self.snapshot

    def readable(self, shown: str) -> bool:
        _, snapshot = self.state()
        if any(record["path"] == shown for record in snapshot["prompt"]["files"]):
            return True
        return shown.endswith("/SKILL.md") and any(
            skill["key"] == shown[: -len("/SKILL.md")] for skill in snapshot["skills"]["skills"])

    def openable(self, shown: str) -> bool:
        _, snapshot = self.state()
        roots = snapshot["roots"]
        known = {roots["agents_home"], roots["source_root"], roots["catalog"], snapshot["skills"]["shared"]}
        known.update(record["path"] for record in snapshot["prompt"]["files"])
        known.update(host["path"] for host in snapshot["skills"]["hosts"])
        known.update(skill["key"] for skill in snapshot["skills"]["skills"])
        known.update(record["path"] for record in snapshot["studio"]["sources"])
        return bool(shown) and shown in known

    def plan(self, ops: Any) -> Dict[str, Any]:
        if not isinstance(ops, list) or not ops or not all(isinstance(op, dict) for op in ops):
            raise TidyError("没有要整理的项目")
        env, snapshot = self.state()
        plan = plan_ops(env, snapshot, ops)
        if not plan["steps"]:
            raise TidyError("这些项目不需要任何改动")
        with self.lock:
            if len(self.plans) >= 20:
                self.plans.pop(next(iter(self.plans)))
            self.plans[plan["batch"]] = plan
        return plan

    def apply(self, batch: str) -> Dict[str, Any]:
        with self.lock:
            plan = self.plans.pop(batch, None)
        if plan is None:
            raise TidyError("计划已过期，请重新预览")
        env, _ = self.state()
        journal = apply_plan(env, plan)
        self.state(refresh=True)
        return journal

    def open_path(self, shown: str, reveal: bool) -> None:
        env, _ = self.state()
        path = env.real(shown)
        if sys.platform == "darwin":
            command = ["open", "-R", path] if reveal else ["open", path]
        elif os.name == "nt":
            command = ["explorer", "/select," + path] if reveal else ["explorer", path]
        else:
            command = ["xdg-open", os.path.dirname(path) if reveal and not os.path.isdir(path) else path]
        try:
            subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError as exc:
            raise TidyError("无法打开：%s" % (exc.strerror or exc))

    def validate(self, shown: str) -> Dict[str, Any]:
        env, snapshot = self.state()
        if not any(record["path"] == shown and record["dir"] for record in snapshot["studio"]["sources"]):
            raise TidyError("只能校验源码根目录里的 Skill")
        try:
            process = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "validate_skill.py"), env.real(shown)],
                capture_output=True, text=True, timeout=90,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise TidyError("校验器无法运行：%s" % exc)
        output = (process.stdout + process.stderr).replace(str(env.home), "~")
        return {"ok": process.returncode == 0, "output": clip(output.strip(), 20000)}


class Handler(BaseHTTPRequestHandler):
    dashboard: Dashboard
    verbose = False
    server_version = "LovHarness"

    def log_message(self, format_string: str, *arguments: Any) -> None:
        if self.verbose:
            super().log_message(format_string, *arguments)

    def _headers(self, content_type: str, length: int, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
        )
        self.end_headers()

    def _json(self, value: Any, status: int = 200) -> None:
        payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self._headers("application/json; charset=utf-8", len(payload), status)
        self.wfile.write(payload)

    def _origin(self) -> str:
        return "http://%s" % self.headers.get("Host", "")

    def _host_allowed(self) -> bool:
        port = int(self.server.server_address[1])
        return self.headers.get("Host", "") in ("127.0.0.1:%d" % port, "localhost:%d" % port)

    def _authorized(self, mutate: bool = False) -> bool:
        if not secrets.compare_digest(self.headers.get("X-Lov-Token", ""), self.dashboard.token):
            return False
        return not mutate or self.headers.get("Origin") in (None, self._origin())

    def do_GET(self) -> None:
        if not self._host_allowed():
            self._json({"error": "invalid Host for the local dashboard"}, 403)
            return
        url = urlparse(self.path)
        name = url.path.lstrip("/")
        if url.path == "/":
            try:
                page = (ASSET_ROOT / "index.html").read_text(encoding="utf-8")
            except OSError:
                self._json({"error": "dashboard assets are missing"}, 500)
                return
            payload = page.replace("__LOV_TOKEN__", self.dashboard.token).encode("utf-8")
            self._headers("text/html; charset=utf-8", len(payload))
            self.wfile.write(payload)
            return
        if name in STATIC_TYPES:
            try:
                payload = (ASSET_ROOT / name).read_bytes()
            except OSError:
                self._json({"error": "not found"}, 404)
                return
            self._headers(STATIC_TYPES[name], len(payload))
            self.wfile.write(payload)
            return
        if not url.path.startswith("/api/"):
            self._json({"error": "not found"}, 404)
            return
        if not self._authorized():
            self._json({"error": "dashboard token rejected"}, 403)
            return
        query = parse_qs(url.query)
        try:
            if url.path == "/api/snapshot":
                self._json(self.dashboard.state(refresh=query.get("refresh") == ["1"])[1])
            elif url.path == "/api/journal":
                self._json({"batches": list_batches(self.dashboard.state()[0])})
            elif url.path == "/api/file":
                shown = (query.get("path") or [""])[0]
                if not self.dashboard.readable(shown):
                    self._json({"error": "这个文件不在本次扫描范围内"}, 403)
                    return
                env = self.dashboard.state()[0]
                self._json({"path": shown, "text": read_text(env.real(shown))})
            else:
                self._json({"error": "not found"}, 404)
        except OSError as exc:
            self._json({"error": exc.strerror or str(exc)}, 500)

    def do_POST(self) -> None:
        if not self._host_allowed():
            self._json({"error": "invalid Host for the local dashboard"}, 403)
            return
        if not self._authorized(mutate=True):
            self._json({"error": "dashboard token rejected"}, 403)
            return
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise TidyError("请求体为空或过大")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise TidyError("请求体必须是 JSON 对象")
            if path == "/api/plan":
                self._json(self.dashboard.plan(payload.get("ops")))
            elif path == "/api/open":
                shown = scalar(payload.get("path"))
                if not self.dashboard.openable(shown):
                    raise TidyError("这个路径不在本次扫描范围内")
                self.dashboard.open_path(shown, bool(payload.get("reveal")))
                self._json({"ok": True})
            elif path == "/api/validate":
                self._json(self.dashboard.validate(scalar(payload.get("path"))))
            elif path in ("/api/apply", "/api/undo"):
                if not self.dashboard.allow_write:
                    self._json({"error": "当前是只读模式；用 --allow-write 重新启动后才能执行整理"}, 403)
                    return
                if path == "/api/apply":
                    self._json(self.dashboard.apply(scalar(payload.get("batch"))))
                else:
                    result = undo_batch(self.dashboard.state()[0], scalar(payload.get("batch")), apply=True)
                    self.dashboard.state(refresh=True)
                    self._json(result)
            else:
                self._json({"error": "not found"}, 404)
        except TidyError as exc:
            self._json({"error": str(exc)}, 400)
        except (ValueError, UnicodeDecodeError):
            self._json({"error": "请求体必须是 UTF-8 JSON"}, 400)
        except OSError as exc:
            self._json({"error": exc.strerror or str(exc)}, 500)


def make_server(dashboard: Dashboard, host: str, port: int, verbose: bool = False) -> ThreadingHTTPServer:
    handler = type("BoundHandler", (Handler,), {"dashboard": dashboard, "verbose": verbose})
    return ThreadingHTTPServer((host, port), handler)


def export_html(snapshot: Dict[str, Any]) -> str:
    """One self-contained, read-only page: assets inlined, snapshot embedded."""
    page = (ASSET_ROOT / "index.html").read_text(encoding="utf-8")
    style = (ASSET_ROOT / "dashboard.css").read_text(encoding="utf-8")
    script = (ASSET_ROOT / "dashboard.js").read_text(encoding="utf-8")
    snapshot = dict(snapshot, meta=dict(snapshot["meta"], static=True, write_enabled=False))
    data = json.dumps(snapshot, ensure_ascii=False).replace("<", "\\u003c")
    page = page.replace('<link rel="stylesheet" href="dashboard.css">', "<style>\n%s\n</style>" % style)
    page = page.replace(
        '<script src="dashboard.js" defer></script>',
        '<script id="lov-snapshot" type="application/json">%s</script>\n<script>\n%s\n</script>'
        % (data, script.replace("</script", "<\\/script")),
    )
    return page.replace("__LOV_TOKEN__", "")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def command_scan(args: argparse.Namespace) -> int:
    snapshot = build_snapshot(resolve_env(args), args.no_git)
    text = json.dumps(snapshot, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.out:
        Path(args.out).expanduser().write_text(text + "\n", encoding="utf-8")
        counts = snapshot["summary"]["findings"]
        print("snapshot=%s" % args.out)
        print("findings=error:%d warn:%d info:%d fixable:%d" % (
            counts["error"], counts["warn"], counts["info"], counts["fixable"]))
    else:
        print(text)
    return 0


def command_report(args: argparse.Namespace) -> int:
    snapshot = build_snapshot(resolve_env(args), args.no_git)
    if args.format == "json":
        print(json.dumps({"meta": snapshot["meta"], "roots": snapshot["roots"], "summary": snapshot["summary"]},
                         ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(render_report(snapshot, args.area, args.severity, args.limit))
    return 0


def command_serve(args: argparse.Namespace) -> int:
    if args.host not in ("127.0.0.1", "localhost"):
        print("error: the dashboard only binds to a loopback host", file=sys.stderr)
        return 2
    dashboard = Dashboard(args, args.allow_write)
    try:
        server = make_server(dashboard, args.host, args.port, args.verbose)
    except OSError:
        server = make_server(dashboard, args.host, 0, args.verbose)
    url = "http://%s:%d/" % (args.host, server.server_address[1])
    env, snapshot = dashboard.state()
    counts = snapshot["summary"]["findings"]
    print("dashboard=%s" % url)
    print("write_enabled=%s" % str(args.allow_write).lower())
    print("agents_home=%s" % env.show(env.agents_home))
    print("source_root=%s" % (env.show(env.source_root) if env.source_root else "unset"))
    print("catalog=%s" % (env.show(env.catalog) if env.catalog else "unset"))
    print("findings=error:%d warn:%d info:%d fixable:%d" % (
        counts["error"], counts["warn"], counts["info"], counts["fixable"]))
    sys.stdout.flush()
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def command_export(args: argparse.Namespace) -> int:
    snapshot = build_snapshot(resolve_env(args), args.no_git)
    target = Path(args.out).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(export_html(snapshot), encoding="utf-8")
    print("exported=%s" % target)
    return 0


def print_steps(steps: List[Dict[str, Any]]) -> None:
    for number, step in enumerate(steps, 1):
        status = step.get("status")
        suffix = "" if not status else "  [%s%s]" % (status, "：" + step["error"] if step.get("error") else "")
        print("%2d. %s%s" % (number, step["text"], suffix))


def command_tidy(args: argparse.Namespace) -> int:
    env = resolve_env(args)
    snapshot = build_snapshot(env, no_git=True)
    ops: List[Dict[str, Any]] = [{"op": "fix", "id": identifier} for identifier in args.fix]
    for code in args.fix_code:
        ops += [{"op": "fix", "id": item["id"]} for item in snapshot["findings"]
                if item["code"] == code and item["fix"]]
    ops += [{"op": "disable", "entry": entry} for entry in args.disable]
    ops += [{"op": "enable", "entry": entry} for entry in args.enable]
    if (args.link or args.unlink) and not args.host:
        print("error: --link / --unlink 需要 --host", file=sys.stderr)
        return 2
    ops += [{"op": "link", "entry": entry, "host": args.host} for entry in args.link]
    ops += [{"op": "unlink", "entry": entry, "host": args.host} for entry in args.unlink]
    if not ops:
        print("error: 没有指定要整理的项目（--fix / --fix-code / --disable / --enable / --link / --unlink）",
              file=sys.stderr)
        return 2
    try:
        plan = plan_ops(env, snapshot, ops)
    except TidyError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    if not args.apply:
        print("计划（未执行，共 %d 步）：" % len(plan["steps"]))
        print_steps(plan["steps"])
        print("确认后加 --apply 执行；每一步都会记入整理记录，可用 undo 撤销。")
        return 0
    journal = apply_plan(env, plan)
    print_steps(journal["steps"])
    failed = any(step["status"] != "done" for step in journal["steps"])
    print("batch=%s" % journal["batch"])
    print("journal=%s" % env.show(env.state_dir / journal["batch"] / "journal.json"))
    print("undo=python3 %s undo --batch %s --apply" % (env.show(Path(__file__).resolve()), journal["batch"]))
    return 1 if failed else 0


def command_journal(args: argparse.Namespace) -> int:
    batches = list_batches(resolve_env(args))
    if not batches:
        print("还没有整理记录。")
    for batch in batches:
        state = "已撤销" if batch["undone_at"] else "已执行"
        print("%s  %s  %s  %d 步完成%s" % (
            batch["batch"], batch["created_at"], state, batch["done"],
            "，%d 步失败" % batch["failed"] if batch["failed"] else ""))
    return 0


def command_undo(args: argparse.Namespace) -> int:
    env = resolve_env(args)
    batch = args.batch or next((item["batch"] for item in list_batches(env) if not item["undone_at"]), "")
    if not batch:
        print("error: 没有可撤销的整理记录", file=sys.stderr)
        return 1
    try:
        result = undo_batch(env, batch, args.apply)
    except TidyError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    print("撤销 %s%s：" % (batch, "" if args.apply else "（未执行）"))
    print_steps(result["steps"])
    if not args.apply:
        print("确认后加 --apply 执行。")
        return 0
    return 0 if result["undone"] else 1


# ---------------------------------------------------------------------------
# Self test on a throwaway home directory
# ---------------------------------------------------------------------------


def build_fixture(home: Path) -> None:
    def write(relative: str, text: str) -> Path:
        path = home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def skill(relative: str, name: str, version: str = "0.1.0", description: str = "") -> Path:
        description = description or "Fixture skill %s used by the harness self test." % name
        write(relative + "/SKILL.md", "---\nname: %s\ndescription: %s\nmetadata:\n  version: \"%s\"\n---\n\n# %s\n"
              % (name, description, version, name))
        return home / relative

    agents = home / ".agents"
    references = "%s/.agents/references" % home
    write(".agents/AGENTS.md",
          "---\nversion: \"0.2.0\"\n---\n\n# Rules\n\n## Intake\n\n"
          "- `01` **First**：do the first thing.\n- `02` **Second**：read `%s/guide.md`.\n"
          "- `02` **Again**：duplicate number.\n- `04` **Route**：read `%s/missing.md`.\n" % (references, references))
    write(".agents/references/guide.md", "# Guide\n\n- `ENG-01` **One**：first.\n- `ENG-01` **Two**：duplicate.\n")
    write(".agents/references/orphan.md", "# Orphan\n\n- `ORP-01` **Lonely**：never routed.\n")
    write(".agents/CHANGELOG.md", "# Changelog\n\n## 0.1.0 — 2026-01-01\n\n- start\n")
    (home / ".claude").mkdir()
    os.symlink("../.agents/AGENTS.md", home / ".claude" / "CLAUDE.md")
    (home / ".codex").mkdir()
    write(".openclaw/workspace/AGENTS.md",
          "local notes\n<!-- source: %s sha256: %s -->\n" % (agents / "AGENTS.md", "0" * 64))

    sources = home / "repo" / "skills"
    beta = skill("repo/skills/beta-skill", "lov-beta", "0.3.0")
    write("repo/skills/beta-skill/skill.yaml", "schema: skill-manifest/v1\nversion: \"0.2.0\"\n")
    write("repo/skills/beta-skill/README.md", "# beta\n")
    skill("repo/skills/delta-skill", "lov-delta", "0.1.0")
    skill("repo/skills/epsilon-skill", "lov-epsilon")
    skill("repo/skills/zeta-skill", "lov-zeta")
    (sources / "empty-skill").mkdir()
    write("repo/catalog/skills.yaml",
          "version: 1\nskills:\n"
          "  - name: beta\n    runtime_name: lov-beta\n    repo: studio/beta-skill\n    paid: false\n    version: \"0.2.0\"\n"
          "  - name: delta\n    runtime_name: lov-delta\n    repo: studio/delta-skill\n    paid: true\n    version: \"0.4.0\"\n"
          "  - name: gamma\n    runtime_name: lov-gamma\n    repo: studio/gamma-skill\n    paid: false\n    version: \"1.0.0\"\n")

    hub = agents / "skills"
    skill(".agents/skills/alpha", "alpha")
    skill(".agents/skills/solo", "solo")
    skill(".agents/skills/twin-a", "twin")
    skill(".agents/skills/twin-b", "twin")
    skill(".agents/skills/Bad Name", "Bad Name")
    write(".agents/skills/nofront/SKILL.md", "# no frontmatter here\n")
    (hub / "hollow").mkdir()
    write(".agents/skills/junk.zip", "not a skill")
    os.symlink(str(beta), hub / "lov-beta")
    os.symlink(str(sources / "epsilon-skill"), hub / "lov-epsilon")
    os.symlink("missing-target", hub / "ghost")
    claude = home / ".claude" / "skills"
    claude.mkdir()
    os.symlink("../../.agents/skills/alpha", claude / "alpha")
    os.symlink("../../.agents/skills/alpha", claude / "alpha-alias")
    os.symlink(str(beta), claude / "lov-beta")
    os.symlink(str(sources / "zeta-skill"), claude / "lov-zeta")
    os.symlink("../../.agents/skills/lov-epsilon", claude / "lov-epsilon")
    os.symlink("../../.agents/skills/gone", claude / "gone")
    for name in ("twin-a", "twin-b"):
        os.symlink("../../.agents/skills/" + name, claude / name)
    codex = home / ".codex" / "skills"
    codex.mkdir()
    os.symlink(str(claude / "alpha"), codex / "alpha")
    skill(".codex/skills/builtin", "builtin")
    (home / ".lovstudio" / "skills").mkdir(parents=True)
    write(".lovstudio/skills/notes.txt", "not a host")

    if git(str(home), "--version")[0] == 0:
        identity = ["-c", "user.name=selftest", "-c", "user.email=selftest@example.invalid",
                    "-c", "commit.gpgsign=false"]
        git(str(beta), "init", "-q")
        git(str(beta), "add", "-A")
        git(str(beta), *identity, "commit", "-qm", "init")
        write("repo/skills/beta-skill/NOTES.md", "uncommitted\n")


def command_selftest(args: argparse.Namespace) -> int:
    failures: List[str] = []

    def check(label: str, condition: bool) -> None:
        print("%s %s" % ("ok  " if condition else "FAIL", label))
        if not condition:
            failures.append(label)

    def request(base: str, path: str, token: str = "", payload: Any = None) -> Tuple[int, Any]:
        headers = {"X-Lov-Token": token} if token else {}
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        try:
            with urllib.request.urlopen(urllib.request.Request(base + path, data=data, headers=headers), timeout=30) as reply:
                body = reply.read().decode("utf-8")
                return reply.status, json.loads(body) if "json" in reply.headers.get("Content-Type", "") else body
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8") or "{}")

    with tempfile.TemporaryDirectory(prefix="lov-harness-selftest-") as temporary:
        home = Path(os.path.realpath(temporary))
        build_fixture(home)
        options = argparse.Namespace(
            home=str(home), agents_home=None, source_root=str(home / "repo" / "skills"),
            catalog=str(home / "repo" / "catalog" / "skills.yaml"), state_dir=None,
            profile=str(home / "no-profile.json"), no_git=False,
        )
        env = resolve_env(options)
        snapshot = build_snapshot(env)
        codes = Counter(item["code"] for item in snapshot["findings"])
        has_git = git(str(home), "--version")[0] == 0

        def one(code: str, path_part: str = "") -> Dict[str, Any]:
            return next(item for item in snapshot["findings"] if item["code"] == code and path_part in item["path"])

        expected = [
            "PRM-RULE-DUP", "PRM-RULE-GAP", "PRM-PATH-MISSING", "PRM-REF-UNROUTED", "PRM-VERSION-DRIFT",
            "PRM-HOST-UNBOUND", "PRM-HOST-STALE", "SKL-BROKEN-LINK", "SKL-STRAY", "SKL-NO-SKILL-MD",
            "SKL-FRONTMATTER", "SKL-NAME-INVALID", "SKL-ALIAS", "SKL-DUP-NAME", "SKL-LINK-ABS",
            "SKL-LINK-CHAIN", "SKL-NOT-SHARED", "SKL-HOST-COPY", "SKL-HUB-UNLINKED", "STU-NO-SKILL-MD",
            "STU-NOT-INSTALLED", "STU-NO-README",
        ]
        if yaml is not None:
            expected += ["STU-VERSION-DRIFT", "STU-CATALOG-BEHIND", "STU-CATALOG-AHEAD", "STU-UNLISTED",
                         "STU-CATALOG-NO-SOURCE"]
        if has_git:
            expected += ["STU-DIRTY", "STU-NO-REMOTE", "STU-NOT-REPO"]
        for code in expected:
            check("scan reports " + code, codes[code] > 0)
        check("rule duplicates count root and reference", codes["PRM-RULE-DUP"] == 2)
        check("paths are shown relative to home", str(home) not in json.dumps(snapshot))
        check("non-skill folder is not a host", all(host["id"] != "lovstudio" for host in snapshot["skills"]["hosts"]))
        check("claude is bound to the root prompt",
              any(host["host"] == "claude" and host["state"] == "linked" for host in snapshot["prompt"]["hosts"]))
        check("report renders", "待处理" in render_report(snapshot, None, None, 5))

        def done(journal: Dict[str, Any]) -> bool:
            return bool(journal["steps"]) and all(step["status"] == "done" for step in journal["steps"])

        chain = {"op": "fix", "id": one("SKL-LINK-CHAIN")["id"]}
        ops = [{"op": "fix", "id": one(code, part)["id"]} for code, part in (
            ("SKL-BROKEN-LINK", "ghost"), ("SKL-LINK-ABS", ""), ("SKL-NOT-SHARED", ""), ("SKL-STRAY", ""),
            ("SKL-NO-SKILL-MD", "hollow"), ("PRM-HOST-UNBOUND", ".codex"))]
        ops += [chain, {"op": "link", "entry": "solo", "host": "codex"}]
        try:
            plan_ops(env, snapshot, [chain, {"op": "disable", "entry": "alpha"}])
            check("operations touching the same path are refused", False)
        except TidyError:
            check("operations touching the same path are refused", True)
        plan = plan_ops(env, snapshot, ops)
        check("plan does not touch the filesystem", os.path.islink(home / ".agents/skills/ghost"))
        check("every step applied", done(apply_plan(env, plan)))
        check("broken link removed", not os.path.lexists(home / ".agents/skills/ghost"))
        check("absolute link became relative",
              os.readlink(home / ".claude/skills/lov-beta") == "../../.agents/skills/lov-beta")
        check("link through another host became relative",
              os.readlink(home / ".codex/skills/alpha") == "../../.agents/skills/alpha")
        check("direct source link adopted into the shared directory",
              os.readlink(home / ".claude/skills/lov-zeta") == "../../.agents/skills/lov-zeta"
              and os.path.realpath(home / ".agents/skills/lov-zeta") == str(home / "repo/skills/zeta-skill"))
        check("stray file quarantined",
              os.path.isfile(env.state_dir / plan["batch"] / "quarantine" / "junk.zip")
              and not os.path.lexists(home / ".agents/skills/junk.zip"))
        check("host prompt linked",
              os.path.realpath(home / ".codex/AGENTS.md") == os.path.realpath(home / ".agents/AGENTS.md"))
        check("link installs a shared skill into a host",
              os.readlink(home / ".codex/skills/solo") == "../../.agents/skills/solo")
        after = Counter(item["code"] for item in build_snapshot(env)["findings"])
        check("fixed findings are gone",
              not after["SKL-LINK-ABS"] and not after["SKL-STRAY"] and not after["PRM-HOST-UNBOUND"]
              and not after["SKL-LINK-CHAIN"] and not after["SKL-NOT-SHARED"])

        disable = apply_plan(env, plan_ops(env, build_snapshot(env), [{"op": "disable", "entry": "alpha"}]))
        check("disable moved the skill and removed host links",
              done(disable) and os.path.isfile(home / ".agents/skills-disabled/alpha/SKILL.md")
              and not os.path.lexists(home / ".claude/skills/alpha")
              and not os.path.lexists(home / ".claude/skills/alpha-alias")
              and not os.path.lexists(home / ".codex/skills/alpha"))
        enable = apply_plan(env, plan_ops(env, build_snapshot(env), [{"op": "enable", "entry": "alpha"}]))
        check("enable restores the skill and its host links",
              done(enable) and os.path.isfile(home / ".agents/skills/alpha/SKILL.md")
              and os.readlink(home / ".claude/skills/alpha") == "../../.agents/skills/alpha"
              and os.readlink(home / ".codex/skills/alpha") == "../../.agents/skills/alpha")
        for label, journal in (("enable", enable), ("disable", disable), ("first", plan)):
            check("undo of the %s batch succeeds" % label, undo_batch(env, journal["batch"], apply=True)["undone"])
        check("undo restores the original layout",
              os.readlink(home / ".agents/skills/ghost") == "missing-target"
              and os.path.isabs(os.readlink(home / ".claude/skills/lov-beta"))
              and os.path.isabs(os.readlink(home / ".codex/skills/alpha"))
              and os.path.isfile(home / ".agents/skills/junk.zip")
              and os.path.isdir(home / ".agents/skills/hollow")
              and not os.path.lexists(home / ".codex/AGENTS.md")
              and not os.path.lexists(home / ".codex/skills/solo")
              and not os.path.lexists(home / ".agents/skills/lov-zeta")
              and os.path.isfile(home / ".agents/skills/alpha/SKILL.md"))
        try:
            undo_batch(env, plan["batch"], apply=True)
            check("a batch cannot be undone twice", False)
        except TidyError:
            check("a batch cannot be undone twice", True)
        refusal = check_step(env, {"do": "unlink", "path": env.show(home / ".agents/skills/alpha")})
        check("real directories are never unlinked", bool(refusal))
        outside = check_step(env, {"do": "move", "src": env.show(home / "repo/skills/beta-skill"),
                                   "dst": env.show(home / ".agents/skills-disabled/beta-skill")})
        check("sources cannot be moved by the tidy engine", bool(outside))

        if ASSET_ROOT.is_dir():
            page = export_html(snapshot)
            check("export embeds the snapshot and inlines assets",
                  'id="lov-snapshot"' in page and "dashboard.js" not in page and "__LOV_TOKEN__" not in page)
            for allow_write in (False, True):
                dashboard = Dashboard(options, allow_write)
                server = make_server(dashboard, "127.0.0.1", 0)
                threading.Thread(target=server.serve_forever, daemon=True).start()
                base = "http://127.0.0.1:%d" % server.server_address[1]
                mode = "write" if allow_write else "read-only"
                try:
                    status, body = request(base, "/")
                    check("%s: page served with its token" % mode, status == 200 and dashboard.token in body)
                    check("%s: api rejects a missing token" % mode, request(base, "/api/snapshot")[0] == 403)
                    status, body = request(base, "/api/snapshot", dashboard.token)
                    check("%s: api returns the snapshot" % mode,
                          status == 200 and body["meta"]["write_enabled"] is allow_write)
                    status, body = request(base, "/api/file?path=~/.agents/AGENTS.md", dashboard.token)
                    check("%s: prompt file is readable" % mode, status == 200 and "Rules" in body["text"])
                    check("%s: unrelated file is refused" % mode,
                          request(base, "/api/file?path=~/.ssh/id_rsa", dashboard.token)[0] == 403)
                    broken = next(item for item in body_findings(request(base, "/api/snapshot", dashboard.token))
                                  if item["code"] == "SKL-BROKEN-LINK" and "ghost" in item["path"])
                    status, planned = request(base, "/api/plan", dashboard.token,
                                              {"ops": [{"op": "fix", "id": broken["id"]}]})
                    check("%s: plan previews one step" % mode, status == 200 and len(planned["steps"]) == 1)
                    status, applied = request(base, "/api/apply", dashboard.token, {"batch": planned["batch"]})
                    if allow_write:
                        check("write: apply runs the plan",
                              status == 200 and not os.path.lexists(home / ".agents/skills/ghost"))
                        status, undone = request(base, "/api/undo", dashboard.token, {"batch": planned["batch"]})
                        check("write: undo restores the link",
                              status == 200 and os.path.islink(home / ".agents/skills/ghost"))
                    else:
                        check("read-only: apply is refused",
                              status == 403 and os.path.islink(home / ".agents/skills/ghost"))
                finally:
                    server.shutdown()
                    server.server_close()
        else:
            check("dashboard assets exist", False)

    print("selftest=%s (%d failed)" % ("FAILED" if failures else "PASSED", len(failures)))
    return 1 if failures else 0


def body_findings(reply: Tuple[int, Any]) -> List[Dict[str, Any]]:
    return reply[1]["findings"] if reply[0] == 200 else []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--home", help="把这个目录当作家目录扫描（默认当前用户的家目录）")
    common.add_argument("--agents-home", help="共享 Agent 配置目录，默认 ~/.agents")
    common.add_argument("--source-root", help="Skill 源码根目录（每个子目录是一个 Skill 仓库）")
    common.add_argument("--catalog", help="目录文件 skills.yaml 的路径")
    common.add_argument("--state-dir", help="整理记录与隔离文件的存放目录")
    common.add_argument("--profile", help="共享 Profile JSON 的路径")
    common.add_argument("--no-git", action="store_true", help="跳过源码仓库的 Git 状态检查")

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    scan = commands.add_parser("scan", parents=[common], help="输出完整快照 JSON")
    scan.add_argument("--out", help="写入文件而不是标准输出")
    scan.add_argument("--pretty", action="store_true")
    scan.set_defaults(run=command_scan)

    report = commands.add_parser("report", parents=[common], help="输出可读的 Markdown 摘要")
    report.add_argument("--format", choices=("md", "json"), default="md")
    report.add_argument("--area", choices=tuple(AREA_LABELS))
    report.add_argument("--severity", choices=SEVERITIES, help="只显示这个级别及更严重的问题")
    report.add_argument("--limit", type=int, default=12, help="每个区域最多列出的问题数")
    report.set_defaults(run=command_report)

    serve = commands.add_parser("serve", parents=[common], help="启动本地 dashboard")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=DEFAULT_PORT)
    serve.add_argument("--open", action="store_true", help="启动后在默认浏览器打开")
    serve.add_argument("--allow-write", action="store_true", help="允许在界面里执行整理与撤销")
    serve.add_argument("--verbose", action="store_true")
    serve.set_defaults(run=command_serve)

    export = commands.add_parser("export", parents=[common], help="导出只读的单文件 dashboard")
    export.add_argument("--out", required=True)
    export.set_defaults(run=command_export)

    tidy = commands.add_parser("tidy", parents=[common], help="预览或执行整理（默认只预览）")
    tidy.add_argument("--fix", action="append", default=[], metavar="ID", help="按问题 ID 整理，可重复")
    tidy.add_argument("--fix-code", action="append", default=[], metavar="CODE", help="整理某一类全部可整理的问题")
    tidy.add_argument("--disable", action="append", default=[], metavar="ENTRY", help="停用共享目录里的 Skill")
    tidy.add_argument("--enable", action="append", default=[], metavar="ENTRY", help="重新启用已停用的 Skill")
    tidy.add_argument("--link", action="append", default=[], metavar="ENTRY", help="把共享目录里的 Skill 链接进 --host")
    tidy.add_argument("--unlink", action="append", default=[], metavar="ENTRY", help="移除 --host 里的 Skill 链接")
    tidy.add_argument("--host", help="--link / --unlink 的目标宿主，例如 claude")
    tidy.add_argument("--apply", action="store_true", help="确认执行；不加则只预览")
    tidy.set_defaults(run=command_tidy)

    journal = commands.add_parser("journal", parents=[common], help="列出整理记录")
    journal.set_defaults(run=command_journal)

    undo = commands.add_parser("undo", parents=[common], help="撤销一次整理（默认最近一次）")
    undo.add_argument("--batch")
    undo.add_argument("--apply", action="store_true", help="确认执行；不加则只预览")
    undo.set_defaults(run=command_undo)

    selftest = commands.add_parser("selftest", help="在临时目录上验证扫描、整理、撤销与 dashboard 接口")
    selftest.set_defaults(run=command_selftest)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.run(args)


if __name__ == "__main__":
    raise SystemExit(main())
