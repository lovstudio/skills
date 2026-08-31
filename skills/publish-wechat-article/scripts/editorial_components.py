#!/usr/bin/env python3
"""Validate profile-driven editorial components in a canonical article source."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class EditorialComponentError(ValueError):
    """Raised when a declared editorial component is missing or invalid."""


def _normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as error:
        raise EditorialComponentError(f"出版组件时间格式无效：{value}") from error
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _heading_matches(content: str, title: str) -> list[re.Match[str]]:
    return list(
        re.finditer(
            rf"^[ \t]*(?P<marks>#{{1,6}})[ \t]+{re.escape(title)}[ \t]*$",
            content,
            re.MULTILINE,
        )
    )


def _section(content: str, title: str) -> tuple[str | None, int | None]:
    matches = _heading_matches(content, title)
    if not matches:
        return None, None
    match = matches[0]
    level = len(match.group("marks"))
    end = len(content)
    for candidate in re.finditer(r"^[ \t]*(?P<marks>#{1,6})[ \t]+.+$", content[match.end() :], re.MULTILINE):
        if len(candidate.group("marks")) <= level:
            end = match.end() + candidate.start()
            break
    return content[match.end() : end], match.start()


def _has_image_markup(content: str) -> bool:
    return bool(re.search(r"<img\b|!\[[^\]]*\]\([^\n)]+\)", content, re.IGNORECASE))


def _contains(content: str, expected: str) -> bool:
    return _normalized(expected) in _normalized(content)


def _asset_evidence(raw_path: object, profile_path: Path) -> dict[str, object] | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    expanded = Path(os.path.expandvars(os.path.expanduser(raw_path.strip())))
    if not expanded.is_absolute():
        expanded = profile_path.parent / expanded
    resolved = expanded.resolve()
    return {"path": str(resolved), "exists": resolved.is_file()}


def _campaign_is_active(campaign: dict[str, Any], now: datetime) -> bool:
    if not campaign.get("enabled", True):
        return False
    status = str(campaign.get("status", "open")).strip().lower()
    capacity = str(campaign.get("capacity_state", "available")).strip().lower()
    if status not in {"active", "open"}:
        return False
    if capacity in {"closed", "full", "paused", "sold_out"}:
        return False
    starts_at = _parse_time(campaign.get("starts_at"))
    ends_at = _parse_time(campaign.get("ends_at"))
    if starts_at and now < starts_at.astimezone(now.tzinfo):
        return False
    if ends_at and now > ends_at.astimezone(now.tzinfo):
        return False
    return True


def validate_editorial_components(
    source: Path,
    content: str,
    profile_path: Path,
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    """Return evidence or raise when active profile components are absent."""
    profile_path = profile_path.expanduser().resolve()
    if not profile_path.is_file():
        raise EditorialComponentError(f"品牌 Profile 不存在：{profile_path}")
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EditorialComponentError(f"品牌 Profile 无法读取：{error}") from error
    if not isinstance(profile, dict):
        raise EditorialComponentError("品牌 Profile 顶层必须是 JSON object。")

    blocks = profile.get("blocks", {})
    if not isinstance(blocks, dict):
        raise EditorialComponentError("品牌 Profile 的 blocks 必须是 object。")

    checked_at = now or datetime.now().astimezone()
    errors: list[str] = []
    endcap_evidence: dict[str, object] = {"required": False, "verified": True}
    endcap_position: int | None = None
    endcap = blocks.get("endcap")
    if isinstance(endcap, dict) and endcap.get("enabled", True):
        title = str(endcap.get("title", "")).strip()
        endcap_evidence = {"required": True, "title": title, "verified": False}
        if not title:
            errors.append("blocks.endcap.title 不能为空。")
            endcap_section = None
        else:
            matches = _heading_matches(content, title)
            if len(matches) != 1:
                errors.append(f"永久品牌尾注标题“{title}”必须且只能出现一次。")
            endcap_section, endcap_position = _section(content, title)
        if endcap_section is not None:
            for paragraph in endcap.get("paragraphs", []):
                if isinstance(paragraph, str) and paragraph.strip() and not _contains(endcap_section, paragraph):
                    errors.append(f"永久品牌尾注缺少已批准文案：{paragraph}")
            for link in endcap.get("links", []):
                if isinstance(link, dict):
                    url = str(link.get("url", "")).strip()
                    if url and url not in endcap_section:
                        errors.append(f"永久品牌尾注缺少链接：{url}")
            card = endcap.get("card")
            if isinstance(card, dict) and card.get("enabled", True):
                marker = str(card.get("marker") or card.get("alt") or "").strip()
                if card.get("required_image", True) and not _has_image_markup(endcap_section):
                    errors.append("永久品牌尾注缺少个人介绍卡片图片。")
                if marker and not _contains(endcap_section, marker):
                    errors.append(f"永久品牌尾注缺少个人卡片标识：{marker}")
                asset = _asset_evidence(card.get("asset"), profile_path)
                if asset and not asset["exists"]:
                    errors.append(f"个人卡片品牌资产不存在：{asset['path']}")
                endcap_evidence["card"] = {
                    "required": True,
                    "marker": marker or None,
                    "asset": asset,
                }
        endcap_evidence["verified"] = not any("永久品牌尾注" in item or "个人卡片" in item for item in errors)

    campaigns = blocks.get("campaigns", [])
    if campaigns is None:
        campaigns = []
    if not isinstance(campaigns, list):
        raise EditorialComponentError("品牌 Profile 的 blocks.campaigns 必须是 list。")

    active_campaigns: list[dict[str, object]] = []
    for index, campaign in enumerate(campaigns):
        if not isinstance(campaign, dict):
            errors.append(f"blocks.campaigns[{index}] 必须是 object。")
            continue
        if not _campaign_is_active(campaign, checked_at):
            continue
        campaign_id = str(campaign.get("id") or f"campaign-{index + 1}")
        title = str(campaign.get("title", "")).strip()
        evidence: dict[str, object] = {"id": campaign_id, "title": title, "verified": False}
        if not title:
            errors.append(f"活动 {campaign_id} 缺少 title。")
            active_campaigns.append(evidence)
            continue
        matches = _heading_matches(content, title)
        if len(matches) != 1:
            errors.append(f"开放活动标题“{title}”必须且只能出现一次。")
        campaign_section, campaign_position = _section(content, title)
        if campaign_section is not None:
            for expected in campaign.get("required_text", []):
                if isinstance(expected, str) and expected.strip() and not _contains(campaign_section, expected):
                    errors.append(f"开放活动“{title}”缺少必要信息：{expected}")
            if campaign.get("required_image", True) and not _has_image_markup(campaign_section):
                errors.append(f"开放活动“{title}”缺少招募海报。")
            if endcap_position is not None and campaign_position is not None and campaign_position > endcap_position:
                errors.append(f"开放活动“{title}”必须放在永久品牌尾注之前。")
        asset = _asset_evidence(campaign.get("asset"), profile_path)
        if asset and not asset["exists"]:
            errors.append(f"开放活动“{title}”的海报资产不存在：{asset['path']}")
        evidence.update({"asset": asset, "verified": not any(f"“{title}”" in item for item in errors)})
        active_campaigns.append(evidence)

    if errors:
        raise EditorialComponentError("；".join(errors))
    return {
        "publicationComponentsVerified": True,
        "brandProfile": str(profile_path),
        "checkedAt": checked_at.isoformat(),
        "endcap": endcap_evidence,
        "activeCampaigns": active_campaigns,
        "source": str(source.expanduser().resolve()),
    }
