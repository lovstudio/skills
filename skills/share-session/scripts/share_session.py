#!/usr/bin/env python3
"""Convert an agent session transcript into a shareable Lovstudio hosted page URL.

Reads a session transcript (Claude Code JSONL, Yoda/JSON, file, or auto-detected
current session), normalizes it into the strict `yodaSessionShareUpload` shape
expected by POST /api/yoda/session-shares, then uploads it and returns the public
share URL. Pure standard library; no third-party packages.

Pipeline: resolve source -> normalize -> obtain Lovstudio token -> POST -> print URL.

Exit codes: 0 success, 1 invalid input / no source, 2 auth/IPC failure, 3 server
rejected the payload.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import gzip
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

# --- Contract constants (must mirror the web repo's strict schema) --------------
KIND = "yoda-session-share"
VERSION = 1
DEFAULT_BASE_URL = "https://lovstudio.ai"
AUTH_SCOPE = "yoda"
GZIP_THRESHOLD_BYTES = 1024 * 1024  # mirror the Yoda client's gzip gate
DISPLAY_LEVELS = ("hidden", "concise", "detailed", "verbose")

# The web schema is `.strict()`: extra fields -> 400 invalid_session_share.
# Keep this exactly aligned with app/api/yoda/session-shares/route.ts + session-share.ts.
ROLES = {"user", "assistant", "tool", "status"}
FORMATS = {"markdown", "code", "plain"}
MAX_CONTENT_LEN = 240_000
MAX_TITLE_LEN = 200
SKILL_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CASE_ID_RE = SKILL_ID_RE
PAID_SESSION_PRICING_RULE = "ceil(target-skill-price/10)"

# Host/runtime context can be stored inside a role="user" Codex message.  Role
# filtering alone is therefore insufficient: strip the known injected envelopes
# from both user and assistant visible text before a share payload is built.
METADATA_PATTERNS = [
    re.compile(r"<oai-mem-citation\b[^>]*>[\s\S]*?</oai-mem-citation>", re.I),
    re.compile(
        r"(?im)^# AGENTS\.md instructions\s*\n"
        r"<INSTRUCTIONS\b[^>]*>[\s\S]*?</INSTRUCTIONS>\s*"
    ),
    re.compile(
        r"<permissions instructions\b[^>]*>[\s\S]*?</permissions instructions>",
        re.I,
    ),
    *[
        re.compile(rf"<{tag}\b[^>]*>[\s\S]*?</{tag}>", re.I)
        for tag in (
            "in-app-browser-context",
            "recommended_plugins",
            "environment_context",
            "skill",
            "app-context",
            "skills_instructions",
            "collaboration_mode",
            "apps_instructions",
            "plugins_instructions",
            # Claude Code envelopes that can ride along inside a real message.
            "system-reminder",
            "task-notification",
        )
    ],
]

# Claude Code folds skill bodies and system notifications into role="user"
# messages as PLAIN TEXT with no enclosing tag, so every tag-based pattern
# above misses them.  Observed leaking 25% of a share payload as two verbatim
# SKILL.md bodies.  None of these is user speech, so drop the block whole.
HOST_BLOCK_DROP_RE = re.compile(
    r"(?is)\A\s*(?:"
    r"Base directory for this skill:|"
    r"\[SYSTEM NOTIFICATION - NOT USER INPUT\]|"
    r"<task-notification\b|"
    r"<system-reminder\b"
    r")"
)

# A slash-command invocation is real user intent; keep the command, drop the
# envelope the host wrapped around it.
COMMAND_ENVELOPE_RE = re.compile(
    r"(?is)\A\s*<command-message>[^<]*</command-message>\s*"
    r"<command-name>\s*(/[\w.-]+)\s*</command-name>\s*"
    r"(?:<command-args>([\s\S]*?)</command-args>\s*)?\Z"
)

INTERNAL_CONTEXT_RESIDUE_RE = re.compile(
    r"(?im)^\s*(?:"
    r"# AGENTS\.md instructions\s*$|"
    r"Base directory for this skill:|"
    r"\[SYSTEM NOTIFICATION - NOT USER INPUT\]|"
    r"<(?:in-app-browser-context|recommended_plugins|environment_context|skill|"
    r"app-context|skills_instructions|collaboration_mode|apps_instructions|"
    r"plugins_instructions|instructions|system-reminder|task-notification|"
    r"command-message)\b|"
    r"<permissions instructions\b"
    r")"
)
PRIVATE_HOME_PATTERNS = (
    re.compile(r"/[U]sers/[^/\s]+"),
    re.compile(r"/home/[^/\s]+"),
    re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+"),
)
SECRET_REDACTIONS = (
    (re.compile(r"\bgh[opusr]_[A-Za-z0-9]{20,}\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"), "[REDACTED_API_KEY]"),
    (
        re.compile(r"\b(?:Bearer|Authorization:)\s+[A-Za-z0-9._~+/-]{12,}", re.I),
        "Authorization: [REDACTED_TOKEN]",
    ),
    (
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?"
            r"-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
        ),
        "[REDACTED_PRIVATE_KEY]",
    ),
)


class ShareError(Exception):
    """Raised for any failing step; carries an exit-code hint."""

    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


# --- Tokens / credentials ------------------------------------------------------
def load_access_token(args: argparse.Namespace) -> str:
    """Resolve a Lovstudio access token with the skill-creator precedence.

    Order: explicit --token > env LOVSTUDIO_ACCESS_TOKEN > stored local cache/cookie
    > refresh from a stored refresh token > device-flow login.
    """
    if args.token:
        return args.token
    for env in ("LOVSTUDIO_ACCESS_TOKEN", "YODA_ACCESS_TOKEN"):
        value = os.environ.get(env)
        if value and value.strip():
            return value.strip()

    cached = load_cached_token(args.profile_path)
    if cached:
        return cached

    refresh = load_refresh_token(args.profile_path)
    if refresh:
        try:
            return run_refresh(args.base_url, refresh, args.timeout, args.profile_path)
        except ShareError:
            # Fall through to a full device-flow sign-in rather than fail hard.
            pass

    return device_flow_signin(args)


def credential_store_path(profile_path: Optional[Path]) -> Path:
    """Where tokens are cached. Not part of durable profile records."""
    base = profile_path.parent if profile_path else Path.home() / ".lovstudio"
    return base / ".session-share-credentials.json"


def load_cached_token(profile_path: Optional[Path]) -> Optional[str]:
    path = credential_store_path(profile_path)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data.get("access_token")


def load_refresh_token(profile_path: Optional[Path]) -> Optional[str]:
    path = credential_store_path(profile_path)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data.get("refresh_token")


def save_credentials(profile_path: Optional[Path], access: str, refresh: Optional[str]) -> None:
    path = credential_store_path(profile_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {}
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    data["access_token"] = access
    if refresh:
        data["refresh_token"] = refresh
    try:
        path.write_text(json.dumps(data), encoding="utf-8")
        os.chmod(path, 0o600)
    except OSError:
        # Non-fatal: never let a cache write block the share.
        pass


def run_refresh(
    base_url: str,
    refresh_token: str,
    timeout: int,
    profile_path: Optional[Path] = None,
) -> str:
    resp = http_json(
        "POST", f"{base_url}/api/cli/auth/refresh",
        body={"refreshToken": refresh_token},
        jwt=None,
        timeout=timeout,
    )
    if "accessToken" not in resp:
        raise ShareError("Lovstudio refresh did not return an access token", 2)
    access = resp["accessToken"]
    save_credentials(profile_path, access, resp.get("refreshToken") or refresh_token)
    return access


def device_flow_signin(args: argparse.Namespace) -> str:
    """Interactive OAuth device flow: print a URL, poll until the user approves."""
    start = http_json(
        "POST", f"{args.base_url}/api/cli/auth/start",
        body={"clientName": "Yoda", "scope": AUTH_SCOPE},
        jwt=None,
        timeout=args.timeout,
    )
    if "verificationUri" not in start or "deviceCode" not in start:
        raise ShareError("Lovstudio device flow did not return a verification URI", 2)

    print("请在浏览器打开以下链接并登录授权：", file=sys.stderr)
    print(f"  {start['verificationUri']}", file=sys.stderr)
    if start.get("userCode"):
        print(f"  授权码：{start['userCode']}", file=sys.stderr)

    device_code = start["deviceCode"]
    interval = max(int(start.get("interval", 5)), 1)
    deadline = time.time() + int(start.get("expiresIn", 600))
    while time.time() < deadline:
        time.sleep(interval)
        try:
            poll = http_json(
                "POST", f"{args.base_url}/api/cli/auth/poll",
                body={"deviceCode": device_code},
                jwt=None,
                timeout=args.timeout,
            )
        except ShareError as exc:
            poll = getattr(exc, "payload", {}) or {}
        if poll.get("status") == "authenticated":
            access = poll["accessToken"]
            save_credentials(args.profile_path, access, poll.get("refreshToken"))
            return access
        error = poll.get("error", "")
        if error == "authorization_pending":
            continue
        if error == "slow_down":
            interval *= 2
            continue
        if error == "expired_token":
            raise ShareError("加载授权码已过期，请重试", 2)
        if error == "access_denied":
            raise ShareError("授权被拒绝", 2)
    raise ShareError("加载授权超时，请重试", 2)


# --- Source resolution ---------------------------------------------------------
def resolve_transcript_paths(args: argparse.Namespace) -> list[Path]:
    if args.file:
        path = Path(args.file).expanduser()
        if not path.is_file():
            raise ShareError(f"输入 transcript 文件不存在: {path}")
        return [path]

    session_id = (
        args.session_id
        or os.environ.get("CLAUDE_CODE_SESSION_ID")
        or os.environ.get("CODEX_SESSION_ID")
        or os.environ.get("CODEX_THREAD_ID")
    )
    if not session_id:
        pty_id = os.environ.get("YODA_PTY_ID", "")
        if pty_id.startswith("claude-conv-"):
            session_id = pty_id[len("claude-conv-") :]

    projects_root = Path(os.environ.get("HOME", Path.home())) / ".claude" / "projects"
    if session_id and projects_root.is_dir():
        # Search every project directory for the session transcript; the current
        # session often lives under a project slug unrelated to the cwd (e.g. a
        # Yoda worktree). Match by filename only, newest wins.
        matches = [
            p
            for p in projects_root.glob("**/*.jsonl")
            if p.stem == session_id and p.is_file()
        ]
        if matches:
            return [sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)[0]]

    if session_id:
        codex_root = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions"
        if codex_root.is_dir():
            # Codex Desktop may continue one logical session in multiple rollout
            # files after compaction or app restart. Keep every segment whose
            # session_meta id matches exactly, then concatenate chronologically.
            codex_matches: list[Path] = []
            for candidate in codex_root.glob(f"**/*{session_id}*.jsonl"):
                if not candidate.is_file() or not codex_session_matches(candidate, session_id):
                    continue
                codex_matches.append(candidate)
            if codex_matches:
                return sorted(codex_matches, key=lambda p: (p.stat().st_mtime, p.name))

    if projects_root.is_dir():
        # Last resort: pick the newest transcript in the cwd's project slug.
        slug = projects_slug(os.getcwd())
        candidates = sorted(
            (projects_root / slug).glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        if candidates:
            return [candidates[0]]

    raise ShareError(
        "无法自动定位会话：请用 --file 提供 transcript，或用 --session-id 指定会话"
    )


def codex_session_matches(path: Path, session_id: str) -> bool:
    """Fail closed when a filename contains an id belonging to another session."""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for _ in range(8):
                line = handle.readline()
                if not line:
                    break
                record = json.loads(line)
                if record.get("type") == "session_meta":
                    payload = record.get("payload")
                    return isinstance(payload, dict) and payload.get("id") == session_id
    except (OSError, json.JSONDecodeError):
        return False
    return False


def projects_slug(cwd: str) -> str:
    # Claude Code encodes the cwd into the project directory name: '/' -> '-',
    # leading '-' becomes '--', and the whole thing is prefixed with '-'.
    tail = re.sub(r"/", "-", cwd.rstrip("/"))
    if tail.startswith("-"):
        tail = "--" + tail[1:]
    return "-" + tail


# --- Normalization -------------------------------------------------------------
def load_transcript(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise ShareError(f"transcript 为空: {path}")

    records: list[dict[str, Any]] = []
    first = lines[0].lstrip()
    if first.startswith("{"):
        for line in lines:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ShareError(f"JSONL 解析失败: {exc}") from exc
    elif first.startswith("["):
        try:
            records = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ShareError(f"JSON 数组解析失败: {exc}") from exc
    else:
        # Plain markdown/text fallback: treat each non-empty line as a user turn.
        records = [{"type": "user", "message": {"content": line}} for line in lines]
    return records


def extract_text(content: Any) -> str:
    """Flatten Claude 'content' which may be a string or a list of content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, str):
                chunks.append(item)
            elif isinstance(item, dict):
                # Claude uses `text`; Codex uses `input_text` / `output_text`.
                # Skip tool calls, tool results, reasoning, and internal status.
                if item.get("type") in {"text", "input_text", "output_text"} and isinstance(item.get("text"), str):
                    chunks.append(item["text"])
        return "".join(chunks)
    return "" if content is None else str(content)


