#!/usr/bin/env python3
"""Chain an IPRoyal ISP proxy behind a RayLink subscription in Clash Verge Rev.

IPRoyal ISP endpoints only speak plaintext HTTP/SOCKS5. Dialed from mainland
China they are reset by the GFW and randomly refused, so the proxy is attached
to the RayLink profile with ``dialer-proxy`` pointing at an encrypted RayLink
TCP group. Everything lives in one managed block of the profile's Clash Verge
script enhancement, which Clash Verge (v2.0+) runs after every other profile
enhancement, so the block also supersedes older hand-made definitions.

Standard library only. PyYAML is used when present but not required.
"""

from __future__ import annotations

import argparse
import datetime as dt
import http.client
import json
import os
from pathlib import Path
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

SKILL_ID = "lov-iproyal-raylink"
APP_ID = "io.github.clash-verge-rev.clash-verge-rev"
APP_NAME = "Clash Verge"
BEGIN = "// >>> lov-iproyal-raylink >>>"
END = "// <<< lov-iproyal-raylink <<<"
MAIN_BEGIN = "// >>> lov-iproyal-raylink:main >>>"
MAIN_END = "// <<< lov-iproyal-raylink:main <<<"
USER_MAIN = "lovUserMain"
STOCK_MAIN = "function main(config, profileName) {\n  return config;\n}\n"
TEST_URL = "https://www.gstatic.com/generate_204"
TRACE_URL = "https://chatgpt.com/cdn-cgi/trace"
RAYLINK_MARKERS = ("raylink-local-", "RayLink 代理", "TCP 稳定", "AI 网站代理")

DEFAULTS = {
    "name": "IPRoyal ISP",
    "exit_group": "IPRoyal 出口",
    "carrier": "TCP 稳定",
    "expose": "RayLink 代理,AI 网站代理",
    "select": "AI 网站代理",
    "type": "http",
}


class SkillError(RuntimeError):
    pass


# --------------------------------------------------------------------------- paths


def default_data_dir() -> Path:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / APP_ID
    if system == "Windows":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / APP_ID
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / APP_ID


def resolve_data_dir(arg: Optional[str]) -> Path:
    value = arg or os.environ.get("CLASH_VERGE_DATA_DIR")
    path = Path(value).expanduser() if value else default_data_dir()
    if not (path / "profiles.yaml").is_file():
        raise SkillError(f"未找到 Clash Verge Rev 数据目录（缺少 profiles.yaml）: {path}；用 --data-dir 指定")
    return path


# ------------------------------------------------------------------ profiles.yaml


