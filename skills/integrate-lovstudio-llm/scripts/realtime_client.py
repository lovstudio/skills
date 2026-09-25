#!/usr/bin/env python3
"""Small dependency-free WebSocket client for LovStudio Realtime audio input.

The input must be mono PCM16 at 24 kHz. The client requests text output so it
can be used as a practical speech-to-text fallback when the HTTP transcription
route has no enabled transcription model.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import select
import socket
import ssl
import struct
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


DEFAULT_REALTIME_URL = "wss://llm.lovstudio.ai/v1/realtime"
DEFAULT_MODEL = "gpt-realtime"
DEFAULT_TRANSCRIPTION_MODEL = "gpt-4o-transcribe"
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class RealtimeError(Exception):
    def __init__(self, message: str, *, operation: str = "realtime") -> None:
        super().__init__(message)
        self.message = message
        self.operation = operation
        self.context_id = f"lovstudio-{uuid.uuid4().hex[:12]}"


def _key() -> str:
    value = os.environ.get("LOVSTUDIO_API_KEY", "").strip()
    if not value:
        raise RealtimeError("Set LOVSTUDIO_API_KEY in the process environment.", operation="config")
    return value


def _url(model: str) -> str:
    raw = os.environ.get("LOVSTUDIO_REALTIME_URL", "").strip()
    if not raw:
        base = os.environ.get("LOVSTUDIO_BASE_URL", "").strip().rstrip("/")
        if base:
            raw = f"{base}/realtime"
        else:
            raw = DEFAULT_REALTIME_URL
    if raw.startswith("http://"):
        raw = "ws://" + raw[len("http://") :]
    elif raw.startswith("https://"):
        raw = "wss://" + raw[len("https://") :]
    parsed = urlsplit(raw)
    if parsed.scheme not in {"ws", "wss"} or not parsed.hostname:
        raise RealtimeError("LOVSTUDIO_REALTIME_URL must be a ws:// or wss:// URL.", operation="config")
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("model", model)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", urlencode(query), parsed.fragment))


def _proxy_for(host: str) -> Optional[Tuple[str, int, Optional[str]]]:
    if host in {"127.0.0.1", "localhost", "::1"}:
        return None
    raw = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if not raw:
        return None
    parsed = urlsplit(raw)
    if not parsed.hostname:
        return None
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    proxy_auth = None
    if parsed.username:
        credentials = f"{parsed.username}:{parsed.password or ''}".encode("utf-8")
        proxy_auth = base64.b64encode(credentials).decode("ascii")
    return parsed.hostname, port, proxy_auth


def _read_until(sock: socket.socket, marker: bytes, limit: int = 65536) -> bytes:
    data = bytearray()
    while marker not in data:
        chunk = sock.recv(4096)
        if not chunk:
            raise RealtimeError("Realtime socket closed during handshake.")
        data.extend(chunk)
        if len(data) > limit:
            raise RealtimeError("Realtime handshake response is too large.")
    return bytes(data)


def _connect(url: str, token: str) -> socket.socket:
    parsed = urlsplit(url)
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "wss" else 80)
    proxy = _proxy_for(host)
    if proxy:
        proxy_host, proxy_port, proxy_auth = proxy
        sock = socket.create_connection((proxy_host, proxy_port), timeout=20)
        connect_lines = [
            f"CONNECT {host}:{port} HTTP/1.1",
            f"Host: {host}:{port}",
            "Connection: keep-alive",
        ]
        if proxy_auth:
            connect_lines.append(f"Proxy-Authorization: Basic {proxy_auth}")
        sock.sendall(("\r\n".join(connect_lines) + "\r\n\r\n").encode("ascii"))
        response = _read_until(sock, b"\r\n\r\n").split(b"\r\n", 1)[0]
        if b" 200 " not in response:
            sock.close()
            raise RealtimeError("HTTPS proxy did not establish the Realtime tunnel.", operation="network")
    else:
        sock = socket.create_connection((host, port), timeout=20)
    if parsed.scheme == "wss":
        context = ssl.create_default_context()
        sock = context.wrap_socket(sock, server_hostname=host)

    websocket_key = base64.b64encode(os.urandom(16)).decode("ascii")
    path = parsed.path or "/"
    if parsed.query:
        path += f"?{parsed.query}"
    lines = [
        f"GET {path} HTTP/1.1",
        f"Host: {host}:{port}",
        "Upgrade: websocket",
        "Connection: Upgrade",
        f"Sec-WebSocket-Key: {websocket_key}",
        "Sec-WebSocket-Version: 13",
        f"Authorization: Bearer {token}",
        "OpenAI-Beta: realtime=v1",
    ]
    sock.sendall(("\r\n".join(lines) + "\r\n\r\n").encode("ascii"))
    response = _read_until(sock, b"\r\n\r\n").decode("iso-8859-1")
    status_line = response.split("\r\n", 1)[0]
    if " 101 " not in status_line:
        sock.close()
        raise RealtimeError(f"Realtime WebSocket handshake returned {status_line}.", operation="network")
    expected = base64.b64encode(hashlib.sha1((websocket_key + WS_GUID).encode("ascii")).digest()).decode("ascii")
    response_headers = {}
    for line in response.split("\r\n")[1:]:
        if ":" in line:
            name, value = line.split(":", 1)
            response_headers[name.strip().lower()] = value.strip()
    if response_headers.get("sec-websocket-accept") != expected:
        sock.close()
        raise RealtimeError("Realtime WebSocket accept header did not match.", operation="network")
    sock.settimeout(5.0)
    return sock


def _send_frame(sock: socket.socket, payload: bytes, opcode: int = 1) -> None:
    first = 0x80 | (opcode & 0x0F)
    length = len(payload)
    if length < 126:
        header = bytes([first, 0x80 | length])
    elif length < 65536:
        header = bytes([first, 0x80 | 126]) + struct.pack("!H", length)
    else:
        header = bytes([first, 0x80 | 127]) + struct.pack("!Q", length)
    mask = os.urandom(4)
    masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
    sock.sendall(header + mask + masked)


def _send_json(sock: socket.socket, value: Dict[str, Any]) -> None:
    _send_frame(sock, json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    payload = bytearray()
    while len(payload) < size:
        chunk = sock.recv(size - len(payload))
        if not chunk:
            raise RealtimeError("Realtime socket closed while reading a frame.", operation="network")
        payload.extend(chunk)
    return bytes(payload)


def _receive_frame(sock: socket.socket) -> Tuple[int, bytes]:
    header = _recv_exact(sock, 2)
    first, second = header
    opcode = first & 0x0F
    length = second & 0x7F
    if length == 126:
        length = struct.unpack("!H", _recv_exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", _recv_exact(sock, 8))[0]
    masked = bool(second & 0x80)
    mask = _recv_exact(sock, 4) if masked else b""
    payload = bytearray(_recv_exact(sock, length))
    if masked:
        payload = bytearray(byte ^ mask[index % 4] for index, byte in enumerate(payload))
    return opcode, bytes(payload)


def _receive_event(sock: socket.socket, deadline: float) -> Optional[Dict[str, Any]]:
    remaining = max(0.1, deadline - time.monotonic())
    readable, _, _ = select.select([sock], [], [], min(1.0, remaining))
    if not readable:
        return None
    opcode, payload = _receive_frame(sock)
    if opcode == 8:
        raise RealtimeError("Realtime server closed the connection.", operation="network")
    if opcode == 9:
        _send_frame(sock, payload, opcode=10)
        return None
    if opcode != 1:
        return None
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RealtimeError("Realtime server returned an invalid JSON event.") from exc
    return decoded if isinstance(decoded, dict) else None


def _print(value: Dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False))


def _send_audio(sock: socket.socket, audio: bytes, chunk_ms: int) -> None:
    bytes_per_chunk = max(480, int(24000 * 2 * chunk_ms / 1000))
    delay = chunk_ms / 1000.0
    for offset in range(0, len(audio), bytes_per_chunk):
        chunk = audio[offset : offset + bytes_per_chunk]
        _send_json(
            sock,
            {"type": "input_audio_buffer.append", "audio": base64.b64encode(chunk).decode("ascii")},
        )
        time.sleep(delay)
    _send_json(sock, {"type": "input_audio_buffer.commit"})


def _error(error: RealtimeError) -> Dict[str, Any]:
    return {
        "status": "error",
        "context_id": error.context_id,
        "operation": error.operation,
        "message": error.message,
    }


def run(args: argparse.Namespace) -> int:
    audio_path = Path(args.file).expanduser()
    if not audio_path.is_file():
        raise RealtimeError(f"Audio file does not exist: {audio_path}", operation="local-input")
    audio = audio_path.read_bytes()
    if not audio:
        raise RealtimeError("Audio file is empty.", operation="local-input")
    token = _key()
    url = _url(args.model)
    started = time.monotonic()
    sock = _connect(url, token)
    response_text = ""
    transcript = ""
    sent_audio = False
    try:
        deadline = started + args.timeout
        while time.monotonic() < deadline:
            event = _receive_event(sock, deadline)
            if not event:
                continue
            event_type = event.get("type")
            if event_type == "session.created":
                _print({"event": event_type, "model": event.get("session", {}).get("model")})
                session: Dict[str, Any] = {
                    "modalities": ["text"],
                    "instructions": args.instructions,
                    "input_audio_format": "pcm16",
                    "turn_detection": None,
                }
                if args.transcription_model.lower() != "none":
                    session["input_audio_transcription"] = {"model": args.transcription_model}
                _send_json(sock, {"type": "session.update", "session": session})
            elif event_type == "session.updated":
                _print({"event": event_type})
                _send_audio(sock, audio, args.chunk_ms)
                sent_audio = True
                response: Dict[str, Any] = {"modalities": ["text"]}
                if args.response_instructions:
                    response["instructions"] = args.response_instructions
                _send_json(sock, {"type": "response.create", "response": response})
                _print({"event": "audio_sent", "bytes": len(audio)})
            elif event_type == "conversation.item.input_audio_transcription.completed":
                transcript = str(event.get("transcript") or "")
                _print({"event": event_type, "transcript": transcript})
            elif event_type in {"response.text.delta", "response.output_text.delta", "response.audio_transcript.delta"}:
                response_text += str(event.get("delta") or "")
            elif event_type in {"response.text.done", "response.output_text.done", "response.audio_transcript.done"}:
                if isinstance(event.get("text"), str):
                    response_text = event["text"]
                if isinstance(event.get("transcript"), str):
                    response_text = event["transcript"]
                _print({"event": event_type, "text": response_text.strip()})
            elif event_type == "error":
                error = event.get("error") if isinstance(event.get("error"), dict) else {}
                raise RealtimeError(
                    str(error.get("message") or "Realtime API returned an error."),
                    operation="realtime",
                )
            elif event_type == "response.done":
                status = event.get("response", {}).get("status")
                _print({"event": event_type, "status": status})
                _print(
                    {
                        "status": "ok" if status == "completed" else "error",
                        "operation": "realtime",
                        "model": args.model,
                        "audio_sent": sent_audio,
                        "transcript": transcript.strip(),
                        "response_text": response_text.strip(),
                        "elapsed_ms": int((time.monotonic() - started) * 1000),
                    }
                )
                return 0 if status == "completed" else 2
        raise RealtimeError("Realtime response timed out.", operation="realtime")
    finally:
        try:
            _send_frame(sock, b"", opcode=8)
        except OSError:
            pass
        sock.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, help="Mono PCM16 24 kHz raw audio file")
    parser.add_argument("--model", default=os.environ.get("LOVSTUDIO_REALTIME_MODEL", DEFAULT_MODEL))
    parser.add_argument("--instructions", default="请用中文简洁回答用户。")
    parser.add_argument("--response-instructions")
    parser.add_argument(
        "--transcription-model",
        default=os.environ.get("LOVSTUDIO_REALTIME_TRANSCRIPTION_MODEL", DEFAULT_TRANSCRIPTION_MODEL),
    )
    parser.add_argument("--chunk-ms", type=int, default=40)
    parser.add_argument("--timeout", type=float, default=45.0)
    args = parser.parse_args()
    try:
        return run(args)
    except (RealtimeError, OSError, ssl.SSLError) as error:
        wrapped = error if isinstance(error, RealtimeError) else RealtimeError(str(error), operation="runtime")
        print(json.dumps(_error(wrapped), ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
