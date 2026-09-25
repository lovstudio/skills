#!/usr/bin/env python3
"""OpenAI-compatible LovStudio LLM API client.

The client intentionally reads the API key from LOVSTUDIO_API_KEY only. It
prints structured JSON so an Agent can inspect results without exposing
credentials in prompts or command arguments.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import ssl
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://llm.lovstudio.ai/v1"
DEFAULT_CHAT_MODEL = "gpt-4o-mini"
DEFAULT_TRANSCRIBE_MODEL = "whisper-1"
DEFAULT_TRANSLATE_MODEL = "whisper-1"
DEFAULT_SPEECH_MODEL = "gpt-4o-mini-tts"


class LovstudioError(Exception):
    """An API or local input error with a copyable diagnostic context."""

    def __init__(
        self,
        message: str,
        *,
        operation: str,
        field: Optional[str] = None,
        status: Optional[int] = None,
        source: str = "lovstudio-api",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.operation = operation
        self.field = field
        self.status = status
        self.source = source
        self.context_id = f"lovstudio-{uuid.uuid4().hex[:12]}"


def _env(name: str, default: str) -> str:
    value = os.environ.get(name, "").strip()
    return value or default


def _base_url() -> str:
    value = _env("LOVSTUDIO_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    if not re.match(r"^https?://", value, flags=re.IGNORECASE):
        raise LovstudioError(
            "LOVSTUDIO_BASE_URL must start with http:// or https://",
            operation="config",
            field="LOVSTUDIO_BASE_URL",
            source="local-config",
        )
    return value


def _api_key(operation: str) -> str:
    value = os.environ.get("LOVSTUDIO_API_KEY", "").strip()
    if not value:
        raise LovstudioError(
            "Set LOVSTUDIO_API_KEY in the process environment before calling the API.",
            operation=operation,
            field="LOVSTUDIO_API_KEY",
            source="local-config",
        )
    return value


def _endpoint(path: str) -> str:
    return f"{_base_url()}/{path.lstrip('/')}"


def _redact(message: str) -> str:
    message = re.sub(r"(?i)(bearer\s+)[^\s]+", r"\1[REDACTED]", message)
    message = re.sub(r"(?i)(api[-_ ]?key[=: ]+)[^\s,;]+", r"\1[REDACTED]", message)
    return message[:1200]


def _decode(raw: bytes, content_type: str) -> Any:
    if not raw:
        return None
    if "json" in content_type.lower():
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return raw.decode("utf-8", errors="replace")
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _api_message(payload: Any, fallback: str) -> str:
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return _redact(message.strip())
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            return _redact(message.strip())
    if isinstance(payload, str) and payload.strip():
        return _redact(payload.strip())
    return fallback


def _request(
    operation: str,
    method: str,
    url: str,
    *,
    body: Optional[bytes] = None,
    content_type: Optional[str] = None,
    timeout: float = 90.0,
) -> Tuple[bytes, str, Dict[str, str]]:
    headers = {
        "Authorization": f"Bearer {_api_key(operation)}",
        "Accept": "application/json",
        "User-Agent": "lov-integrate-lovstudio-llm-skill/0.1.0",
    }
    if content_type:
        headers["Content-Type"] = content_type
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
            response_headers = {
                "content-type": response.headers.get("Content-Type", ""),
                "x-request-id": response.headers.get("x-request-id", ""),
            }
            return raw, response_headers["content-type"], response_headers
    except HTTPError as exc:
        raw = exc.read()
        payload = _decode(raw, exc.headers.get("Content-Type", ""))
        raise LovstudioError(
            _api_message(payload, f"LovStudio API returned HTTP {exc.code}"),
            operation=operation,
            status=exc.code,
        ) from exc
    except URLError as exc:
        reason = getattr(exc, "reason", exc)
        reason_text = str(reason)
        if "EOF occurred" in reason_text:
            reason_text = (
                "TLS handshake failed; use a Python build with modern OpenSSL "
                "or verify the configured endpoint and network path."
            )
        raise LovstudioError(
            f"LovStudio API request failed: {_redact(reason_text)}",
            operation=operation,
            source="network",
        ) from exc
    except ssl.SSLError as exc:
        reason_text = str(exc)
        if "EOF occurred" in reason_text:
            reason_text = (
                "TLS handshake failed; use a Python build with modern OpenSSL "
                "or verify the configured endpoint and network path."
            )
        raise LovstudioError(
            f"LovStudio API request failed: {_redact(reason_text)}",
            operation=operation,
            source="network",
        ) from exc
    except TimeoutError as exc:
        raise LovstudioError(
            "LovStudio API request timed out.",
            operation=operation,
            source="network",
        ) from exc


def _json_request(
    operation: str,
    method: str,
    url: str,
    payload: Dict[str, Any],
    *,
    timeout: float = 90.0,
) -> Tuple[Any, Dict[str, str]]:
    raw, content_type, headers = _request(
        operation,
        method,
        url,
        body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        content_type="application/json",
        timeout=timeout,
    )
    decoded = _decode(raw, content_type)
    if isinstance(decoded, str) or decoded is None:
        raise LovstudioError(
            "LovStudio API returned a non-JSON response.",
            operation=operation,
            source="lovstudio-api",
        )
    return decoded, headers


def _multipart(
    fields: Iterable[Tuple[str, str]],
    file_field: str,
    file_path: Path,
) -> Tuple[bytes, str]:
    boundary = f"----sgcLovstudio{uuid.uuid4().hex}"
    chunks: List[bytes] = []
    for name, value in fields:
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(
                    "utf-8"
                ),
                str(value).encode("utf-8"),
                b"\r\n",
            ]
        )
    filename = file_path.name.replace('"', "_")
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    chunks.extend(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            (
                f'Content-Disposition: form-data; name="{file_field}"; '
                f'filename="{filename}"\r\n'
            ).encode("utf-8"),
            f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
            file_path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _parse_messages(args: argparse.Namespace) -> List[Dict[str, Any]]:
    if args.messages_json and args.messages_file:
        raise LovstudioError(
            "Choose one of --messages-json and --messages-file.",
            operation="chat",
            field="messages",
            source="local-input",
        )
    if args.messages_file:
        raw = Path(args.messages_file).read_text(encoding="utf-8")
        try:
            messages = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LovstudioError(
                f"Messages file is not valid JSON: {exc.msg}",
                operation="chat",
                field="messages-file",
                source="local-input",
            ) from exc
    elif args.messages_json:
        try:
            messages = json.loads(args.messages_json)
        except json.JSONDecodeError as exc:
            raise LovstudioError(
                f"--messages-json is not valid JSON: {exc.msg}",
                operation="chat",
                field="messages-json",
                source="local-input",
            ) from exc
    elif args.prompt:
        messages = [{"role": "user", "content": args.prompt}]
    else:
        raise LovstudioError(
            "Provide --prompt, --messages-json, or --messages-file.",
            operation="chat",
            field="messages",
            source="local-input",
        )
    if not isinstance(messages, list) or not messages:
        raise LovstudioError(
            "messages must be a non-empty JSON array.",
            operation="chat",
            field="messages",
            source="local-input",
        )
    if args.system:
        messages.insert(0, {"role": "system", "content": args.system})
    return messages


def _message_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts)
    return ""


def _chat(args: argparse.Namespace) -> int:
    messages = _parse_messages(args)
    payload: Dict[str, Any] = {
        "model": args.model,
        "messages": messages,
    }
    if args.temperature is not None:
        payload["temperature"] = args.temperature
    if args.max_tokens is not None:
        payload["max_tokens"] = args.max_tokens
    response, headers = _json_request(
        "chat.completions",
        "POST",
        _endpoint("chat/completions"),
        payload,
        timeout=args.timeout,
    )
    choices = response.get("choices") if isinstance(response, dict) else None
    choice = choices[0] if isinstance(choices, list) and choices else {}
    message = choice.get("message") if isinstance(choice, dict) else {}
    result = {
        "status": "ok",
        "operation": "chat.completions",
        "model": response.get("model", args.model) if isinstance(response, dict) else args.model,
        "text": _message_text(message.get("content") if isinstance(message, dict) else ""),
        "finish_reason": choice.get("finish_reason") if isinstance(choice, dict) else None,
        "usage": response.get("usage") if isinstance(response, dict) else None,
    }
    if headers.get("x-request-id"):
        result["request_id"] = headers["x-request-id"]
    _print_json(result)
    return 0


def _audio_request(args: argparse.Namespace, operation: str, path: str) -> int:
    audio_path = Path(args.file).expanduser()
    if not audio_path.is_file():
        raise LovstudioError(
            f"Audio file does not exist: {audio_path}",
            operation=operation,
            field="file",
            source="local-input",
        )
    fields: List[Tuple[str, str]] = [("model", args.model)]
    if args.language:
        fields.append(("language", args.language))
    if args.prompt:
        fields.append(("prompt", args.prompt))
    if args.response_format:
        fields.append(("response_format", args.response_format))
    body, content_type = _multipart(fields, "file", audio_path)
    raw, response_content_type, headers = _request(
        operation,
        "POST",
        _endpoint(path),
        body=body,
        content_type=content_type,
        timeout=args.timeout,
    )
    decoded = _decode(raw, response_content_type)
    result: Dict[str, Any] = {
        "status": "ok",
        "operation": operation,
        "model": args.model,
        "text": decoded.get("text", "") if isinstance(decoded, dict) else decoded,
    }
    if isinstance(decoded, dict):
        for key in ("language", "duration", "segments"):
            if key in decoded:
                result[key] = decoded[key]
    if headers.get("x-request-id"):
        result["request_id"] = headers["x-request-id"]
    _print_json(result)
    return 0


def _speech(args: argparse.Namespace) -> int:
    if bool(args.text) == bool(args.text_file):
        raise LovstudioError(
            "Choose exactly one of --text and --text-file.",
            operation="audio.speech",
            field="input",
            source="local-input",
        )
    text = args.text
    if args.text_file:
        text = Path(args.text_file).expanduser().read_text(encoding="utf-8")
    if not text.strip():
        raise LovstudioError(
            "Speech input is empty.",
            operation="audio.speech",
            field="input",
            source="local-input",
        )
    output_path = Path(args.output).expanduser()
    payload = {
        "model": args.model,
        "input": text,
        "voice": args.voice,
        "response_format": args.response_format,
    }
    raw, _content_type, headers = _request(
        "audio.speech",
        "POST",
        _endpoint("audio/speech"),
        body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        content_type="application/json",
        timeout=args.timeout,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(raw)
    result: Dict[str, Any] = {
        "status": "ok",
        "operation": "audio.speech",
        "model": args.model,
        "voice": args.voice,
        "format": args.response_format,
        "output": str(output_path),
        "bytes": len(raw),
    }
    if headers.get("x-request-id"):
        result["request_id"] = headers["x-request-id"]
    _print_json(result)
    return 0


def _config(_args: argparse.Namespace) -> int:
    _print_json(
        {
            "status": "ok",
            "operation": "config",
            "base_url": _base_url(),
            "defaults": {
                "chat_model": _env("LOVSTUDIO_CHAT_MODEL", DEFAULT_CHAT_MODEL),
                "transcribe_model": _env(
                    "LOVSTUDIO_TRANSCRIBE_MODEL", DEFAULT_TRANSCRIBE_MODEL
                ),
                "translate_model": _env(
                    "LOVSTUDIO_TRANSLATE_MODEL", DEFAULT_TRANSLATE_MODEL
                ),
                "speech_model": _env("LOVSTUDIO_SPEECH_MODEL", DEFAULT_SPEECH_MODEL),
            },
            "key_source": "LOVSTUDIO_API_KEY",
        }
    )
    return 0


def _print_json(value: Dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _error_json(error: LovstudioError) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "status": "error",
        "context_id": error.context_id,
        "operation": error.operation,
        "source": error.source,
        "message": _redact(error.message),
    }
    if error.field:
        result["field"] = error.field
    if error.status is not None:
        result["http_status"] = error.status
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    chat = subparsers.add_parser("chat", help="Call /v1/chat/completions")
    chat.add_argument("--prompt")
    chat.add_argument("--messages-json")
    chat.add_argument("--messages-file")
    chat.add_argument("--system")
    chat.add_argument("--model", default=_env("LOVSTUDIO_CHAT_MODEL", DEFAULT_CHAT_MODEL))
    chat.add_argument("--temperature", type=float)
    chat.add_argument("--max-tokens", type=int)
    chat.add_argument("--timeout", type=float, default=90.0)
    chat.set_defaults(handler=_chat)

    for command, path, default_model, help_text in (
        ("transcribe", "audio/transcriptions", DEFAULT_TRANSCRIBE_MODEL, "Call /v1/audio/transcriptions"),
        ("translate", "audio/translations", DEFAULT_TRANSLATE_MODEL, "Call /v1/audio/translations"),
    ):
        audio = subparsers.add_parser(command, help=help_text)
        audio.add_argument("--file", required=True)
        env_name = "LOVSTUDIO_TRANSCRIBE_MODEL" if command == "transcribe" else "LOVSTUDIO_TRANSLATE_MODEL"
        audio.add_argument("--model", default=_env(env_name, default_model))
        audio.add_argument("--language")
        audio.add_argument("--prompt")
        audio.add_argument("--response-format", default="json")
        audio.add_argument("--timeout", type=float, default=90.0)
        audio.set_defaults(handler=lambda args, op=command, endpoint=path: _audio_request(args, op, endpoint))

    speech = subparsers.add_parser("speech", help="Call /v1/audio/speech")
    speech.add_argument("--text")
    speech.add_argument("--text-file")
    speech.add_argument("--model", default=_env("LOVSTUDIO_SPEECH_MODEL", DEFAULT_SPEECH_MODEL))
    speech.add_argument("--voice", default=_env("LOVSTUDIO_SPEECH_VOICE", "alloy"))
    speech.add_argument("--response-format", default="mp3", choices=("mp3", "opus", "aac", "flac", "wav", "pcm"))
    speech.add_argument("--output", required=True)
    speech.add_argument("--timeout", type=float, default=90.0)
    speech.set_defaults(handler=_speech)

    config = subparsers.add_parser("config", help="Show resolved non-secret configuration")
    config.set_defaults(handler=_config)
    return parser


def main() -> int:
    parser = _parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except LovstudioError as error:
        print(json.dumps(_error_json(error), ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    except (OSError, UnicodeError) as error:
        wrapped = LovstudioError(
            _redact(str(error)),
            operation=args.command or "unknown",
            source="local-runtime",
        )
        print(json.dumps(_error_json(wrapped), ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
