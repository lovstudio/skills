#!/usr/bin/env python3
"""Locate local files that are evidenced by earlier AI conversations."""

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
from typing import Any, Iterable, Optional


INDEX_VERSION = 1
MAX_MESSAGE_CHARS = 800
MAX_MESSAGES = 240
MAX_MENTIONS = 400
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "target"}

KIND_EXTENSIONS = {
    "image": {".avif", ".gif", ".heic", ".jpeg", ".jpg", ".png", ".svg", ".webp"},
    "document": {".doc", ".docx", ".epub", ".html", ".md", ".pdf", ".ppt", ".pptx", ".rtf", ".txt", ".xls", ".xlsx"},
    "archive": {".7z", ".dmg", ".gz", ".rar", ".tar", ".tgz", ".zip"},
    "audio": {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".wav"},
    "video": {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".webm"},
    "code": {".c", ".cpp", ".css", ".go", ".html", ".java", ".js", ".json", ".jsx", ".kt", ".m", ".mm", ".py", ".rs", ".sh", ".swift", ".toml", ".ts", ".tsx", ".yaml", ".yml"},
}

ALIASES = [
    {"图片", "照片", "头像", "形象照", "p图", "修图", "磨皮", "image", "images", "photo", "photos", "picture", "portrait", "avatar"},
    {"文档", "文章", "报告", "方案", "稿件", "document", "doc", "report", "article"},
    {"幻灯片", "演示", "ppt", "pptx", "slides", "deck"},
    {"视频", "影片", "录像", "video", "movie", "recording"},
    {"音频", "录音", "声音", "audio", "voice", "podcast"},
    {"压缩包", "归档", "安装包", "archive", "zip", "dmg", "package"},
]

AGENT_STOPWORDS = {
    "ai", "codex", "chatgpt", "claude", "yoda", "agent", "助手", "对话", "聊天",
    "之前", "以前", "上次", "给我", "帮我", "生成", "做的", "文件", "找到", "找一下",
}

PREFILTER_GENERIC_ALIASES = {
    "图片", "照片", "文件", "image", "images", "photo", "photos", "picture", "doc", "document",
}

OUTPUT_MARKERS = ("成品", "最终", "下载", "保存", "归档", "交付", "输出", "output", "saved", "download", "final")


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower()
    return re.sub(r"[\s\W_]+", "", value, flags=re.UNICODE)


def query_terms(query: str) -> tuple[list[str], list[str]]:
    exact: list[str] = []
    for part in re.findall(r"[\u3400-\u9fff]+|[A-Za-z0-9_.-]+", unicodedata.normalize("NFKC", query).lower()):
        if part in AGENT_STOPWORDS:
            continue
        if re.fullmatch(r"[a-z]", part) and part != "p":
            continue
        exact.append(part)

    compact_query = normalize_text(query)
    alias_terms: set[str] = set()
    seeds = set(exact)
    if "p" in seeds and any(word in compact_query for word in ("图", "头像", "照片")):
        seeds.add("p图")
    for group in ALIASES:
        if any(normalize_text(seed) in {normalize_text(item) for item in group} for seed in seeds):
            alias_terms.update(group)

    return list(dict.fromkeys(exact)), sorted(alias_terms - set(exact))


def infer_kind(query: str, requested: str) -> str:
    if requested != "auto":
        return requested
    compact = normalize_text(query)
    mapping = [
        ("image", ALIASES[0]),
        ("document", ALIASES[1] | ALIASES[2]),
        ("video", ALIASES[3]),
        ("audio", ALIASES[4]),
        ("archive", ALIASES[5]),
    ]
    for kind, terms in mapping:
        if any(normalize_text(term) in compact for term in terms):
            return kind
    return "any"


def extract_content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict):
            value = block.get("text") or block.get("content")
            if isinstance(value, str):
                parts.append(value)
    return "\n".join(parts)


def clean_path(raw: str, home: Path) -> Optional[str]:
    value = raw.strip().replace("\\/", "/")
    value = value.rstrip(".,;:，。；：!?！？)]}")
    if value.startswith("$HOME/"):
        value = str(home / value[6:])
    elif value.startswith("~/"):
        value = str(home / value[2:])
    if not value.startswith("/"):
        return None
    if value.startswith("//") or "://" in value:
        return None
    return os.path.normpath(value)


