#!/usr/bin/env python3
"""Diagnose and reversibly repair Clash Verge Rev TUN application failures."""

from __future__ import annotations

import argparse
import datetime as dt
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


APP_BUNDLE = "Clash Verge"
DEFAULT_SOCKET = Path("/tmp/verge/verge-mihomo.sock")
CONNECTION_LOG_RE = re.compile(
    r"\[(?:TCP|UDP)\]\s+\S+\((?P<process>[^)]*)\)\s+-->\s+"
    r"(?P<host>[^:\s]+):\d+\s+match\s+(?P<rule>.+?)\s+using\s+(?P<proxy>.+?)\"?$"
)
HOSTNAME_RE = re.compile(
    r"(?=.{1,253}\.?$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.?$",
    re.IGNORECASE,
)
WECHAT_RULES = [
    "PROCESS-NAME,WeChat,DIRECT",
    "PROCESS-NAME,WeChatAppEx,DIRECT",
    "PROCESS-NAME,WeChatAppEx Helper,DIRECT",
    "DOMAIN-SUFFIX,weixin.qq.com,DIRECT",
    "DOMAIN-SUFFIX,wechat.com,DIRECT",
    "DOMAIN-SUFFIX,servicewechat.com,DIRECT",
    "DOMAIN-SUFFIX,qpic.cn,DIRECT",
    "DOMAIN-SUFFIX,qlogo.cn,DIRECT",
]


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path: Path, timeout: float = 3.0) -> None:
        super().__init__("localhost", timeout=timeout)
        self.socket_path = str(socket_path)

    def connect(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect(self.socket_path)
        self.sock = sock


def api_json(
    socket_path: Path,
    path: str,
    method: str = "GET",
    body: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    if not socket_path.exists():
        return None
    connection = UnixHTTPConnection(socket_path)
    try:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers = {} if payload is None else {"Content-Type": "application/json"}
        connection.request(method, path, body=payload, headers=headers)
        response = connection.getresponse()
        response_payload = response.read()
        if not 200 <= response.status < 300:
            return None
        return json.loads(response_payload.decode("utf-8")) if response_payload else {}
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    finally:
        connection.close()


def resolve_data_dir(cli_value: Optional[str]) -> Path:
    raw = cli_value or os.environ.get("LOVSTUDIO_CLASH_TUN_DOCTOR_DATA_DIR")
    if raw:
        return Path(os.path.expandvars(os.path.expanduser(raw))).resolve()
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/io.github.clash-verge-rev.clash-verge-rev"
    raise SystemExit("Cannot auto-detect Clash Verge Rev data directory; pass --data-dir.")


def resolve_socket(data_dir: Path, cli_value: Optional[str]) -> Path:
    if cli_value:
        return Path(os.path.expandvars(os.path.expanduser(cli_value))).resolve()
    if DEFAULT_SOCKET.exists():
        return DEFAULT_SOCKET
    return data_dir / "mihomo.sock"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def yaml_bool(text: str, key: str, indent: int = 0) -> Optional[bool]:
    prefix = " " * indent
    match = re.search(rf"(?m)^{re.escape(prefix + key)}:\s*(true|false)\s*$", text)
    return None if not match else match.group(1) == "true"


def generated_ipv6(text: str) -> Dict[str, Optional[bool]]:
    top = yaml_bool(text, "ipv6", 0)
    dns_value: Optional[bool] = None
    dns_match = re.search(r"(?ms)^dns:\s*\n(?P<body>(?:^[ \t]+.*\n?)*)", text)
    if dns_match:
        dns_value = yaml_bool(dns_match.group("body"), "ipv6", 2)
    return {"top_level": top, "dns": dns_value}


def current_rules_file(data_dir: Path) -> Optional[Path]:
    profile_text = read_text(data_dir / "profiles.yaml")
    current_match = re.search(r"(?m)^current:\s*([^\s#]+)", profile_text)
    if not current_match:
        return None
    current = re.escape(current_match.group(1))
    block_match = re.search(
        rf"(?ms)^- uid:\s*{current}\s*$\n(?P<body>.*?)(?=^- uid:|\Z)", profile_text
    )
    if not block_match:
        return None
    rules_match = re.search(r"(?m)^\s+rules:\s*([^\s#]+)", block_match.group("body"))
    if not rules_match:
        return None
    candidate = data_dir / "profiles" / f"{rules_match.group(1)}.yaml"
    return candidate if candidate.exists() else None


def service_log(data_dir: Path) -> Path:
    candidates = [
        data_dir / "service-logs/service/service_latest.log",
        data_dir / "logs/service/service_latest.log",
    ]
    return next((path for path in candidates if path.exists()), candidates[0])


def recent_service_logs(data_dir: Path, max_files: int = 8) -> List[Path]:
    roots = [
        data_dir / "service-logs/service",
        data_dir / "logs/service",
    ]
    candidates: List[Path] = []
    for root in roots:
        if not root.exists():
            continue
        latest = root / "service_latest.log"
        if latest.exists():
            candidates.append(latest)
        candidates.extend(
            sorted(
                (
                    path
                    for path in root.glob("service_*.log")
                    if path.name != "service_latest.log"
                ),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
        )
        if candidates:
            break
    output: List[Path] = []
    seen: Set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        output.append(path)
        if len(output) >= max_files:
            break
    return output


def filtered_connections(payload: Optional[Dict[str, Any]], app: str) -> List[Dict[str, Any]]:
    if not payload:
        return []
    pattern = re.compile(app, re.IGNORECASE)
    output = []
    for connection in payload.get("connections", []):
        metadata = connection.get("metadata", {})
        haystack = " ".join(
            str(metadata.get(field) or "")
            for field in ("process", "host", "destinationIP")
        )
        if pattern.search(haystack):
            output.append(
                {
                    "network": metadata.get("network"),
                    "process": metadata.get("process"),
                    "host": metadata.get("host"),
                    "destination_ip": metadata.get("destinationIP"),
                    "destination_port": metadata.get("destinationPort"),
                    "rule": connection.get("rule"),
                    "rule_payload": connection.get("rulePayload"),
                    "chains": connection.get("chains", []),
                    "upload": connection.get("upload", 0),
                    "download": connection.get("download", 0),
                }
            )
    return output


def filtered_rules(payload: Optional[Dict[str, Any]], app: str) -> List[Dict[str, Any]]:
    if not payload:
        return []
    terms = [app]
    if app.lower() == "wechat":
        terms += ["weixin", "qpic", "qlogo", "servicewechat"]
    pattern = re.compile("|".join(map(re.escape, terms)), re.IGNORECASE)
    return [
        {"type": item.get("type"), "payload": item.get("payload"), "proxy": item.get("proxy")}
        for item in payload.get("rules", [])
        if pattern.search(str(item.get("payload") or ""))
    ]


def recent_log_findings(log_text: str, app: str, limit: int = 4000) -> Dict[str, Any]:
    lines = log_text.splitlines()[-limit:]
    app_pattern = re.compile(app, re.IGNORECASE)
    relevant = [line for line in lines if app_pattern.search(line)]
    no_route = [line for line in relevant if "no route to host" in line.lower()]
    timeouts = [line for line in relevant if "deadline exceeded" in line.lower() or "i/o timeout" in line.lower()]
    ipv6 = [line for line in relevant if re.search(r"\[[0-9a-f:]{3,}\]", line, re.IGNORECASE)]
    return {
        "matched_lines": len(relevant),
        "no_route_to_host": len(no_route),
        "timeouts": len(timeouts),
        "ipv6_lines": len(ipv6),
        "samples": (no_route + timeouts)[:5],
    }


def normalize_host(value: str) -> Optional[str]:
    host = value.strip().lower().rstrip(".")
    return host if HOSTNAME_RE.fullmatch(host) else None


def compile_filter(value: str) -> re.Pattern[str]:
    try:
        return re.compile(value, re.IGNORECASE)
    except re.error as error:
        raise SystemExit(f"Invalid --app regular expression: {error}") from error


def persistent_prepend_rules(text: str) -> List[str]:
    lines = text.splitlines()
    start = next(
        (index for index, line in enumerate(lines) if re.match(r"^prepend:\s*(?:#.*)?$", line)),
        None,
    )
    if start is None:
        return []
    output: List[str] = []
    for line in lines[start + 1 :]:
        if line.strip() and not line.startswith((" ", "\t", "#")):
            break
        match = re.match(r"^\s*-\s*(.+?)\s*$", line)
        if not match:
            continue
        raw = match.group(1)
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = raw.strip("\"'")
        if isinstance(value, str):
            output.append(value)
    return output


def merge_prepend(text: str, rules: Iterable[str]) -> str:
    requested = list(dict.fromkeys(rules))
    existing = set(persistent_prepend_rules(text))
    missing = [rule for rule in requested if rule not in existing]
    if not missing:
        return text

    lines = text.splitlines(keepends=True)
    empty_inline = next(
        (
            index
            for index, line in enumerate(lines)
            if re.match(r"^prepend:\s*\[\]\s*(?:#.*)?$", line.rstrip("\n"))
        ),
        None,
    )
    rendered = [f'  - {json.dumps(rule, ensure_ascii=False)}\n' for rule in missing]
    if empty_inline is not None:
        return "".join(lines[:empty_inline] + ["prepend:\n"] + rendered + lines[empty_inline + 1 :])

    start = next(
        (
            index
            for index, line in enumerate(lines)
            if re.match(r"^prepend:\s*(?:#.*)?$", line.rstrip("\n"))
        ),
        None,
    )
    if start is None:
        prefix = ["prepend:\n"] + rendered
        if text and not text.startswith("\n"):
            prefix.append("\n")
        return "".join(prefix) + text.lstrip("\n")
    return "".join(lines[: start + 1] + rendered + lines[start + 1 :])


def merge_generated_rules(text: str, rules: Iterable[str]) -> str:
    requested = list(dict.fromkeys(rules))
    existing = {
        match.group(1).strip()
        for match in re.finditer(r"(?m)^-\s+(.+?)\s*$", text)
    }
    missing = [rule for rule in requested if rule not in existing]
    if not missing:
        return text
    lines = text.splitlines(keepends=True)
    start = next(
        (index for index, line in enumerate(lines) if re.match(r"^rules:\s*$", line.rstrip("\n"))),
        None,
    )
    if start is None:
        raise SystemExit("Generated Clash config has no top-level rules section.")
    rendered = [f"- {rule}\n" for rule in missing]
    return "".join(lines[: start + 1] + rendered + lines[start + 1 :])


def _add_direct_observation(
    records: Dict[str, Dict[str, Any]],
    host_value: str,
    source: str,
    rule: Optional[str] = None,
    proxy: Optional[str] = None,
) -> None:
    host = normalize_host(host_value)
    if host is None:
        return
    record = records.setdefault(
        host,
        {"host": host, "occurrences": 0, "sources": set(), "observed_routes": set()},
    )
    record["occurrences"] += 1
    record["sources"].add(source)
    if rule or proxy:
        record["observed_routes"].add((rule or "", proxy or ""))


def route_is_direct(proxy: str) -> bool:
    return proxy.strip().upper() == "DIRECT"


def discover_direct_list(
    data_dir: Path,
    socket_path: Path,
    app: str,
    explicit_hosts: Iterable[str] = (),
    log_limit: int = 4000,
) -> Dict[str, Any]:
    pattern = compile_filter(app)
    records: Dict[str, Dict[str, Any]] = {}
    for host in explicit_hosts:
        normalized = normalize_host(host)
        if normalized is None:
            raise SystemExit(f"Invalid --host value: {host}")
        _add_direct_observation(records, normalized, "explicit")

    connections_payload = api_json(socket_path, "/connections") or {}
    for connection in connections_payload.get("connections", []):
        metadata = connection.get("metadata", {})
        host = str(metadata.get("host") or "")
        process = str(metadata.get("process") or "")
        if not pattern.search(f"{process} {host}"):
            continue
        chains = connection.get("chains") or []
        proxy = " > ".join(map(str, chains))
        _add_direct_observation(
            records,
            host,
            "runtime-connection",
            str(connection.get("rule") or ""),
            proxy,
        )

    log_paths = recent_service_logs(data_dir)
    seen_log_lines: Set[str] = set()
    for log_path in log_paths:
        for line in read_text(log_path).splitlines()[-log_limit:]:
            if line in seen_log_lines:
                continue
            seen_log_lines.add(line)
            match = CONNECTION_LOG_RE.search(line)
            if not match:
                continue
            host = match.group("host")
            process = match.group("process")
            if not pattern.search(f"{process} {host}"):
                continue
            _add_direct_observation(
                records,
                host,
                "service-log",
                match.group("rule").strip(),
                match.group("proxy").strip().rstrip('"'),
            )

    runtime_rules = api_json(socket_path, "/rules") or {}
    exact_runtime_rules: Dict[str, Dict[str, Any]] = {}
    for rule in runtime_rules.get("rules", []):
        host = normalize_host(str(rule.get("payload") or ""))
        if host is not None and str(rule.get("type") or "").lower() == "domain":
            exact_runtime_rules[host] = {
                "type": rule.get("type"),
                "payload": rule.get("payload"),
                "proxy": rule.get("proxy"),
            }

    rules_path = current_rules_file(data_dir)
    persisted = set(persistent_prepend_rules(read_text(rules_path))) if rules_path else set()
    observed_items = []
    for host in sorted(records):
        record = records[host]
        rule = f"DOMAIN,{host},DIRECT"
        current = exact_runtime_rules.get(host)
        routes = [
            {"rule": route, "proxy": proxy}
            for route, proxy in sorted(record["observed_routes"])
        ]
        non_direct_observed = any(
            route["proxy"] and not route_is_direct(route["proxy"])
            for route in routes
        )
        item = {
            "host": host,
            "rule": rule,
            "explicit_direct": rule in persisted,
            "runtime_direct": bool(current and current.get("proxy") == "DIRECT"),
            "runtime_rule": current,
            "non_direct_observed": non_direct_observed,
            "occurrences": record["occurrences"],
            "sources": sorted(record["sources"]),
            "observed_routes": routes,
        }
        observed_items.append(item)
    items = [
        item
        for item in observed_items
        if item["explicit_direct"]
        or item["runtime_direct"]
        or item["non_direct_observed"]
        or "explicit" in item["sources"]
    ]
    rules = [item["rule"] for item in items]
    return {
        "filter": app,
        "service_logs": [str(path) for path in log_paths],
        "rules_file": None if rules_path is None else str(rules_path),
        "items": items,
        "rules": rules,
        "missing_rules": [item["rule"] for item in items if not item["explicit_direct"]],
        "ignored_direct_hosts": [
            item["host"] for item in observed_items if item not in items
        ],
    }


def diagnose(data_dir: Path, socket_path: Path, app: str) -> Dict[str, Any]:
    app_config = read_text(data_dir / "config.yaml")
    generated = read_text(data_dir / "clash-verge.yaml")
    runtime = api_json(socket_path, "/configs")
    connections = filtered_connections(api_json(socket_path, "/connections"), app)
    ipv6_destinations = sum(1 for item in connections if ":" in str(item.get("destination_ip") or ""))
    return {
        "data_dir": str(data_dir),
        "socket": str(socket_path),
        "app_config_ipv6": yaml_bool(app_config, "ipv6"),
        "generated_ipv6": generated_ipv6(generated),
        "runtime_ipv6": None if runtime is None else runtime.get("ipv6"),
        "rules": filtered_rules(api_json(socket_path, "/rules"), app),
        "connections": connections,
        "ipv6_destinations": ipv6_destinations,
        "logs": recent_log_findings(read_text(service_log(data_dir)), app),
    }


def replace_top_level_ipv6(text: str) -> str:
    pattern = re.compile(r"(?m)^ipv6:\s*(?:true|false)\s*$")
    if pattern.search(text):
        return pattern.sub("ipv6: false", text, count=1)
    suffix = "" if text.endswith("\n") else "\n"
    return text + suffix + "ipv6: false\n"


def stop_clash() -> None:
    if sys.platform != "darwin":
        return
    subprocess.run(
        ["osascript", "-e", f'tell application "{APP_BUNDLE}" to quit'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    for _ in range(30):
        result = subprocess.run(["pgrep", "-x", "clash-verge"], stdout=subprocess.DEVNULL, check=False)
        if result.returncode != 0:
            break
        time.sleep(0.2)


def start_clash() -> None:
    if sys.platform == "darwin":
        subprocess.run(["open", "-a", APP_BUNDLE], check=True)


def backup_files(data_dir: Path, files: Iterable[Path]) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    root = data_dir / "backups/clash-tun-doctor" / stamp
    root.mkdir(parents=True, exist_ok=False)
    mappings = []
    for index, source in enumerate(files):
        target = root / f"{index:02d}-{source.name}"
        shutil.copy2(source, target)
        mappings.append({"source": str(source), "backup": str(target)})
    (root / "manifest.json").write_text(json.dumps({"files": mappings}, indent=2), encoding="utf-8")
    return root


def wait_for_runtime(socket_path: Path, timeout: float = 15.0) -> Optional[Dict[str, Any]]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        payload = api_json(socket_path, "/configs")
        if payload is not None:
            return payload
        time.sleep(0.25)
    return None


def verify_direct_hosts(socket_path: Path, hosts: Iterable[str], timeout: float = 5.0) -> bool:
    required = {host.lower() for host in hosts}
    deadline = time.time() + timeout
    while time.time() < deadline:
        payload = api_json(socket_path, "/rules") or {}
        direct = {
            str(rule.get("payload") or "").lower()
            for rule in payload.get("rules", [])
            if str(rule.get("type") or "").lower() == "domain"
            and rule.get("proxy") == "DIRECT"
        }
        if required.issubset(direct):
            return True
        time.sleep(0.25)
    return False


def write_direct_list(path_value: str, rules: Iterable[str]) -> Path:
    path = Path(os.path.expandvars(os.path.expanduser(path_value))).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = "payload:\n" + "".join(f"  - {rule}\n" for rule in rules)
    path.write_text(rendered, encoding="utf-8")
    return path


def apply_direct_list(
    data_dir: Path,
    socket_path: Path,
    discovery: Dict[str, Any],
    reload_runtime: bool,
) -> Tuple[int, Dict[str, Any]]:
    rules = discovery["rules"]
    if not rules:
        return 2, {
            "ok": False,
            "reason": "No matching host evidence found.",
            "discovery": discovery,
        }
    rules_path = current_rules_file(data_dir)
    if rules_path is None:
        raise SystemExit("Cannot resolve current profile rule file from profiles.yaml.")
    generated_path = data_dir / "clash-verge.yaml"
    if not generated_path.exists():
        raise SystemExit(f"Missing generated Clash config: {generated_path}")

    rules_new = merge_prepend(read_text(rules_path), rules)
    generated_new = merge_generated_rules(read_text(generated_path), rules)
    changed_files = []
    if rules_new != read_text(rules_path):
        changed_files.append(rules_path)
    if generated_new != read_text(generated_path):
        changed_files.append(generated_path)

    backup = backup_files(data_dir, changed_files) if changed_files else None
    if rules_path in changed_files:
        rules_path.write_text(rules_new, encoding="utf-8")
    if generated_path in changed_files:
        generated_path.write_text(generated_new, encoding="utf-8")

    reloaded: Optional[bool] = None
    verified: Optional[bool] = None
    if reload_runtime:
        reloaded = api_json(
            socket_path,
            "/configs?force=true",
            method="PUT",
            body={"path": str(generated_path)},
        ) is not None
        verified = reloaded and verify_direct_hosts(
            socket_path,
            [item["host"] for item in discovery["items"]],
        )

    result = {
        "ok": verified if reload_runtime else True,
        "backup": None if backup is None else str(backup),
        "changed_files": [str(path) for path in changed_files],
        "runtime_reloaded": reloaded,
        "runtime_verified": verified,
        "discovery": discovery,
    }
    return (0 if result["ok"] else 2), result


def print_direct_list(result: Dict[str, Any]) -> None:
    print(f"DIRECT target list: {len(result['rules'])} host(s); filter={result['filter']}")
    for item in result["items"]:
        status = "DIRECT" if item["runtime_direct"] else "candidate"
        persisted = "saved" if item["explicit_direct"] else "missing"
        print(
            f"- {item['host']} [{status}, {persisted}, evidence={item['occurrences']}]"
        )
    print("Rules:")
    for rule in result["rules"]:
        print(f"  {rule}")
    if result["missing_rules"]:
        print("Missing explicit DIRECT rules:")
        for rule in result["missing_rules"]:
            print(f"  {rule}")


def repair_plan(data_dir: Path) -> Tuple[Path, Path, str, str]:
    config_path = data_dir / "config.yaml"
    rules_path = current_rules_file(data_dir)
    if not config_path.exists():
        raise SystemExit(f"Missing Clash Verge config: {config_path}")
    if rules_path is None:
        raise SystemExit("Cannot resolve current profile rule file from profiles.yaml.")
    return (
        config_path,
        rules_path,
        replace_top_level_ipv6(read_text(config_path)),
        merge_prepend(read_text(rules_path), WECHAT_RULES),
    )


def fix_wechat(data_dir: Path, socket_path: Path, apply: bool, restart: bool) -> int:
    config_path, rules_path, config_new, rules_new = repair_plan(data_dir)
    changes = [
        {"path": str(config_path), "changed": config_new != read_text(config_path), "action": "set global ipv6=false"},
        {"path": str(rules_path), "changed": rules_new != read_text(rules_path), "action": "prepend WeChat DIRECT rules"},
    ]
    if not apply:
        print(json.dumps({"dry_run": True, "changes": changes, "rules": WECHAT_RULES}, ensure_ascii=False, indent=2))
        return 0

    stop_clash()
    backup = backup_files(data_dir, [config_path, rules_path])
    config_path.write_text(config_new, encoding="utf-8")
    rules_path.write_text(rules_new, encoding="utf-8")
    if restart:
        start_clash()
        wait_for_runtime(socket_path)
    result = diagnose(data_dir, socket_path, "wechat")
    verified = result.get("runtime_ipv6") is False and all(
        rule.get("proxy") == "DIRECT" for rule in result.get("rules", [])[: len(WECHAT_RULES)]
    )
    print(json.dumps({"ok": verified, "backup": str(backup), "diagnosis": result}, ensure_ascii=False, indent=2))
    return 0 if verified else 2


def latest_backup(data_dir: Path) -> Optional[Path]:
    root = data_dir / "backups/clash-tun-doctor"
    candidates = sorted((p for p in root.glob("*") if (p / "manifest.json").exists()), reverse=True)
    return candidates[0] if candidates else None


def rollback(data_dir: Path, apply: bool, restart: bool, backup_arg: Optional[str]) -> int:
    root = Path(backup_arg).resolve() if backup_arg else latest_backup(data_dir)
    if root is None:
        raise SystemExit("No clash-tun-doctor backup found.")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if not apply:
        print(json.dumps({"dry_run": True, "backup": str(root), "restore": manifest["files"]}, indent=2))
        return 0
    stop_clash()
    for item in manifest["files"]:
        shutil.copy2(item["backup"], item["source"])
    if restart:
        start_clash()
        wait_for_runtime(resolve_socket(data_dir, None))
    print(json.dumps({"ok": True, "restored": str(root)}, indent=2))
    return 0


def print_human(result: Dict[str, Any]) -> None:
    print(f"Data dir: {result['data_dir']}")
    print(
        "IPv6: app-config={app} generated={generated} dns={dns} runtime={runtime}".format(
            app=result["app_config_ipv6"],
            generated=result["generated_ipv6"]["top_level"],
            dns=result["generated_ipv6"]["dns"],
            runtime=result["runtime_ipv6"],
        )
    )
    print(f"Connections: {len(result['connections'])}; IPv6 destinations: {result['ipv6_destinations']}")
    print(
        "Recent logs: no-route={no_route_to_host} timeouts={timeouts} IPv6-lines={ipv6_lines}".format(
            **result["logs"]
        )
    )
    for rule in result["rules"][:12]:
        print(f"Rule: {rule['type']},{rule['payload']} => {rule['proxy']}")
    for sample in result["logs"]["samples"]:
        print(f"Log: {sample}")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--data-dir", help="Clash Verge Rev application data directory")
    root.add_argument("--socket", help="Mihomo controller Unix socket")
    subparsers = root.add_subparsers(dest="command", required=True)

    diagnose_parser = subparsers.add_parser("diagnose", help="Read-only evidence collection")
    diagnose_parser.add_argument("--app", default="wechat", help="Application/process/host filter")
    diagnose_parser.add_argument("--json", action="store_true", help="Emit JSON")

    direct_parser = subparsers.add_parser(
        "direct-list",
        help="Discover, export, or apply a reusable DIRECT target list",
    )
    direct_parser.add_argument(
        "--app",
        default="wechat",
        help="Regular expression matched against process and host evidence",
    )
    direct_parser.add_argument(
        "--host",
        action="append",
        default=[],
        help="Include an explicit hostname; repeat for multiple hosts",
    )
    direct_parser.add_argument(
        "--log-limit",
        type=int,
        default=4000,
        help="Number of recent service-log lines to inspect",
    )
    direct_parser.add_argument(
        "--output",
        help="Write a Mihomo classical rule-provider YAML list",
    )
    direct_parser.add_argument("--apply", action="store_true", help="Persist and hot-load the list")
    direct_parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Persist without hot-loading the generated config",
    )
    direct_parser.add_argument("--json", action="store_true", help="Emit JSON")

    fix_parser = subparsers.add_parser("fix-wechat", help="Preview or apply WeChat direct/IPv4 repair")
    fix_parser.add_argument("--apply", action="store_true", help="Apply changes")
    fix_parser.add_argument("--no-restart", action="store_true", help="Do not restart Clash Verge")

    rollback_parser = subparsers.add_parser("rollback", help="Preview or restore a repair backup")
    rollback_parser.add_argument("--backup", help="Specific backup directory; newest is default")
    rollback_parser.add_argument("--apply", action="store_true", help="Restore files")
    rollback_parser.add_argument("--no-restart", action="store_true", help="Do not restart Clash Verge")
    return root


def main() -> int:
    args = parser().parse_args()
    data_dir = resolve_data_dir(args.data_dir)
    socket_path = resolve_socket(data_dir, args.socket)
    if args.command == "diagnose":
        result = diagnose(data_dir, socket_path, args.app)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print_human(result)
        return 0
    if args.command == "direct-list":
        result = discover_direct_list(
            data_dir,
            socket_path,
            args.app,
            explicit_hosts=args.host,
            log_limit=args.log_limit,
        )
        if args.output:
            result["output"] = str(write_direct_list(args.output, result["rules"]))
        if args.apply:
            exit_code, applied = apply_direct_list(
                data_dir,
                socket_path,
                result,
                reload_runtime=not args.no_reload,
            )
            print(json.dumps(applied, ensure_ascii=False, indent=2))
            return exit_code
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print_direct_list(result)
        return 0
    if args.command == "fix-wechat":
        return fix_wechat(data_dir, socket_path, args.apply, not args.no_restart)
    return rollback(data_dir, args.apply, not args.no_restart, args.backup)


if __name__ == "__main__":
    raise SystemExit(main())
