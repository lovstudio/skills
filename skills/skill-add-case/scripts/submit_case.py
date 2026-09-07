#!/usr/bin/env python3
"""Prepare, check and publish a case through the signed-in website API."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import importlib.util
import ipaddress
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ORIGIN = "https://lovstudio.ai"
MIB = 1024 * 1024
ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SESSION = re.compile(r"https://lovstudio\.ai/yoda/session/yss_[A-Za-z0-9_-]{43}(?:\?detail=(?:concise|full))?")
SECRET = re.compile(r"/(?:Users|home)/|[A-Z]:\\Users\\|-----BEGIN [A-Z ]*PRIVATE KEY-----|\b(?:sk_live_|sk-proj-|ghp_|github_pat_)[A-Za-z0-9_]{12,}|Bearer\s+[A-Za-z0-9._-]{20,}", re.I)


class SubmissionError(ValueError):
    def __init__(self, message: str, status: int = 0):
        super().__init__(message)
        self.status = status


def encoded(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def fingerprint(payload: dict) -> str:
    # Approval covers text, image bytes and the optional Session, not transport flags.
    return hashlib.sha256(encoded({k: v for k, v in payload.items() if k not in {"consent", "dryRun"}})).hexdigest()


def read_json(path: Path) -> Any:
    if path.stat().st_size > 3 * MIB:
        raise SubmissionError("payload_too_large: JSON must be at most 3 MiB")
    return json.loads(path.read_text(encoding="utf-8"))


def keys(value: Any, allowed: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) - allowed:
        raise SubmissionError(f"invalid_case: unsupported {label} fields; do not include session, price or transcripts")


def string(value: Any, low: int, high: int, label: str) -> None:
    if not isinstance(value, str) or not low <= len(value.strip().encode("utf-16-le")) // 2 <= high:
        raise SubmissionError(f"invalid_case: {label} must contain {low}–{high} characters")


def public_url(value: str) -> bool:
    try:
        url = urllib.parse.urlsplit(value)
        host = url.hostname or ""
        if url.scheme != "https" or url.username or url.password or url.port or "." not in host:
            return False
        if host.endswith((".local", ".internal", ".localhost")):
            return False
        try:
            return ipaddress.ip_address(host).is_global
        except ValueError:
            return True
    except ValueError:
        return False


def validate(payload: Any) -> dict:
    keys(payload, {"case", "images", "sessionUrl", "consent", "dryRun"}, "submission")
    case = payload.get("case")
    keys(case, {"id", "type", "title", "description", "input", "prompt", "output", "author", "cover", "gallery", "evidence"}, "case")
    if not isinstance(case.get("id"), str) or not 3 <= len(case["id"]) <= 100 or not ID.fullmatch(case["id"]):
        raise SubmissionError("invalid_case: use a stable lowercase kebab-case id (3–100 characters)")
    if case.get("type") != "case":
        raise SubmissionError("invalid_case: type must be case")
    for key, low, high in [("title", 2, 120), ("description", 5, 1200), ("prompt", 1, 8000)]:
        string(case.get(key), low, high, key)
    if "author" in case:
        string(case["author"], 0, 80, "author")
    for key in ("input", "output"):
        field = case.get(key)
        keys(field, {"text", "items"}, key)
        if "text" in field:
            string(field["text"], 0, 8000, key)
        items = field.get("items", [])
        if not isinstance(items, list) or len(items) > 20:
            raise SubmissionError(f"invalid_case: {key}.items supports at most 20 items")
        for item in items:
            string(item, 1, 2000, key)
        if not (field.get("text", "").strip() or items):
            raise SubmissionError(f"invalid_case: {key} is required")
    evidence = case.get("evidence")
    keys(evidence, {"acceptance", "verified_at", "method", "privacy", "artifact_type"}, "evidence")
    if evidence.get("acceptance") != "user-confirmed" or evidence.get("artifact_type") not in ("visual", "other"):
        raise SubmissionError("invalid_case: explicit acceptance and artifact_type visual/other are required")
    try:
        date = dt.date.fromisoformat(evidence["verified_at"])
        if date.isoformat() != evidence["verified_at"] or date > dt.datetime.now(dt.timezone.utc).date() + dt.timedelta(days=1):
            raise ValueError()
    except (KeyError, TypeError, ValueError):
        raise SubmissionError("invalid_case: verified_at must be a real acceptance date YYYY-MM-DD") from None
    for key in ("method", "privacy"):
        string(evidence.get(key), 2, 1200, key)
    gallery = case.get("gallery", [])
    if not isinstance(gallery, list) or len(gallery) > 3:
        raise SubmissionError("invalid_case: gallery supports at most 3 images")
    refs = ([case["cover"]] if "cover" in case else []) + gallery
    if evidence["artifact_type"] == "visual" and not case.get("cover"):
        raise SubmissionError("visual_cover_required: attach the accepted final image")
    images = payload.get("images", [])
    if not isinstance(images, list) or len(images) > 4:
        raise SubmissionError("images_too_large: at most 4 images")
    total = 0
    for index, image in enumerate(images):
        keys(image, {"contentType", "dataBase64"}, "image")
        try:
            data = base64.b64decode(image["dataBase64"], validate=True)
        except (KeyError, TypeError, ValueError):
            raise SubmissionError("invalid_image: use base64 PNG, JPEG or WebP") from None
        kind = image_type(data)
        if kind != image.get("contentType"):
            raise SubmissionError("invalid_image: content does not match the declared image type")
        if len(data) > MIB:
            raise SubmissionError("images_too_large: each image must be at most 1 MiB")
        total += len(data)
        if f"upload:{index}" not in refs:
            raise SubmissionError("unused_image: reference each upload in cover or gallery")
    if total > 2 * MIB:
        raise SubmissionError("images_too_large: images together must be at most 2 MiB")
    for ref in refs:
        if not isinstance(ref, str):
            raise SubmissionError("invalid_image: expected an HTTPS URL or upload reference")
        if re.fullmatch(r"upload:[0-3]", ref):
            if int(ref[-1]) >= len(images):
                raise SubmissionError("missing_image: upload reference has no image")
        elif len(ref) > 2000 or not public_url(ref):
            raise SubmissionError("invalid_image: use a public HTTPS URL or --image; local paths are not public")
    if "sessionUrl" in payload and (not isinstance(payload["sessionUrl"], str) or not SESSION.fullmatch(payload["sessionUrl"])):
        raise SubmissionError("invalid_case: sessionUrl must be your existing public LovStudio Session URL")
    if SECRET.search(json.dumps(case, ensure_ascii=False).replace("\\\\", "\\")):
        raise SubmissionError("private_content_detected: redact secrets and private paths")
    for flag in ("consent", "dryRun"):
        if flag in payload and not isinstance(payload[flag], bool):
            raise SubmissionError(f"invalid_case: {flag} must be boolean")
    payload = {**payload, "images": images, "consent": False, "dryRun": True}
    if len(encoded(payload)) > 3 * MIB:
        raise SubmissionError("payload_too_large: request must be at most 3 MiB")
    return payload


def image_type(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    raise SubmissionError("invalid_image: only PNG, JPEG and WebP are supported")


def prepare(case_path: Path, image_paths: list[Path], session_url: str | None) -> dict:
    case = read_json(case_path)
    if not isinstance(case, dict):
        raise SubmissionError("invalid_case: --case expects one public case object")
    case.setdefault("type", "case")
    case.setdefault("id", "case-" + hashlib.sha256(encoded(case)).hexdigest()[:20])
    images = []
    if image_paths and (case.get("cover") or case.get("gallery")):
        raise SubmissionError("invalid_image: use --image or existing cover/gallery, not both")
    if len(image_paths) > 4:
        raise SubmissionError("images_too_large: at most 4 images")
    for path in image_paths:
        if path.stat().st_size > MIB:
            raise SubmissionError("images_too_large: compress to 1 MiB or upload in the website editor")
        data = path.read_bytes()
        images.append({"contentType": image_type(data), "dataBase64": base64.b64encode(data).decode("ascii")})
    if images:
        case["cover"] = "upload:0"
        if len(images) > 1:
            case["gallery"] = [f"upload:{i}" for i in range(1, len(images))]
    return validate({"case": case, "images": images, **({"sessionUrl": session_url} if session_url else {})})


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def http_json(method: str, url: str, body: dict | None = None, token: str | None = None, timeout: int = 60) -> dict:
    headers = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "Mozilla/5.0 LovStudioCaseContributor"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    # The case API expects plain JSON; the Session uploader's gzip transport is incompatible.
    req = urllib.request.Request(url, data=encoded(body) if body is not None else None, headers=headers, method=method)
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=timeout) as response:
            result = json.load(response)
        if not isinstance(result, dict):
            raise SubmissionError("invalid_response: expected a JSON object")
        return result
    except urllib.error.HTTPError as exc:
        try:
            error = json.loads(exc.read()).get("error", "request_failed")
        except (ValueError, AttributeError):
            error = "request_failed"
        # Never echo arbitrary server bodies or credentials into diagnostics.
        code = error if isinstance(error, str) and re.fullmatch(r"[a-z_]{1,80}", error) else "request_failed"
        raise SubmissionError(f"HTTP {exc.code}: {code}; keep the same case.id when retrying", exc.code) from None
    except (urllib.error.URLError, TimeoutError):
        raise SubmissionError("network_error: retry the same payload and case.id; publication may have succeeded") from None


def load_auth(path: Path | None):
    from add_case_with_session import resolve_share_script
    script = resolve_share_script(path)
    spec = importlib.util.spec_from_file_location("lov_case_shared_auth", script)
    if not spec or not spec.loader:
        raise SubmissionError("auth_unavailable: install lov-share-session")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def authenticated_post(url: str, payload: dict, args: argparse.Namespace, auth) -> dict:
    options = argparse.Namespace(token=None, profile_path=args.profile_path, base_url=ORIGIN, timeout=args.timeout)
    try:
        token = auth.load_access_token(options)
        try:
            return http_json("POST", url, payload, token, args.timeout)
        except SubmissionError as exc:
            if exc.status != 401 or any(os.environ.get(name) for name in ("LOVSTUDIO_ACCESS_TOKEN", "YODA_ACCESS_TOKEN")):
                raise
        refresh = auth.load_refresh_token(args.profile_path)
        try:
            token = auth.run_refresh(ORIGIN, refresh, args.timeout, args.profile_path) if refresh else auth.device_flow_signin(options)
        except auth.ShareError:
            token = auth.device_flow_signin(options)
        return http_json("POST", url, payload, token, args.timeout)
    except auth.ShareError:
        raise SubmissionError("auth_failed: complete LovStudio device sign-in and retry; never share credentials") from None


def contract(skill: str, timeout: int) -> dict:
    if not ID.fullmatch(skill):
        raise SubmissionError("invalid_skill: use the exact ID from the website URL")
    endpoint = f"{ORIGIN}/api/skills/{skill}/cases"
    result = http_json("GET", endpoint, timeout=timeout)
    if result.get("skillId") != skill or result.get("endpoint") != endpoint or result.get("formUrl") != f"{ORIGIN}/skills/{skill}/cases/new":
        raise SubmissionError("contract_mismatch: do not send credentials to an unexpected endpoint")
    if result.get("available") is not True:
        raise SubmissionError("source_write_unavailable: retain the draft; the website operator must enable this source")
    return result


def run(args: argparse.Namespace) -> dict:
    if not ID.fullmatch(args.skill):
        raise SubmissionError("invalid_skill: use the exact ID from the website URL")
    form = f"{ORIGIN}/skills/{args.skill}/cases/new"
    if args.action == "contract":
        return contract(args.skill, args.timeout)
    if args.action == "prepare":
        payload = prepare(args.case, args.image, args.session_url)
        # Exclusive creation preserves an existing user's draft.
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        return {"status": "prepared", "submission": str(args.output), "payloadFingerprint": fingerprint(payload), "formUrl": form, "contract": "not_checked"}
    payload = validate(read_json(args.submission))
    digest = fingerprint(payload)
    if args.action == "publish" and args.confirm != digest:
        raise SubmissionError("consent_mismatch: review this exact file and images, run check, then pass its payloadFingerprint to --confirm")
    api = contract(args.skill, args.timeout)
    auth = load_auth(args.share_session_script)
    preflight = authenticated_post(api["endpoint"], payload, args, auth)
    if preflight.get("status") != "validated" or preflight.get("caseId") != payload["case"]["id"]:
        raise SubmissionError("invalid_response: preflight did not validate this case")
    if args.action == "check":
        return {"status": "validated", "caseId": payload["case"]["id"], "payloadFingerprint": digest, "formUrl": form}
    result = authenticated_post(api["endpoint"], {**payload, "dryRun": False, "consent": True}, args, auth)
    if result.get("status") != "published" or result.get("caseId") != payload["case"]["id"] or result.get("url") != f"/skills/{args.skill}/cases/{payload['case']['id']}":
        raise SubmissionError("invalid_response: publication unconfirmed; retry the unchanged payload and case.id")
    return {**result, "url": ORIGIN + result["url"], "payloadFingerprint": digest, "liveVerification": "pending"}


def build_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    for action in ("contract", "prepare", "check", "publish"):
        command = commands.add_parser(action)
        command.add_argument("skill", help="Exact catalog ID from /skills/<id>, not a local path")
        command.add_argument("--timeout", type=int, default=60)
        if action == "prepare":
            command.add_argument("--case", type=Path, required=True)
            command.add_argument("--image", type=Path, action="append", default=[])
            command.add_argument("--session-url", help="Optional existing public Session owned by you")
            command.add_argument("--output", type=Path, required=True)
        elif action in {"check", "publish"}:
            command.add_argument("--submission", type=Path, required=True)
            command.add_argument("--share-session-script", type=Path)
            command.add_argument("--profile-path", type=Path, help="Existing LovStudio auth cache location; never stores case content")
            if action == "publish":
                command.add_argument("--confirm", required=True, help="Reviewed payloadFingerprint; provide only after explicit publication consent")
    return parser.parse_args(argv)


def main() -> int:
    try:
        result = run(build_args())
    except (ValueError, OSError, RuntimeError) as exc:
        message = str(exc) if isinstance(exc, SubmissionError) else f"{type(exc).__name__}: check input files and dependency installation"
        print(f"context_id=skill-case-submission error={message}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