def extract_paths(text: str, home: Path) -> list[str]:
    patterns = [
        r"<(/[^>\n]+)>",
        r"@(/[^\s\"'<>`]+)",
        r"\"(/[^\"\n]+)\"",
        r"'(/[^'\n]+)'",
        r"(?<![\w:])(/(?:Users|Volumes|private|var|tmp|home|Library|Applications)/[^\s<>\"'`]+)",
        r"(?<![\w])((?:\$HOME|~)/[^\s<>\"'`]+)",
    ]
    found: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            value = clean_path(match.group(1), home)
            if value and value not in found:
                found.append(value)
    return found


def short_evidence(text: str, path: str, limit: int = 320) -> str:
    single = re.sub(r"\s+", " ", text).strip()
    pos = single.find(path)
    if pos < 0:
        pos = 0
    start = max(0, pos - 90)
    excerpt = single[start : start + limit]
    if start:
        excerpt = "…" + excerpt
    if start + limit < len(single):
        excerpt += "…"
    return excerpt


def parse_transcript(path: Path, home: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "source": str(path),
        "session_id": "",
        "cwd": "",
        "timestamp": "",
        "messages": [],
        "mentions": [],
    }
    messages: list[dict[str, str]] = []
    mentions: list[dict[str, str]] = []

    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    item = json.loads(line)
                except (json.JSONDecodeError, TypeError):
                    continue
                timestamp = item.get("timestamp")
                if isinstance(timestamp, str) and not record["timestamp"]:
                    record["timestamp"] = timestamp

                item_type = item.get("type")
                payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
                if item_type == "session_meta":
                    record["session_id"] = str(payload.get("id") or record["session_id"])
                    record["cwd"] = str(payload.get("cwd") or record["cwd"])
                    continue

                role = ""
                phase = ""
                text = ""
                if item_type == "response_item" and payload.get("type") == "message":
                    role = str(payload.get("role") or "")
                    if role not in {"user", "assistant"}:
                        continue
                    phase = str(payload.get("phase") or "")
                    text = extract_content_text(payload.get("content"))
                elif item_type in {"user", "assistant"} and isinstance(item.get("message"), dict):
                    message = item["message"]
                    role = str(message.get("role") or item_type)
                    text = extract_content_text(message.get("content"))
                    if not record["session_id"]:
                        record["session_id"] = str(item.get("sessionId") or item.get("session_id") or "")
                    if not record["cwd"]:
                        record["cwd"] = str(item.get("cwd") or "")
                elif item_type == "response_item" and payload.get("type") in {"function_call", "custom_tool_call"}:
                    role = "tool"
                    text = str(payload.get("arguments") or payload.get("input") or "")
                else:
                    continue

                if not text:
                    continue
                if role in {"user", "assistant"} and len(messages) < MAX_MESSAGES:
                    messages.append({"role": role, "text": text[:MAX_MESSAGE_CHARS]})
                for local_path in extract_paths(text, home):
                    if len(mentions) >= MAX_MENTIONS:
                        break
                    mentions.append({
                        "path": local_path,
                        "role": role,
                        "phase": phase,
                        "evidence": short_evidence(text, local_path),
                    })
    except OSError as exc:
        record["error"] = str(exc)

    if not record["session_id"]:
        uuid_match = re.search(r"([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})", path.name, re.I)
        if uuid_match:
            record["session_id"] = uuid_match.group(1)
    record["messages"] = messages
    record["mentions"] = mentions
    return record


def default_transcript_roots(home: Path) -> list[Path]:
    codex_home = Path(os.environ.get("CODEX_HOME", home / ".codex")).expanduser()
    roots = [codex_home / "sessions", codex_home / "archived_sessions", home / ".claude" / "projects"]
    return [root for root in roots if root.exists()]


def default_cache_path(home: Path) -> Path:
    if os.environ.get("XDG_CACHE_HOME"):
        return Path(os.environ["XDG_CACHE_HOME"]) / "lov-search-file" / "index-v1.json"
    if sys.platform == "darwin":
        return home / "Library" / "Caches" / "lov-search-file" / "index-v1.json"
    return home / ".cache" / "lov-search-file" / "index-v1.json"