def strip_metadata(value: str) -> str:
    out = value
    # Repeat because one host envelope may contain another known envelope.
    previous = None
    while out != previous:
        previous = out
        for pattern in METADATA_PATTERNS:
            out = pattern.sub("", out)
    return re.sub(r"\n{3,}", "\n\n", out).strip()


def redact_sensitive(value: str) -> str:
    out = value
    for pattern in PRIVATE_HOME_PATTERNS:
        out = pattern.sub("$HOME", out)
    for pattern, replacement in SECRET_REDACTIONS:
        out = pattern.sub(replacement, out)
    return out


def role_for(type_name: str) -> Optional[str]:
    if type_name == "assistant":
        return "assistant"
    if type_name == "user":
        return "user"
    # tool / status are not produced by the JSONL we read, but map defensively.
    return type_name if type_name in ROLES else None


MAX_TOOL_CONTENT_CHARS = 16 * 1024
TOOL_OUTPUT_TITLE = "Tool output"
TOOL_ERROR_TITLE = "Tool error"
COMMAND_TOOL_NAMES = {"Bash", "bash", "exec_command", "shell", "container.exec"}
# Tool blocks whose content matches any of these (multiline, case-insensitive)
# are dropped before upload: set from --exclude-tool-pattern for content that is
# legitimate transcript but must not be published (paid Skill bodies, private notes).
TOOL_EXCLUDE_PATTERNS: list[re.Pattern[str]] = []


