#!/usr/bin/env python3
"""Validate a lov-algo-viz-creator step model JSON file.

Usage:
    python3 scripts/validate_viz.py model.json [--strict]

Errors (exit 1) break the build; warnings (exit 0) are quality hints.
With --strict, warnings are promoted to errors.

Also importable:
    from validate_viz import validate_model
    errors, warnings = validate_model(data)
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, List, Tuple

VALID_LAYOUTS = {"sequence", "network", "matrix", "bars"}
NODE_LAYOUTS = {"sequence", "network", "matrix"}


def _is_str(value: Any, *, nonempty: bool = True) -> bool:
    return isinstance(value, str) and (not nonempty or value.strip() != "")


def validate_model(data: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(data, dict):
        return ["model must be a JSON object"], []

    title = data.get("title")
    if not _is_str(title):
        errors.append("'title' must be a non-empty string")

    layout = data.get("layout")
    if layout not in VALID_LAYOUTS:
        errors.append(f"'layout' must be one of {sorted(VALID_LAYOUTS)}; got {layout!r}")

    code = data.get("code")
    if not isinstance(code, list) or not code:
        errors.append("'code' must be a non-empty array of strings")
        code = []
    else:
        for i, line in enumerate(code):
            if not _is_str(line):
                errors.append(f"'code[{i}]' must be a non-empty string")

    for key in ("insight", "inputLabel", "metricLabel"):
        value = data.get(key)
        if value is not None and not _is_str(value):
            errors.append(f"'{key}' must be a string")

    frames = data.get("frames")
    if not isinstance(frames, list) or not frames:
        errors.append("'frames' must be a non-empty array")
        frames = []

    # ---------- bars layout ----------
    if layout == "bars":
        value_lens = set()
        total_frames = len(frames)
        for i, frame in enumerate(frames):
            errs, warns = _check_bars_frame(frame, i, len(code), total_frames)
            errors.extend(errs)
            warnings.extend(warns)
            if isinstance(frame, dict) and isinstance(frame.get("values"), list):
                value_lens.add(len(frame["values"]))
        if len(value_lens) > 1:
            warnings.append(
                f"bars frame 'values' lengths differ across frames: {sorted(value_lens)}"
            )
        return errors, warnings

    # ---------- node layouts (sequence / network / matrix) ----------
    nodes = data.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        errors.append(f"layout {layout!r} requires a non-empty 'nodes' array")
        nodes = []

    node_ids: List[str] = []
    seen_ids = set()
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"nodes[{i}] must be an object")
            continue
        nid = node.get("id")
        if not _is_str(nid):
            errors.append(f"nodes[{i}].id must be a non-empty string")
            continue
        if nid in seen_ids:
            errors.append(f"nodes[{i}].id {nid!r} is duplicated")
        seen_ids.add(nid)
        node_ids.append(nid)
        if not _is_str(node.get("label")):
            errors.append(f"nodes[{i}].label must be a non-empty string")
        for axis in ("x", "y"):
            value = node.get(axis)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"nodes[{i}].{axis} must be a number")
            elif value < 0 or value > 100:
                errors.append(f"nodes[{i}].{axis} must be within 0-100; got {value}")

    node_id_set = set(node_ids)
    for i in range(len(node_ids)):
        for j in range(i + 1, len(node_ids)):
            a, b = nodes[i], nodes[j]
            if (
                isinstance(a, dict)
                and isinstance(b, dict)
                and isinstance(a.get("x"), (int, float))
                and isinstance(b.get("x"), (int, float))
                and isinstance(a.get("y"), (int, float))
                and isinstance(b.get("y"), (int, float))
            ):
                if abs(a["x"] - b["x"]) < 2.0 and abs(a["y"] - b["y"]) < 2.0:
                    warnings.append(
                        f"nodes {a.get('id')!r} and {b.get('id')!r} overlap at "
                        f"({a['x']}, {a['y']})"
                    )

    edges = data.get("edges", [])
    edge_ids: List[str] = []
    seen_edge_ids = set()
    if edges is not None and not isinstance(edges, list):
        errors.append("'edges' must be an array")
        edges = []
    for i, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"edges[{i}] must be an object")
            continue
        eid = edge.get("id")
        if not _is_str(eid):
            errors.append(f"edges[{i}].id must be a non-empty string")
            continue
        if eid in seen_edge_ids:
            errors.append(f"edges[{i}].id {eid!r} is duplicated")
        seen_edge_ids.add(eid)
        edge_ids.append(eid)
        for endpoint in ("from", "to"):
            if edge.get(endpoint) not in node_id_set:
                errors.append(f"edges[{i}].{endpoint} {edge.get(endpoint)!r} is not a node id")
        if "directed" in edge and not isinstance(edge.get("directed"), bool):
            errors.append(f"edges[{i}].directed must be a boolean")
    edge_id_set = set(edge_ids)

    total_frames = len(frames)
    for i, frame in enumerate(frames):
        errs, warns = _check_node_frame(frame, i, len(code), node_id_set, edge_id_set, total_frames)
        errors.extend(errs)
        warnings.extend(warns)

    # frame-count quality
    if 0 < len(frames) < 3:
        warnings.append(f"only {len(frames)} frames: too few for a meaningful demo")
    elif len(frames) > 60:
        warnings.append(f"{len(frames)} frames: long for a step-by-step demo; merge mechanical steps")

    return errors, warnings


def _check_bars_frame(
    frame: Any, index: int, code_len: int, total_frames: int
) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    if not isinstance(frame, dict):
        return [f"frames[{index}] must be an object"], []

    values = frame.get("values")
    if not isinstance(values, list) or not values:
        errors.append(f"frames[{index}].values must be a non-empty array for bars layout")
        values = []
    else:
        for j, v in enumerate(values):
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                errors.append(f"frames[{index}].values[{j}] must be a number")

    for field in ("active", "settled"):
        items = frame.get(field, [])
        if not isinstance(items, list):
            errors.append(f"frames[{index}].{field} must be an array")
            continue
        for j, item in enumerate(items):
            if not isinstance(item, int) or isinstance(item, bool) or item < 0 or item >= len(values):
                errors.append(f"frames[{index}].{field}[{j}] must be a valid bar index")

    if not _is_str(frame.get("note")):
        errors.append(f"frames[{index}].note must be a non-empty string")

    line = frame.get("codeLine")
    if not isinstance(line, int) or isinstance(line, bool) or not (0 <= line < code_len):
        errors.append(f"frames[{index}].codeLine must be an int in [0, {code_len - 1}]; got {line!r}")

    _quality_warnings(frame, index, total_frames, warnings)
    return errors, warnings


def _check_node_frame(
    frame: Any, index: int, code_len: int, node_ids: set, edge_ids: set, total_frames: int
) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    if not isinstance(frame, dict):
        return [f"frames[{index}] must be an object"], []

    for field in ("active", "settled"):
        items = frame.get(field, [])
        if not isinstance(items, list):
            errors.append(f"frames[{index}].{field} must be an array")
            continue
        for j, item in enumerate(items):
            if item not in node_ids:
                errors.append(f"frames[{index}].{field}[{j}] {item!r} is not a node id")

    values = frame.get("values")
    if values is not None:
        if not isinstance(values, dict):
            errors.append(f"frames[{index}].values must be an object of {{nodeId: text}}")
        else:
            for key in values:
                if key not in node_ids:
                    errors.append(f"frames[{index}].values key {key!r} is not a node id")

    for field in ("activeEdges", "settledEdges", "rejectedEdges"):
        items = frame.get(field)
        if items is None:
            continue
        if not isinstance(items, list):
            errors.append(f"frames[{index}].{field} must be an array")
            continue
        for j, item in enumerate(items):
            if item not in edge_ids:
                errors.append(f"frames[{index}].{field}[{j}] {item!r} is not an edge id")

    if not _is_str(frame.get("note")):
        errors.append(f"frames[{index}].note must be a non-empty string")

    line = frame.get("codeLine")
    if not isinstance(line, int) or isinstance(line, bool) or not (0 <= line < code_len):
        errors.append(f"frames[{index}].codeLine must be an int in [0, {code_len - 1}]; got {line!r}")

    _quality_warnings(frame, index, total_frames, warnings)
    return errors, warnings


def _quality_warnings(frame: Any, index: int, total_frames: int, warnings: List[str]) -> None:
    note = frame.get("note")
    if isinstance(note, str) and len(note) > 60:
        warnings.append(f"frames[{index}].note is {len(note)} chars; consider splitting")
    active = frame.get("active")
    # the final summary frame legitimately has no active element
    if isinstance(active, list) and not active and 0 < index < total_frames - 1:
        warnings.append(
            f"frames[{index}].active is empty (mid-demo) — ensure it is intentional"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", help="path to the step model JSON")
    parser.add_argument("--strict", action="store_true", help="promote warnings to errors")
    args = parser.parse_args()

    try:
        with open(args.model, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read {args.model}: {exc}", file=sys.stderr)
        return 2

    errors, warnings = validate_model(data)

    for warning in warnings:
        print(f"WARN  {warning}")
    for error in errors:
        print(f"ERROR {error}")

    print(f"result={len(errors)} errors, {len(warnings)} warnings")
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
