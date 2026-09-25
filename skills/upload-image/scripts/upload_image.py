#!/usr/bin/env python3
"""Upload local images through PicGo and rewrite local Markdown image URLs."""

from __future__ import annotations

import argparse
import html
import json
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
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_SERVER_URL = "http://127.0.0.1:36677"
DEFAULT_TIMEOUT = 120.0
URL_RE = re.compile(r"https?://[^\s<>\"']+")
REMOTE_PREFIX_RE = re.compile(
    r"^(?:https?:|data:|blob:|ftp:|mailto:|tel:|#|//)", re.IGNORECASE
)
INLINE_IMAGE_RE = re.compile(
    r"!\[[^\]\n]*\]\(\s*"
    r"(?P<path><[^>\n]+>|(?:\\.|[^()\s]|\([^()\n]*\))+?)"
    r"(?P<title>\s+(?:\"[^\"\n]*\"|'[^'\n]*'|\([^()\n]*\)))?\s*\)"
)
HTML_IMAGE_RE = re.compile(
    r"<img\b[^>]*?\bsrc\s*=\s*(?P<quote>['\"])(?P<path>[^'\"]+)(?P=quote)",
    re.IGNORECASE,
)
WIKI_IMAGE_RE = re.compile(
    r"!\[\[(?P<path>[^\]|\n]+)(?:\|(?P<label>[^\]\n]+))?\]\]"
)
IMAGE_REFERENCE_USE_RE = re.compile(
    r"!\[(?P<alt>[^\]\n]*)\]\[(?P<id>[^\]\n]*)\]"
)
REFERENCE_DEFINITION_RE = re.compile(
    r"(?m)^[ \t]{0,3}\[(?P<id>[^\]\n]+)\]:[ \t]*"
    r"(?P<path><[^>\n]+>|\S+)"
)
INLINE_CODE_RE = re.compile(r"(?P<ticks>`+)[^\n]*?(?P=ticks)")


class UploadImageError(RuntimeError):
    """A user-facing, classified error."""

    def __init__(self, message: str, code: str = "runtime") -> None:
        super().__init__(message)
        self.code = code


class BackendUnavailable(UploadImageError):
    """Raised only when the selected PicGo transport cannot be reached."""


@dataclass(frozen=True)
class UploadResult:
    source: Path
    url: str


@dataclass(frozen=True)
class Occurrence:
    start: int
    end: int
    raw_path: str
    replacement_kind: str = "plain"
    label: str = ""


@dataclass(frozen=True)
class ResolvedOccurrence:
    occurrence: Occurrence
    source: Path