def _scalar(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "'\"":
        return raw[1:-1]
    return "" if raw in ("null", "~") else raw


def load_profiles(data_dir: Path) -> Dict[str, Any]:
    text = (data_dir / "profiles.yaml").read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or {}
        items = []
        for item in data.get("items") or []:
            items.append({
                "uid": str(item.get("uid")),
                "type": item.get("type"),
                "name": item.get("name") or "",
                "file": item.get("file"),
                "option": item.get("option") or {},
                "selected": item.get("selected") or [],
            })
        return {"current": data.get("current"), "items": items, "text": text}
    except ImportError:
        pass
    current = re.search(r"^current:\s*(.+)$", text, re.M)
    items = []
    for block in re.split(r"^(?=- uid:)", text, flags=re.M)[1:]:
        item: Dict[str, Any] = {"option": {}, "selected": []}
        item["uid"] = _scalar(re.match(r"- uid:\s*(.+)", block).group(1))
        for key in ("type", "name", "file"):
            m = re.search(rf"^  {key}:\s*(.*)$", block, re.M)
            item[key] = _scalar(m.group(1)) if m else ""
        for m in re.finditer(r"^    (merge|script|rules|proxies|groups):\s*(\S+)\s*$", block, re.M):
            item["option"][m.group(1)] = _scalar(m.group(2))
        for m in re.finditer(r"^  - name:\s*(.+)\n    now:\s*(.+)$", block, re.M):
            item["selected"].append({"name": _scalar(m.group(1)), "now": _scalar(m.group(2))})
        items.append(item)
    return {"current": _scalar(current.group(1)) if current else None, "items": items, "text": text}


def raylink_score(text: str) -> int:
    return sum(1 for marker in RAYLINK_MARKERS if marker in text)


def group_defined(text: str, name: str) -> bool:
    return re.search(r"name:\s*[\"']?" + re.escape(name) + r"[\"']?\s*$", text, re.M) is not None


def pick_profile(data_dir: Path, profiles: Dict[str, Any], wanted: Optional[str]) -> Dict[str, Any]:
    candidates = []
    for item in profiles["items"]:
        if item.get("type") not in ("remote", "local") or not item.get("file"):
            continue
        path = data_dir / "profiles" / item["file"]
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        item = dict(item, path=path, text=text, score=raylink_score(text),
                    current=item["uid"] == profiles["current"])
        if wanted and wanted in (item["uid"], item["name"]):
            return item
        candidates.append(item)
    if wanted:
        raise SkillError(f"找不到配置 {wanted!r}；用 detect 查看可用的 uid")
    raylink = sorted((c for c in candidates if c["score"] >= 3), key=lambda c: (not c["current"], -c["score"]))
    if not raylink:
        raise SkillError("没有识别到 RayLink 订阅（需要包含 RayLink 代理 / TCP 稳定 分组）；用 --profile 指定")
    if len(raylink) > 1 and not raylink[0]["current"]:
        names = ", ".join(f"{c['uid']}({c['name']})" for c in raylink)
        raise SkillError(f"识别到多个 RayLink 配置: {names}；用 --profile 指定")
    return raylink[0]


def script_path(data_dir: Path, profile: Dict[str, Any]) -> Path:
    uid = (profile.get("option") or {}).get("script")
    if not uid:
        raise SkillError("该配置没有 Script 增强项；请先在 Clash Verge 中打开一次该配置的“扩展脚本”")
    path = data_dir / "profiles" / f"{uid}.js"
    if not path.is_file():
        raise SkillError(f"脚本增强文件不存在: profiles/{uid}.js")
    return path


# ------------------------------------------------------------------ credentials


def parse_proxy(raw: str) -> Dict[str, Any]:
    raw = raw.strip()
    if "://" in raw:
        u = urllib.parse.urlsplit(raw)
        if not (u.hostname and u.port and u.username and u.password is not None):
            raise SkillError("代理 URL 需要包含 用户名:密码@主机:端口")
        return {"host": u.hostname, "port": u.port, "username": urllib.parse.unquote(u.username),
                "password": urllib.parse.unquote(u.password),
                "type": "socks5" if u.scheme.startswith("socks") else "http"}
    parts = raw.split(":", 3)
    if len(parts) != 4 or not parts[1].isdigit():
        raise SkillError("代理字符串格式应为 IPRoyal 后台的 主机:端口:用户名:密码")
    return {"host": parts[0], "port": int(parts[1]), "username": parts[2], "password": parts[3]}


def read_credentials(args: argparse.Namespace) -> Dict[str, Any]:
    if args.proxy_file:
        raw = Path(args.proxy_file).expanduser().read_text(encoding="utf-8").strip().splitlines()[0]
    else:
        raw = os.environ.get(args.proxy_env, "")
    if not raw:
        raise SkillError(f"缺少 IPRoyal 代理：设置环境变量 {args.proxy_env}=主机:端口:用户名:密码，或用 --proxy-file")
    cred = parse_proxy(raw)
    cred["type"] = args.type or cred.get("type") or DEFAULTS["type"]
    return cred


def masked(cred: Dict[str, Any]) -> str:
    return f"{cred['type']}://***:***@{cred['host']}:{cred['port']}"


# ----------------------------------------------------------------------- script


def build_block(settings: Dict[str, Any]) -> str:
    payload = json.dumps(settings, ensure_ascii=False, indent=2)
    return f"""{BEGIN}
// Managed by the {SKILL_ID} skill; re-run the skill instead of editing this block.
// IPRoyal ISP speaks plaintext HTTP/SOCKS5. Dialed from mainland China it is reset by the
// GFW and randomly refused, so it always rides an encrypted RayLink group via dialer-proxy.
const LOV_IPROYAL_RAYLINK = {payload};

function lovIproyalRaylink(config) {{
  const s = LOV_IPROYAL_RAYLINK;
  const isp = s.proxy.name;
  config.proxies = [s.proxy, ...(config.proxies || []).filter(p => p && p.name !== isp)];
  const groups = (config["proxy-groups"] || []).filter(g => g && g.name !== s.exitGroup);
  const byName = {{}};
  for (const g of groups) byName[g.name] = g;
  // Groups behind the carrier must never route back into the exit, or the chain loops.
  const behind = new Set();
  const walk = name => {{
    if (behind.has(name) || !byName[name]) return;
    behind.add(name);
    for (const member of byName[name].proxies || []) walk(member);
  }};
  walk(s.proxy["dialer-proxy"]);
  for (const g of groups) {{
    if (!Array.isArray(g.proxies)) continue;
    // Clash Verge copies proxies-enhancement entries into the first group; the ISP is only
    // reachable through its exit group.
    let list = g.proxies.filter(name => name !== isp);
    if (s.expose.includes(g.name) && !behind.has(g.name)) {{
      const rest = list.filter(name => name !== s.exitGroup);
      // Only groups the user chose lead with the exit; others just offer it.
      list = s.prefer.includes(g.name) ? [s.exitGroup, ...rest] : [...rest, s.exitGroup];
    }}
    g.proxies = list;
  }}
  groups.push({{ name: s.exitGroup, type: "select", proxies: [isp] }});
  config["proxy-groups"] = groups;
  return config;
}}
{END}
"""


def _strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def script_state(text: str) -> str:
    if BEGIN in text:
        return "managed"
    body = re.sub(r"\s+", "", _strip_comments(text))
    if re.fullmatch(r"(function)?main\(config(,profileName)?\)\{returnconfig;?\}", body) or body == "":
        return "stock"
    return "custom"


def _without_blocks(text: str) -> str:
    for begin, end in ((BEGIN, END), (MAIN_BEGIN, MAIN_END)):
        text = re.sub(re.escape(begin) + r".*?" + re.escape(end) + r"\n?", "", text, flags=re.S)
    return text


def render_script(current: str, block: str, wrap_existing: bool) -> Tuple[str, str]:
    state = script_state(current)
    if state == "managed":
        rest = _without_blocks(current)
        main = re.search(re.escape(MAIN_BEGIN) + r".*?" + re.escape(MAIN_END) + r"\n?", current, re.S)
        return block + (main.group(0) if main else "") + rest.lstrip("\n"), "updated managed block"
    if state == "stock":
        main = (f"{MAIN_BEGIN}\nfunction main(config, profileName) {{\n"
                f"  return lovIproyalRaylink(config);\n}}\n{MAIN_END}\n")
        return block + main, "replaced stock template"
    if not wrap_existing:
        raise SkillError("该配置的脚本增强已有自定义内容。加 --wrap-existing 让原 main 先运行、再接入 IPRoyal；"
                         "或手动在原 main 的 return 前加一行 config = lovIproyalRaylink(config);")
    if not re.search(r"function\s+main\s*\(", current):
        raise SkillError("自定义脚本里找不到 function main(...)，无法自动包装")
    renamed = re.sub(r"function\s+main\s*\(", f"function {USER_MAIN}(", current, count=1)
    main = (f"{MAIN_BEGIN}\n// Wraps the original main (renamed {USER_MAIN}).\n"
            f"function main(config, profileName) {{\n"
            f"  return lovIproyalRaylink({USER_MAIN}(config, profileName));\n}}\n{MAIN_END}\n")
    return block + main + renamed, "wrapped existing main"


def remove_from_script(current: str) -> str:
    text = _without_blocks(current)
    if re.search(rf"function\s+{USER_MAIN}\s*\(", text):
        text = re.sub(rf"function\s+{USER_MAIN}\s*\(", "function main(", text, count=1)
    if not re.search(r"function\s+main\s*\(", text):
        text = text.rstrip("\n") + ("\n\n" if text.strip() else "") + STOCK_MAIN
    return text.lstrip("\n")


def managed_settings(text: str) -> Optional[Dict[str, Any]]:
    m = re.search(r"const LOV_IPROYAL_RAYLINK = (\{.*?\n\});", text, re.S)
    return json.loads(m.group(1)) if m else None


def node_check(text: str) -> Optional[str]:
    node = shutil.which("node")
    if not node:
        return None
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(text)
        tmp = fh.name
    try:
        r = subprocess.run([node, "--check", tmp], capture_output=True, text=True)
        return None if r.returncode == 0 else r.stderr.strip()[-400:]
    finally:
        os.unlink(tmp)


# ----------------------------------------------------------------------- backup


def backup(data_dir: Path, files: List[Path], meta: Dict[str, Any]) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    target = data_dir / "backups" / f"{SKILL_ID}-{stamp}"
    target.mkdir(parents=True, exist_ok=False)
    os.chmod(target, 0o700)
    rel = []
    for f in files:
        dest = target / f.relative_to(data_dir)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        rel.append(str(f.relative_to(data_dir)))
    (target / "manifest.json").write_text(json.dumps(dict(meta, files=rel, created=stamp),
                                                     ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def write_private(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


# ------------------------------------------------------------------- controller


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, path: str, timeout: float) -> None:
        super().__init__("localhost", timeout=timeout)
        self.unix_path = path

    def connect(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect(self.unix_path)
        self.sock = sock


def read_app_config(data_dir: Path) -> Dict[str, str]:
    path = data_dir / "config.yaml"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    out = {}
    for key in ("external-controller", "external-controller-unix", "secret", "mixed-port"):
        m = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, re.M)
        if m:
            out[key] = _scalar(m.group(1))
    return out


class Controller:
    def __init__(self, data_dir: Path, socket_path: Optional[str], tcp: Optional[str], secret: Optional[str]):
        cfg = read_app_config(data_dir)
        self.secret = secret if secret is not None else cfg.get("secret", "")
        self.target: Optional[Tuple[str, str]] = None
        sockets = [socket_path] if socket_path else []
        if hasattr(os, "getuid"):
            sockets.append(f"/var/run/clash-verge-service/users/{os.getuid()}/verge-mihomo.sock")
        sockets += [cfg.get("external-controller-unix"), "/tmp/verge/verge-mihomo.sock"]
        candidates = [("unix", s) for s in sockets if s and not tcp]
        tcp_addr = tcp or cfg.get("external-controller")
        if tcp_addr:
            candidates.append(("tcp", tcp_addr))
        for kind, addr in candidates:
            self.target = (kind, addr)
            try:
                self.request("GET", "/version", timeout=3)
                return
            except Exception:
                self.target = None
        self.tried = [a for _, a in candidates]

    @property
    def ok(self) -> bool:
        return self.target is not None

    def request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None, timeout: float = 15) -> Any:
        kind, addr = self.target  # type: ignore[misc]
        if kind == "unix":
            conn: http.client.HTTPConnection = UnixHTTPConnection(addr, timeout)
        else:
            host, _, port = addr.rpartition(":")
            conn = http.client.HTTPConnection(host.strip("[]") or "127.0.0.1", int(port), timeout=timeout)
        headers = {"Content-Type": "application/json"}
        if kind == "tcp" and self.secret:
            headers["Authorization"] = f"Bearer {self.secret}"
        conn.request(method, urllib.parse.quote(path, safe="/?=&%"), json.dumps(body) if body else None, headers)
        resp = conn.getresponse()
        data = resp.read()
        if resp.status >= 400:
            raise SkillError(f"controller {method} {path} -> {resp.status} {data[:200]!r}")
        return json.loads(data) if data else {}

    def proxy(self, name: str) -> Optional[Dict[str, Any]]:
        try:
            return self.request("GET", f"/proxies/{name}")
        except SkillError:
            return None


# ---------------------------------------------------------------- app lifecycle


def app_running() -> bool:
    return subprocess.run(["pgrep", "-f", f"{APP_NAME}.app/Contents/MacOS/clash-verge"],
                          capture_output=True).returncode == 0


def restart_app(data_dir: Path, args: argparse.Namespace, edit: Any, exit_group: str) -> Controller:
    if platform.system() != "Darwin":
        raise SkillError("--restart 只支持 macOS；请手动重启 Clash Verge")
    subprocess.run(["osascript", "-e", f'quit app "{APP_NAME}"'], check=False)
    for _ in range(60):
        if not app_running():
            break
        time.sleep(0.5)
    else:
        raise SkillError("Clash Verge 未能退出")
    if edit:
        edit()
    subprocess.run(["open", "-a", APP_NAME], check=True)
    for _ in range(60):
        time.sleep(1)
        ctl = Controller(data_dir, args.socket, args.controller, args.secret)
        if ctl.ok and ctl.proxy(exit_group):
            return ctl
    raise SkillError("Clash Verge 已重启，但运行时里没有出现出口分组；查看 Clash Verge 的配置报错")


def set_selected(profiles_text: str, uid: str, group: str, now: str) -> Optional[str]:
    """Persist a group selection in profiles.yaml (Clash Verge re-applies it on activation)."""
    blocks = re.split(r"^(?=- uid:)", profiles_text, flags=re.M)
    for i, block in enumerate(blocks):
        if not re.match(rf"- uid:\s*['\"]?{re.escape(uid)}['\"]?\s*$", block.split("\n", 1)[0]):
            continue
        entry = re.compile(rf"(^  - name:\s*['\"]?{re.escape(group)}['\"]?\s*\n    now:\s*).*$", re.M)
        if entry.search(block):
            block = entry.sub(lambda m: m.group(1) + now, block, count=1)
        elif re.search(r"^  selected:\s*$", block, re.M):
            block = re.sub(r"^(  selected:\s*\n)", rf"\1  - name: {group}\n    now: {now}\n", block, count=1, flags=re.M)
        elif re.search(r"^  selected:\s*\[\]\s*$", block, re.M):
            block = re.sub(r"^  selected:\s*\[\]\s*$", f"  selected:\n  - name: {group}\n    now: {now}", block, count=1, flags=re.M)
        else:
            return None
        blocks[i] = block
        return "".join(blocks)
    return None


# --------------------------------------------------------------------- commands


def split_list(value: str) -> List[str]:
    return [] if value.strip().lower() in ("", "none") else [v.strip() for v in value.split(",") if v.strip()]


def cmd_detect(args: argparse.Namespace) -> int:
    data_dir = resolve_data_dir(args.data_dir)
    profiles = load_profiles(data_dir)
    report: Dict[str, Any] = {"data_dir": str(data_dir), "current": profiles["current"], "profiles": []}
    for item in profiles["items"]:
        if item.get("type") in ("remote", "local") and item.get("file"):
            path = data_dir / "profiles" / item["file"]
            text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
            report["profiles"].append({"uid": item["uid"], "name": item["name"], "type": item["type"],
                                       "raylink": raylink_score(text) >= 3, "current": item["uid"] == profiles["current"]})
    try:
        target = pick_profile(data_dir, profiles, args.profile)
        spath = script_path(data_dir, target)
        stext = spath.read_text(encoding="utf-8")
        settings = managed_settings(stext)
        seq_hits = []
        for kind in ("proxies", "groups"):
            uid = target["option"].get(kind)
            f = data_dir / "profiles" / f"{uid}.yaml" if uid else None
            if f and f.is_file():
                t = f.read_text(encoding="utf-8")
                seq_hits += [f"{kind}: {n}" for n in (DEFAULTS["name"], DEFAULTS["exit_group"]) if group_defined(t, n)]
        report["target"] = {
            "uid": target["uid"], "name": target["name"], "current": target["current"],
            "script": spath.name, "script_state": script_state(stext),
            "carrier_present": group_defined(target["text"], args.carrier),
            "expose_present": {g: group_defined(target["text"], g) for g in split_list(args.expose)},
            "installed": None if not settings else {
                "endpoint": f"{settings['proxy']['type']}://{settings['proxy']['server']}:{settings['proxy']['port']}",
                "carrier": settings["proxy"].get("dialer-proxy"), "exit_group": settings.get("exitGroup")},
            "superseded_seq_definitions": seq_hits,
        }
    except SkillError as exc:
        report["target_error"] = str(exc)
    ctl = Controller(data_dir, args.socket, args.controller, args.secret)
    report["controller"] = f"{ctl.target[0]}:{ctl.target[1]}" if ctl.ok else None
    report["mixed_port"] = read_app_config(data_dir).get("mixed-port")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if "target" in report else 1


def cmd_apply(args: argparse.Namespace) -> int:
    data_dir = resolve_data_dir(args.data_dir)
    profiles = load_profiles(data_dir)
    target = pick_profile(data_dir, profiles, args.profile)
    spath = script_path(data_dir, target)
    current = spath.read_text(encoding="utf-8")
    expose = split_list(args.expose)
    if args.carrier in expose:
        raise SkillError("承载分组不能同时作为暴露分组，否则会形成代理环路")
    missing = [g for g in [args.carrier] + expose if not group_defined(target["text"], g)]
    if missing:
        raise SkillError(f"RayLink 配置里找不到分组: {', '.join(missing)}；用 --carrier / --expose 指定实际名称")
    cred = read_credentials(args)
    proxy = {"name": args.name, "type": cred["type"], "server": cred["host"], "port": cred["port"],
             "username": cred["username"], "password": cred["password"], "dialer-proxy": args.carrier}
    selections = split_list(args.select)
    unknown = [g for g in selections if g not in expose]
    if unknown:
        raise SkillError(f"--select 的分组必须也在 --expose 中: {', '.join(unknown)}")
    settings = {"proxy": proxy, "exitGroup": args.exit_group, "expose": expose, "prefer": selections}
    new_text, action = render_script(current, build_block(settings), args.wrap_existing)
    plan = {
        "profile": f"{target['uid']} ({target['name']})", "current_profile": target["current"],
        "script": f"profiles/{spath.name}", "action": action, "endpoint": masked(cred),
        "carrier": args.carrier, "exit_group": args.exit_group, "expose": expose,
        "select_after_reload": selections, "mode": "apply" if args.apply else "dry-run",
    }
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    if not args.apply:
        print("dry-run：未写入任何文件；确认后加 --apply")
        return 0
    syntax = node_check(new_text)
    if syntax:
        raise SkillError(f"生成的脚本未通过 node --check：{syntax}")
    bdir = backup(data_dir, [spath, data_dir / "profiles.yaml"],
                  {"profile": target["uid"], "script": spath.name, "action": action})
    write_private(spath, new_text)
    print(f"backup={bdir}")
    print(f"written=profiles/{spath.name}")
    if not target["current"]:
        print(f"该配置当前未激活：在 Clash Verge 订阅页切到 {target['name'] or target['uid']} 后生效，"
              f"再把 {', '.join(selections) or '目标分组'} 选为 {args.exit_group}")
        return 0
    if not args.restart:
        print(f"需要重启 Clash Verge 让脚本生效（macOS 可加 --restart 自动完成），"
              f"然后把 {', '.join(selections) or '目标分组'} 选为 {args.exit_group}")
        return 0

    def persist_selection() -> None:
        text = (data_dir / "profiles.yaml").read_text(encoding="utf-8")
        for group in selections:
            updated = set_selected(text, target["uid"], group, args.exit_group)
            if updated is None:
                print(f"warning: profiles.yaml 结构不符合预期，未持久化 {group} 的选择")
                continue
            text = updated
        (data_dir / "profiles.yaml").write_text(text, encoding="utf-8")

    ctl = restart_app(data_dir, args, persist_selection if selections else None, args.exit_group)
    for group in selections:
        ctl.request("PUT", f"/proxies/{group}", {"name": args.exit_group})
    print(f"reloaded=yes controller={ctl.target[0]}:{ctl.target[1]}")
    print(f"next: python3 {Path(__file__).name} verify")
    return 0


def fetch_via(port: str, url: str, timeout: float = 20) -> str:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler(
        {"http": f"http://127.0.0.1:{port}", "https": f"http://127.0.0.1:{port}"}))
    with opener.open(urllib.request.Request(url, headers={"User-Agent": "curl/8"}), timeout=timeout) as resp:
        return resp.read(4096).decode("utf-8", "replace")


def cmd_verify(args: argparse.Namespace) -> int:
    data_dir = resolve_data_dir(args.data_dir)
    profiles = load_profiles(data_dir)
    target = pick_profile(data_dir, profiles, args.profile)
    settings = managed_settings(script_path(data_dir, target).read_text(encoding="utf-8"))
    if not settings:
        raise SkillError("该配置还没有安装受管块；先运行 apply --apply")
    ctl = Controller(data_dir, args.socket, args.controller, args.secret)
    if not ctl.ok:
        raise SkillError(f"连不上 Clash 控制接口（尝试过 {', '.join(ctl.tried)}）；用 --socket 或 --controller 指定")
    isp, exit_group = settings["proxy"]["name"], settings["exitGroup"]
    expect = args.expect_ip or settings["proxy"]["server"]
    result: Dict[str, Any] = {"exit_group_loaded": bool(ctl.proxy(exit_group))}
    try:
        delay = ctl.request("GET", f"/proxies/{isp}/delay?url={urllib.parse.quote(TEST_URL, safe='')}&timeout=10000", timeout=20)
        result["chain_delay_ms"] = delay.get("delay")
    except SkillError as exc:
        result["chain_delay_ms"] = None
        result["chain_error"] = str(exc)[:160]
    result["selections"] = {g: (ctl.proxy(g) or {}).get("now") for g in settings.get("expose", [])}
    port = args.mixed_port or read_app_config(data_dir).get("mixed-port")
    if port:
        try:
            trace = fetch_via(port, args.trace_url)
            ip = next((line[3:] for line in trace.splitlines() if line.startswith("ip=")), trace.strip()[:45])
            result["trace_ip"] = ip
        except Exception as exc:
            result["trace_ip"] = None
            result["trace_error"] = str(exc)[:160]
    result["expected_ip"] = expect
    result["pass"] = bool(result["exit_group_loaded"] and result.get("chain_delay_ms")
                          and (result.get("trace_ip") == expect or args.skip_trace))
    if not result["pass"] and result.get("chain_delay_ms") and result.get("trace_ip") != expect:
        result["hint"] = f"链路可用但 {args.trace_url} 未走 {exit_group}；确认 AI 网站代理 已选 {exit_group}"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 2


def latest_backup(data_dir: Path) -> Path:
    found = sorted((data_dir / "backups").glob(f"{SKILL_ID}-*/manifest.json"))
    if not found:
        raise SkillError("没有找到本 Skill 的备份")
    return found[-1].parent


def cmd_rollback(args: argparse.Namespace) -> int:
    data_dir = resolve_data_dir(args.data_dir)
    bdir = Path(args.backup).expanduser() if args.backup else latest_backup(data_dir)
    manifest = json.loads((bdir / "manifest.json").read_text(encoding="utf-8"))
    print(json.dumps({"backup": str(bdir), "files": manifest["files"], "mode": "apply" if args.apply else "dry-run"},
                     ensure_ascii=False, indent=2))
    if not args.apply:
        print("dry-run：未恢复；确认后加 --apply")
        return 0

    def restore() -> None:
        for rel in manifest["files"]:
            shutil.copy2(bdir / rel, data_dir / rel)

    profiles = load_profiles(data_dir)
    if args.restart and profiles["current"] == manifest.get("profile"):
        restart_app(data_dir, args, restore, "GLOBAL")
        print("restored=yes reloaded=yes")
    else:
        restore()
        print("restored=yes；重启 Clash Verge 或重新激活该配置后生效")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    data_dir = resolve_data_dir(args.data_dir)
    profiles = load_profiles(data_dir)
    target = pick_profile(data_dir, profiles, args.profile)
    spath = script_path(data_dir, target)
    current = spath.read_text(encoding="utf-8")
    if script_state(current) != "managed":
        print("该配置没有受管块，无需移除")
        return 0
    new_text = remove_from_script(current)
    print(json.dumps({"profile": target["uid"], "script": spath.name, "mode": "apply" if args.apply else "dry-run"},
                     ensure_ascii=False, indent=2))
    if not args.apply:
        print("dry-run：未写入；确认后加 --apply")
        return 0
    bdir = backup(data_dir, [spath], {"profile": target["uid"], "script": spath.name, "action": "remove"})
    write_private(spath, new_text)
    print(f"backup={bdir}\nremoved=yes；重启 Clash Verge 或重新激活该配置后生效")
    return 0


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data-dir", help="Clash Verge Rev 数据目录（默认按平台推断，或 CLASH_VERGE_DATA_DIR）")
    common.add_argument("--profile", help="目标配置的 uid 或名称（默认自动识别 RayLink 订阅）")
    common.add_argument("--socket", help="mihomo 控制接口 Unix socket")
    common.add_argument("--controller", help="mihomo 控制接口 host:port（覆盖 socket）")
    common.add_argument("--secret", help="TCP 控制接口密钥（默认读 config.yaml）")
    common.add_argument("--carrier", default=DEFAULTS["carrier"], help="承载 IPRoyal 的 RayLink 加密分组")
    common.add_argument("--expose", default=DEFAULTS["expose"], help="放入出口分组的目标分组，逗号分隔")

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("detect", parents=[common], help="只读：识别 RayLink 配置与当前状态")

    p = sub.add_parser("apply", parents=[common], help="写入受管块（默认 dry-run）")
    p.add_argument("--proxy-env", default="IPROYAL_PROXY", help="存放 主机:端口:用户名:密码 的环境变量名")
    p.add_argument("--proxy-file", help="第一行为 主机:端口:用户名:密码 的文件")
    p.add_argument("--type", choices=["http", "socks5"], help="IPRoyal 协议（默认 http，端口 12323；socks5 默认 12324）")
    p.add_argument("--name", default=DEFAULTS["name"], help="代理节点名")
    p.add_argument("--exit-group", default=DEFAULTS["exit_group"], help="出口分组名")
    p.add_argument("--select", default=DEFAULTS["select"], help="重启后选为出口分组的分组，逗号分隔；none 表示不改")
    p.add_argument("--wrap-existing", action="store_true", help="脚本已有自定义 main 时自动包装")
    p.add_argument("--restart", action="store_true", help="macOS：写入后重启 Clash Verge 并设置选择")
    p.add_argument("--apply", action="store_true", help="真正写入")

    v = sub.add_parser("verify", parents=[common], help="验证链路延迟与 AI 网站出口 IP")
    v.add_argument("--mixed-port", help="Clash 混合端口（默认读 config.yaml）")
    v.add_argument("--expect-ip", help="期望出口 IP（默认取 IPRoyal 服务器地址）")
    v.add_argument("--trace-url", default=TRACE_URL, help="用于读取出口 IP 的 AI 网站地址")
    v.add_argument("--skip-trace", action="store_true", help="只验证链路延迟")

    r = sub.add_parser("rollback", parents=[common], help="恢复最近一次备份（默认 dry-run）")
    r.add_argument("--backup", help="指定备份目录")
    r.add_argument("--restart", action="store_true", help="macOS：恢复后重启 Clash Verge")
    r.add_argument("--apply", action="store_true", help="真正恢复")

    m = sub.add_parser("remove", parents=[common], help="移除受管块（默认 dry-run）")
    m.add_argument("--apply", action="store_true", help="真正移除")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {"detect": cmd_detect, "apply": cmd_apply, "verify": cmd_verify,
                "rollback": cmd_rollback, "remove": cmd_remove}
    try:
        return handlers[args.command](args)
    except SkillError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
