#!/usr/bin/env python3
"""Turn audio/video into timestamped SRT with vocabulary-aware cloud ASR.

The CLI keeps credentials out of source files and generated reports.  It supports
DashScope Qwen Audio ASR for short, parallelizable chunks and Volcengine's fast
recording-file endpoint for long recordings.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DASHSCOPE_ENDPOINT = (
    "https://dashscope.aliyuncs.com/api/v1/services/aigc/"
    "multimodal-generation/generation"
)
VOLCENGINE_ENDPOINT = (
    "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash"
)
DEFAULT_DASHSCOPE_MODEL = "qwen-audio-3.0-asr-flash"
DEFAULT_VOLCENGINE_MODEL = "bigmodel"
DEFAULT_WHISPER_MODEL_NAME = "ggml-large-v3-turbo-q5_0.bin"
DEFAULT_PRICE_CNY_PER_SECOND = {
    "dashscope": 0.00022,
    "volcengine": 0.0,
    "whisper-cpp": 0.0,
}
OPENLESS_SERVICE = "com.openless.app"
OPENLESS_ACCOUNT = "credentials.v1"
OPENLESS_HOTWORD_CAP = 80


class Voice2SrtError(RuntimeError):
    """Actionable command failure without credential leakage."""


@dataclass
class Cue:
    start_ms: int
    end_ms: int
    text: str
    source_chunk: int = 0


@dataclass
class Chunk:
    index: int
    start_ms: int
    duration_ms: int
    path: Path


def run_checked(args: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=True,
        text=True,
        capture_output=capture,
    )


def require_binary(name: str) -> str:
    resolved = shutil.which(name)
    if not resolved:
        raise Voice2SrtError(f"required executable not found: {name}")
    return resolved


def media_duration_seconds(path: Path) -> float:
    require_binary("ffprobe")
    try:
        result = run_checked(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture=True,
        )
        duration = float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as exc:
        raise Voice2SrtError(f"cannot probe media duration: {path}") from exc
    if not math.isfinite(duration) or duration <= 0:
        raise Voice2SrtError(f"invalid media duration: {duration!r}")
    return duration


def _entry_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("entries", "vocabulary", "items", "words"):
            if isinstance(value.get(key), list):
                return value[key]
    return []


def load_vocabulary(path: Path | None, *, cap: int = OPENLESS_HOTWORD_CAP) -> list[str]:
    if path is None:
        return []
    if not path.is_file():
        raise Voice2SrtError(f"vocabulary file not found: {path}")
    if path.suffix.lower() in {".json", ".jsonl"}:
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise Voice2SrtError(f"invalid vocabulary JSON: {path}") from exc
        values = _entry_list(parsed)
    else:
        values = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]

    terms: list[str] = []
    seen: set[str] = set()
    for item in values:
        enabled = True
        phrase: Any = item
        if isinstance(item, dict):
            enabled = item.get("enabled", True) is not False
            phrase = item.get("phrase", item.get("word", item.get("text", "")))
        if not enabled or not isinstance(phrase, str):
            continue
        phrase = phrase.strip()
        folded = phrase.casefold()
        if not phrase or folded in seen:
            continue
        terms.append(phrase)
        seen.add(folded)
        if len(terms) >= cap:
            break
    return terms


def default_vocabulary_path() -> Path | None:
    configured = os.environ.get("LOV_VOCABULARY_PATH")
    if configured:
        return Path(os.path.expandvars(configured)).expanduser()
    openless = Path.home() / "Library" / "Application Support" / "OpenLess" / "dictionary.json"
    return openless if openless.is_file() else None


def vocabulary_fingerprint(terms: Iterable[str]) -> str:
    stable = "\n".join(term.casefold() for term in terms).encode("utf-8")
    return hashlib.sha256(stable).hexdigest()


def read_openless_preferences() -> dict[str, Any]:
    path = Path.home() / "Library" / "Application Support" / "OpenLess" / "preferences.json"
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _security_password(account: str, *, timeout: float = 20.0) -> str:
    require_binary("security")
    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-s",
                OPENLESS_SERVICE,
                "-a",
                account,
                "-w",
            ],
            check=True,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise Voice2SrtError(
            "OpenLess Keychain read timed out; approve the one-time macOS prompt or use env credentials"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise Voice2SrtError(
            "OpenLess Keychain item could not be read; use VOLCENGINE_* env credentials"
        ) from exc
    return result.stdout.rstrip("\n")


def read_openless_credentials() -> dict[str, Any]:
    """Read the OpenLess v1 vault after explicit --openless-keychain opt-in."""
    first = _security_password(OPENLESS_ACCOUNT)
    try:
        value = json.loads(first)
    except json.JSONDecodeError as exc:
        raise Voice2SrtError("OpenLess Keychain payload is not valid JSON") from exc
    if isinstance(value, dict) and value.get("openless_credentials_storage") == "chunked":
        count = value.get("chunks")
        generation = value.get("generation")
        if not isinstance(count, int) or count < 1:
            raise Voice2SrtError("OpenLess Keychain chunk manifest is invalid")
        parts: list[str] = []
        for index in range(count):
            if generation:
                account = f"credentials.v1.chunk.{generation}.{index}"
            else:
                account = f"credentials.v1.chunk.{index}"
            parts.append(_security_password(account))
        try:
            value = json.loads("".join(parts))
        except json.JSONDecodeError as exc:
            raise Voice2SrtError("OpenLess Keychain chunks are not valid JSON") from exc
    if not isinstance(value, dict):
        raise Voice2SrtError("OpenLess Keychain root must be an object")
    return value


def extract_openless_volcengine(root: dict[str, Any]) -> dict[str, str]:
    active = root.get("active") if isinstance(root.get("active"), dict) else {}
    active_id = active.get("asr")
    providers = root.get("providers") if isinstance(root.get("providers"), dict) else {}
    asr = providers.get("asr") if isinstance(providers.get("asr"), dict) else {}
    candidates: list[dict[str, Any]] = []
    if isinstance(active_id, str) and isinstance(asr.get(active_id), dict):
        candidates.append(asr[active_id])
    for key, entry in asr.items():
        if not isinstance(entry, dict) or entry in candidates:
            continue
        provider_type = entry.get("providerType", key)
        if provider_type == "volcengine":
            candidates.append(entry)
    for entry in candidates:
        provider_type = entry.get("providerType", active_id or "volcengine")
        if provider_type != "volcengine" and active_id != "volcengine":
            continue
        auth_mode = str(entry.get("authMode") or "app_id_token")
        result = {
            "auth_mode": auth_mode,
            "app_key": str(entry.get("appKey") or ""),
            "access_key": str(entry.get("accessKey") or ""),
            "api_key": str(entry.get("volcengineApiKey") or ""),
            "resource_id": str(entry.get("resourceId") or "volc.bigasr.auc_turbo"),
        }
        if (auth_mode == "api_key" and result["api_key"]) or (
            result["app_key"] and result["access_key"]
        ):
            return result
    raise Voice2SrtError("OpenLess has no usable Volcengine ASR credential set")


def extract_openless_dashscope(root: dict[str, Any]) -> dict[str, str]:
    active = root.get("active") if isinstance(root.get("active"), dict) else {}
    active_id = active.get("asr")
    providers = root.get("providers") if isinstance(root.get("providers"), dict) else {}
    asr = providers.get("asr") if isinstance(providers.get("asr"), dict) else {}
    ordered: list[tuple[str, dict[str, Any]]] = []
    if isinstance(active_id, str) and isinstance(asr.get(active_id), dict):
        ordered.append((active_id, asr[active_id]))
    ordered.extend(
        (str(key), entry)
        for key, entry in asr.items()
        if isinstance(entry, dict) and all(entry is not existing for _, existing in ordered)
    )
    for key, entry in ordered:
        provider_type = str(entry.get("providerType") or key)
        if provider_type not in {
            "bailian",
            "bailian-qwen3-realtime",
            "bailian-fun-asr-flash",
        }:
            continue
        api_key = str(entry.get("apiKey") or "").strip()
        if api_key:
            return {
                "api_key": api_key,
                "configured_model": str(entry.get("model") or ""),
                "configured_base_url": str(entry.get("baseURL") or ""),
                "provider_type": provider_type,
            }
    raise Voice2SrtError("OpenLess has no usable DashScope/Bailian ASR credential set")


def resolve_volcengine_credentials(use_openless_keychain: bool) -> dict[str, str]:
    api_key = os.environ.get("VOLCENGINE_API_KEY", "").strip()
    app_key = os.environ.get("VOLCENGINE_APP_KEY", "").strip()
    access_key = os.environ.get("VOLCENGINE_ACCESS_KEY", "").strip()
    if api_key:
        return {
            "auth_mode": "api_key",
            "api_key": api_key,
            "app_key": "",
            "access_key": "",
            "resource_id": os.environ.get("VOLCENGINE_RESOURCE_ID", "volc.bigasr.auc_turbo"),
        }
    if app_key and access_key:
        return {
            "auth_mode": "app_id_token",
            "api_key": "",
            "app_key": app_key,
            "access_key": access_key,
            "resource_id": os.environ.get("VOLCENGINE_RESOURCE_ID", "volc.bigasr.auc_turbo"),
        }
    if use_openless_keychain:
        return extract_openless_volcengine(read_openless_credentials())
    raise Voice2SrtError(
        "Volcengine credentials missing; set VOLCENGINE_API_KEY or VOLCENGINE_APP_KEY + "
        "VOLCENGINE_ACCESS_KEY, or pass --openless-keychain"
    )


def select_provider(requested: str, use_openless_keychain: bool) -> str:
    if requested != "auto":
        return requested
    if os.environ.get("DASHSCOPE_API_KEY"):
        return "dashscope"
    if any(os.environ.get(name) for name in ("VOLCENGINE_API_KEY", "VOLCENGINE_APP_KEY")):
        return "volcengine"
    if use_openless_keychain:
        return "volcengine"
    raise Voice2SrtError("no cloud ASR credentials found for provider=auto")


def default_whisper_model_path() -> Path:
    configured = os.environ.get("WHISPER_CPP_MODEL")
    if configured:
        path = Path(os.path.expandvars(configured)).expanduser()
    else:
        path = Path.home() / "Library" / "Caches" / "whisper.cpp" / DEFAULT_WHISPER_MODEL_NAME
    if not path.is_file():
        raise Voice2SrtError(
            f"Whisper model not found: {path}; set WHISPER_CPP_MODEL to a ggml model"
        )
    return path


def encode_chunks(
    source: Path,
    directory: Path,
    duration_seconds: float,
    chunk_seconds: float,
    provider: str,
) -> list[Chunk]:
    require_binary("ffmpeg")
    directory.mkdir(parents=True, exist_ok=True)
    effective = duration_seconds if provider in {"volcengine", "whisper-cpp"} else chunk_seconds
    count = max(1, math.ceil(duration_seconds / effective))
    chunks: list[Chunk] = []
    for index in range(count):
        start = index * effective
        duration = min(effective, duration_seconds - start)
        target = directory / f"chunk-{index:03d}.mp3"
        run_checked(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{start:.6f}",
                "-t",
                f"{duration:.6f}",
                "-i",
                str(source),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-c:a",
                "libmp3lame",
                "-b:a",
                "64k",
                "-y",
                str(target),
            ]
        )
        chunks.append(
            Chunk(
                index=index,
                start_ms=round(start * 1000),
                duration_ms=round(duration * 1000),
                path=target,
            )
        )
    return chunks


def _post_json(
    endpoint: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    *,
    timeout: float,
) -> tuple[dict[str, str], bytes]:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(endpoint, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    for key, value in headers.items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {key.lower(): value for key, value in response.headers.items()}, response.read()
    except urllib.error.HTTPError as exc:
        response_text = exc.read().decode("utf-8", errors="replace")[:800]
        raise Voice2SrtError(f"ASR HTTP {exc.code}: {response_text}") from exc
    except urllib.error.URLError as exc:
        raise Voice2SrtError(f"ASR connection failed: {exc.reason}") from exc


def _post_sse(
    endpoint: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    *,
    timeout: float,
) -> list[dict[str, Any]]:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(endpoint, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    for key, value in headers.items():
        request.add_header(key, value)
    events: list[dict[str, Any]] = []
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if not data or data == "[DONE]":
                    continue
                try:
                    value = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    events.append(value)
    except urllib.error.HTTPError as exc:
        response_text = exc.read().decode("utf-8", errors="replace")[:800]
        raise Voice2SrtError(f"ASR HTTP {exc.code}: {response_text}") from exc
    except urllib.error.URLError as exc:
        raise Voice2SrtError(f"ASR connection failed: {exc.reason}") from exc
    return events


def retry_call(callable_obj: Any, attempts: int = 3) -> Any:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return callable_obj()
        except Voice2SrtError as exc:
            last_error = exc
            if "HTTP 40" in str(exc) or attempt == attempts:
                raise
            time.sleep(float(attempt))
    raise Voice2SrtError(str(last_error or "ASR call failed"))


def transcribe_dashscope(
    chunk: Chunk,
    *,
    api_key: str,
    endpoint: str,
    model: str,
    language: str | None,
    vocabulary: list[str],
    timeout: float,
) -> tuple[list[Cue], dict[str, Any]]:
    encoded = base64.b64encode(chunk.path.read_bytes()).decode("ascii")
    parameters: dict[str, Any] = {
        "format": "mp3",
        "sample_rate": "16000",
    }
    if vocabulary:
        parameters["vocabulary"] = {term: 5 for term in vocabulary}
    if language:
        parameters["language_hints"] = [language]
    payload = {
        "model": model,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {"data": f"data:audio/mpeg;base64,{encoded}"},
                        }
                    ],
                }
            ]
        },
        "parameters": parameters,
    }
    events = retry_call(
        lambda: _post_sse(
            endpoint,
            payload,
            {
                "Authorization": f"Bearer {api_key}",
                "X-DashScope-SSE": "enable",
            },
            timeout=timeout,
        )
    )
    cues = dashscope_events_to_cues(events, chunk)
    if not cues:
        raise Voice2SrtError(
            f"DashScope returned no finalized timestamped sentences for chunk {chunk.index}"
        )
    return cues, {"events": events}


def dashscope_events_to_cues(events: list[dict[str, Any]], chunk: Chunk) -> list[Cue]:
    """Convert cumulative or per-sentence DashScope SSE events into incremental cues."""
    cues: list[Cue] = []
    previous_text = ""
    previous_word_count = 0
    for event in events:
        output = event.get("output") if isinstance(event.get("output"), dict) else {}
        sentence = output.get("sentence") if isinstance(output.get("sentence"), dict) else None
        if not sentence or sentence.get("sentence_end") is not True:
            continue
        full_text = str(sentence.get("text") or "").strip()
        words = sentence.get("words") if isinstance(sentence.get("words"), list) else []
        new_words = words[previous_word_count:] if len(words) >= previous_word_count else words
        if new_words:
            cues.extend(dashscope_words_to_cues(new_words, chunk))
            previous_text = full_text
            previous_word_count = len(words)
            continue
        text = full_text[len(previous_text):].strip() if previous_text and full_text.startswith(previous_text) else full_text
        begin = (
            new_words[0].get("begin_time")
            if new_words and isinstance(new_words[0], dict)
            else sentence.get("begin_time")
        )
        end = (
            new_words[-1].get("end_time")
            if new_words and isinstance(new_words[-1], dict)
            else sentence.get("end_time")
        )
        previous_text = full_text
        previous_word_count = len(words)
        if not text or not isinstance(begin, (int, float)) or not isinstance(end, (int, float)):
            continue
        cues.append(
            Cue(
                start_ms=chunk.start_ms + round(begin),
                end_ms=chunk.start_ms + round(end),
                text=text,
                source_chunk=chunk.index,
            )
        )
    return cues


def dashscope_words_to_cues(words: list[Any], chunk: Chunk) -> list[Cue]:
    """Group word timestamps into readable subtitle cues without losing timing."""
    cues: list[Cue] = []
    current: list[dict[str, Any]] = []
    strong = {"。", "！", "？", "!", "?", ";", "；"}
    soft = {"，", ",", "、", ":", "："}

    def flush() -> None:
        nonlocal current
        if not current:
            return
        begin = current[0].get("begin_time")
        end = current[-1].get("end_time")
        text = "".join(
            f"{word.get('text', '')}{word.get('punctuation', '')}" for word in current
        ).strip()
        if text and isinstance(begin, (int, float)) and isinstance(end, (int, float)):
            cues.append(
                Cue(
                    start_ms=chunk.start_ms + round(begin),
                    end_ms=chunk.start_ms + round(end),
                    text=text,
                    source_chunk=chunk.index,
                )
            )
        current = []

    for value in words:
        if not isinstance(value, dict):
            continue
        begin = value.get("begin_time")
        end = value.get("end_time")
        if not isinstance(begin, (int, float)) or not isinstance(end, (int, float)):
            continue
        current.append(value)
        text = "".join(str(word.get("text", "")) for word in current)
        duration = float(end) - float(current[0].get("begin_time", end))
        punctuation = str(value.get("punctuation") or "")
        if (
            punctuation in strong
            or duration >= 5_200
            or (len(text) >= 24 and punctuation in soft)
        ):
            flush()
    flush()
    return cues


def canonicalize_text(text: str, vocabulary: list[str]) -> str:
    """Restore user-owned casing for exact ASCII vocabulary matches."""
    result = text
    for term in sorted(vocabulary, key=len, reverse=True):
        if len(term) < 3 or not any(character.isascii() and character.isalpha() for character in term):
            continue
        pattern = re.compile(
            rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])",
            re.IGNORECASE,
        )
        result = pattern.sub(term, result)
    return result


def transcribe_volcengine(
    chunk: Chunk,
    *,
    credentials: dict[str, str],
    endpoint: str,
    vocabulary: list[str],
    timeout: float,
) -> tuple[list[Cue], dict[str, Any]]:
    request_id = str(uuid.uuid4())
    headers = {
        "X-Api-Resource-Id": "volc.bigasr.auc_turbo",
        "X-Api-Request-Id": request_id,
        "X-Api-Sequence": "-1",
    }
    if credentials.get("auth_mode") == "api_key":
        headers["X-Api-Key"] = credentials["api_key"]
        uid = "voice2srt"
    else:
        headers["X-Api-App-Key"] = credentials["app_key"]
        headers["X-Api-Access-Key"] = credentials["access_key"]
        uid = credentials["app_key"]
    request_options: dict[str, Any] = {
        "model_name": DEFAULT_VOLCENGINE_MODEL,
        "enable_itn": True,
        "enable_punc": True,
        "show_utterances": True,
    }
    if vocabulary:
        request_options["context"] = json.dumps(
            {"hotwords": [{"word": term} for term in vocabulary]},
            ensure_ascii=False,
            separators=(",", ":"),
        )
    payload = {
        "user": {"uid": uid},
        "audio": {"data": base64.b64encode(chunk.path.read_bytes()).decode("ascii")},
        "request": request_options,
    }
    response_headers, body = retry_call(
        lambda: _post_json(endpoint, payload, headers, timeout=timeout)
    )
    status = response_headers.get("x-api-status-code", "")
    if status and status != "20000000":
        message = response_headers.get("x-api-message", "unknown error")
        raise Voice2SrtError(f"Volcengine ASR failed: {status} {message}")
    try:
        value = json.loads(body)
    except json.JSONDecodeError as exc:
        raise Voice2SrtError("Volcengine returned invalid JSON") from exc
    result = value.get("result") if isinstance(value.get("result"), dict) else {}
    utterances = result.get("utterances") if isinstance(result.get("utterances"), list) else []
    cues: list[Cue] = []
    for utterance in utterances:
        if not isinstance(utterance, dict):
            continue
        text = str(utterance.get("text") or "").strip()
        begin = utterance.get("start_time")
        end = utterance.get("end_time")
        if text and isinstance(begin, (int, float)) and isinstance(end, (int, float)):
            cues.append(
                Cue(
                    start_ms=chunk.start_ms + round(begin),
                    end_ms=chunk.start_ms + round(end),
                    text=text,
                    source_chunk=chunk.index,
                )
            )
    if not cues:
        raise Voice2SrtError("Volcengine returned no timestamped utterances")
    return cues, {
        "response": value,
        "status_code": status,
        "log_id": response_headers.get("x-tt-logid"),
    }


def transcribe_whisper_cpp(
    chunk: Chunk,
    *,
    model_path: Path,
    language: str | None,
    vocabulary: list[str],
) -> tuple[list[Cue], dict[str, Any]]:
    binary = require_binary("whisper-cli")
    output_base = chunk.path.with_name(f"{chunk.path.stem}.whisper")
    command = [
        binary,
        "--model",
        str(model_path),
        "--file",
        str(chunk.path),
        "--language",
        language or "auto",
        "--output-json-full",
        "--output-srt",
        "--output-file",
        str(output_base),
        "--no-prints",
    ]
    if vocabulary:
        command.extend(["--prompt", "，".join(vocabulary)])
    try:
        run_checked(command)
    except subprocess.CalledProcessError as exc:
        raise Voice2SrtError(f"whisper-cli failed for chunk {chunk.index}") from exc
    json_path = whisper_output_path(output_base, ".json")
    if not json_path.is_file():
        raise Voice2SrtError(f"whisper-cli did not create JSON: {json_path}")
    try:
        value = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Voice2SrtError(f"invalid whisper-cli JSON: {json_path}") from exc
    transcription = value.get("transcription") if isinstance(value, dict) else None
    if not isinstance(transcription, list):
        raise Voice2SrtError("whisper-cli JSON has no transcription array")
    cues: list[Cue] = []
    for segment in transcription:
        if not isinstance(segment, dict):
            continue
        offsets = segment.get("offsets") if isinstance(segment.get("offsets"), dict) else {}
        begin = offsets.get("from")
        end = offsets.get("to")
        text = str(segment.get("text") or "").strip()
        if text and isinstance(begin, (int, float)) and isinstance(end, (int, float)):
            cues.append(
                Cue(
                    start_ms=chunk.start_ms + round(begin),
                    end_ms=chunk.start_ms + round(end),
                    text=text,
                    source_chunk=chunk.index,
                )
            )
    if not cues:
        raise Voice2SrtError("whisper-cli returned no timestamped segments")
    return cues, {
        "response": value,
        "runtime": {
            "binary": binary,
            "model": str(model_path),
            "prompt_term_count": len(vocabulary),
        },
    }


def whisper_output_path(output_base: Path, suffix: str) -> Path:
    """Return the path produced when whisper-cli appends an output suffix."""

    if not suffix.startswith("."):
        raise ValueError("whisper output suffix must start with a dot")
    return Path(f"{output_base}{suffix}")


def clean_text(text: str) -> str:
    return " ".join(text.replace("\u3000", " ").split()).strip()


def normalize_cues(cues: list[Cue], duration_ms: int) -> list[Cue]:
    ordered = sorted(cues, key=lambda cue: (cue.start_ms, cue.end_ms, cue.source_chunk))
    result: list[Cue] = []
    for cue in ordered:
        cue.text = clean_text(cue.text)
        cue.start_ms = max(0, min(cue.start_ms, duration_ms))
        cue.end_ms = max(cue.start_ms + 1, min(cue.end_ms, duration_ms))
        if not cue.text:
            continue
        if result and cue.text.casefold() == result[-1].text.casefold():
            if cue.start_ms - result[-1].end_ms < 1200:
                result[-1].end_ms = max(result[-1].end_ms, cue.end_ms)
                continue
        if result and cue.start_ms < result[-1].end_ms:
            if cue.start_ms - result[-1].start_ms >= 120:
                result[-1].end_ms = cue.start_ms
            else:
                cue.start_ms = result[-1].end_ms
                cue.end_ms = max(cue.end_ms, cue.start_ms + 120)
        if cue.end_ms > cue.start_ms:
            result.append(cue)
    return result


def srt_timestamp(milliseconds: int) -> str:
    milliseconds = max(0, milliseconds)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def write_srt(path: Path, cues: list[Cue]) -> None:
    blocks = []
    for index, cue in enumerate(cues, 1):
        blocks.append(
            f"{index}\n{srt_timestamp(cue.start_ms)} --> {srt_timestamp(cue.end_ms)}\n{cue.text}"
        )
    path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def validate_cues(cues: list[Cue], duration_ms: int) -> dict[str, Any]:
    invalid = 0
    overlaps = 0
    previous_end = 0
    for cue in cues:
        if cue.start_ms < 0 or cue.end_ms <= cue.start_ms or cue.end_ms > duration_ms + 1000:
            invalid += 1
        if cue.start_ms < previous_end:
            overlaps += 1
        previous_end = max(previous_end, cue.end_ms)
    return {
        "ok": bool(cues) and invalid == 0 and overlaps == 0,
        "cue_count": len(cues),
        "invalid_cues": invalid,
        "overlaps": overlaps,
        "first_start_ms": cues[0].start_ms if cues else None,
        "last_end_ms": cues[-1].end_ms if cues else None,
        "duration_ms": duration_ms,
    }


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def reported_processed_seconds(raw_files: Iterable[str | Path]) -> int | None:
    """Sum each provider chunk's final reported duration without treating it as an invoice."""
    total = 0
    found = False
    for raw_file in raw_files:
        try:
            payload = json.loads(Path(raw_file).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        events = payload.get("events") if isinstance(payload, dict) else None
        if not isinstance(events, list):
            continue
        durations = []
        for event in events:
            usage = event.get("usage") if isinstance(event, dict) else None
            duration = usage.get("duration") if isinstance(usage, dict) else None
            if isinstance(duration, (int, float)) and duration >= 0:
                durations.append(duration)
        if durations:
            total += round(max(durations))
            found = True
    return total if found else None


def output_paths(output_dir: Path) -> dict[str, Path]:
    return {
        "srt": output_dir / "transcript.srt",
        "json": output_dir / "transcript.json",
        "txt": output_dir / "transcript.txt",
        "report": output_dir / "report.json",
        "raw": output_dir / "raw",
        "chunks": output_dir / "chunks",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Audio or video input")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--provider",
        choices=("auto", "dashscope", "volcengine", "whisper-cpp"),
        default="auto",
    )
    parser.add_argument("--model", default=None)
    parser.add_argument("--endpoint", default=None)
    parser.add_argument("--vocabulary", type=Path, default=None)
    parser.add_argument("--no-vocabulary", action="store_true")
    parser.add_argument("--language", default="zh")
    parser.add_argument("--chunk-seconds", type=float, default=240.0)
    parser.add_argument("--price-per-second", type=float, default=None)
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument("--openless-keychain", action="store_true")
    parser.add_argument("--confirm-cost", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep-chunks", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source = args.input.expanduser().resolve()
    if not source.is_file():
        raise Voice2SrtError(f"input not found: {source}")
    duration_seconds = media_duration_seconds(source)
    provider = select_provider(args.provider, args.openless_keychain)
    whisper_model_path: Path | None = None
    if provider == "whisper-cpp":
        whisper_model_path = Path(args.model).expanduser() if args.model else default_whisper_model_path()
        if not whisper_model_path.is_file():
            raise Voice2SrtError(f"Whisper model not found: {whisper_model_path}")
        model = str(whisper_model_path)
        endpoint = ""
    else:
        model = args.model or (
            DEFAULT_DASHSCOPE_MODEL if provider == "dashscope" else DEFAULT_VOLCENGINE_MODEL
        )
        endpoint = args.endpoint or (
            os.environ.get("DASHSCOPE_BASE_URL", DASHSCOPE_ENDPOINT)
            if provider == "dashscope"
            else VOLCENGINE_ENDPOINT
        )
    vocab_path = None if args.no_vocabulary else (args.vocabulary or default_vocabulary_path())
    terms = load_vocabulary(vocab_path)
    price = args.price_per_second
    if price is None:
        price = DEFAULT_PRICE_CNY_PER_SECOND[provider]
    estimated_cost = round(duration_seconds * price, 4)
    preferences = read_openless_preferences()
    summary = {
        "status": "planned" if args.dry_run else "ready",
        "input": str(source),
        "duration_seconds": round(duration_seconds, 3),
        "provider": provider,
        "model": model,
        "endpoint_host": urllib.parse.urlparse(endpoint).netloc or None,
        "language": args.language or None,
        "vocabulary_source": str(vocab_path) if vocab_path else None,
        "vocabulary_count": len(terms),
        "vocabulary_sha256": vocabulary_fingerprint(terms),
        "estimated_cost_cny": estimated_cost,
        "openless_active_asr_provider": preferences.get("activeAsrProvider"),
        "credential_source": (
            "none"
            if provider == "whisper-cpp"
            else "openless-keychain"
            if args.openless_keychain
            else "environment"
        ),
        "requires_cost_confirmation": price > 0,
    }
    if args.dry_run:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if price > 0 and not args.confirm_cost:
        raise Voice2SrtError(
            f"estimated API cost is CNY {estimated_cost:.4f}; rerun with --confirm-cost"
        )
    if provider == "dashscope":
        if args.openless_keychain:
            dashscope_key = extract_openless_dashscope(read_openless_credentials())["api_key"]
        else:
            dashscope_key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
        if not dashscope_key:
            raise Voice2SrtError("DASHSCOPE_API_KEY is required")
        volcengine_credentials = None
    elif provider == "volcengine":
        dashscope_key = ""
        volcengine_credentials = resolve_volcengine_credentials(args.openless_keychain)
    else:
        dashscope_key = ""
        volcengine_credentials = None

    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = output_paths(output_dir)
    paths["raw"].mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="voice2srt-") as temporary:
        chunk_dir = paths["chunks"] if args.keep_chunks else Path(temporary) / "chunks"
        chunks = encode_chunks(
            source,
            chunk_dir,
            duration_seconds,
            args.chunk_seconds,
            provider,
        )
        cues: list[Cue] = []
        raw_files: list[str] = []
        for chunk in chunks:
            if provider == "dashscope":
                chunk_cues, raw = transcribe_dashscope(
                    chunk,
                    api_key=dashscope_key,
                    endpoint=endpoint,
                    model=model,
                    language=args.language or None,
                    vocabulary=terms,
                    timeout=args.timeout,
                )
            elif provider == "volcengine":
                assert volcengine_credentials is not None
                chunk_cues, raw = transcribe_volcengine(
                    chunk,
                    credentials=volcengine_credentials,
                    endpoint=endpoint,
                    vocabulary=terms,
                    timeout=args.timeout,
                )
            else:
                assert whisper_model_path is not None
                chunk_cues, raw = transcribe_whisper_cpp(
                    chunk,
                    model_path=whisper_model_path,
                    language=args.language or None,
                    vocabulary=terms,
                )
            raw_path = paths["raw"] / f"chunk-{chunk.index:03d}.json"
            write_json(raw_path, raw)
            raw_files.append(str(raw_path))
            cues.extend(chunk_cues)

    duration_ms = round(duration_seconds * 1000)
    for cue in cues:
        cue.text = canonicalize_text(cue.text, terms)
    cues = normalize_cues(cues, duration_ms)
    validation = validate_cues(cues, duration_ms)
    if not validation["ok"]:
        raise Voice2SrtError(f"subtitle validation failed: {validation}")
    write_srt(paths["srt"], cues)
    paths["txt"].write_text("\n".join(cue.text for cue in cues) + "\n", encoding="utf-8")
    transcript = {
        "schema": "lov-voice2srt/transcript/v1",
        "source": str(source),
        "provider": provider,
        "model": model,
        "duration_ms": duration_ms,
        "cues": [asdict(cue) for cue in cues],
    }
    write_json(paths["json"], transcript)
    report = {
        "schema": "lov-voice2srt/report/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **summary,
        "status": "complete",
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "provider_processed_seconds_reported": reported_processed_seconds(raw_files),
        "estimated_cost_cny": estimated_cost,
        "chunk_count": len(chunks),
        "validation": validation,
        "outputs": {key: str(value) for key, value in paths.items() if key != "chunks"},
        "raw_files": raw_files,
        "credentials": "runtime-only; not persisted",
    }
    write_json(paths["report"], report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Voice2SrtError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
