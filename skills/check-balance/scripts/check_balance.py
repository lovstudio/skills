#!/usr/bin/env python3
"""lov-check-balance — 统一查看 agent 账号的剩余用量与重置时间。

只读探测：不刷新 token、不写入凭据、不打印任何密钥。
每个 provider 独立探测，缺失即标记 unavailable，不影响其它 provider。
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VERSION = "0.1.0"
UA = "lov-check-balance/" + VERSION
SKILL_ID = "lov-check-balance"

PROFILE_CANDIDATES = (
    Path.home() / ".lovstudio" / "skills" / "profile.json",
    Path.home() / ".skill-publisher" / "skills" / "profile.json",
    Path.home() / ".config" / "agent-skills" / "profile.json",
)


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def keychain_secret(service: str, account: Optional[str] = None) -> Optional[str]:
    """从 macOS Keychain 读取一个 secret，其它平台返回 None。"""
    if platform.system() != "Darwin" or not shutil.which("security"):
        return None
    cmd = ["security", "find-generic-password", "-w", "-s", service]
    if account:
        cmd += ["-a", account]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    except Exception:
        return None
    value = (out.stdout or "").strip()
    return value or None


def http_get(url: str, headers: Dict[str, str], timeout: float = 20.0) -> Tuple[Optional[int], str]:
    req = urllib.request.Request(url, headers=dict(headers, **{"User-Agent": UA}))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")[:400]
    except Exception as exc:
        return None, "%s: %s" % (type(exc).__name__, exc)


def load_profile(path: Optional[str]) -> Dict[str, Any]:
    candidates = [Path(path)] if path else list(PROFILE_CANDIDATES)
    for candidate in candidates:
        try:
            if candidate.is_file():
                return json.loads(candidate.read_text(encoding="utf-8"))
        except Exception:
            continue
    return {}


def profile_lookup(profile: Dict[str, Any], dotted: str) -> Any:
    node: Any = profile
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def skill_setting(profile: Dict[str, Any], field: str) -> Any:
    """读取 skills.<skill_id> 下的 records 或 profile 字段。"""
    for scope in ("records", "profile"):
        value = profile_lookup(profile, "skills.%s.%s.%s" % (SKILL_ID, scope, field))
        if value not in (None, ""):
            return value
    return None


def resolve_timezone(name: str):
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo(name)
    except Exception:
        return datetime.timezone(datetime.timedelta(hours=8), name or "UTC+8")


def iso_local(epoch: float, tz) -> str:
    return datetime.datetime.fromtimestamp(epoch, tz).strftime("%Y-%m-%d %H:%M")


def humanize_delta(seconds: float) -> str:
    if seconds < 0:
        return "已过 " + humanize_delta(-seconds)
    if seconds < 3600:
        return "%.0f 分钟" % (seconds / 60)
    if seconds < 86400:
        return "%.1f 小时" % (seconds / 3600)
    return "%.2f 天" % (seconds / 86400)


def short(value: float) -> str:
    if abs(value) >= 1000:
        return "%.0f" % value
    if abs(value) >= 1:
        return "%.2f" % value
    return "%.4f" % value


def probe_codex(args, profile, tz) -> Dict[str, Any]:
    """ChatGPT / Codex 官方额度（Codex CLI 与 Codex 桌面版同源）。"""
    result: Dict[str, Any] = {
        "id": "codex",
        "label": "ChatGPT / Codex 官方额度",
        "status": "unavailable",
        "detail": "",
        "windows": [],
    }
    token = None
    account_id = None
    source = ""

    auth_path = Path(args.codex_auth_json) if args.codex_auth_json else Path.home() / ".codex" / "auth.json"
    if auth_path.is_file():
        try:
            data = json.loads(auth_path.read_text(encoding="utf-8"))
            tokens = data.get("tokens") or {}
            token = tokens.get("access_token")
            account_id = tokens.get("account_id")
            source = str(auth_path)
        except Exception:
            pass

    if not token and args.cc_switch_db:
        db_path = Path(args.cc_switch_db)
        if db_path.is_file():
            try:
                con = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
                row = con.execute(
                    "select settings_config from providers where app_type='codex' and id='default'"
                ).fetchone()
                if row and row[0]:
                    cfg = json.loads(row[0])
                    tokens = (cfg.get("auth") or {}).get("tokens") or {}
                    token = tokens.get("access_token")
                    account_id = tokens.get("account_id")
                    source = "%s (cc-switch codex/default)" % db_path
            except Exception as exc:
                result["detail"] = "读取 cc-switch 失败: %s" % exc

    if not token:
        result["detail"] = "未找到 ChatGPT 登录态（--codex-auth-json 或 --cc-switch-db）"
        return result

    status, body = http_get(
        "https://chatgpt.com/backend-api/wham/usage",
        {
            "Authorization": "Bearer " + token,
            "chatgpt-account-id": account_id or "",
            "Accept": "application/json",
        },
        timeout=args.timeout,
    )
    if status != 200:
        result["detail"] = "查询失败 HTTP %s" % status
        return result

    try:
        payload = json.loads(body)
    except Exception as exc:
        result["detail"] = "响应解析失败: %s" % exc
        return result

    now = time.time()
    result["status"] = "ok"
    result["detail"] = source
    result["account"] = payload.get("email")
    result["plan"] = payload.get("plan_type")

    rate = payload.get("rate_limit") or {}
    for name, window in (("primary", rate.get("primary_window")), ("secondary", rate.get("secondary_window"))):
        if not window:
            continue
        window_seconds = window.get("limit_window_seconds") or 0
        result["windows"].append(
            {
                "id": name,
                "label": "%.0f 天窗口" % (window_seconds / 86400) if window_seconds else name,
                "used_percent": window.get("used_percent"),
                "window_seconds": window_seconds,
                "reset_at": iso_local(window["reset_at"], tz) if window.get("reset_at") else None,
                "reset_in": humanize_delta(window["reset_at"] - now) if window.get("reset_at") else None,
                "limit_reached": rate.get("limit_reached"),
            }
        )
    result["limit_reached"] = rate.get("limit_reached")
    result["allowed"] = rate.get("allowed")

    extras = []
    for item in payload.get("additional_rate_limits") or []:
        window = (item.get("rate_limit") or {}).get("primary_window") or {}
        extras.append(
            {
                "label": item.get("limit_name"),
                "used_percent": window.get("used_percent"),
                "reset_at": iso_local(window["reset_at"], tz) if window.get("reset_at") else None,
            }
        )
    result["extra_pools"] = extras
    result["credits"] = payload.get("credits")
    return result


def probe_claude(args, profile, tz) -> Dict[str, Any]:
    """Claude 官方订阅额度（Claude Code OAuth 凭据）。"""
    result: Dict[str, Any] = {
        "id": "claude",
        "label": "Claude 官方订阅",
        "status": "unavailable",
        "detail": "",
        "windows": [],
    }
    raw = keychain_secret(args.claude_keychain_service, args.claude_keychain_account or None)
    if not raw and args.claude_credentials:
        cred_file = Path(args.claude_credentials)
        if cred_file.is_file():
            raw = cred_file.read_text(encoding="utf-8")
    if not raw:
        result["detail"] = "未找到 Claude 凭据（Keychain 服务 %s 或 --claude-credentials）" % args.claude_keychain_service
        return result

    try:
        oauth = json.loads(raw).get("claudeAiOauth") or {}
    except Exception as exc:
        result["detail"] = "凭据解析失败: %s" % exc
        return result

    token = oauth.get("accessToken")
    expires_at = oauth.get("expiresAt")
    result["plan"] = oauth.get("subscriptionType")
    if not token:
        result["detail"] = "凭据中缺少 accessToken"
        return result

    if expires_at:
        expires_epoch = float(expires_at) / 1000.0
        result["expires_at"] = iso_local(expires_epoch, tz)
        if expires_epoch <= time.time():
            result["status"] = "expired"
            result["detail"] = "登录态已于 %s 过期，重新登录后才能查询官方额度" % result["expires_at"]
            return result

    status, body = http_get(
        "https://api.anthropic.com/api/oauth/usage",
        {
            "Authorization": "Bearer " + token,
            "anthropic-beta": "oauth-2025-04-20",
            "Accept": "application/json",
        },
        timeout=args.timeout,
    )
    if status != 200:
        result["detail"] = "查询失败 HTTP %s" % status
        return result

    try:
        payload = json.loads(body)
    except Exception as exc:
        result["detail"] = "响应解析失败: %s" % exc
        return result

    result["status"] = "ok"
    result["detail"] = "api.anthropic.com/api/oauth/usage"
    for key, value in payload.items():
        if not isinstance(value, dict):
            continue
        utilization = value.get("utilization")
        if utilization is None:
            continue
        window: Dict[str, Any] = {
            "id": key,
            "label": key.replace("_", " "),
            "used_percent": utilization,
        }
        reset = value.get("resets_at")
        if reset:
            window["reset_at"] = reset
            try:
                parsed = datetime.datetime.fromisoformat(str(reset).replace("Z", "+00:00"))
                window["reset_in"] = humanize_delta(parsed.timestamp() - time.time())
            except Exception:
                pass
        result["windows"].append(window)
    return result


def probe_deepseek(args, profile, tz) -> Dict[str, Any]:
    """DeepSeek 预付费余额（按量计费，无固定重置窗口）。"""
    result: Dict[str, Any] = {"id": "deepseek", "label": "DeepSeek 余额", "status": "unavailable", "detail": ""}
    key = os.environ.get("DEEPSEEK_API_KEY") or keychain_secret(
        args.deepseek_keychain_service, args.deepseek_keychain_account or None
    )
    if not key:
        result["detail"] = "未找到 DeepSeek key（环境变量 DEEPSEEK_API_KEY 或 Keychain 服务 %s）" % args.deepseek_keychain_service
        return result

    status, body = http_get(
        "https://api.deepseek.com/user/balance",
        {"Authorization": "Bearer " + key, "Accept": "application/json"},
        timeout=args.timeout,
    )
    if status != 200:
        result["detail"] = "查询失败 HTTP %s" % status
        return result

    try:
        payload = json.loads(body)
    except Exception as exc:
        result["detail"] = "响应解析失败: %s" % exc
        return result

    result["status"] = "ok"
    result["detail"] = "api.deepseek.com/user/balance"
    result["available"] = payload.get("is_available")
    result["balances"] = [
        {
            "currency": item.get("currency"),
            "total": float(item.get("total_balance") or 0),
            "granted": item.get("granted_balance"),
            "topped_up": item.get("topped_up_balance"),
        }
        for item in payload.get("balance_infos") or []
    ]
    result["resets"] = "按量扣费，无固定重置窗口（充值即续）"
    return result


def probe_openrouter(args, profile, tz) -> Dict[str, Any]:
    """OpenRouter /api/v1/key：额度、剩余与 limit_reset。"""
    result: Dict[str, Any] = {"id": "openrouter", "label": "OpenRouter 额度", "status": "unavailable", "detail": ""}
    key = os.environ.get("OPENROUTER_API_KEY") or keychain_secret(
        args.openrouter_keychain_service, args.openrouter_keychain_account or None
    )
    if not key:
        result["detail"] = "未找到 OpenRouter key（环境变量 OPENROUTER_API_KEY 或 Keychain 服务 %s）" % args.openrouter_keychain_service
        return result

    status, body = http_get(
        "https://openrouter.ai/api/v1/key",
        {"Authorization": "Bearer " + key, "Accept": "application/json"},
        timeout=args.timeout,
    )
    if status != 200:
        result["detail"] = "查询失败 HTTP %s" % status
        return result

    try:
        data = json.loads(body).get("data") or {}
    except Exception as exc:
        result["detail"] = "响应解析失败: %s" % exc
        return result

    result["status"] = "ok"
    result["detail"] = "openrouter.ai/api/v1/key"
    result["usage_usd"] = data.get("usage")
    result["limit_usd"] = data.get("limit")
    result["remaining_usd"] = data.get("limit_remaining")
    result["limit_reset"] = data.get("limit_reset") or "未设置重置周期"
    result["label_name"] = data.get("label")
    return result


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        return []
    return records


def probe_gateway(args, profile, tz) -> Dict[str, Any]:
    """本地 LiteLLM 网关消费：按天聚合 cost 与 tokens。"""
    result: Dict[str, Any] = {"id": "gateway", "label": "本地网关消费", "status": "unavailable", "detail": "", "days": []}
    log_path = args.gateway_log or os.environ.get("LITELLM_REQUEST_LOG") or skill_setting(profile, "gateway_log")
    if not log_path:
        result["detail"] = "未提供网关日志路径（--gateway-log、LITELLM_REQUEST_LOG 或 profile records.gateway_log）"
        return result

    path = Path(str(log_path)).expanduser()
    if not path.is_file():
        result["detail"] = "日志不存在: %s" % path
        return result

    records = _read_jsonl(path)
    if not records:
        result["detail"] = "日志为空或不是 JSONL: %s" % path
        return result

    days: Dict[str, Dict[str, float]] = {}
    for record in records:
        stamp = str(record.get("start_time") or record.get("logged_at") or "")[:10]
        if not stamp:
            continue
        entry = days.setdefault(stamp, {"requests": 0, "cost": 0.0, "input": 0, "output": 0, "cached": 0})
        entry["requests"] += 1
        entry["cost"] += float(record.get("cost") or 0)
        usage = record.get("usage") or {}
        entry["input"] += float(usage.get("input_tokens") or 0)
        entry["output"] += float(usage.get("output_tokens") or 0)
        entry["cached"] += float((usage.get("input_tokens_details") or {}).get("cached_tokens") or 0)

    today = datetime.datetime.now(tz).strftime("%Y-%m-%d")
    result["status"] = "ok"
    result["detail"] = str(path)
    result["days"] = [
        {
            "date": day,
            "requests": int(value["requests"]),
            "cost_usd": round(value["cost"], 4),
            "input_tokens": int(value["input"]),
            "output_tokens": int(value["output"]),
            "cached_tokens": int(value["cached"]),
        }
        for day, value in sorted(days.items())
    ]
    result["today"] = next((item for item in result["days"] if item["date"] == today), None)
    result["total_cost_usd"] = round(sum(item["cost_usd"] for item in result["days"]), 4)
    return result


def probe_cc_switch(args, profile, tz) -> Dict[str, Any]:
    """cc-switch 本地代理：各 app 用量汇总与已配置的日/月限额。"""
    db_path = Path(args.cc_switch_db) if args.cc_switch_db else None
    if not db_path or not db_path.is_file():
        return {
            "id": "cc-switch",
            "label": "cc-switch 代理与限额",
            "status": "unavailable",
            "detail": "未找到 cc-switch 数据库（--cc-switch-db）",
            "entries": [],
            "limits": [],
        }

    result: Dict[str, Any] = {
        "id": "cc-switch",
        "label": "cc-switch 代理与限额",
        "status": "ok",
        "detail": str(db_path),
        "entries": [],
        "limits": [],
    }
    try:
        con = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
        for app, provider, count, cost, last in con.execute(
            """select app_type, provider_id, count(*), round(sum(cast(total_cost_usd as real)),4),
                      datetime(max(created_at),'unixepoch','+8 hours')
                 from proxy_request_logs group by app_type, provider_id order by 3 desc"""
        ):
            result["entries"].append(
                {"app_type": app, "provider_id": provider, "requests": count, "cost_usd": cost, "last_at": last}
            )
        for app, name, daily, monthly in con.execute(
            "select app_type, name, limit_daily_usd, limit_monthly_usd from providers where is_current=1"
        ):
            result["limits"].append(
                {
                    "app_type": app,
                    "provider": name,
                    "limit_daily_usd": daily,
                    "limit_monthly_usd": monthly,
                    "reset": "每日 00:00" if daily else ("每月 1 日" if monthly else "未设置限额"),
                }
            )
    except Exception as exc:
        result["status"] = "unavailable"
        result["detail"] = "查询失败: %s" % exc
    return result


def measure_burn(args, probes_before: List[Dict[str, Any]], tz) -> Optional[Dict[str, Any]]:
    """二次采样余额与网关消费，估算真实消耗速率与可用时长。"""
    if args.watch <= 0:
        return None
    log("采样中：等待 %s 秒以估算消耗速率…" % args.watch)
    time.sleep(args.watch)

    after_deepseek = probe_deepseek(args, {}, tz)
    after_gateway = probe_gateway(args, {}, tz)
    before_deepseek = next((p for p in probes_before if p["id"] == "deepseek"), {})
    before_gateway = next((p for p in probes_before if p["id"] == "gateway"), {})

    def balance_of(probe: Dict[str, Any]) -> Optional[float]:
        balances = probe.get("balances") or []
        for item in balances:
            if item.get("currency") == "CNY":
                return float(item.get("total"))
        return float(balances[0]["total"]) if balances else None

    burn: Dict[str, Any] = {"window_seconds": args.watch}
    start_balance, end_balance = balance_of(before_deepseek), balance_of(after_deepseek)
    start_cost, end_cost = before_gateway.get("total_cost_usd"), after_gateway.get("total_cost_usd")
    if start_balance is not None and end_balance is not None:
        spend_cny = start_balance - end_balance
        burn["spend_cny"] = round(spend_cny, 4)
        burn["cny_per_hour"] = round(spend_cny / args.watch * 3600, 3)
        if end_balance > 0 and burn["cny_per_hour"]:
            burn["runway_hours"] = round(end_balance / burn["cny_per_hour"], 1)
            burn["runway_days"] = round(burn["runway_hours"] / 24, 2)
    if start_cost is not None and end_cost is not None:
        spend_usd = end_cost - start_cost
        burn["gateway_spend_usd"] = round(spend_usd, 5)
        burn["gateway_usd_per_hour"] = round(spend_usd / args.watch * 3600, 4)
        if burn.get("spend_cny") and spend_usd > 0:
            burn["implied_fx_cny_per_usd"] = round(burn["spend_cny"] / spend_usd, 2)
            # 余额按批次结算，短窗口的汇率不可作为结论。
            burn["fx_reliable"] = args.watch >= 120

    # 余额按 ¥0.01 步进批量结算，短窗口可能为 0；此时用网关计价回退估算。
    if not burn.get("cny_per_hour") and burn.get("gateway_usd_per_hour"):
        estimated = burn["gateway_usd_per_hour"] * args.usd_cny
        burn["estimated_cny_per_hour"] = round(estimated, 3)
        if end_balance and estimated > 0:
            burn["estimated_runway_hours"] = round(end_balance / estimated, 1)
            burn["estimated_runway_days"] = round(burn["estimated_runway_hours"] / 24, 2)
        burn["estimate_basis"] = "网关计价 × %.2f ¥/USD；余额步进 ¥0.01，短窗口可能不变化" % args.usd_cny
    return burn


def render_text(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("Agent 账号额度体检 · %s" % payload["generated_at"])
    lines.append("时区: %s" % payload["timezone"])
    lines.append("")

    for probe in payload["providers"]:
        status_label = {"ok": "正常", "expired": "登录态过期", "unavailable": "不可用"}.get(probe["status"], probe["status"])
        lines.append("【%s】%s" % (probe["label"], status_label))
        if probe.get("account"):
            suffix = "  计划: %s" % probe["plan"] if probe.get("plan") else ""
            lines.append("  账号: %s%s" % (probe["account"], suffix))
        elif probe.get("plan"):
            lines.append("  计划: %s" % probe["plan"])
        if probe.get("expires_at"):
            lines.append("  凭据到期: %s" % probe["expires_at"])
        for window in probe.get("windows") or []:
            bits = ["%s 已用 %s%%" % (window.get("label", window.get("id")), window.get("used_percent"))]
            if window.get("reset_at"):
                bits.append("重置 %s（%s 后）" % (window["reset_at"], window.get("reset_in", "?")))
            if window.get("limit_reached") is not None:
                bits.append("limit_reached=%s" % window["limit_reached"])
            lines.append("  " + " | ".join(bits))
        for pool in probe.get("extra_pools") or []:
            tail = "  重置 %s" % pool["reset_at"] if pool.get("reset_at") else ""
            lines.append("  附加池 %s: 已用 %s%%%s" % (pool.get("label"), pool.get("used_percent"), tail))
        for item in probe.get("balances") or []:
            lines.append(
                "  余额: %s %s（充值 %s / 赠送 %s）"
                % (item.get("currency"), short(item.get("total", 0)), item.get("topped_up"), item.get("granted"))
            )
        if probe.get("usage_usd") is not None or probe.get("remaining_usd") is not None:
            lines.append(
                "  已用 $%s / 限额 %s / 剩余 %s / 重置策略 %s"
                % (probe.get("usage_usd"), probe.get("limit_usd"), probe.get("remaining_usd"), probe.get("limit_reset"))
            )
        if probe.get("resets"):
            lines.append("  重置: %s" % probe["resets"])
        for day in probe.get("days") or []:
            lines.append(
                "  %s: %s 次 · $%s · in %.1fM / out %.2fM（缓存 %.1fM）"
                % (day["date"], day["requests"], day["cost_usd"],
                   day["input_tokens"] / 1e6, day["output_tokens"] / 1e6, day["cached_tokens"] / 1e6)
            )
        if probe.get("days") and probe.get("total_cost_usd") is not None:
            lines.append("  网关累计: $%s" % probe["total_cost_usd"])
        for entry in probe.get("entries") or []:
            lines.append(
                "  代理 %s/%s: %s 次 · $%s · 最近 %s"
                % (entry["app_type"], entry["provider_id"][:18], entry["requests"], entry["cost_usd"], entry["last_at"])
            )
        for limit in probe.get("limits") or []:
            lines.append(
                "  限额 %s/%s: 日 %s / 月 %s（%s）"
                % (limit["app_type"], limit["provider"], limit["limit_daily_usd"], limit["limit_monthly_usd"], limit["reset"])
            )
        if probe["status"] != "ok" and probe.get("detail"):
            lines.append("  说明: %s" % probe["detail"])
        lines.append("")

    burn = payload.get("burn_rate")
    if burn:
        lines.append("【消耗速率】%s 秒采样" % burn["window_seconds"])
        if burn.get("spend_cny") is not None:
            lines.append("  余额变化 -¥%s → 约 ¥%s/小时" % (short(burn["spend_cny"]), burn.get("cny_per_hour")))
        if burn.get("runway_days"):
            lines.append("  按此速率余额可用约 %s 天" % burn["runway_days"])
        if burn.get("implied_fx_cny_per_usd"):
            suffix = "" if burn.get("fx_reliable") else "（窗口 <120 秒，批量结算下不可靠）"
            lines.append("  隐含汇率 ¥%s/USD%s" % (burn["implied_fx_cny_per_usd"], suffix))
        if burn.get("estimated_cny_per_hour"):
            lines.append("  网关回退估算: 约 ¥%s/小时" % burn["estimated_cny_per_hour"])
            if burn.get("estimated_runway_days"):
                lines.append("  按此估算余额可用约 %s 天" % burn["estimated_runway_days"])
            if burn.get("estimate_basis"):
                lines.append("  说明: %s" % burn["estimate_basis"])
        lines.append("")

    if payload.get("alerts"):
        lines.append("【提醒】")
        for alert in payload["alerts"]:
            lines.append("  - %s" % alert)
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="查看 agent 账号剩余用量与重置时间（只读）")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    parser.add_argument("--only", action="append", default=[], help="只探测指定 provider，可重复")
    parser.add_argument("--watch", type=int, default=0, metavar="SECONDS", help="二次采样以估算消耗速率（建议 >=60 秒）")
    parser.add_argument("--usd-cny", type=float, default=7.1, help="回退估算使用的汇率（默认 7.1）")
    parser.add_argument("--timezone", default="", help="展示时区，默认取 profile 或 Asia/Shanghai")
    parser.add_argument("--timeout", type=float, default=20.0, help="单次 HTTP 超时秒数")
    parser.add_argument("--min-balance-cny", type=float, default=None, help="余额低于该值时告警")
    parser.add_argument("--strict", action="store_true", help="有 provider 不可用时返回非零退出码")
    parser.add_argument("--profile", default="", help="共享 profile JSON 路径")
    parser.add_argument("--gateway-log", default="", help="LiteLLM 请求日志（requests-brief.jsonl）")
    parser.add_argument("--cc-switch-db", default=str(Path.home() / ".cc-switch" / "cc-switch.db"))
    parser.add_argument("--codex-auth-json", default="")
    parser.add_argument("--claude-keychain-service", default="Claude Code-credentials")
    parser.add_argument("--claude-keychain-account", default="")
    parser.add_argument("--claude-credentials", default=str(Path.home() / ".claude" / ".credentials.json"))
    parser.add_argument("--deepseek-keychain-service", default="codex-litellm-deepseek")
    parser.add_argument("--deepseek-keychain-account", default="deepseek")
    parser.add_argument("--openrouter-keychain-service", default="openrouter-api-key")
    parser.add_argument("--openrouter-keychain-account", default="")
    parser.add_argument("--version", action="version", version="lov-check-balance " + VERSION)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    profile = load_profile(args.profile or None)
    tz_name = args.timezone or profile_lookup(profile, "user.timezone") or "Asia/Shanghai"
    tz = resolve_timezone(tz_name)

    probes = [
        probe_codex(args, profile, tz),
        probe_claude(args, profile, tz),
        probe_deepseek(args, profile, tz),
        probe_openrouter(args, profile, tz),
        probe_gateway(args, profile, tz),
        probe_cc_switch(args, profile, tz),
    ]
    if args.only:
        wanted = set(args.only)
        probes = [probe for probe in probes if probe["id"] in wanted]

    burn = measure_burn(args, probes, tz)

    alerts: List[str] = []
    threshold = args.min_balance_cny
    if threshold is None:
        value = skill_setting(profile, "min_balance_cny")
        threshold = float(value) if value not in (None, "") else None
    for probe in probes:
        if probe["id"] == "codex":
            for window in probe.get("windows") or []:
                if window.get("used_percent") is not None and float(window["used_percent"]) >= 100:
                    alerts.append("%s 已用满（%s 重置）" % (window.get("label"), window.get("reset_at")))
        if probe["id"] == "deepseek" and threshold is not None:
            for item in probe.get("balances") or []:
                if item.get("currency") == "CNY" and item.get("total", 0) < threshold:
                    alerts.append("DeepSeek 余额 ¥%s 低于阈值 ¥%s" % (short(item["total"]), threshold))
        if probe["id"] == "cc-switch":
            for limit in probe.get("limits") or []:
                if not limit.get("limit_daily_usd") and not limit.get("limit_monthly_usd"):
                    alerts.append("%s/%s 未设置日/月限额" % (limit["app_type"], limit["provider"]))

    payload = {
        "schema": "lov-check-balance/v1",
        "version": VERSION,
        "generated_at": datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": tz_name,
        "providers": probes,
        "alerts": alerts,
    }
    if burn:
        payload["burn_rate"] = burn

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(render_text(payload))

    ok = [probe["id"] for probe in probes if probe["status"] == "ok"]
    unavailable = [probe["id"] for probe in probes if probe["status"] == "unavailable"]
    if not ok:
        return 2
    if args.strict and unavailable:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