def load_cache(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("version") == INDEX_VERSION and isinstance(data.get("files"), dict):
            return data
    except (OSError, json.JSONDecodeError, AttributeError):
        pass
    return {"version": INDEX_VERSION, "files": {}}


def save_cache(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def prefilter_terms(exact: list[str], aliases: list[str]) -> list[str]:
    terms: list[str] = []
    prefer_cjk = any(re.search(r"[\u3400-\u9fff]", value) for value in exact)
    for value in exact:
        compact = normalize_text(value)
        if len(compact) < 2:
            continue
        if compact in AGENT_STOPWORDS:
            continue
        terms.append(value)
    for value in aliases:
        compact = normalize_text(value)
        if len(compact) < 2 or compact in AGENT_STOPWORDS:
            continue
        if prefer_cjk and not re.search(r"[\u3400-\u9fff]", value):
            continue
        if value.lower() in PREFILTER_GENERIC_ALIASES:
            continue
        terms.append(value)
    return list(dict.fromkeys(terms))[:40]


def find_candidate_transcripts(roots: list[Path], terms: list[str], session_id: str, maximum: int) -> list[Path]:
    candidates: set[Path] = set()
    if session_id:
        for root in roots:
            candidates.update(root.rglob(f"*{session_id}*.jsonl"))
        if candidates:
            return sorted(candidates, key=lambda path: path.stat().st_mtime_ns, reverse=True)[:maximum]

    rg = shutil.which("rg")
    if rg and terms:
        term_pattern = "|".join(re.escape(term) for term in terms)
        pattern = rf'"role"\s*:\s*"(?:user|assistant)".*(?:{term_pattern})'
        command = [rg, "--count-matches", "--no-messages", "-i", "-g", "*.jsonl", "-e", pattern, *map(str, roots)]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
            counted: list[tuple[int, Path]] = []
            for line in result.stdout.splitlines():
                raw_path, separator, raw_count = line.rpartition(":")
                if not separator or not raw_count.isdigit():
                    continue
                counted.append((int(raw_count), Path(raw_path)))
            counted.sort(key=lambda item: item[0], reverse=True)
            candidates.update(path for _, path in counted[:maximum])
        except (OSError, subprocess.TimeoutExpired):
            pass

    if not candidates:
        for root in roots:
            candidates.update(root.rglob("*.jsonl"))

    def modified(path: Path) -> int:
        try:
            return path.stat().st_mtime_ns
        except OSError:
            return 0

    return sorted(candidates, key=modified, reverse=True)[:maximum]


def record_search_text(record: dict[str, Any]) -> str:
    parts = [record.get("session_id", ""), record.get("cwd", "")]
    parts.extend(message.get("text", "") for message in record.get("messages", []))
    parts.extend(mention.get("path", "") for mention in record.get("mentions", []))
    return normalize_text("\n".join(parts))


def relevance_score(record: dict[str, Any], query: str, exact: list[str], aliases: list[str], session_id: str) -> int:
    haystack = record_search_text(record)
    score = 0
    compact_query = normalize_text(query)
    if compact_query and compact_query in haystack:
        score += 40
    for term in exact:
        compact = normalize_text(term)
        if compact and compact in haystack:
            score += 22
    alias_hits = sum(1 for term in aliases if normalize_text(term) in haystack)
    score += min(alias_hits, 4) * 8
    if session_id and session_id in str(record.get("session_id", "")):
        score += 100
    return score


def kind_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    for kind, extensions in KIND_EXTENSIONS.items():
        if suffix in extensions:
            return kind
    return "other"


def path_matches_kind(path: Path, kind: str) -> bool:
    return kind in {"any", "auto"} or path.suffix.lower() in KIND_EXTENSIONS.get(kind, set())


def durability(path: str, home: Path) -> tuple[str, int]:
    normalized = path.replace("\\", "/")
    if normalized.startswith(("/tmp/", "/private/tmp/", "/var/folders/")):
        return "temporary", -45
    if "/output/" in normalized or "/outputs/" in normalized:
        return "project-output", 35
    if normalized.startswith(str(home / "Downloads")):
        return "downloads", 25
    if "/generated_images/" in normalized or "/visualizations/" in normalized:
        return "ai-cache", 5
    if normalized.startswith(str(home / "Documents")):
        return "documents", 20
    return "local", 10


def file_metadata(path: Path) -> dict[str, Any]:
    try:
        stat = path.stat()
        modified = dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.timezone.utc).astimezone().isoformat(timespec="seconds")
        return {"exists": True, "size": stat.st_size, "modified": modified}
    except OSError:
        return {"exists": False, "size": None, "modified": None}


def add_candidate(
    candidates: dict[str, dict[str, Any]],
    local_path: str,
    record: Optional[dict[str, Any]],
    base_score: int,
    role: str,
    phase: str,
    evidence: str,
    origin: str,
    home: Path,
    kind: str,
    exact: list[str],
    aliases: list[str],
) -> None:
    path = Path(local_path).expanduser()
    if not path_matches_kind(path, kind):
        return
    metadata = file_metadata(path)
    durability_name, durability_score = durability(str(path), home)
    score = base_score + durability_score + (100 if metadata["exists"] else -70)
    score += {"assistant": 45, "user": -5, "tool": 8, "derived": 12, "filename": 5}.get(role, 0)
    if phase == "final_answer":
        score += 25
    if any(marker in evidence.lower() for marker in OUTPUT_MARKERS):
        score += 20
    name_haystack = normalize_text(path.name)
    score += sum(12 for term in exact if normalize_text(term) and normalize_text(term) in name_haystack)
    score += min(sum(1 for term in aliases if normalize_text(term) in name_haystack), 2) * 5

    key = os.path.normcase(os.path.normpath(str(path)))
    item = {
        "path": str(path),
        **metadata,
        "kind": kind_for_path(path),
        "durability": durability_name,
        "score": score,
        "origin": origin,
        "session_id": record.get("session_id", "") if record else "",
        "conversation_source": record.get("source", "") if record else "",
        "cwd": record.get("cwd", "") if record else "",
        "evidence": [evidence] if evidence else [],
    }
    previous = candidates.get(key)
    if previous is None:
        candidates[key] = item
        return
    if score > previous["score"]:
        previous.update({key: value for key, value in item.items() if key != "evidence"})
    for excerpt in item["evidence"]:
        if excerpt not in previous["evidence"] and len(previous["evidence"]) < 3:
            previous["evidence"].append(excerpt)


def iter_files(root: Path, maximum: int = 300) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    count = 0
    for current, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS and not name.startswith(".git")]
        for name in files:
            yield Path(current) / name
            count += 1
            if count >= maximum:
                return