def _normalize_reference_id(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _range_contains(ranges: Sequence[Tuple[int, int]], start: int, end: int) -> bool:
    return any(start < blocked_end and end > blocked_start for blocked_start, blocked_end in ranges)


def _fenced_code_ranges(text: str) -> List[Tuple[int, int]]:
    ranges: List[Tuple[int, int]] = []
    active_char: Optional[str] = None
    active_length = 0
    active_start = 0
    offset = 0
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^[ \t]{0,3}(`{3,}|~{3,})", line)
        if active_char is None and marker:
            active_char = marker.group(1)[0]
            active_length = len(marker.group(1))
            active_start = offset
        elif active_char is not None:
            closing = re.match(
                r"^[ \t]{0,3}" + re.escape(active_char) + "{" + str(active_length) + r",}[ \t]*$",
                line.rstrip("\r\n"),
            )
            if closing:
                ranges.append((active_start, offset + len(line)))
                active_char = None
                active_length = 0
        offset += len(line)
    if active_char is not None:
        ranges.append((active_start, len(text)))
    return ranges


def find_image_occurrences(text: str) -> List[Occurrence]:
    """Return editable Markdown image references outside code spans and fences."""
    blocked = _fenced_code_ranges(text)
    blocked.extend((match.start(), match.end()) for match in INLINE_CODE_RE.finditer(text))
    occurrences: List[Occurrence] = []

    for match in INLINE_IMAGE_RE.finditer(text):
        start, end = match.span("path")
        if not _range_contains(blocked, start, end):
            kind = "angle" if match.group("path").startswith("<") else "plain"
            occurrences.append(Occurrence(start, end, match.group("path"), kind))

    for match in HTML_IMAGE_RE.finditer(text):
        start, end = match.span("path")
        if not _range_contains(blocked, start, end):
            occurrences.append(Occurrence(start, end, match.group("path")))

    for match in WIKI_IMAGE_RE.finditer(text):
        start, end = match.span()
        if not _range_contains(blocked, start, end):
            label = match.group("label") or Path(match.group("path")).stem
            occurrences.append(
                Occurrence(start, end, match.group("path"), "wiki", label)
            )

    image_reference_ids = set()
    for match in IMAGE_REFERENCE_USE_RE.finditer(text):
        if _range_contains(blocked, match.start(), match.end()):
            continue
        reference_id = match.group("id") or match.group("alt")
        image_reference_ids.add(_normalize_reference_id(reference_id))

    for match in REFERENCE_DEFINITION_RE.finditer(text):
        if _normalize_reference_id(match.group("id")) not in image_reference_ids:
            continue
        start, end = match.span("path")
        if not _range_contains(blocked, start, end):
            kind = "angle" if match.group("path").startswith("<") else "plain"
            occurrences.append(Occurrence(start, end, match.group("path"), kind))

    occurrences.sort(key=lambda item: (item.start, item.end))
    accepted: List[Occurrence] = []
    for occurrence in occurrences:
        if accepted and occurrence.start < accepted[-1].end:
            continue
        accepted.append(occurrence)
    return accepted


def _is_remote_reference(value: str) -> bool:
    return bool(REMOTE_PREFIX_RE.match(html.unescape(value.strip().lstrip("<").rstrip(">"))))


def resolve_local_reference(raw_path: str, base_dir: Path) -> Optional[Path]:
    """Resolve one Markdown path; return None for an already remote reference."""
    value = html.unescape(raw_path.strip())
    if value.startswith("<") and value.endswith(">"):
        value = value[1:-1]
    if _is_remote_reference(value):
        return None

    value = value.replace("\\ ", " ").replace("\\(", "(").replace("\\)", ")")
    if value.lower().startswith("file://"):
        parsed_file = urllib.parse.urlsplit(value)
        if parsed_file.netloc not in ("", "localhost"):
            raise UploadImageError(
                "Markdown contains a non-local file URL host.", "markdown_input"
            )
        value = urllib.parse.unquote(parsed_file.path)
    else:
        parsed = urllib.parse.urlsplit(value)
        value = urllib.parse.unquote(parsed.path)

    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    candidate = candidate.resolve()
    if not candidate.is_file():
        raise UploadImageError(
            "Local image reference does not exist: " + raw_path, "markdown_input"
        )
    return candidate


def resolve_markdown_occurrences(
    text: str, markdown_path: Path
) -> List[ResolvedOccurrence]:
    resolved: List[ResolvedOccurrence] = []
    failures: List[str] = []
    for occurrence in find_image_occurrences(text):
        try:
            source = resolve_local_reference(occurrence.raw_path, markdown_path.parent)
        except UploadImageError:
            failures.append(occurrence.raw_path)
            continue
        if source is not None:
            resolved.append(ResolvedOccurrence(occurrence, source))
    if failures:
        shown = ", ".join(failures[:5])
        suffix = "" if len(failures) <= 5 else " and %d more" % (len(failures) - 5)
        raise UploadImageError(
            "Missing local image references: " + shown + suffix, "markdown_input"
        )
    return resolved


def unique_paths(resolved: Sequence[ResolvedOccurrence]) -> List[Path]:
    seen = set()
    paths: List[Path] = []
    for item in resolved:
        key = str(item.source)
        if key not in seen:
            seen.add(key)
            paths.append(item.source)
    return paths


def rewrite_markdown(
    text: str, resolved: Sequence[ResolvedOccurrence], url_by_path: Dict[str, str]
) -> str:
    edits: List[Tuple[int, int, str]] = []
    for item in resolved:
        occurrence = item.occurrence
        url = url_by_path[str(item.source)]
        if occurrence.replacement_kind == "angle":
            replacement = "<" + url + ">"
        elif occurrence.replacement_kind == "wiki":
            safe_label = occurrence.label.replace("]", "\\]")
            replacement = "![" + safe_label + "](" + url + ")"
        else:
            replacement = url
        edits.append((occurrence.start, occurrence.end, replacement))
    for start, end, replacement in sorted(edits, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def _request_json(
    url: str,
    payload: Dict[str, Any],
    timeout: float,
    secret: Optional[str] = None,
) -> Dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if secret:
        headers["Authorization"] = "Bearer " + secret
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        message = "HTTP %d" % exc.code
        try:
            detail = json.loads(raw)
            message = str(detail.get("message") or detail.get("error") or message)
        except (json.JSONDecodeError, AttributeError):
            pass
        if exc.code == 404:
            raise BackendUnavailable("PicGo Server upload endpoint was not found.", "picgo_server")
        raise UploadImageError("PicGo Server rejected the request: " + message, "picgo_server")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise BackendUnavailable(
            "PicGo Server is unavailable at " + url + ": " + str(exc),
            "picgo_server",
        )
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise UploadImageError(
            "PicGo Server returned invalid JSON: " + str(exc), "picgo_server"
        )
    if not isinstance(decoded, dict):
        raise UploadImageError("PicGo Server returned a non-object response.", "picgo_server")
    return decoded


def _extract_response_urls(data: Dict[str, Any]) -> List[str]:
    urls: List[str] = []
    direct = data.get("imgUrl") or data.get("url")
    if isinstance(direct, str):
        urls.append(direct)
    items = data.get("items")
    if not urls and isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                value = item.get("imgUrl") or item.get("url")
                if isinstance(value, str):
                    urls.append(value)
    if not urls:
        result = data.get("result")
        if isinstance(result, str):
            urls = [result]
        elif isinstance(result, list):
            for item in result:
                if isinstance(item, str):
                    urls.append(item)
                elif isinstance(item, dict):
                    value = item.get("imgUrl") or item.get("url")
                    if isinstance(value, str):
                        urls.append(value)
    return urls


def upload_via_server(
    paths: Sequence[Path], server_url: str, timeout: float, secret: Optional[str]
) -> List[UploadResult]:
    endpoint = server_url.rstrip("/")
    if not endpoint.endswith("/upload"):
        endpoint += "/upload"
    data = _request_json(
        endpoint, {"list": [str(path) for path in paths]}, timeout, secret
    )
    if data.get("success") is not True:
        message = str(data.get("message") or data.get("error") or "upload failed")
        raise UploadImageError("PicGo upload failed: " + message, "picgo_server")
    urls = _extract_response_urls(data)
    if len(urls) != len(paths):
        raise UploadImageError(
            "PicGo returned %d URL(s) for %d input file(s)." % (len(urls), len(paths)),
            "picgo_server",
        )
    return _validate_result_urls(paths, urls)


def _picgo_major_version(binary: str) -> Optional[int]:
    try:
        process = subprocess.run(
            [binary, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r"(?:^|\s)v?(\d+)\.", process.stdout)
    return int(match.group(1)) if match else None


def _extract_cli_urls(output: str, expected: int) -> List[str]:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    for line in reversed(lines):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            urls = _extract_response_urls(value)
            if urls:
                return urls
        if isinstance(value, list):
            urls = []
            for item in value:
                if isinstance(item, str) and item.startswith(("http://", "https://")):
                    urls.append(item)
                elif isinstance(item, dict) and isinstance(item.get("imgUrl"), str):
                    urls.append(item["imgUrl"])
            if urls:
                return urls
    candidates: List[str] = []
    for line in lines:
        for match in URL_RE.finditer(line):
            candidate = match.group(0).rstrip(".,;)]}")
            if candidate not in candidates:
                candidates.append(candidate)
    return candidates[-expected:]


def upload_via_cli(
    paths: Sequence[Path], picgo_bin: Optional[str], timeout: float
) -> List[UploadResult]:
    binary = picgo_bin or os.environ.get("PICGO_BIN") or shutil.which("picgo")
    if not binary:
        raise BackendUnavailable(
            "PicGo CLI was not found in PATH and PICGO_BIN is not set.", "picgo_cli"
        )
    command = [binary, "upload"] + [str(path) for path in paths]
    if (_picgo_major_version(binary) or 0) >= 3:
        command += ["--format", "json"]
    try:
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise BackendUnavailable("PicGo CLI could not run: " + str(exc), "picgo_cli")
    if process.returncode != 0:
        tail = " | ".join(process.stdout.strip().splitlines()[-3:])
        raise UploadImageError(
            "PicGo CLI exited with code %d: %s" % (process.returncode, tail),
            "picgo_cli",
        )
    urls = _extract_cli_urls(process.stdout, len(paths))
    if len(urls) != len(paths):
        raise UploadImageError(
            "PicGo CLI returned %d URL(s) for %d input file(s)."
            % (len(urls), len(paths)),
            "picgo_cli",
        )
    return _validate_result_urls(paths, urls)


def _validate_result_urls(paths: Sequence[Path], urls: Sequence[str]) -> List[UploadResult]:
    results: List[UploadResult] = []
    for source, url in zip(paths, urls):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise UploadImageError("PicGo returned an invalid public URL.", "picgo_output")
        results.append(UploadResult(source, url))
    return results


def _secret_from_env(name: str) -> Optional[str]:
    value = os.environ.get(name, "").strip()
    return value or None


def _heartbeat(server_url: str, timeout: float, secret: Optional[str]) -> bool:
    endpoint = server_url.rstrip("/")
    if endpoint.endswith("/upload"):
        endpoint = endpoint[: -len("/upload")]
    data = _request_json(endpoint + "/heartbeat", {}, timeout, secret)
    return data.get("success") is True and data.get("result") == "alive"


def _start_picgo_app(server_url: str, timeout: float, secret: Optional[str]) -> bool:
    if sys.platform != "darwin" or not Path("/Applications/PicGo.app").exists():
        return False
    subprocess.run(
        ["open", "-gja", "PicGo"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    deadline = time.monotonic() + min(timeout, 15.0)
    while time.monotonic() < deadline:
        try:
            if _heartbeat(server_url, min(2.0, timeout), secret):
                return True
        except UploadImageError:
            pass
        time.sleep(0.4)
    return False


def upload_paths(paths: Sequence[Path], args: argparse.Namespace) -> List[UploadResult]:
    secret = _secret_from_env(args.secret_env)
    if args.backend in ("server", "auto"):
        try:
            return upload_via_server(paths, args.server_url, args.timeout, secret)
        except BackendUnavailable as server_error:
            if args.start_app and _start_picgo_app(args.server_url, args.timeout, secret):
                return upload_via_server(paths, args.server_url, args.timeout, secret)
            if args.backend == "server":
                raise server_error
            try:
                return upload_via_cli(paths, args.picgo_bin, args.timeout)
            except BackendUnavailable as cli_error:
                raise BackendUnavailable(
                    str(server_error) + " " + str(cli_error), "picgo_backend"
                )
    return upload_via_cli(paths, args.picgo_bin, args.timeout)


def verify_url(url: str, timeout: float) -> int:
    request = urllib.request.Request(
        url, method="HEAD", headers={"User-Agent": "lov-upload-image/0.1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return int(response.status)
    except urllib.error.HTTPError as exc:
        if exc.code not in (403, 405):
            raise UploadImageError(
                "Uploaded URL verification failed with HTTP %d." % exc.code,
                "verification",
            )
    except (urllib.error.URLError, TimeoutError, OSError):
        # Some origins or network intermediaries reject HEAD. Try one ranged GET
        # before classifying the URL as unreachable.
        pass
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": "lov-upload-image/0.1.0", "Range": "bytes=0-0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return int(response.status)
    except urllib.error.HTTPError as exc:
        raise UploadImageError(
            "Uploaded URL verification failed with HTTP %d." % exc.code,
            "verification",
        )
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise UploadImageError(
            "Uploaded URL verification failed: " + str(exc), "verification"
        )


def _prepare_direct_paths(values: Sequence[str]) -> List[Path]:
    paths: List[Path] = []
    for value in values:
        path = Path(value).expanduser().resolve()
        if not path.is_file():
            raise UploadImageError("Input image does not exist: " + value, "input")
        paths.append(path)
    return paths


def _write_atomic(path: Path, content: str, mode_source: Optional[Path] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".lov-upload-image-", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if mode_source and mode_source.exists():
            os.chmod(temporary, mode_source.stat().st_mode)
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _default_markdown_output(source: Path) -> Path:
    return source.with_name(source.stem + ".uploaded" + source.suffix)


def _resolve_markdown_destinations(
    args: argparse.Namespace, source: Path
) -> Tuple[Path, Optional[Path]]:
    if args.in_place and args.output:
        raise UploadImageError("Use either --in-place or --output, not both.", "input")
    if args.no_backup and not args.in_place:
        raise UploadImageError("--no-backup is valid only with --in-place.", "input")
    output = source if args.in_place else (
        Path(args.output).expanduser().resolve() if args.output else _default_markdown_output(source)
    )
    if output == source and not args.in_place:
        raise UploadImageError(
            "Use --in-place when the output target is the source Markdown file.", "output"
        )
    if output.exists() and output != source and not args.force:
        raise UploadImageError(
            "Output already exists; use --force or choose another --output.", "output"
        )
    backup = None if not args.in_place or args.no_backup else source.with_name(source.name + ".bak")
    if backup and backup.exists() and not args.force:
        raise UploadImageError(
            "Backup already exists; use --force or --no-backup.", "output"
        )
    if not args.dry_run:
        try:
            output.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(prefix=".lov-upload-image-preflight-", dir=str(output.parent)):
                pass
        except OSError as exc:
            raise UploadImageError(
                "Markdown output directory is not writable: " + str(exc), "output"
            )
    return output, backup


def _result_payload(results: Sequence[UploadResult], verified: Dict[str, int]) -> Dict[str, Any]:
    return {
        "success": True,
        "uploaded": [
            {
                "source": str(result.source),
                "url": result.url,
                "http_status": verified.get(result.url),
            }
            for result in results
        ],
    }


def command_upload(args: argparse.Namespace) -> int:
    paths = _prepare_direct_paths(args.paths)
    results = upload_paths(paths, args)
    verified: Dict[str, int] = {}
    if args.verify:
        for result in results:
            verified[result.url] = verify_url(result.url, min(args.timeout, 20.0))
    if args.json:
        print(json.dumps(_result_payload(results, verified), ensure_ascii=False, indent=2))
    elif len(results) == 1:
        print(results[0].url)
    else:
        for result in results:
            print(result.source.name + " -> " + result.url)
    return 0


def command_markdown(args: argparse.Namespace) -> int:
    source = Path(args.markdown).expanduser().resolve()
    if not source.is_file():
        raise UploadImageError("Markdown input does not exist: " + args.markdown, "input")
    text = source.read_text(encoding="utf-8")
    resolved = resolve_markdown_occurrences(text, source)
    paths = unique_paths(resolved)
    if not paths:
        raise UploadImageError("Markdown contains no local image references.", "markdown_input")

    output, backup = _resolve_markdown_destinations(args, source)

    if args.dry_run:
        payload = {
            "success": True,
            "dry_run": True,
            "references": len(resolved),
            "unique_files": len(paths),
            "files": [str(path) for path in paths],
            "planned_output": str(output),
            "planned_backup": str(backup) if backup else None,
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print("references=%d unique_files=%d" % (len(resolved), len(paths)))
            for path in paths:
                print(path.name)
        return 0

    results = upload_paths(paths, args)
    verified: Dict[str, int] = {}
    if args.verify:
        for result in results:
            verified[result.url] = verify_url(result.url, min(args.timeout, 20.0))
    url_by_path = {str(result.source): result.url for result in results}
    rewritten = rewrite_markdown(text, resolved, url_by_path)
    if backup:
        shutil.copy2(str(source), str(backup))
    _write_atomic(output, rewritten, source)

    payload = _result_payload(results, verified)
    payload.update(
        {
            "markdown": str(source),
            "output": str(output),
            "backup": str(backup) if backup else None,
            "references_rewritten": len(resolved),
            "unique_files_uploaded": len(paths),
        }
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("output=" + str(output))
        print("references_rewritten=%d unique_files_uploaded=%d" % (len(resolved), len(paths)))
        if backup:
            print("backup=" + str(backup))
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    secret = _secret_from_env(args.secret_env)
    server_alive = False
    server_error: Optional[str] = None
    try:
        server_alive = _heartbeat(args.server_url, min(args.timeout, 3.0), secret)
    except UploadImageError as exc:
        server_error = str(exc)
    binary = args.picgo_bin or os.environ.get("PICGO_BIN") or shutil.which("picgo")
    payload = {
        "success": server_alive or bool(binary),
        "server_url": args.server_url,
        "server_alive": server_alive,
        "server_error": server_error,
        "cli": binary,
        "macos_app_installed": Path("/Applications/PicGo.app").exists(),
        "secret_env_set": bool(secret),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("server_alive=" + str(server_alive).lower())
        print("server_url=" + args.server_url)
        print("cli=" + (binary or "not-found"))
        print("macos_app_installed=" + str(payload["macos_app_installed"]).lower())
        if server_error:
            print("server_error=" + server_error)
    return 0 if payload["success"] else 1


def _add_backend_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--backend",
        choices=("auto", "server", "cli"),
        default=os.environ.get("PICGO_BACKEND", "auto"),
        help="PicGo transport; auto prefers the GUI/Core Server API.",
    )
    parser.add_argument(
        "--server-url",
        default=os.environ.get("PICGO_SERVER_URL", DEFAULT_SERVER_URL),
        help="PicGo Server base URL (default: %(default)s).",
    )
    parser.add_argument("--picgo-bin", help="Explicit PicGo-Core CLI path.")
    parser.add_argument(
        "--secret-env",
        default="PICGO_SERVER_SECRET",
        help="Name of the environment variable containing the PicGo Server secret.",
    )
    parser.add_argument(
        "--start-app",
        action="store_true",
        help="On macOS, start an installed PicGo.app if the server is unavailable.",
    )
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT, help="Upload timeout in seconds."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Upload local images through the user's existing PicGo configuration."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    upload_parser = subparsers.add_parser("upload", help="Upload one or more local images.")
    upload_parser.add_argument("paths", nargs="+")
    upload_parser.add_argument("--verify", action="store_true", help="Verify returned URLs.")
    upload_parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    _add_backend_arguments(upload_parser)
    upload_parser.set_defaults(handler=command_upload)

    markdown_parser = subparsers.add_parser(
        "markdown", help="Upload and rewrite local images in one Markdown document."
    )
    markdown_parser.add_argument("markdown")
    markdown_parser.add_argument("--output")
    markdown_parser.add_argument("--in-place", action="store_true")
    markdown_parser.add_argument("--no-backup", action="store_true")
    markdown_parser.add_argument("--force", action="store_true")
    markdown_parser.add_argument("--dry-run", action="store_true")
    markdown_parser.add_argument("--verify", action="store_true", help="Verify returned URLs.")
    markdown_parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    _add_backend_arguments(markdown_parser)
    markdown_parser.set_defaults(handler=command_markdown)

    doctor_parser = subparsers.add_parser("doctor", help="Inspect PicGo availability safely.")
    doctor_parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    _add_backend_arguments(doctor_parser)
    doctor_parser.set_defaults(handler=command_doctor)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        return int(args.handler(args))
    except UploadImageError as exc:
        context_id = "lov-upload-image-" + uuid.uuid4().hex[:8]
        print(
            "ERROR context_id=%s code=%s: %s" % (context_id, exc.code, exc),
            file=sys.stderr,
        )
        return 2
    except Exception as exc:
        context_id = "lov-upload-image-" + uuid.uuid4().hex[:8]
        print(
            "ERROR context_id=%s code=internal: %s: %s"
            % (context_id, type(exc).__name__, exc),
            file=sys.stderr,
        )
        return 2
    except KeyboardInterrupt:
        print("ERROR context_id=lov-upload-image-interrupted code=interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
