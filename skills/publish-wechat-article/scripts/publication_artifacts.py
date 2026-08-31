#!/usr/bin/env python3
"""Validate upstream article artifacts without performing remote writes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


COVER_COMPOSITION_SCHEMA = "lov-wechat-cover-composition/v1"


class ArtifactContractError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_cover_composition_receipt(receipt_path: Path, cover: Path) -> dict[str, Any]:
    receipt_path = receipt_path.expanduser().resolve()
    cover = cover.expanduser().resolve()
    if not receipt_path.is_file():
        raise ArtifactContractError(f"品牌封面合成收据不存在：{receipt_path}")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ArtifactContractError(f"品牌封面合成收据无法读取：{error}") from None
    if not isinstance(receipt, dict) or receipt.get("schema") != COVER_COMPOSITION_SCHEMA:
        raise ArtifactContractError(
            f"品牌封面合成收据 schema 必须为 {COVER_COMPOSITION_SCHEMA}。"
        )
    if receipt.get("publisherLogoPresent") is not True:
        raise ArtifactContractError("品牌封面合成收据未确认公众号 Logo 已叠加。")

    upload_value = receipt.get("shareCoverUpload")
    if not isinstance(upload_value, str) or not upload_value.strip():
        raise ArtifactContractError("品牌封面合成收据缺少 shareCoverUpload。")
    upload_path = Path(upload_value).expanduser().resolve()
    if not upload_path.is_file():
        raise ArtifactContractError(f"品牌封面上传件不存在：{upload_path}")
    if upload_path != cover:
        raise ArtifactContractError(
            f"--cover 必须使用合成收据中的 shareCoverUpload：{upload_path}"
        )

    wide = receipt.get("artifacts", {}).get("wide") if isinstance(receipt.get("artifacts"), dict) else None
    wide_jpg = wide.get("jpg") if isinstance(wide, dict) else None
    if not isinstance(wide_jpg, str) or Path(wide_jpg).expanduser().resolve() != cover:
        raise ArtifactContractError("品牌封面合成收据中的 artifacts.wide.jpg 与上传件不一致。")

    logo_value = receipt.get("logo")
    logo_sha256 = receipt.get("logoSha256")
    if not isinstance(logo_value, str) or not isinstance(logo_sha256, str):
        raise ArtifactContractError("品牌封面合成收据缺少 Logo 路径或 SHA-256。")
    logo_path = Path(logo_value).expanduser().resolve()
    if not logo_path.is_file() or sha256_file(logo_path) != logo_sha256:
        raise ArtifactContractError("品牌封面 Logo 文件或 SHA-256 与合成收据不一致。")

    return {
        "coverCompositionVerified": True,
        "coverCompositionReceipt": str(receipt_path),
        "coverCompositionSchema": COVER_COMPOSITION_SCHEMA,
        "coverArtifactSha256": sha256_file(cover),
        "coverLogoSha256": logo_sha256,
        "coverLogoVariant": receipt.get("logoVariant"),
    }
