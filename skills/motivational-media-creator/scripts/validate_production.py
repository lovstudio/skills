#!/usr/bin/env python3
"""Validate a motivational-video production package without third-party libraries."""
import argparse
import json
import math
import re
import sys
from pathlib import Path


CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U0002ebef]")


def load_json(path):
    def reject_constant(value):
        raise ValueError("non-finite JSON number: " + value)
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream, parse_constant=reject_constant)


def type_matches(value, kind):
    return {
        "object": lambda: isinstance(value, dict),
        "array": lambda: isinstance(value, list),
        "string": lambda: isinstance(value, str),
        "boolean": lambda: isinstance(value, bool),
        "integer": lambda: isinstance(value, int) and not isinstance(value, bool),
        "number": lambda: isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value),
        "null": lambda: value is None,
    }[kind]()


def schema_check(value, rule, root, path, errors):
    if "$ref" in rule:
        target = root
        for part in rule["$ref"][2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        schema_check(value, target, root, path, errors)
        return
    if "type" in rule and not type_matches(value, rule["type"]):
        errors.append(path + ": expected " + rule["type"])
        return
    if "const" in rule and value != rule["const"]:
        errors.append(path + ": must equal " + repr(rule["const"]))
    if "enum" in rule and value not in rule["enum"]:
        errors.append(path + ": value is outside allowed enum")
    if isinstance(value, dict):
        for field in rule.get("required", []):
            if field not in value:
                errors.append(path + "." + field + ": required field missing")
        properties = rule.get("properties", {})
        for key, item in value.items():
            if key in properties:
                schema_check(item, properties[key], root, path + "." + key, errors)
            elif rule.get("additionalProperties") is False:
                errors.append(path + "." + key + ": unexpected field")
    elif isinstance(value, list):
        if len(value) < rule.get("minItems", 0):
            errors.append(path + ": too few items")
        if "maxItems" in rule and len(value) > rule["maxItems"]:
            errors.append(path + ": too many items")
        if rule.get("uniqueItems") and len({json.dumps(x, sort_keys=True, ensure_ascii=False) for x in value}) != len(value):
            errors.append(path + ": duplicate items")
        for index, item in enumerate(value):
            schema_check(item, rule.get("items", {}), root, path + "[" + str(index) + "]", errors)
    elif isinstance(value, str):
        if len(value) < rule.get("minLength", 0) or ("minLength" in rule and not value.strip()):
            errors.append(path + ": string is empty or too short")
        if "maxLength" in rule and len(value) > rule["maxLength"]:
            errors.append(path + ": string too long")
        if "pattern" in rule and not re.search(rule["pattern"], value):
            errors.append(path + ": string pattern mismatch")
    elif type_matches(value, "number"):
        if "minimum" in rule and value < rule["minimum"]:
            errors.append(path + ": below minimum")
        if "maximum" in rule and value > rule["maximum"]:
            errors.append(path + ": above maximum")
        if "exclusiveMinimum" in rule and value <= rule["exclusiveMinimum"]:
            errors.append(path + ": must be greater than minimum")


def index_by_id(items, label, errors):
    indexed = {}
    for item in items:
        if item["id"] in indexed:
            errors.append(label + ": duplicate id " + item["id"])
        indexed[item["id"]] = item
    return indexed


def approximately(a, b):
    return abs(a - b) <= 0.000001


def semantic_check(data, errors, warnings):
    project = data["project"]
    duration, fps = project["duration_seconds"], project["fps"]
    ready = data["status"] == "ready"
    assets = index_by_id(data["assets"], "assets", errors)
    rights = index_by_id(data["rights_ledger"], "rights_ledger", errors)
    voices = index_by_id(data["narration"], "narration", errors)
    cues = index_by_id(data["audio_cues"], "audio_cues", errors)
    shots = index_by_id(data["timeline"], "timeline", errors)
    evidence = index_by_id(data["evidence_ledger"], "evidence_ledger", errors)
    hooks = index_by_id(data["hooks"], "hooks", errors)
    if len(data["hooks"]) != 3:
        errors.append("hooks: exactly three opening candidates required")
    index_by_id(data["formats"], "formats", errors)
    if {item["ratio"] for item in data["formats"]} != {"9:16", "16:9"}:
        errors.append("formats: both 9:16 and 16:9 are required")
    selected = hooks.get(data["selected_hook_id"])
    if selected is None:
        errors.append("selected_hook_id: unknown hook")
    elif data["narration"][0]["text"] != selected["text"]:
        errors.append("selected_hook_id: selected text must be the first narration segment")
    if data["narration_full_text"] != "\n".join(item["text"] for item in data["narration"]):
        errors.append("narration_full_text: must match ordered narration text exactly")
    if project["language"] == "zh-CN":
        for item in data["narration"]:
            if not CJK.search(item["text"]):
                errors.append("narration." + item["id"] + ": Chinese narration requires CJK text")
    if not approximately(duration * fps, round(duration * fps)):
        errors.append("project: duration must end on an integer frame")
    used_assets = set()
    used_voices, used_cues = set(), set()
    previous = 0.0
    for shot in data["timeline"]:
        label = "timeline." + shot["id"]
        if not approximately(shot["start_seconds"], previous):
            errors.append(label + ": gap or overlap; expected start " + str(previous))
        if shot["end_seconds"] <= shot["start_seconds"]:
            errors.append(label + ": end must follow start")
        if not approximately(shot["duration_seconds"], shot["end_seconds"] - shot["start_seconds"]):
            errors.append(label + ": duration disagrees with boundaries")
        if shot["start_frame"] != round(shot["start_seconds"] * fps) or shot["end_frame"] != round(shot["end_seconds"] * fps):
            errors.append(label + ": frame and second boundaries disagree")
        for seconds in (shot["start_seconds"], shot["end_seconds"]):
            if not approximately(seconds * fps, round(seconds * fps)):
                errors.append(label + ": boundary is not on an integer frame")
        previous = shot["end_seconds"]
        for asset_id in shot["asset_ids"]:
            used_assets.add(asset_id)
            if asset_id not in assets:
                errors.append(label + ": unknown asset " + asset_id)
        if not any(assets[asset_id]["kind"] in ("video", "image", "graphic") for asset_id in shot["asset_ids"] if asset_id in assets):
            errors.append(label + ": needs a visual asset")
        for field, lookup, used in (("narration_ids", voices, used_voices), ("audio_cue_ids", cues, used_cues)):
            for ref_id in shot[field]:
                used.add(ref_id)
                item = lookup.get(ref_id)
                if item is None:
                    errors.append(label + ": unknown " + field + " " + ref_id)
                elif item["start_seconds"] < shot["start_seconds"] or item["end_seconds"] > shot["end_seconds"]:
                    errors.append(label + ": referenced segment extends outside shot: " + ref_id)
                elif item["asset_id"] not in shot["asset_ids"]:
                    errors.append(label + ": referenced audio asset missing from asset_ids: " + item["asset_id"])
    if not approximately(previous, duration):
        errors.append("timeline: final end must equal project duration")
    voice_end = 0.0
    for voice in data["narration"]:
        if voice["start_seconds"] < voice_end:
            errors.append("narration." + voice["id"] + ": overlaps previous narration")
        voice_end = voice["end_seconds"]
    for label, items, used in (("narration", data["narration"], used_voices), ("audio_cues", data["audio_cues"], used_cues)):
        for item in items:
            if item["id"] not in used:
                errors.append(label + "." + item["id"] + ": not referenced by timeline")
            if not 0 <= item["start_seconds"] < item["end_seconds"] <= duration:
                errors.append(label + "." + item["id"] + ": invalid time bounds")
            asset = assets.get(item["asset_id"])
            if asset is None:
                errors.append(label + "." + item["id"] + ": unknown asset " + item["asset_id"])
            elif asset["kind"] != "audio":
                errors.append(label + "." + item["id"] + ": requires an audio asset")
    for item in data["assets"]:
        right = rights.get(item["rights_id"])
        if right is None:
            errors.append("assets." + item["id"] + ": unknown rights ledger id")
            continue
        if item["id"] not in used_assets:
            warnings.append("assets." + item["id"] + ": not used in timeline")
        if item["id"] in used_assets:
            if right["status"] == "restricted":
                errors.append("assets." + item["id"] + ": restricted material cannot be used")
            elif right["status"] != "cleared" or item["availability"] != "available":
                message = "assets." + item["id"] + ": not release-cleared/available (" + right["status"] + "/" + item["availability"] + ")"
                (errors if ready else warnings).append(message)
            if right["status"] == "cleared" and (not right["evidence"].strip() or right["evidence_status"] != "verified"):
                errors.append("rights_ledger." + right["id"] + ": cleared requires verified evidence")
            if ready and not item["locator"].strip():
                errors.append("assets." + item["id"] + ": ready requires a local or source locator")
    for item in data["claims"]:
        if item["evidence_id"] not in evidence:
            errors.append("claims: unknown evidence " + item["evidence_id"])
        elif item["kind"] == "fact" and evidence[item["evidence_id"]]["status"] != "verified":
            (errors if ready else warnings).append("claims: factual claim lacks verified evidence: " + item["text"])
    for item in data["emotion_curve"]:
        if item["shot_id"] not in shots:
            errors.append("emotion_curve: unknown shot " + item["shot_id"])
    if len({item["shot_id"] for item in data["emotion_curve"]}) != len(data["emotion_curve"]):
        errors.append("emotion_curve: duplicate shot_id")
    if set(item["shot_id"] for item in data["emotion_curve"]) != set(shots):
        errors.append("emotion_curve: every shot needs an emotional beat")
    if ready or data["execution_status"] == "rendered-reviewed":
        logo = assets.get("brand-logo")
        if logo is None or "brand-logo" not in used_assets:
            errors.append("brand_logo: branded final requires official brand-logo used in timeline")
        elif logo["origin"] != "brand-provided" or logo["kind"] not in ("image", "graphic"):
            errors.append("brand_logo: requires a brand-provided official image/graphic, not text or generated substitute")
    for item in data["qc"]:
        if item["status"] != "pass":
            (errors if ready else warnings).append("qc." + item["id"] + ": " + item["status"] + " — " + item["evidence"])
    if ready and data["rights_review_status"] != "approved":
        errors.append("rights_review_status: ready requires approved")
    if not ready:
        warnings.append("draft: this package is a production plan, not a rendered or publishable video")
    if ready and data["execution_status"] != "rendered-reviewed":
        errors.append("execution_status: ready requires rendered-reviewed")
    if data["ab_test"]["status"] == "not-run" and data["ab_test"]["observed_results"] != "尚未执行，无效果结论。":
        errors.append("ab_test: not-run must explicitly state no observed results")
    for version in data["formats"]:
        ratio_width, ratio_height = [int(part) for part in version["ratio"].split(":")]
        if version["width"] * ratio_height != version["height"] * ratio_width:
            errors.append("formats." + version["id"] + ": dimensions disagree with ratio")
        for field in ("safe_title", "safe_subtitle"):
            box = version[field]
            if box["left"] + box["width"] > 1 or box["top"] + box["height"] > 1:
                errors.append("formats." + version["id"] + "." + field + ": normalized box exceeds frame")
    return len(used_assets)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate production JSON, timeline and rights readiness. Draft warnings do not authorize publication.")
    parser.add_argument("production", type=Path, help="UTF-8 production JSON file")
    parser.add_argument("--schema", type=Path, default=Path(__file__).resolve().parent.parent / "assets" / "production.schema.json", help="explicit production schema (default: bundled schema)")
    args = parser.parse_args(argv)
    errors, warnings = [], []
    try:
        data, schema = load_json(args.production), load_json(args.schema)
        schema_check(data, schema, schema, "$", errors)
        count = semantic_check(data, errors, warnings) if not errors else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)], "warnings": [], "exit_status": 2}, ensure_ascii=False, indent=2))
        return 2
    code = 1 if errors else 0
    print(json.dumps({"valid": not errors, "status": data.get("status") if isinstance(data, dict) else None, "duration_seconds": data.get("project", {}).get("duration_seconds") if isinstance(data, dict) else None, "used_asset_count": count, "errors": errors, "warnings": warnings, "exit_status": code}, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
