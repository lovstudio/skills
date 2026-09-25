#!/usr/bin/env python3
"""Validate the WeChat-specific projection of a user-owned Skill Profile."""

from __future__ import annotations

import argparse
import copy
import json
import re
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
EXTENSION_KEY = "lov-wechat-article-branding-skill"


def load_profile(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Profile root must be an object")
    return data


def valid_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def text_value(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for locale in ("zh-CN", "en-US", "zh", "en"):
            if isinstance(value.get(locale), str) and value[locale].strip():
                return value[locale].strip()
        for item in value.values():
            if isinstance(item, str) and item.strip():
                return item.strip()
    return ""


def nonempty(value: Any) -> bool:
    return bool(text_value(value))


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if isinstance(result.get(key), dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def normalized(profile: dict[str, Any]) -> dict[str, Any]:
    extension = profile.get("extensions", {}).get(EXTENSION_KEY, {})
    if not isinstance(extension, dict):
        extension = {}
    result = deep_merge(profile, extension)

    identity = profile.get("identity", {})
    if not isinstance(identity, dict):
        identity = {}
    publication = result.get("publication")
    if not isinstance(publication, dict):
        publication = {}
    publication.setdefault("name", identity.get("name"))
    logo = identity.get("logo")
    if isinstance(logo, dict):
        logo = logo.get("light") or logo.get("dark")
    publication.setdefault("logo", logo)
    publication.setdefault("logo_policy", "publisher_only")
    result["publication"] = publication

    brand = result.get("brand")
    if not isinstance(brand, dict):
        brand = {}
    brand.setdefault("name", identity.get("name"))
    brand.setdefault("public_facts", [])
    brand.setdefault("forbidden_context", [])
    result["brand"] = brand

    visual = result.get("visual")
    if not isinstance(visual, dict):
        visual = {}
    generic_colors = brand.get("colors", {})
    if isinstance(generic_colors, dict) and "primary_color" not in visual:
        visual["primary_color"] = generic_colors.get("primary")
    result["visual"] = visual
    result.setdefault("products", [])
    result.setdefault("blocks", {})
    return result


def validate(profile: dict[str, Any]) -> list[str]:
    profile = normalized(profile)
    errors: list[str] = []
    publication = profile.get("publication")
    if not isinstance(publication, dict):
        errors.append("publication must be an object")
        publication = {}
    if not nonempty(publication.get("name")):
        errors.append("publication.name is required")
    if not nonempty(publication.get("logo")):
        errors.append("publication.logo is required")
    if "cover_logo" in publication and not nonempty(publication.get("cover_logo")):
        errors.append("publication.cover_logo must be a non-empty asset path")
    if "cover_logo_variant" in publication and not nonempty(publication.get("cover_logo_variant")):
        errors.append("publication.cover_logo_variant must be a non-empty variant name")
    if publication.get("logo_policy") != "publisher_only":
        errors.append("publication.logo_policy must be publisher_only")

    brand = profile.get("brand")
    if not isinstance(brand, dict):
        errors.append("brand must be an object")
        brand = {}
    if "site" in brand and not valid_url(brand.get("site")):
        errors.append("brand.site must be an HTTP(S) URL")
    for key in ("public_facts", "forbidden_context"):
        values = brand.get(key, [])
        if not isinstance(values, list) or not all(nonempty(item) for item in values):
            errors.append(f"brand.{key} must be a list of non-empty strings")

    visual = profile.get("visual", {})
    if not isinstance(visual, dict):
        errors.append("visual must be an object")
        visual = {}
    color = visual.get("primary_color")
    if color is not None and (not isinstance(color, str) or not HEX_COLOR.fullmatch(color)):
        errors.append("visual.primary_color must use #RRGGBB")
    ratios = visual.get("cover_ratios", [])
    if not isinstance(ratios, list) or not all(nonempty(item) for item in ratios):
        errors.append("visual.cover_ratios must be a list of ratio strings")
    if "logo" in visual:
        errors.append("visual.logo is ambiguous; use publication.logo")

    products = profile.get("products", [])
    product_urls: set[str] = set()
    if not isinstance(products, list):
        errors.append("products must be a list")
    else:
        for index, product in enumerate(products):
            if not isinstance(product, dict):
                errors.append(f"products[{index}] must be an object")
                continue
            if not nonempty(product.get("name")):
                errors.append(f"products[{index}].name is required")
            if not nonempty(product.get("promise")):
                errors.append(f"products[{index}].promise is required")
            if not valid_url(product.get("url")):
                errors.append(f"products[{index}].url must be an HTTP(S) URL")
            else:
                product_urls.add(product["url"])

    blocks = profile.get("blocks", {})
    if not isinstance(blocks, dict):
        errors.append("blocks must be an object")
    else:
        endcap = blocks.get("endcap")
        if endcap is not None and not isinstance(endcap, (bool, dict)):
            errors.append("blocks.endcap must be a boolean or object")
        if isinstance(endcap, dict):
            enabled = endcap.get("enabled", True)
            if not isinstance(enabled, bool):
                errors.append("blocks.endcap.enabled must be a boolean")
            if endcap.get("mode", "stable") != "stable":
                errors.append("blocks.endcap.mode must be stable")
            if endcap.get("product_link_policy", "primary_only") != "primary_only":
                errors.append("blocks.endcap.product_link_policy must be primary_only")
            if enabled and not nonempty(endcap.get("title")):
                errors.append("blocks.endcap.title is required when enabled")
            paragraphs = endcap.get("paragraphs", [])
            if not isinstance(paragraphs, list) or not all(nonempty(item) for item in paragraphs):
                errors.append("blocks.endcap.paragraphs must be a list of non-empty strings")
            links = endcap.get("links", [])
            if not isinstance(links, list):
                errors.append("blocks.endcap.links must be a list")
            else:
                for index, link in enumerate(links):
                    if not isinstance(link, dict):
                        errors.append(f"blocks.endcap.links[{index}] must be an object")
                        continue
                    if not nonempty(link.get("label")):
                        errors.append(f"blocks.endcap.links[{index}].label is required")
                    if not valid_url(link.get("url")):
                        errors.append(f"blocks.endcap.links[{index}].url must be an HTTP(S) URL")
                    elif link["url"] in product_urls:
                        errors.append(
                            f"blocks.endcap.links[{index}].url duplicates a products[].url; "
                            "product links are resolved from products[].url"
                        )
    return errors


def self_test() -> int:
    profile = {
        "schema": "skill-profile/v1",
        "profile_id": "example-profile",
        "revision": 1,
        "identity": {
            "id": "example-publisher",
            "name": {"zh-CN": "示例发布主体"},
            "logo": "./assets/example-publisher-logo.svg",
        },
        "brand": {
            "site": "https://example.com",
            "public_facts": ["Builds useful software"],
            "forbidden_context": ["private note"],
        },
        "extensions": {
            EXTENSION_KEY: {
                "publication": {
                    "name": "Example Publisher",
                    "logo": "./assets/example-publisher-logo.svg",
                    "cover_logo": "./assets/example-publisher-cover-logo-white.png",
                    "cover_logo_variant": "white",
                    "logo_policy": "publisher_only",
                },
                "products": [
                    {"name": "Example Product", "promise": "A clear user result", "url": "https://example.com/product"}
                ],
                "blocks": {
                    "endcap": {
                        "enabled": True,
                        "mode": "stable",
                        "product_link_policy": "primary_only",
                        "title": "Create useful things",
                        "paragraphs": ["Approved reusable endcap copy"],
                        "links": [{"label": "Example Studio", "url": "https://example.com"}],
                    }
                },
            }
        },
    }
    if validate(profile):
        print("SELF-TEST FAILED: valid extension profile rejected")
        return 1
    legacy = copy.deepcopy(profile["extensions"][EXTENSION_KEY])
    legacy["brand"] = profile["brand"]
    if validate(legacy):
        print("SELF-TEST FAILED: legacy profile rejected")
        return 1
    invalid_logo = copy.deepcopy(profile)
    invalid_logo["identity"]["logo"] = ""
    invalid_logo["extensions"][EXTENSION_KEY]["publication"]["logo"] = ""
    if not validate(invalid_logo):
        print("SELF-TEST FAILED: missing Logo accepted")
        return 1
    invalid_endcap = copy.deepcopy(profile)
    invalid_endcap["extensions"][EXTENSION_KEY]["blocks"]["endcap"]["mode"] = "article-adaptive"
    if not validate(invalid_endcap):
        print("SELF-TEST FAILED: invalid endcap mode accepted")
        return 1
    duplicate = copy.deepcopy(profile)
    duplicate["extensions"][EXTENSION_KEY]["blocks"]["endcap"]["links"].append(
        {"label": "Example Product", "url": "https://example.com/product"}
    )
    if not validate(duplicate):
        print("SELF-TEST FAILED: duplicate product link accepted")
        return 1
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "profile.json"
        path.write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")
        if validate(load_profile(path)):
            print("SELF-TEST FAILED: JSON round trip")
            return 1
    print("SELF-TEST PASSED")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", nargs="?", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.profile is None:
        parser.error("profile JSON is required")
    try:
        errors = validate(load_profile(args.profile.expanduser()))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAILED: {exc}")
        return 1
    if errors:
        print(f"FAILED: {len(errors)} issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASSED: WeChat Profile projection is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