def set_tool_exclude_patterns(patterns: list[str]) -> None:
    TOOL_EXCLUDE_PATTERNS[:] = [re.compile(p, re.I | re.M) for p in patterns]


def truncate(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return f"{value[:max_chars]}\n[... truncated {len(value) - max_chars} chars]"


def format_tool_input(name: str, value: Any) -> str:
    """Render a tool call the way a reader would type it: shell commands as
    `$ cmd`, everything else as pretty JSON (mirrors Yoda's transcript view)."""
    if isinstance(value, str):
        parsed: Any = None
        if value.lstrip().startswith("{"):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                parsed = None
        if parsed is None:
            return value
        value = parsed
    if isinstance(value, dict):
        command = value.get("command") or value.get("cmd")
        if name in COMMAND_TOOL_NAMES and isinstance(command, str) and command.strip():
            description = value.get("description")
            rendered = f"$ {command.strip()}"
            if isinstance(description, str) and description.strip():
                rendered += f"\n# {description.strip()}"
            return rendered
    try:
        return json.dumps(value, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return str(value)


def tool_output_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts)
    return "" if content is None else str(content)


def tool_block(title: str, raw: str, timestamp: Any) -> Optional[dict[str, Any]]:
    """Tool activity is never user speech, so a block that still carries host
    context after stripping is dropped instead of failing the whole share."""
    content = redact_sensitive(strip_metadata(raw))
    if not content or INTERNAL_CONTEXT_RESIDUE_RE.search(content):
        return None
    if any(p.search(content) for p in TOOL_EXCLUDE_PATTERNS):
        return None
    return {
        "role": "tool",
        "timestamp": normalize_timestamp(timestamp) if isinstance(timestamp, str) and timestamp else None,
        "format": "code",
        "title": title[:160],
        "content": truncate(content, MAX_TOOL_CONTENT_CHARS),
    }


def text_block(role: str, raw: str, timestamp: Any, title: Any = None) -> Optional[dict[str, Any]]:
    content = raw
    if role == "user":
        if HOST_BLOCK_DROP_RE.match(content):
            return None
        command = COMMAND_ENVELOPE_RE.match(content)
        if command:
            args = (command.group(2) or "").strip()
            content = f"{command.group(1)} {args}".strip()
    content = redact_sensitive(strip_metadata(content))
    if not content:
        return None
    if INTERNAL_CONTEXT_RESIDUE_RE.search(content):
        raise ShareError("检测到未清理的宿主注入上下文，已阻止上传")
    if len(content) > MAX_CONTENT_LEN:
        content = content[:MAX_CONTENT_LEN]
    block: dict[str, Any] = {
        "role": role,
        "timestamp": normalize_timestamp(timestamp) if isinstance(timestamp, str) and timestamp else None,
        "format": "markdown",
        "content": content,
    }
    if isinstance(title, str) and title.strip():
        block["title"] = title.strip()[:160]
    return block


def is_narration_signature(signature: Any) -> bool:
    """Claude Code stores the user-visible progress narration as a `thinking`
    item whose signature protobuf carries a `narration` tag; genuine reasoning
    is tagged `thinking` and arrives redacted (empty text). Only narration is
    ever shared."""
    if not isinstance(signature, str) or not signature:
        return False
    try:
        head = base64.b64decode(signature[:96] + "==", validate=False)[:64]
    except (ValueError, binascii.Error):
        return False
    return b"narration" in head and b"thinking" not in head


def claude_agent_phase(message: dict[str, Any]) -> str:
    stop_reason = message.get("stop_reason")
    return "final" if isinstance(stop_reason, str) and stop_reason and stop_reason != "tool_use" else "commentary"


def record_blocks(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand one JSONL record into share blocks: visible prose plus tool calls
    and outputs (role="tool"), so the verbose level can replay the session."""
    out: list[dict[str, Any]] = []
    timestamp = record.get("timestamp")

    if record.get("type") == "response_item":
        payload = record.get("payload")
        if not isinstance(payload, dict):
            return out
        ptype = payload.get("type")
        if ptype in {"function_call", "custom_tool_call"}:
            name = payload.get("name") if isinstance(payload.get("name"), str) else "tool"
            raw = format_tool_input(name, payload.get("arguments", payload.get("input")))
            block = tool_block(f"Tool · {name}", raw or name, timestamp)
            return [block] if block else out
        if ptype in {"function_call_output", "custom_tool_call_output"}:
            block = tool_block(TOOL_OUTPUT_TITLE, tool_output_text(payload.get("output")), timestamp)
            return [block] if block else out

    mtype, message, record_timestamp = message_record(record)
    role = role_for(mtype)
    if not role:
        return out
    timestamp = record_timestamp or message.get("timestamp")
    content = message.get("content")
    phase = claude_agent_phase(message) if role == "assistant" else None

    if not isinstance(content, list):
        block = text_block(role, extract_text(content), timestamp, message.get("title"))
        if block:
            if phase:
                block["agentPhase"] = phase
            out.append(block)
        return out

    text_parts: list[str] = []

    def flush() -> None:
        if not text_parts:
            return
        block = text_block(role, "\n\n".join(text_parts), timestamp, message.get("title"))
        text_parts.clear()
        if block:
            if phase:
                block["agentPhase"] = phase
            out.append(block)

    for item in content:
        if isinstance(item, str):
            text_parts.append(item)
            continue
        if not isinstance(item, dict):
            continue
        itype = item.get("type")
        if itype in {"text", "input_text", "output_text"} and isinstance(item.get("text"), str):
            text_parts.append(item["text"])
        elif itype == "thinking":
            narration = item.get("thinking")
            if isinstance(narration, str) and narration.strip() and is_narration_signature(item.get("signature")):
                text_parts.append(narration.strip())
        elif itype == "tool_use":
            flush()
            name = item.get("name") if isinstance(item.get("name"), str) else "tool"
            block = tool_block(f"Tool · {name}", format_tool_input(name, item.get("input")) or name, timestamp)
            if block:
                out.append(block)
        elif itype == "tool_result":
            flush()
            title = TOOL_ERROR_TITLE if item.get("is_error") is True else TOOL_OUTPUT_TITLE
            block = tool_block(title, tool_output_text(item.get("content")), timestamp)
            if block:
                out.append(block)
        # thinking / reasoning / other internal items are never shared
    flush()
    return out


def promote_unconcluded_turn_replies(blocks: list[dict[str, Any]]) -> None:
    """The concise level shows only agentPhase=final replies; an interrupted
    turn would otherwise render as silence (mirrors the server normalizer)."""
    last_reply = -1
    concluded = False

    def close_turn() -> None:
        nonlocal last_reply, concluded
        if not concluded and last_reply >= 0:
            blocks[last_reply]["agentPhase"] = "final"
        last_reply, concluded = -1, False

    for index, block in enumerate(blocks):
        if block["role"] == "user":
            close_turn()
        elif block["role"] == "assistant":
            if block.get("agentPhase") == "final":
                concluded = True
            else:
                last_reply = index
    close_turn()


def normalize_transcript(records: list[dict[str, Any]], display_level: str) -> list[dict[str, Any]]:
    """Emit blocks that satisfy the strict transcriptBlockSchema.

    Every visible level is derived server-side from the same block list:
    `hidden` shows user prompts, `concise` adds agentPhase=final replies,
    `detailed` adds commentary and status, `verbose` adds role="tool" blocks.
    """
    blocks: list[dict[str, Any]] = []
    for record in records:
        for block in record_blocks(record):
            block = {"id": f"block-{len(blocks) + 1}", **block}
            blocks.append(block)
    promote_unconcluded_turn_replies(blocks)
    if not blocks:
        raise ShareError("该会话没有可分享的对话内容")
    return blocks


def message_record(record: dict[str, Any]) -> tuple[Any, dict[str, Any], Any]:
    """Return a common message view for Claude/Yoda and Codex JSONL records."""
    mtype = record.get("type")
    message = record.get("message") if isinstance(record.get("message"), dict) else {}
    timestamp = record.get("timestamp")
    if mtype != "response_item":
        return mtype, message, timestamp

    payload = record.get("payload")
    if not isinstance(payload, dict) or payload.get("type") != "message":
        return None, {}, timestamp
    role = payload.get("role")
    if role not in {"user", "assistant"}:
        return None, {}, timestamp
    return role, {"content": payload.get("content")}, timestamp


def normalize_timestamp(value: str) -> str:
    """Coerce any parseable timestamp into an ISO-8601 datetime with offset.

    The strict server schema requires `zod.string().datetime({ offset: true })`,
    so 'Z' is fine but a naive local time is not — convert to an offset string.
    """
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (ValueError, OSError, OverflowError):
            return value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat()


def build_upload(
    records: list[dict[str, Any]],
    display_level: str,
    title: str,
    paid_skill: Optional[str] = None,
    case_id: Optional[str] = None,
) -> dict[str, Any]:
    blocks = normalize_transcript(records, display_level)
    started = next((b["timestamp"] for b in blocks if b.get("timestamp")), None)
    upload = {
        "kind": KIND,
        "version": VERSION,
        "title": title.strip()[:MAX_TITLE_LEN] or "Agent Session",
        "runtimeId": runtime_id(),
        "sessionStartedAt": started,
        "blocks": blocks,
        "truncated": False,
        "assets": [],
        "omittedAssetCount": 0,
    }
    if paid_skill or case_id:
        if not paid_skill or not SKILL_ID_RE.fullmatch(paid_skill):
            raise ShareError("--paid-skill 必须是目标 Skill 的 lowercase kebab-case id")
        if not case_id or not CASE_ID_RE.fullmatch(case_id):
            raise ShareError("付费 Session 必须同时提供 lowercase kebab-case --case-id")
        upload["access"] = {
            "mode": "paid",
            "sourceSkillName": paid_skill,
            "caseId": case_id,
        }
    return upload


def runtime_id() -> str:
    """A stable id satisfying the server regex ^[a-z0-9][a-z0-9._-]*$/i."""
    agent = os.environ.get("AI_AGENT", "")
    if agent:
        candidate = re.sub(r"[^A-Za-z0-9._-]", "-", agent).strip("-").lower()
        if candidate:
            return candidate[:64]
    if os.environ.get("CODEX_SESSION_ID") or os.environ.get("CODEX_THREAD_ID"):
        return "codex"
    if os.environ.get("CLAUDE_CODE_SESSION_ID"):
        return "claude-code"
    return "generic-agent"


# --- HTTP ----------------------------------------------------------------------
def http_json(
    method: str,
    url: str,
    body: Optional[dict[str, Any]],
    jwt: Optional[str],
    timeout: int,
) -> dict[str, Any]:
    data = None
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        # Cloudflare rejects the bare Python urllib fingerprint with 403 error
        # 1010. Sending a browser-like User-Agent + Accept head the TLS/HTTP
        # fingerprint check off, regardless of whether the request routes via a proxy.
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"
    if body is not None:
        raw = json.dumps(body).encode("utf-8")
        if len(raw) > GZIP_THRESHOLD_BYTES:
            data = gzip.compress(raw)
            headers["Content-Encoding"] = "gzip"
        else:
            data = raw
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()
            if payload:
                return json.loads(payload.decode("utf-8"))
            return {}
    except urllib.error.HTTPError as exc:
        payload: dict[str, Any] = {}
        raw = exc.read()
        if raw:
            try:
                payload = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                payload = {"message": raw.decode("utf-8", errors="replace")}
        err = ShareError(f"HTTP {exc.code}: {payload.get('error') or payload.get('message', '')}", 3)
        err.payload = payload
        err.status = exc.code
        raise err
    except urllib.error.URLError as exc:
        raise ShareError(f"网络请求失败: {exc.reason}", 2) from exc
    except OSError as exc:
        raise ShareError(f"网络请求失败: {exc}", 2) from exc


def upload_share(upload: dict[str, Any], token: str, base_url: str, timeout: int) -> dict[str, Any]:
    resp = http_json(
        "POST", f"{base_url}/api/yoda/session-shares",
        body=upload,
        jwt=token,
        timeout=timeout,
    )
    if "url" not in resp:
        raise ShareError("服务器未返回分享 URL", 3)
    return resp


def upload_with_auth_retry(upload: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    """Retry one unauthorized upload after refreshing cached local auth."""
    token = load_access_token(args)
    try:
        return upload_share(upload, token, args.base_url, args.timeout)
    except ShareError as exc:
        if getattr(exc, "status", None) != 401:
            raise
        if args.token or any(os.environ.get(name) for name in ("LOVSTUDIO_ACCESS_TOKEN", "YODA_ACCESS_TOKEN")):
            raise

    refresh = load_refresh_token(args.profile_path)
    if refresh:
        try:
            token = run_refresh(args.base_url, refresh, args.timeout, args.profile_path)
        except ShareError:
            token = device_flow_signin(args)
    else:
        token = device_flow_signin(args)
    return upload_share(upload, token, args.base_url, args.timeout)


def with_display_level(url: str, level: str) -> str:
    if level in DISPLAY_LEVELS and "?" not in url:
        return f"{url}?detail={level}"
    return url


def result_payload(result: dict[str, Any], level: str, paid_skill: Optional[str]) -> dict[str, Any]:
    url = with_display_level(result["url"], level)
    payload: dict[str, Any] = {
        "url": url,
        "assetCount": result.get("assetCount", 0),
        "access": result.get("accessMode", "public"),
    }
    if paid_skill:
        price = result.get("priceCredits")
        source_skill = result.get("sourceSkillName")
        case_id = result.get("caseId")
        if (
            result.get("accessMode") != "paid"
            or source_skill != paid_skill
            or not isinstance(case_id, str)
            or not isinstance(price, int)
            or isinstance(price, bool)
            or price <= 0
            or result.get("pricingRule") != PAID_SESSION_PRICING_RULE
        ):
            raise ShareError("服务器没有返回可信的付费 Session 定价结果", 3)
        payload.update(
            {
                "access": "paid",
                "priceCredits": price,
                "pricingRule": result["pricingRule"],
                "targetSkill": source_skill,
                "caseId": case_id,
            }
        )
    return payload


# --- Main ----------------------------------------------------------------------
def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--file", help="Path to a transcript (JSONL/JSON/markdown).")
    source.add_argument(
        "--session-id",
        help="A Claude or Codex session id to resolve from the local transcript stores.",
    )
    parser.add_argument(
        "--detail",
        default="concise",
        choices=DISPLAY_LEVELS,
        help="Reply depth baked into the share URL via ?detail= (default concise).",
    )
    parser.add_argument("--title", default="Agent Session", help="Share title (max 200 chars).")
    parser.add_argument(
        "--paid-skill",
        default=None,
        help="Target paid Skill id. The server prices this session at ceil(Skill price / 10).",
    )
    parser.add_argument(
        "--case-id",
        default=None,
        help="Stable case id linked to --paid-skill; both options are required together.",
    )
    parser.add_argument(
        "--exclude-tool-pattern",
        action="append",
        default=[],
        metavar="REGEX",
        help="Drop tool call/output blocks whose content matches REGEX (repeatable). "
        "Use for legitimate but unpublishable transcript content such as decrypted paid Skill bodies.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the structured upload result instead of only the URL.",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Lovstudio api base url.")
    parser.add_argument("--token", default=None, help="Explicit Lovstudio access token.")
    parser.add_argument(
        "--profile-path",
        type=Path,
        default=None,
        help="Path to the user profile json.",
    )
    parser.add_argument("--timeout", type=int, default=60, help="Request timeout in seconds.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Normalize and print the JSON payload without uploading.",
    )
    return parser.parse_args()


def main() -> int:
    args = build_args()
    try:
        set_tool_exclude_patterns(args.exclude_tool_pattern)
        paths = resolve_transcript_paths(args)
        records = [record for path in paths for record in load_transcript(path)]
        upload = build_upload(
            records,
            args.detail,
            args.title,
            paid_skill=args.paid_skill,
            case_id=args.case_id,
        )

        if args.dry_run:
            print(json.dumps(upload, ensure_ascii=True, indent=2))
            return 0

        result = upload_with_auth_retry(upload, args)
        payload = result_payload(result, args.detail, args.paid_skill)
        rendered = json.dumps(payload, ensure_ascii=True)
        print(rendered if args.json else payload["url"])
        print(f"[session-share] {rendered}", file=sys.stderr)
        return 0
    except ShareError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return int(getattr(exc, "code", 1))


if __name__ == "__main__":
    raise SystemExit(main())
