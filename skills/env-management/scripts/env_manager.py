#!/usr/bin/env python3
"""Manage redacted environment credential metadata and safe local projections."""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import pty
import re
import secrets
import select
import signal
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import time as time_module
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import date, datetime, time, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable


REGISTRY_SCHEMA = "lov-env-management/registry/v1"
VAULT_SCHEMA = "lov-env-management/vault/v1"
KEYCHAIN_SERVICE = "lov-env-management"
SHELL_START = "# >>> lov-env-management >>>"
SHELL_END = "# <<< lov-env-management <<<"
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ENV_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
HEADER_RE = re.compile(r"^[A-Za-z0-9!#$%&'*+.^_|~-]+$")
STATUSES = ("active", "standby", "disabled", "revoked")
VALIDATION_RESULTS = ("valid", "invalid", "unknown", "error")
TARGETS = ("shell", "system")
UNHEALTHY = {"revoked", "disabled", "not-yet-valid", "expired", "invalid"}
DASHBOARD_TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "dashboard.html"


class EnvManagerError(Exception):
    """A redacted, user-actionable failure."""

    def __init__(self, message: str, *, code: str = "operation_failed") -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.context_id = "env-" + secrets.token_hex(5)

    def as_dict(self) -> dict[str, str]:
        return {
            "status": "error",
            "code": self.code,
            "message": self.message,
            "context_id": self.context_id,
        }


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_datetime(value: str | None, *, end_of_day: bool = False) -> str | None:
    if value is None:
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            parsed_date = date.fromisoformat(raw)
            parsed = datetime.combine(
                parsed_date,
                time(23, 59, 59) if end_of_day else time(0, 0),
                tzinfo=timezone.utc,
            )
        else:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            parsed = parsed.astimezone(timezone.utc)
    except ValueError as exc:
        raise EnvManagerError(
            "Date must be YYYY-MM-DD or an ISO-8601 timestamp.",
            code="invalid_date",
        ) from exc
    return parsed.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_instant(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def require_id(value: str, label: str) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise EnvManagerError(f"{label} must be kebab-case.", code="invalid_identifier")
    return value


def require_env(value: str) -> str:
    if not isinstance(value, str) or not ENV_RE.fullmatch(value):
        raise EnvManagerError(
            "Environment variable must use shell identifier syntax.",
            code="invalid_environment_variable",
        )
    return value


def locator_parts(locator: str) -> tuple[str, str, str]:
    if not isinstance(locator, str):
        raise EnvManagerError("Key locator is required.", code="invalid_locator")
    parts = locator.split("/")
    if len(parts) != 3:
        raise EnvManagerError("Key locator must be platform/account/key.", code="invalid_locator")
    return (
        require_id(parts[0], "platform"),
        require_id(parts[1], "account"),
        require_id(parts[2], "key"),
    )


def file_mode(path: Path) -> int | None:
    try:
        return stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        return None


def atomic_write_text(path: Path, content: str, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_mode = file_mode(path)
    selected_mode = existing_mode if existing_mode is not None else mode
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix="." + path.name + ".",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_name, selected_mode)
        os.replace(temporary_name, path)
    finally:
        if temporary_name:
            temporary = Path(temporary_name)
            if temporary.exists():
                temporary.unlink()


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    atomic_write_text(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        0o600,
    )


def read_json(path: Path, *, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EnvManagerError(
            f"Cannot read the credential metadata file: {path.name}.",
            code="invalid_storage",
        ) from exc
    if not isinstance(value, dict):
        raise EnvManagerError(
            f"Credential metadata root must be an object: {path.name}.",
            code="invalid_storage",
        )
    return value


def nested_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def profile_defaults() -> dict[str, Any]:
    configured = os.environ.get("SKILL_PROFILE_PATH") or os.environ.get(
        "SKILLS_PROFILE_PATH"
    )
    if not configured:
        return {}
    path = Path(os.path.expandvars(configured)).expanduser()
    if not path.is_file():
        return {}
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(profile, dict):
        return {}
    skill = nested_dict(nested_dict(profile.get("skills")).get("lov-env-management"))
    merged: dict[str, Any] = {}
    merged.update(nested_dict(nested_dict(profile.get("preferences")).get("env_management")))
    merged.update(nested_dict(skill.get("profile")))
    merged.update(nested_dict(skill.get("records")))
    return merged


def default_home() -> Path:
    configured = os.environ.get("LOV_ENV_HOME")
    if configured:
        return Path(os.path.expandvars(configured)).expanduser()
    saved = profile_defaults().get("store_dir")
    if isinstance(saved, str) and saved.strip():
        return Path(os.path.expandvars(saved)).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME")
    root = Path(os.path.expandvars(xdg)).expanduser() if xdg else Path.home() / ".config"
    return root / "lov-env-management"


def default_warning_days() -> int:
    raw: Any = os.environ.get("LOV_ENV_WARNING_DAYS")
    if raw is None:
        raw = profile_defaults().get("warning_days")
    try:
        value = int(raw) if raw is not None else 14
    except (TypeError, ValueError):
        value = 14
    return max(0, min(value, 365))


def default_backend() -> str:
    configured: Any = os.environ.get("LOV_ENV_BACKEND")
    if not configured:
        configured = profile_defaults().get("default_backend", "auto")
    return configured if configured in {"auto", "file", "keychain", "op", "env"} else "auto"


class Store:
    def __init__(self, home: Path, warning_days: int = 14) -> None:
        self.home = home.expanduser().resolve()
        self.warning_days = warning_days
        self.registry_path = self.home / "registry.json"
        self.vault_path = self.home / "vault.json"
        self.shell_path = self.home / "active.zsh"

    def empty_registry(self) -> dict[str, Any]:
        return {
            "schema": REGISTRY_SCHEMA,
            "revision": 0,
            "updated_at": iso_now(),
            "platforms": {},
            "bindings": {"shell": {}, "system": {}},
            "projections": {"shell": {}, "system": {}},
        }

    def ensure_home(self) -> None:
        existed = self.home.exists()
        self.home.mkdir(parents=True, exist_ok=True)
        if not existed:
            os.chmod(self.home, 0o700)

    def load(self) -> dict[str, Any]:
        registry = read_json(self.registry_path, default=self.empty_registry())
        if registry.get("schema") != REGISTRY_SCHEMA:
            raise EnvManagerError("Unsupported registry schema.", code="unsupported_registry")
        if not isinstance(registry.get("platforms"), dict):
            raise EnvManagerError("Registry platforms must be an object.", code="invalid_storage")
        bindings = registry.get("bindings")
        if not isinstance(bindings, dict):
            registry["bindings"] = {"shell": {}, "system": {}}
        else:
            for target in TARGETS:
                if not isinstance(bindings.get(target), dict):
                    bindings[target] = {}
        if not isinstance(registry.get("projections"), dict):
            registry["projections"] = {"shell": {}, "system": {}}
        return registry

    def save(self, registry: dict[str, Any]) -> None:
        self.ensure_home()
        revision = registry.get("revision", 0)
        registry["revision"] = revision + 1 if isinstance(revision, int) else 1
        registry["updated_at"] = iso_now()
        atomic_write_json(self.registry_path, registry)
        os.chmod(self.registry_path, 0o600)

    def init(self) -> dict[str, Any]:
        self.ensure_home()
        if not self.registry_path.exists():
            atomic_write_json(self.registry_path, self.empty_registry())
        os.chmod(self.registry_path, 0o600)
        return {
            "status": "ready",
            "home": str(self.home),
            "registry": str(self.registry_path),
            "registry_mode": oct(file_mode(self.registry_path) or 0),
        }

    def vault(self) -> dict[str, Any]:
        value = read_json(
            self.vault_path,
            default={"schema": VAULT_SCHEMA, "secrets": {}},
        )
        if value.get("schema") != VAULT_SCHEMA or not isinstance(value.get("secrets"), dict):
            raise EnvManagerError("Unsupported local vault format.", code="invalid_storage")
        return value

    def write_vault(self, value: dict[str, Any]) -> None:
        self.ensure_home()
        atomic_write_json(self.vault_path, value)
        os.chmod(self.vault_path, 0o600)

    def get_record(
        self, registry: dict[str, Any], locator: str
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        platform_id, account_id, key_id = locator_parts(locator)
        platform = nested_dict(registry.get("platforms")).get(platform_id)
        if not isinstance(platform, dict):
            raise EnvManagerError("Platform was not found.", code="key_not_found")
        account = nested_dict(platform.get("accounts")).get(account_id)
        if not isinstance(account, dict):
            raise EnvManagerError("Account was not found.", code="key_not_found")
        record = nested_dict(account.get("keys")).get(key_id)
        if not isinstance(record, dict):
            raise EnvManagerError("Key was not found.", code="key_not_found")
        return platform, account, record

    def put_secret(self, locator: str, backend: str, value: str) -> None:
        validate_secret(value)
        if backend == "file":
            vault = self.vault()
            secrets_map = nested_dict(vault.get("secrets"))
            secrets_map[locator] = value
            vault["secrets"] = secrets_map
            self.write_vault(vault)
            return
        if backend == "keychain":
            if sys.platform != "darwin" or not shutil.which("security"):
                raise EnvManagerError(
                    "macOS Keychain backend is unavailable.",
                    code="backend_unavailable",
                )
            # `security ... -w` reads and confirms the password from a terminal.
            # Supplying a single line through subprocess stdin silently creates an
            # empty Keychain value on macOS.  A private pseudo-terminal preserves
            # hidden prompt input without placing the secret in argv or logs.
            child_pid, master_fd = pty.fork()
            if child_pid == 0:
                os.execvp(
                    "security",
                    [
                        "security",
                        "add-generic-password",
                        "-U",
                        "-a",
                        locator,
                        "-s",
                        KEYCHAIN_SERVICE,
                        "-w",
                    ],
                )
            child_status: int | None = None
            timed_out = False
            try:
                deadline = time_module.monotonic() + 8.0
                prompt_round = 0
                prompt_buffer = bytearray()
                while time_module.monotonic() < deadline:
                    completed_pid, status = os.waitpid(child_pid, os.WNOHANG)
                    if completed_pid == child_pid:
                        child_status = status
                        break
                    readable, _, _ = select.select([master_fd], [], [], 0.1)
                    if not readable:
                        continue
                    try:
                        chunk = os.read(master_fd, 4096)
                    except OSError:
                        chunk = b""
                    if not chunk:
                        continue
                    prompt_buffer.extend(chunk)
                    normalized_prompt = bytes(prompt_buffer).lower()
                    first_prompt = b"password data" in normalized_prompt
                    confirmation_prompt = b"retype password" in normalized_prompt
                    if prompt_round == 0 and first_prompt:
                        os.write(master_fd, (value + "\n").encode("utf-8"))
                        prompt_round = 1
                        prompt_buffer.clear()
                    elif prompt_round == 1 and confirmation_prompt:
                        os.write(master_fd, (value + "\n").encode("utf-8"))
                        prompt_round = 2
                        prompt_buffer.clear()
                if child_status is None:
                    timed_out = True
                    os.kill(child_pid, signal.SIGTERM)
                    _, child_status = os.waitpid(child_pid, 0)
            except (OSError, ChildProcessError):
                if child_status is None:
                    try:
                        os.kill(child_pid, signal.SIGTERM)
                    except OSError:
                        pass
                    try:
                        _, child_status = os.waitpid(child_pid, 0)
                    except ChildProcessError:
                        pass
            finally:
                try:
                    os.close(master_fd)
                except OSError:
                    pass
            return_code = (
                os.waitstatus_to_exitcode(child_status)
                if child_status is not None
                else 1
            )
            if timed_out or return_code != 0:
                raise EnvManagerError(
                    "macOS Keychain refused the credential write.",
                    code="keychain_write_failed",
                )
            return
        raise EnvManagerError(
            "Selected backend cannot store a supplied secret.",
            code="invalid_backend",
        )

    def read_secret(self, locator: str, record: dict[str, Any]) -> str:
        secret = nested_dict(record.get("secret"))
        backend = secret.get("backend")
        reference = secret.get("reference")
        value: Any = None
        if backend == "file":
            value = nested_dict(self.vault().get("secrets")).get(locator)
        elif backend == "keychain":
            if sys.platform != "darwin" or not shutil.which("security"):
                raise EnvManagerError(
                    "macOS Keychain backend is unavailable.",
                    code="backend_unavailable",
                )
            completed = subprocess.run(
                [
                    "security",
                    "find-generic-password",
                    "-a",
                    locator,
                    "-s",
                    KEYCHAIN_SERVICE,
                    "-w",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                raise EnvManagerError(
                    "The Keychain item cannot be resolved.",
                    code="secret_unavailable",
                )
            value = completed.stdout.rstrip("\r\n")
        elif backend == "op":
            if not isinstance(reference, str) or not reference.startswith("op://"):
                raise EnvManagerError("Invalid 1Password reference.", code="secret_unavailable")
            if not shutil.which("op"):
                raise EnvManagerError("1Password CLI is unavailable.", code="backend_unavailable")
            completed = subprocess.run(
                ["op", "read", reference],
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                raise EnvManagerError(
                    "The 1Password reference cannot be resolved.",
                    code="secret_unavailable",
                )
            value = completed.stdout.rstrip("\r\n")
        elif backend == "env":
            if not isinstance(reference, str) or not ENV_RE.fullmatch(reference):
                raise EnvManagerError("Invalid environment secret reference.", code="secret_unavailable")
            value = os.environ.get(reference)
        else:
            raise EnvManagerError("Unsupported secret backend.", code="invalid_backend")
        if not isinstance(value, str) or not value:
            raise EnvManagerError("The selected secret is unavailable.", code="secret_unavailable")
        validate_secret(value)
        return value

    def secret_configured(self, locator: str, record: dict[str, Any]) -> bool | None:
        secret = nested_dict(record.get("secret"))
        backend = secret.get("backend")
        reference = secret.get("reference")
        if backend == "file":
            return locator in nested_dict(self.vault().get("secrets"))
        if backend == "env":
            return isinstance(reference, str) and bool(os.environ.get(reference))
        if backend in {"keychain", "op"}:
            return None
        return None


def validate_secret(value: str) -> None:
    if not value:
        raise EnvManagerError("Secret input is empty.", code="empty_secret")
    if any(character in value for character in ("\x00", "\r", "\n")):
        raise EnvManagerError(
            "Secret values containing NUL or newline are unsupported.",
            code="invalid_secret_shape",
        )


def choose_backend(requested: str) -> str:
    if requested != "auto":
        return requested
    if sys.platform == "darwin" and shutil.which("security"):
        return "keychain"
    return "file"


def read_secret_input(use_stdin: bool) -> str:
    if use_stdin:
        value = sys.stdin.read()
        if value.endswith("\n"):
            value = value[:-1]
        if value.endswith("\r"):
            value = value[:-1]
    else:
        if not sys.stdin.isatty():
            raise EnvManagerError(
                "Non-interactive secret input requires --secret-stdin.",
                code="secret_input_required",
            )
        value = getpass.getpass("Secret value: ")
    validate_secret(value)
    return value


def effective_health(record: dict[str, Any], warning_days: int) -> str:
    status_value = record.get("status", "standby")
    if status_value == "revoked":
        return "revoked"
    if status_value == "disabled":
        return "disabled"
    now = utc_now()
    not_before = load_instant(record.get("not_before"))
    expires_at = load_instant(record.get("expires_at"))
    if not_before and not_before > now:
        return "not-yet-valid"
    if expires_at and expires_at <= now:
        return "expired"
    if nested_dict(record.get("validation")).get("result") == "invalid":
        return "invalid"
    if expires_at and expires_at <= now + timedelta(days=warning_days):
        return "expiring"
    return "active" if status_value == "active" else "standby"


def validation_age_days(record: dict[str, Any]) -> int | None:
    checked = load_instant(nested_dict(record.get("validation")).get("checked_at"))
    if checked is None:
        return None
    return max(0, (utc_now() - checked).days)


def iter_records(
    registry: dict[str, Any],
) -> Iterable[tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]]]:
    platforms = nested_dict(registry.get("platforms"))
    for platform_id in sorted(platforms):
        platform = platforms.get(platform_id)
        if not isinstance(platform, dict):
            continue
        accounts = nested_dict(platform.get("accounts"))
        for account_id in sorted(accounts):
            account = accounts.get(account_id)
            if not isinstance(account, dict):
                continue
            keys = nested_dict(account.get("keys"))
            for key_id in sorted(keys):
                record = keys.get(key_id)
                if isinstance(record, dict):
                    locator = f"{platform_id}/{account_id}/{key_id}"
                    yield locator, platform, account, record


def binding_targets(registry: dict[str, Any], locator: str) -> list[str]:
    result: list[str] = []
    for target in TARGETS:
        target_bindings = nested_dict(nested_dict(registry.get("bindings")).get(target))
        for env_var, binding in target_bindings.items():
            if isinstance(binding, dict) and binding.get("locator") == locator:
                result.append(f"{target}:{env_var}")
    return sorted(result)


def redacted_record(
    store: Store,
    registry: dict[str, Any],
    locator: str,
    platform: dict[str, Any],
    account: dict[str, Any],
    record: dict[str, Any],
) -> dict[str, Any]:
    validation = nested_dict(record.get("validation"))
    secret = nested_dict(record.get("secret"))
    return {
        "locator": locator,
        "platform_label": platform.get("label"),
        "account_label": account.get("label"),
        "key_label": record.get("label"),
        "env_var": record.get("env_var"),
        "status": record.get("status"),
        "health": effective_health(record, store.warning_days),
        "not_before": record.get("not_before"),
        "expires_at": record.get("expires_at"),
        "validation": {
            "result": validation.get("result", "unknown"),
            "checked_at": validation.get("checked_at"),
            "age_days": validation_age_days(record),
            "origin": validation.get("origin"),
            "status_code": validation.get("status_code"),
            "note": validation.get("note"),
        },
        "secret_backend": secret.get("backend"),
        "secret_configured": store.secret_configured(locator, record),
        "bindings": binding_targets(registry, locator),
        "created_at": record.get("created_at"),
        "updated_at": record.get("updated_at"),
    }


def list_state(
    store: Store,
    registry: dict[str, Any],
    *,
    platform_filter: str | None = None,
    account_filter: str | None = None,
    health_filter: str | None = None,
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for locator, platform, account, record in iter_records(registry):
        platform_id, account_id, _ = locator_parts(locator)
        health = effective_health(record, store.warning_days)
        if platform_filter and platform_id != platform_filter:
            continue
        if account_filter and account_id != account_filter:
            continue
        if health_filter and health != health_filter:
            continue
        items.append(redacted_record(store, registry, locator, platform, account, record))
    bindings: dict[str, dict[str, str]] = {}
    for target in TARGETS:
        bindings[target] = {
            env_var: nested_dict(binding).get("locator", "")
            for env_var, binding in nested_dict(
                nested_dict(registry.get("bindings")).get(target)
            ).items()
        }
    return {
        "status": "ready",
        "revision": registry.get("revision"),
        "warning_days": store.warning_days,
        "items": items,
        "bindings": bindings,
    }


def add_key(store: Store, args: argparse.Namespace) -> dict[str, Any]:
    platform_id = require_id(args.platform, "platform")
    account_id = require_id(args.account, "account")
    key_id = require_id(args.key, "key")
    env_var = require_env(args.env_var)
    locator = f"{platform_id}/{account_id}/{key_id}"
    backend = choose_backend(args.backend)
    registry = store.load()
    platforms = nested_dict(registry.get("platforms"))
    existing_platform = platforms.get(platform_id)
    if isinstance(existing_platform, dict):
        existing_account = nested_dict(existing_platform.get("accounts")).get(account_id)
        if isinstance(existing_account, dict) and key_id in nested_dict(existing_account.get("keys")):
            raise EnvManagerError(
                "Key ID already exists; use a new rotation ID.",
                code="key_already_exists",
            )
    if backend == "op":
        if not args.secret_ref or not args.secret_ref.startswith("op://"):
            raise EnvManagerError(
                "The op backend requires --secret-ref with an op:// reference.",
                code="secret_reference_required",
            )
        reference = args.secret_ref
        supplied_secret = None
    elif backend == "env":
        if not args.secret_ref or not ENV_RE.fullmatch(args.secret_ref):
            raise EnvManagerError(
                "The env backend requires --secret-ref with an environment variable name.",
                code="secret_reference_required",
            )
        reference = args.secret_ref
        supplied_secret = None
    elif backend in {"file", "keychain"}:
        if args.secret_ref:
            raise EnvManagerError(
                "Stored secret backends do not accept --secret-ref.",
                code="invalid_secret_reference",
            )
        reference = locator
        supplied_secret = read_secret_input(args.secret_stdin)
    else:
        raise EnvManagerError("Unsupported secret backend.", code="invalid_backend")
    platform = platforms.setdefault(
        platform_id,
        {"label": args.platform_label or platform_id, "accounts": {}, "created_at": iso_now()},
    )
    accounts = nested_dict(platform.setdefault("accounts", {}))
    account = accounts.setdefault(
        account_id,
        {"label": args.account_label or account_id, "keys": {}, "created_at": iso_now()},
    )
    keys = nested_dict(account.setdefault("keys", {}))
    if supplied_secret is not None:
        store.put_secret(locator, backend, supplied_secret)
    now = iso_now()
    keys[key_id] = {
        "label": args.label or key_id,
        "env_var": env_var,
        "status": args.status,
        "not_before": parse_datetime(args.not_before),
        "expires_at": parse_datetime(args.expires_at, end_of_day=True),
        "secret": {"backend": backend, "reference": reference},
        "validation": {
            "result": "unknown",
            "checked_at": None,
            "origin": None,
            "status_code": None,
            "note": "No remote validation evidence yet.",
        },
        "created_at": now,
        "updated_at": now,
    }
    platform["accounts"] = accounts
    platform["updated_at"] = now
    account["keys"] = keys
    account["updated_at"] = now
    registry["platforms"] = platforms
    store.save(registry)
    return {
        "status": "added",
        "locator": locator,
        "env_var": env_var,
        "backend": backend,
        "administrative_status": args.status,
        "secret_echoed": False,
    }


def update_status(store: Store, args: argparse.Namespace) -> dict[str, Any]:
    registry = store.load()
    _, _, record = store.get_record(registry, args.locator)
    if args.status is not None:
        record["status"] = args.status
    if args.not_before is not None:
        record["not_before"] = parse_datetime(args.not_before)
    if args.expires_at is not None:
        record["expires_at"] = parse_datetime(args.expires_at, end_of_day=True)
    if args.clear_not_before:
        record["not_before"] = None
    if args.clear_expires:
        record["expires_at"] = None
    record["updated_at"] = iso_now()
    store.save(registry)
    return {
        "status": "updated",
        "locator": args.locator,
        "administrative_status": record.get("status"),
        "health": effective_health(record, store.warning_days),
        "not_before": record.get("not_before"),
        "expires_at": record.get("expires_at"),
    }


def mark_validation(store: Store, args: argparse.Namespace) -> dict[str, Any]:
    registry = store.load()
    _, _, record = store.get_record(registry, args.locator)
    note = args.note.strip() if args.note else "Manual validation result."
    if len(note) > 200:
        raise EnvManagerError("Validation note must be 200 characters or fewer.", code="invalid_note")
    if re.search(r"[A-Za-z0-9_./+=-]{24,}", note):
        raise EnvManagerError(
            "Validation note looks secret-like; store only a short redacted observation.",
            code="secret_like_note",
        )
    record["validation"] = {
        "result": args.result,
        "checked_at": iso_now(),
        "origin": "manual",
        "status_code": None,
        "note": note,
    }
    record["updated_at"] = iso_now()
    store.save(registry)
    return {
        "status": "validation-recorded",
        "locator": args.locator,
        "result": args.result,
        "checked_at": record["validation"]["checked_at"],
    }


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def parse_static_headers(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if ":" not in value:
            raise EnvManagerError(
                "Static headers must use Name: Value syntax.",
                code="invalid_header",
            )
        name, header_value = value.split(":", 1)
        name = name.strip()
        header_value = header_value.strip()
        if not HEADER_RE.fullmatch(name) or "\r" in header_value or "\n" in header_value:
            raise EnvManagerError("Static header is invalid.", code="invalid_header")
        if name.casefold() in {"authorization", "proxy-authorization", "cookie"}:
            raise EnvManagerError(
                "Secret-bearing static headers are not accepted.",
                code="unsafe_header",
            )
        result[name] = header_value
    return result


def probe_key(store: Store, args: argparse.Namespace) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(args.url)
    is_local_http = parsed.scheme == "http" and parsed.hostname in {
        "127.0.0.1",
        "localhost",
        "::1",
    }
    if parsed.scheme != "https" and not (is_local_http and args.allow_local_http):
        raise EnvManagerError(
            "Probe URL must use HTTPS; local HTTP requires --allow-local-http.",
            code="unsafe_probe_url",
        )
    if not parsed.hostname or parsed.username or parsed.password:
        raise EnvManagerError("Probe URL is invalid.", code="invalid_probe_url")
    if parsed.query or parsed.fragment:
        raise EnvManagerError(
            "Probe URL must not contain query parameters or a fragment.",
            code="unsafe_probe_url",
        )
    registry = store.load()
    _, _, record = store.get_record(registry, args.locator)
    secret = store.read_secret(args.locator, record)
    headers = {
        "Accept": "application/json",
        "User-Agent": "lov-env-management/0.1.0",
    }
    headers.update(parse_static_headers(args.header))
    if args.auth == "bearer":
        headers["Authorization"] = "Bearer " + secret
    else:
        header_name = args.header_name or "X-API-Key"
        if not HEADER_RE.fullmatch(header_name):
            raise EnvManagerError("Authentication header name is invalid.", code="invalid_header")
        headers[header_name] = (args.prefix or "") + secret
    request = urllib.request.Request(args.url, method="GET", headers=headers)
    opener = urllib.request.build_opener(NoRedirect())
    status_code: int | None = None
    result = "error"
    note = "Remote validation could not establish credential validity."
    try:
        with opener.open(request, timeout=args.timeout) as response:
            status_code = int(response.status)
            if 200 <= status_code < 300:
                result = "valid"
                note = "Remote endpoint accepted the authenticated request."
    except urllib.error.HTTPError as exc:
        status_code = int(exc.code)
        if status_code in {401, 403}:
            result = "invalid"
            note = "Remote endpoint rejected the credential."
        elif 300 <= status_code < 400:
            note = "Redirects are blocked to prevent credential forwarding."
        else:
            note = "Remote endpoint returned a non-authentication error."
    except (urllib.error.URLError, TimeoutError, OSError):
        note = "Remote endpoint was unavailable or timed out."
    origin = parsed.scheme + "://" + (parsed.hostname or "")
    if parsed.port:
        origin += ":" + str(parsed.port)
    record["validation"] = {
        "result": result,
        "checked_at": iso_now(),
        "origin": origin,
        "status_code": status_code,
        "note": note,
    }
    record["updated_at"] = iso_now()
    store.save(registry)
    return {
        "status": "probe-complete",
        "locator": args.locator,
        "result": result,
        "status_code": status_code,
        "origin": origin,
        "checked_at": record["validation"]["checked_at"],
        "secret_echoed": False,
    }


def bind_key(store: Store, args: argparse.Namespace) -> dict[str, Any]:
    env_var = require_env(args.env_var)
    if args.target not in TARGETS:
        raise EnvManagerError("Target must be shell or system.", code="invalid_target")
    registry = store.load()
    _, _, record = store.get_record(registry, args.locator)
    health = effective_health(record, store.warning_days)
    if health in UNHEALTHY and not args.allow_unhealthy:
        raise EnvManagerError(
            f"Binding rejected because Key health is {health}.",
            code="unhealthy_key",
        )
    expected = record.get("env_var")
    if isinstance(expected, str) and expected != env_var and not args.allow_variable_mismatch:
        raise EnvManagerError(
            f"Key expects {expected}; use --allow-variable-mismatch to bind {env_var}.",
            code="variable_mismatch",
        )
    bindings = nested_dict(registry.get("bindings"))
    target_bindings = nested_dict(bindings.setdefault(args.target, {}))
    previous = nested_dict(target_bindings.get(env_var)).get("locator")
    target_bindings[env_var] = {"locator": args.locator, "bound_at": iso_now()}
    bindings[args.target] = target_bindings
    registry["bindings"] = bindings
    store.save(registry)
    return {
        "status": "bound",
        "target": args.target,
        "env_var": env_var,
        "locator": args.locator,
        "previous_locator": previous,
        "health": health,
    }


def unbind_key(store: Store, args: argparse.Namespace) -> dict[str, Any]:
    env_var = require_env(args.env_var)
    registry = store.load()
    bindings = nested_dict(registry.get("bindings"))
    target_bindings = nested_dict(bindings.get(args.target))
    previous = target_bindings.pop(env_var, None)
    if previous is None:
        raise EnvManagerError("Binding was not found.", code="binding_not_found")
    bindings[args.target] = target_bindings
    registry["bindings"] = bindings
    store.save(registry)
    return {
        "status": "unbound",
        "target": args.target,
        "env_var": env_var,
        "previous_locator": nested_dict(previous).get("locator"),
    }


def resolve_bindings(
    store: Store,
    registry: dict[str, Any],
    target: str,
    *,
    include_values: bool,
    allow_unhealthy: bool,
) -> list[tuple[str, str, str | None]]:
    resolved: list[tuple[str, str, str | None]] = []
    target_bindings = nested_dict(nested_dict(registry.get("bindings")).get(target))
    for env_var in sorted(target_bindings):
        locator = nested_dict(target_bindings.get(env_var)).get("locator")
        if not isinstance(locator, str):
            raise EnvManagerError("Binding is missing its locator.", code="dangling_binding")
        _, _, record = store.get_record(registry, locator)
        health = effective_health(record, store.warning_days)
        if health in UNHEALTHY and not allow_unhealthy:
            raise EnvManagerError(
                f"Projection rejected: {env_var} selects a {health} Key.",
                code="unhealthy_binding",
            )
        value = store.read_secret(locator, record) if include_values else None
        resolved.append((env_var, locator, value))
    return resolved


def replace_managed_block(content: str, block: str) -> str:
    pattern = re.compile(
        re.escape(SHELL_START) + r".*?" + re.escape(SHELL_END) + r"\n?",
        re.DOTALL,
    )
    stripped = pattern.sub("", content).rstrip()
    return (stripped + "\n\n" if stripped else "") + block.rstrip() + "\n"


def sync_shell(store: Store, args: argparse.Namespace) -> dict[str, Any]:
    registry = store.load()
    preview = resolve_bindings(
        store,
        registry,
        "shell",
        include_values=False,
        allow_unhealthy=args.allow_unhealthy,
    )
    rcfile = Path(os.path.expandvars(args.rcfile)).expanduser().resolve()
    result: dict[str, Any] = {
        "status": "preview",
        "target": "shell",
        "variables": [item[0] for item in preview],
        "count": len(preview),
        "rcfile": str(rcfile),
        "generated_file": str(store.shell_path),
        "secret_echoed": False,
    }
    if not args.apply:
        return result
    values = resolve_bindings(
        store,
        registry,
        "shell",
        include_values=True,
        allow_unhealthy=args.allow_unhealthy,
    )
    exports = [
        "# Generated by lov-env-management. Do not edit.",
        "# Updated " + iso_now(),
    ]
    for env_var, _, value in values:
        if value is None:
            raise EnvManagerError("A projected secret is unavailable.", code="secret_unavailable")
        exports.append("export " + env_var + "=" + shlex.quote(value))
    exports.append("")
    store.ensure_home()
    atomic_write_text(store.shell_path, "\n".join(exports), 0o600)
    os.chmod(store.shell_path, 0o600)
    source_path = shlex.quote(str(store.shell_path))
    block = "\n".join(
        [
            SHELL_START,
            "if [ -r " + source_path + " ]; then",
            "  source " + source_path,
            "fi",
            SHELL_END,
        ]
    )
    existing = rcfile.read_text(encoding="utf-8") if rcfile.exists() else ""
    updated = replace_managed_block(existing, block)
    backup_path: Path | None = None
    if updated != existing:
        if rcfile.exists():
            stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
            backup_path = rcfile.with_name(
                rcfile.name + ".lov-env-management." + stamp + ".bak"
            )
            atomic_write_text(backup_path, existing, file_mode(rcfile) or 0o600)
        atomic_write_text(rcfile, updated, file_mode(rcfile) or 0o600)
    projections = nested_dict(registry.setdefault("projections", {}))
    projections["shell"] = {
        "last_synced_at": iso_now(),
        "variables": [item[0] for item in values],
        "rcfile": str(rcfile),
        "generated_file": str(store.shell_path),
    }
    store.save(registry)
    result.update(
        {
            "status": "applied",
            "generated_mode": oct(file_mode(store.shell_path) or 0),
            "rcfile_changed": updated != existing,
            "backup": str(backup_path) if backup_path else None,
        }
    )
    return result


def system_command(action: str, env_var: str, value: str | None = None) -> list[str]:
    if sys.platform == "darwin":
        if not shutil.which("launchctl"):
            raise EnvManagerError("launchctl is unavailable.", code="system_target_unavailable")
        if action == "set":
            return ["launchctl", "setenv", env_var, value or ""]
        return ["launchctl", "unsetenv", env_var]
    if shutil.which("systemctl"):
        if action == "set":
            return ["systemctl", "--user", "set-environment", env_var + "=" + (value or "")]
        return ["systemctl", "--user", "unset-environment", env_var]
    raise EnvManagerError(
        "No supported current-user environment manager is available.",
        code="system_target_unavailable",
    )


def sync_system(store: Store, args: argparse.Namespace) -> dict[str, Any]:
    registry = store.load()
    preview = resolve_bindings(
        store,
        registry,
        "system",
        include_values=False,
        allow_unhealthy=args.allow_unhealthy,
    )
    result: dict[str, Any] = {
        "status": "preview",
        "target": "system",
        "variables": [item[0] for item in preview],
        "count": len(preview),
        "secret_echoed": False,
    }
    if not args.apply:
        return result
    if not args.acknowledge_process_env_risk:
        raise EnvManagerError(
            "System projection requires --acknowledge-process-env-risk.",
            code="risk_acknowledgement_required",
        )
    values = resolve_bindings(
        store,
        registry,
        "system",
        include_values=True,
        allow_unhealthy=args.allow_unhealthy,
    )
    projections = nested_dict(registry.setdefault("projections", {}))
    previous = nested_dict(projections.get("system")).get("variables", [])
    previous_vars = {item for item in previous if isinstance(item, str)}
    current_vars = {item[0] for item in values}
    cleared: list[str] = []
    if args.clear_stale:
        for env_var in sorted(previous_vars - current_vars):
            completed = subprocess.run(
                system_command("unset", env_var),
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                raise EnvManagerError(
                    f"Failed to clear stale system variable {env_var}.",
                    code="system_projection_failed",
                )
            cleared.append(env_var)
    for env_var, _, value in values:
        completed = subprocess.run(
            system_command("set", env_var, value),
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise EnvManagerError(
                f"Failed to set current-user variable {env_var}.",
                code="system_projection_failed",
            )
    projections["system"] = {
        "last_synced_at": iso_now(),
        "variables": sorted(current_vars),
        "manager": "launchctl" if sys.platform == "darwin" else "systemctl-user",
    }
    store.save(registry)
    result.update({"status": "applied", "cleared": cleared})
    return result


def audit_store(store: Store, *, max_check_age_days: int) -> dict[str, Any]:
    registry = store.load()
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    def add(bucket: list[dict[str, str]], code: str, message: str) -> None:
        bucket.append({"code": code, "message": message})

    mode = file_mode(store.home)
    if mode is not None and mode & 0o077:
        add(errors, "unsafe_home_permissions", "Storage directory is accessible by group or others.")
    for path in (store.registry_path, store.vault_path, store.shell_path):
        mode = file_mode(path)
        if mode is not None and mode & 0o077:
            add(errors, "unsafe_file_permissions", path.name + " is accessible by group or others.")
    for locator, _, _, record in iter_records(registry):
        if store.secret_configured(locator, record) is False:
            add(errors, "missing_secret", locator + " cannot resolve its configured secret source.")
        if effective_health(record, store.warning_days) == "expiring":
            add(warnings, "key_expiring", locator + " is inside the expiry warning window.")
    for target in TARGETS:
        target_bindings = nested_dict(nested_dict(registry.get("bindings")).get(target))
        for env_var, binding in target_bindings.items():
            locator = nested_dict(binding).get("locator")
            if not isinstance(locator, str):
                add(errors, "dangling_binding", target + ":" + env_var + " has no locator.")
                continue
            try:
                _, _, record = store.get_record(registry, locator)
            except EnvManagerError:
                add(errors, "dangling_binding", target + ":" + env_var + " points to a missing Key.")
                continue
            health = effective_health(record, store.warning_days)
            if health in UNHEALTHY:
                add(errors, "unhealthy_binding", target + ":" + env_var + " selects a " + health + " Key.")
            validation = nested_dict(record.get("validation"))
            age = validation_age_days(record)
            if validation.get("result") == "unknown" or age is None:
                add(warnings, "unverified_binding", target + ":" + env_var + " has no remote validation evidence.")
            elif age > max_check_age_days:
                add(warnings, "stale_validation", target + ":" + env_var + " validation is stale.")
    status_value = "error" if errors else "warning" if warnings else "ready"
    return {
        "status": status_value,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "keys": sum(1 for _ in iter_records(registry)),
            "bindings": sum(
                len(nested_dict(nested_dict(registry.get("bindings")).get(target)))
                for target in TARGETS
            ),
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "paths": {
            "home": str(store.home),
            "registry": str(store.registry_path),
            "vault": str(store.vault_path) if store.vault_path.exists() else None,
            "shell_projection": str(store.shell_path) if store.shell_path.exists() else None,
        },
    }


def dashboard_state(store: Store) -> dict[str, Any]:
    registry = store.load()
    state = list_state(store, registry)
    items = state["items"]
    state["summary"] = {
        "keys": len(items),
        "bindings": sum(len(values) for values in state["bindings"].values()),
        "expiring": sum(1 for item in items if item["health"] == "expiring"),
        "invalid": sum(
            1
            for item in items
            if item["health"] in {"invalid", "expired", "revoked", "disabled"}
        ),
    }
    state["platforms"] = sorted({item["locator"].split("/", 1)[0] for item in items})
    state["accounts"] = sorted(
        {"/".join(item["locator"].split("/")[:2]) for item in items}
    )
    return state


def dashboard_handler(store: Store, token: str, origin: str) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "LovEnvDashboard/0.1"

        def log_message(self, format_string: str, *args: Any) -> None:
            return

        def headers_common(self, content_type: str) -> None:
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
                "connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'",
            )

        def send_json(self, status_code: int, payload: dict[str, Any]) -> None:
            content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status_code)
            self.headers_common("application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def authorized(self, *, mutate: bool = False) -> bool:
            if self.headers.get("X-Lov-Token") != token:
                return False
            return not mutate or self.headers.get("Origin") == origin

        def body_json(self) -> dict[str, Any]:
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise EnvManagerError("Invalid request length.", code="invalid_request") from exc
            if size <= 0 or size > 16384:
                raise EnvManagerError("Invalid Dashboard request body.", code="invalid_request")
            try:
                payload = json.loads(self.rfile.read(size).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise EnvManagerError("Dashboard request must be JSON.", code="invalid_request") from exc
            if not isinstance(payload, dict):
                raise EnvManagerError("Dashboard request root must be an object.", code="invalid_request")
            return payload

        def do_GET(self) -> None:
            path = urllib.parse.urlparse(self.path).path
            if path == "/":
                try:
                    template = DASHBOARD_TEMPLATE.read_text(encoding="utf-8")
                except OSError:
                    self.send_json(500, {"status": "error", "message": "Dashboard asset is unavailable."})
                    return
                content = template.replace("__TOKEN_JSON__", json.dumps(token)).encode("utf-8")
                self.send_response(200)
                self.headers_common("text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            if path == "/api/state":
                if not self.authorized():
                    self.send_json(403, {"status": "error", "message": "Dashboard token rejected."})
                    return
                self.send_json(200, dashboard_state(store))
                return
            self.send_json(404, {"status": "error", "message": "Not found."})

        def do_POST(self) -> None:
            path = urllib.parse.urlparse(self.path).path
            if not self.authorized(mutate=True):
                self.send_json(403, {"status": "error", "message": "Dashboard write rejected."})
                return
            try:
                payload = self.body_json()
                if path == "/api/bind":
                    result = bind_key(
                        store,
                        argparse.Namespace(
                            target=payload.get("target"),
                            env_var=payload.get("env_var"),
                            locator=payload.get("locator"),
                            allow_unhealthy=False,
                            allow_variable_mismatch=False,
                        ),
                    )
                elif path == "/api/status":
                    locator = payload.get("locator")
                    status_value = payload.get("status")
                    validation = payload.get("validation")
                    if not isinstance(locator, str):
                        raise EnvManagerError("A Key locator is required.", code="invalid_request")
                    result: dict[str, Any] = {"status": "unchanged", "locator": locator}
                    if status_value:
                        if status_value not in STATUSES:
                            raise EnvManagerError("Invalid administrative status.", code="invalid_request")
                        result = update_status(
                            store,
                            argparse.Namespace(
                                locator=locator,
                                status=status_value,
                                not_before=None,
                                expires_at=None,
                                clear_not_before=False,
                                clear_expires=False,
                            ),
                        )
                    if validation:
                        if validation not in VALIDATION_RESULTS:
                            raise EnvManagerError("Invalid validation result.", code="invalid_request")
                        result = mark_validation(
                            store,
                            argparse.Namespace(
                                locator=locator,
                                result=validation,
                                note="Recorded from the local Dashboard.",
                            ),
                        )
                else:
                    self.send_json(404, {"status": "error", "message": "Not found."})
                    return
                self.send_json(200, result)
            except EnvManagerError as exc:
                self.send_json(400, exc.as_dict())

    return Handler


def serve_dashboard(store: Store, args: argparse.Namespace) -> int:
    if not DASHBOARD_TEMPLATE.is_file():
        raise EnvManagerError("Dashboard asset is unavailable.", code="missing_dashboard")
    token = secrets.token_urlsafe(24)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), BaseHTTPRequestHandler)
    port = int(server.server_address[1])
    origin = "http://127.0.0.1:" + str(port)
    server.RequestHandlerClass = dashboard_handler(store, token, origin)
    print(
        json.dumps(
            {
                "status": "serving",
                "url": origin + "/",
                "bind": "127.0.0.1",
                "port": port,
                "secrets_exposed": False,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    if args.open:
        webbrowser.open(origin + "/", new=2)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def human_output(result: dict[str, Any]) -> str:
    lines = ["status: " + str(result.get("status", "ready"))]
    for key, value in result.items():
        if key == "status" or value is None:
            continue
        if isinstance(value, (dict, list)):
            lines.append(key + ": " + json.dumps(value, ensure_ascii=False))
        else:
            lines.append(key + ": " + str(value))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=None, help="Credential metadata directory")
    parser.add_argument("--warning-days", type=int, default=default_warning_days())
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize secure local metadata storage")
    add = subparsers.add_parser("add", help="Add one platform/account/key record")
    add.add_argument("--platform", required=True)
    add.add_argument("--account", required=True)
    add.add_argument("--key", required=True)
    add.add_argument("--env-var", required=True)
    add.add_argument("--platform-label")
    add.add_argument("--account-label")
    add.add_argument("--label")
    add.add_argument("--backend", choices=("auto", "file", "keychain", "op", "env"), default=default_backend())
    add.add_argument("--secret-ref")
    add.add_argument("--secret-stdin", action="store_true")
    add.add_argument("--status", choices=STATUSES, default="standby")
    add.add_argument("--not-before")
    add.add_argument("--expires-at")

    list_parser = subparsers.add_parser("list", help="List redacted Key metadata")
    list_parser.add_argument("--platform")
    list_parser.add_argument("--account")
    list_parser.add_argument("--health")
    show = subparsers.add_parser("show", help="Show one redacted Key record")
    show.add_argument("locator")
    show.add_argument("--fingerprint", action="store_true")
    status_parser = subparsers.add_parser("status", help="Update administrative state or dates")
    status_parser.add_argument("locator")
    status_parser.add_argument("--status", choices=STATUSES)
    status_parser.add_argument("--not-before")
    status_parser.add_argument("--expires-at")
    status_parser.add_argument("--clear-not-before", action="store_true")
    status_parser.add_argument("--clear-expires", action="store_true")
    validation = subparsers.add_parser("mark-validation", help="Record redacted validation evidence")
    validation.add_argument("locator")
    validation.add_argument("--result", choices=VALIDATION_RESULTS, required=True)
    validation.add_argument("--note")
    probe = subparsers.add_parser("probe", help="Validate one Key through guarded HTTP")
    probe.add_argument("locator")
    probe.add_argument("--url", required=True)
    probe.add_argument("--auth", choices=("bearer", "header"), default="bearer")
    probe.add_argument("--header-name")
    probe.add_argument("--prefix")
    probe.add_argument("--header", action="append", default=[])
    probe.add_argument("--timeout", type=float, default=10.0)
    probe.add_argument("--allow-local-http", action="store_true")
    bind = subparsers.add_parser("bind", help="Bind one Key to one target variable")
    bind.add_argument("locator")
    bind.add_argument("--target", choices=TARGETS, required=True)
    bind.add_argument("--env-var", required=True)
    bind.add_argument("--allow-unhealthy", action="store_true")
    bind.add_argument("--allow-variable-mismatch", action="store_true")
    unbind = subparsers.add_parser("unbind", help="Remove one target variable binding")
    unbind.add_argument("--target", choices=TARGETS, required=True)
    unbind.add_argument("--env-var", required=True)
    shell = subparsers.add_parser("sync-shell", help="Preview or apply zsh projection")
    shell.add_argument("--rcfile", default=str(Path.home() / ".zshenv"))
    shell.add_argument("--apply", action="store_true")
    shell.add_argument("--allow-unhealthy", action="store_true")
    system = subparsers.add_parser("sync-system", help="Preview or apply current-user session projection")
    system.add_argument("--apply", action="store_true")
    system.add_argument("--acknowledge-process-env-risk", action="store_true")
    system.add_argument("--clear-stale", action="store_true")
    system.add_argument("--allow-unhealthy", action="store_true")
    audit = subparsers.add_parser("audit", help="Audit storage, lifecycle, and bindings")
    audit.add_argument("--max-check-age-days", type=int, default=30)
    dashboard = subparsers.add_parser("dashboard", help="Run the redacted local Dashboard")
    dashboard.add_argument("--port", type=int, default=8765)
    dashboard.add_argument("--open", action="store_true")
    return parser


def run(args: argparse.Namespace) -> dict[str, Any] | int:
    home = args.home if args.home is not None else default_home()
    if args.warning_days < 0 or args.warning_days > 365:
        raise EnvManagerError("warning-days must be between 0 and 365.", code="invalid_warning_days")
    store = Store(home, args.warning_days)
    if args.command == "init":
        return store.init()
    if args.command == "add":
        return add_key(store, args)
    if args.command == "list":
        return list_state(
            store,
            store.load(),
            platform_filter=args.platform,
            account_filter=args.account,
            health_filter=args.health,
        )
    if args.command == "show":
        registry = store.load()
        platform, account, record = store.get_record(registry, args.locator)
        result = redacted_record(store, registry, args.locator, platform, account, record)
        result["status"] = "ready"
        if args.fingerprint:
            value = store.read_secret(args.locator, record)
            result["fingerprint"] = (
                "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
            )
        return result
    if args.command == "status":
        if not any(
            (
                args.status,
                args.not_before,
                args.expires_at,
                args.clear_not_before,
                args.clear_expires,
            )
        ):
            raise EnvManagerError("No status or date change was requested.", code="no_change")
        return update_status(store, args)
    if args.command == "mark-validation":
        return mark_validation(store, args)
    if args.command == "probe":
        return probe_key(store, args)
    if args.command == "bind":
        return bind_key(store, args)
    if args.command == "unbind":
        return unbind_key(store, args)
    if args.command == "sync-shell":
        return sync_shell(store, args)
    if args.command == "sync-system":
        return sync_system(store, args)
    if args.command == "audit":
        return audit_store(store, max_check_age_days=args.max_check_age_days)
    if args.command == "dashboard":
        return serve_dashboard(store, args)
    raise EnvManagerError("Unsupported command.", code="unsupported_command")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    raw_args = list(argv) if argv is not None else sys.argv[1:]
    json_requested = "--json" in raw_args
    raw_args = [item for item in raw_args if item != "--json"]
    args = parser.parse_args(raw_args)
    args.json = bool(args.json or json_requested)
    try:
        result = run(args)
    except EnvManagerError as exc:
        print(json.dumps(exc.as_dict(), ensure_ascii=False), file=sys.stderr)
        return 2
    if isinstance(result, int):
        return result
    print(
        json.dumps(result, ensure_ascii=False, indent=2)
        if args.json
        else human_output(result)
    )
    return 1 if result.get("status") == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