def derived_roots(record: dict[str, Any], home: Path) -> list[tuple[Path, str]]:
    roots: list[tuple[Path, str]] = []
    session_id = record.get("session_id")
    codex_home = Path(os.environ.get("CODEX_HOME", home / ".codex")).expanduser()
    if session_id:
        roots.append((codex_home / "generated_images" / session_id, "session-generated-cache"))
    cwd = record.get("cwd")
    if cwd and Path(cwd).is_dir():
        roots.extend((Path(cwd) / name, f"session-{name}") for name in ("output", "outputs"))
    return roots


def format_size(size: Optional[int]) -> str:
    if size is None:
        return "-"
    value = float(size)
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return str(size)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Find local files linked to earlier AI conversations.")
    parser.add_argument("query", help="Conversation topic, remembered phrase, filename, or artifact description.")
    parser.add_argument("--kind", choices=["auto", "any", *KIND_EXTENSIONS], default="auto")
    parser.add_argument("--session-id", default="", help="Prefer one known conversation/session UUID.")
    parser.add_argument("--transcript-root", action="append", default=[], help="Additional transcript root; repeatable.")
    parser.add_argument("--root", action="append", default=[], help="Additional file root for filename fallback; repeatable.")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--max-transcripts", type=int, default=40)
    parser.add_argument("--refresh", action="store_true", help="Reparse matched transcripts even when cached.")
    parser.add_argument("--no-cache", action="store_true", help="Do not read or write the local transcript index.")
    parser.add_argument("--include-missing", action="store_true", help="Include paths mentioned in chat but no longer present.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    home = Path.home()
    exact, aliases = query_terms(args.query)
    kind = infer_kind(args.query, args.kind)
    roots = default_transcript_roots(home)
    roots.extend(Path(value).expanduser() for value in args.transcript_root)
    roots = list(dict.fromkeys(root.resolve() for root in roots if root.exists()))
    if not roots:
        print("No transcript roots found. Use --transcript-root PATH.", file=sys.stderr)
        return 2

    cache_path = default_cache_path(home)
    cache = {"version": INDEX_VERSION, "files": {}} if args.no_cache else load_cache(cache_path)
    candidate_paths = find_candidate_transcripts(roots, prefilter_terms(exact, aliases), args.session_id, args.max_transcripts)
    records: list[dict[str, Any]] = []
    parsed = 0
    cached = 0
    for transcript in candidate_paths:
        try:
            stat = transcript.stat()
        except OSError:
            continue
        key = str(transcript)
        entry = cache["files"].get(key)
        if (
            not args.refresh
            and entry
            and entry.get("mtime_ns") == stat.st_mtime_ns
            and entry.get("size") == stat.st_size
            and isinstance(entry.get("record"), dict)
        ):
            record = entry["record"]
            cached += 1
        else:
            record = parse_transcript(transcript, home)
            cache["files"][key] = {"mtime_ns": stat.st_mtime_ns, "size": stat.st_size, "record": record}
            parsed += 1
        records.append(record)
    if not args.no_cache:
        save_cache(cache_path, cache)

    ranked_records: list[tuple[int, dict[str, Any]]] = []
    for record in records:
        score = relevance_score(record, args.query, exact, aliases, args.session_id)
        if score > 0:
            ranked_records.append((score, record))
    ranked_records.sort(key=lambda item: item[0], reverse=True)

    candidates: dict[str, dict[str, Any]] = {}
    for session_score, record in ranked_records[:40]:
        for mention in record.get("mentions", []):
            add_candidate(
                candidates,
                mention["path"],
                record,
                session_score,
                mention.get("role", ""),
                mention.get("phase", ""),
                mention.get("evidence", ""),
                "conversation-mention",
                home,
                kind,
                exact,
                aliases,
            )
        for root, origin in derived_roots(record, home):
            if not root.exists():
                continue
            for local_file in iter_files(root, maximum=300):
                add_candidate(
                    candidates,
                    str(local_file),
                    record,
                    session_score,
                    "derived",
                    "",
                    f"由会话 {record.get('session_id', '')} 的存储目录推导",
                    origin,
                    home,
                    kind,
                    exact,
                    aliases,
                )

    for root_value in args.root:
        root = Path(root_value).expanduser()
        if not root.exists():
            continue
        for local_file in iter_files(root, maximum=5000):
            name_haystack = normalize_text(str(local_file))
            filename_score = sum(20 for term in exact if normalize_text(term) in name_haystack)
            filename_score += min(sum(1 for term in aliases if normalize_text(term) in name_haystack), 3) * 8
            if filename_score:
                add_candidate(
                    candidates,
                    str(local_file),
                    None,
                    filename_score,
                    "filename",
                    "",
                    f"文件名或父目录命中：{local_file.name}",
                    "filename-fallback",
                    home,
                    kind,
                    exact,
                    aliases,
                )

    hits = sorted(candidates.values(), key=lambda item: (item["exists"], item["score"]), reverse=True)
    if not args.include_missing:
        hits = [item for item in hits if item["exists"]]
    hits = hits[: max(1, args.limit)]
    result = {
        "query": args.query,
        "kind": kind,
        "hits": hits,
        "search": {
            "transcript_roots": [str(root) for root in roots],
            "matched_transcripts": len(candidate_paths),
            "parsed_transcripts": parsed,
            "cached_transcripts": cached,
            "cache_path": None if args.no_cache else str(cache_path),
        },
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"找到 {len(hits)} 个候选文件（类型：{kind}）")
        for index, hit in enumerate(hits, start=1):
            print(f"\n{index}. {hit['path']}")
            print(f"   状态：存在 | {format_size(hit['size'])} | {hit['durability']} | score={hit['score']}")
            if hit["session_id"]:
                print(f"   会话：{hit['session_id']}")
            if hit["evidence"]:
                print(f"   证据：{hit['evidence'][0]}")
        print(
            f"\n检索：{len(candidate_paths)} 个候选 transcript，"
            f"解析 {parsed}，缓存命中 {cached}。"
        )
    return 0 if hits else 1


if __name__ == "__main__":
    raise SystemExit(main())
