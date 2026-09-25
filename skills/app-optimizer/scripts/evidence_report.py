#!/usr/bin/env python3
"""Validate cross-platform app evidence and render a read-only optimization report."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCHEMA = "app-runtime-evidence/v1"
LEGACY_SCHEMAS = {"electron-runtime-evidence/v1"}
REPORT_SCHEMA = "app-runtime-report/v1"
STAGES = {"before", "after", "context"}
EVIDENCE_KINDS = {"measurement", "code_fact", "inference", "acceptance"}
COMPARISON_QUALITIES = {"paired", "implementation_bound", "directional"}
TERMINAL_STATUSES = {
    "diagnosed",
    "implemented_not_runtime_verified",
    "partially_verified",
    "verified",
    "blocked",
}
GATE_STATUSES = {"passed", "failed", "blocked", "not_run"}
POLICIES = {"inventory_only", "orphan_only", "idle_resumable"}
OWNER_STATES = {"active", "archived", "missing", "unknown"}
ACTIVITY_STATES = {"working", "awaiting_input", "idle", "unknown"}
IDENTITY_STATES = {"stable", "changed", "unknown"}
ARTIFACT_STATES = {"complete", "missing", "malformed", "oversized", "unknown"}
RETENTION_STATES = {"eligible", "retain", "unknown"}
PRIORITIES = {"P0", "P1", "P2", "P3"}
FILESYSTEM_KINDS = {"worktree", "directory"}


class EvidenceError(ValueError):
    """Raised when the evidence document violates the portable contract."""


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise EvidenceError(f"{label} must be an array")
    return value


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"{label} must be a non-empty string")
    return value.strip()


def require_enum(value: Any, allowed: set[str], label: str) -> str:
    text = require_string(value, label)
    if text not in allowed:
        choices = ", ".join(sorted(allowed))
        raise EvidenceError(f"{label} must be one of: {choices}")
    return text


def require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise EvidenceError(f"{label} must be boolean")
    return value


def optional_bool(value: Any, label: str) -> bool | None:
    if value is None:
        return None
    return require_bool(value, label)


def require_count(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise EvidenceError(f"{label} must be a non-negative integer")
    return value


def normalize_string_list(raw: Any, label: str) -> list[str]:
    return [require_string(value, f"{label}[{index}]") for index, value in enumerate(require_list(raw, label))]


def normalize_provenance(
    raw: Any, kind: str, label: str, *, legacy: bool, source: str
) -> dict[str, Any]:
    if raw is None and legacy:
        return {"source_ref": source, "legacy_unstructured": True}
    provenance = require_object(raw, f"{label}.provenance")
    normalized: dict[str, Any] = {
        "source_ref": require_string(
            provenance.get("source_ref"), f"{label}.provenance.source_ref"
        )
    }
    for key in ("build_ref", "observed_at", "sample_window", "sampler", "workload_id"):
        value = provenance.get(key)
        if value is not None:
            normalized[key] = require_string(value, f"{label}.provenance.{key}")
    if kind == "measurement" and not any(
        key in normalized for key in ("observed_at", "sample_window")
    ):
        raise EvidenceError(
            f"{label}.provenance must include observed_at or sample_window for measurement"
        )
    if kind == "inference":
        derivation = require_object(provenance.get("derivation"), f"{label}.provenance.derivation")
        normalized["derivation"] = {
            "formula": require_string(
                derivation.get("formula"), f"{label}.provenance.derivation.formula"
            ),
            "inputs": require_object(
                derivation.get("inputs"), f"{label}.provenance.derivation.inputs"
            ),
            "assumptions": normalize_string_list(
                derivation.get("assumptions", []), f"{label}.provenance.derivation.assumptions"
            ),
        }
    if kind == "acceptance":
        acceptance = require_object(provenance.get("acceptance"), f"{label}.provenance.acceptance")
        normalized["acceptance"] = {
            "threshold": require_string(
                acceptance.get("threshold"), f"{label}.provenance.acceptance.threshold"
            ),
            "workload_contract": require_string(
                acceptance.get("workload_contract"),
                f"{label}.provenance.acceptance.workload_contract",
            ),
        }
    return normalized


def normalize_comparison(raw: Any, label: str) -> dict[str, Any] | None:
    if raw is None:
        return None
    comparison = require_object(raw, f"{label}.comparison")
    return {
        "quality": require_enum(
            comparison.get("quality"), COMPARISON_QUALITIES, f"{label}.comparison.quality"
        ),
        "note": require_string(comparison.get("note"), f"{label}.comparison.note"),
    }


def normalize_observations(raw: Any, *, legacy: bool) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for index, item in enumerate(require_list(raw, "observations")):
        source = require_object(item, f"observations[{index}]")
        label = f"observations[{index}]"
        kind = require_enum(source.get("kind"), EVIDENCE_KINDS, f"{label}.kind")
        source_label = require_string(source.get("source"), f"{label}.source")
        observation = {
            "id": require_string(source.get("id"), f"observations[{index}].id"),
            "stage": require_enum(source.get("stage"), STAGES, f"observations[{index}].stage"),
            "kind": kind,
            "value": source.get("value"),
            "unit": require_string(source.get("unit"), f"observations[{index}].unit"),
            "source": source_label,
            "note": require_string(source.get("note"), f"observations[{index}].note"),
            "provenance": normalize_provenance(
                source.get("provenance"), kind, label, legacy=legacy, source=source_label
            ),
        }
        comparison = normalize_comparison(source.get("comparison"), label)
        if comparison is not None:
            observation["comparison"] = comparison
        value = observation["value"]
        if value is None or isinstance(value, (dict, list)):
            raise EvidenceError(f"observations[{index}].value must be a scalar")
        if isinstance(value, float) and not math.isfinite(value):
            raise EvidenceError(f"observations[{index}].value must be finite")
        observations.append(observation)
    if not observations:
        raise EvidenceError("observations must include at least one evidence record")
    return observations


def evaluate_resource(source: dict[str, Any], index: int) -> dict[str, Any]:
    label = f"resources[{index}]"
    resource_id = require_string(source.get("id"), f"{label}.id")
    kind = require_string(source.get("kind"), f"{label}.kind")
    policy = require_enum(source.get("policy"), POLICIES, f"{label}.policy")
    owner_state = require_enum(source.get("owner_state"), OWNER_STATES, f"{label}.owner_state")
    activity_state = require_enum(
        source.get("activity_state"), ACTIVITY_STATES, f"{label}.activity_state"
    )
    resumable = optional_bool(source.get("resumable"), f"{label}.resumable")
    attachments = require_count(source.get("attachments"), f"{label}.attachments")
    registration_active = require_bool(
        source.get("registration_active"), f"{label}.registration_active"
    )
    operation_active = require_bool(source.get("operation_active"), f"{label}.operation_active")
    cwd_in_use = require_bool(source.get("cwd_in_use"), f"{label}.cwd_in_use")
    dirty = optional_bool(source.get("dirty"), f"{label}.dirty")
    identity_state = require_enum(
        source.get("identity_state"), IDENTITY_STATES, f"{label}.identity_state"
    )
    evidence_state = require_enum(
        source.get("evidence_state"), ARTIFACT_STATES, f"{label}.evidence_state"
    )
    retention_state = require_enum(
        source.get("retention_state"), RETENTION_STATES, f"{label}.retention_state"
    )

    reasons: list[str] = []
    if policy == "inventory_only":
        reasons.append("inventory_only_policy")
    if owner_state == "unknown":
        reasons.append("owner_unknown")
    if activity_state != "idle":
        reasons.append(f"activity_{activity_state}")
    if attachments > 0:
        reasons.append("attached_or_subscribed")
    if registration_active:
        reasons.append("registration_active")
    if operation_active:
        reasons.append("operation_active")
    if cwd_in_use:
        reasons.append("cwd_in_use")
    if identity_state != "stable":
        reasons.append(f"identity_{identity_state}")
    if evidence_state != "complete":
        reasons.append(f"evidence_{evidence_state}")
    if retention_state != "eligible":
        reasons.append(f"retention_{retention_state}")
    if kind in FILESYSTEM_KINDS and dirty is not False:
        reasons.append("dirty_unknown" if dirty is None else "dirty")
    elif dirty is True:
        reasons.append("dirty")

    if policy == "orphan_only" and owner_state not in {"missing", "archived"}:
        reasons.append("owner_not_reclaimable")
    if policy == "idle_resumable" and owner_state == "active" and resumable is not True:
        reasons.append("active_owner_not_resumable")

    verdict = "candidate" if not reasons else "protect"
    return {
        "id": resource_id,
        "kind": kind,
        "policy": policy,
        "owner_state": owner_state,
        "activity_state": activity_state,
        "verdict": verdict,
        "reasons": reasons or ["all_required_proofs_present"],
    }


def normalize_hypotheses(raw: Any, observation_ids: set[str]) -> list[dict[str, Any]]:
    hypotheses: list[dict[str, Any]] = []
    hypothesis_ids: set[str] = set()
    for index, item in enumerate(require_list(raw, "hypotheses")):
        source = require_object(item, f"hypotheses[{index}]")
        hypothesis_id = require_string(source.get("id"), f"hypotheses[{index}].id")
        if hypothesis_id in hypothesis_ids:
            raise EvidenceError(f"hypotheses[{index}].id must be unique")
        hypothesis_ids.add(hypothesis_id)
        supports = require_list(source.get("supports"), f"hypotheses[{index}].supports")
        normalized_supports = [
            require_string(value, f"hypotheses[{index}].supports") for value in supports
        ]
        missing = sorted(set(normalized_supports) - observation_ids)
        if missing:
            raise EvidenceError(
                f"hypotheses[{index}].supports references unknown observations: {', '.join(missing)}"
            )
        hypotheses.append(
            {
                "id": hypothesis_id,
                "statement": require_string(
                    source.get("statement"), f"hypotheses[{index}].statement"
                ),
                "supports": normalized_supports,
                "falsifier": require_string(
                    source.get("falsifier"), f"hypotheses[{index}].falsifier"
                ),
                "priority": require_enum(
                    source.get("priority"), PRIORITIES, f"hypotheses[{index}].priority"
                ),
            }
        )
    return hypotheses


def compute_deltas(
    observations: list[dict[str, Any]], *, legacy: bool
) -> tuple[list[dict[str, Any]], list[str]]:
    grouped: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: {"before": [], "after": []}
    )
    for item in observations:
        value = item["value"]
        if item["stage"] in {"before", "after"} and isinstance(value, (int, float)) and not isinstance(value, bool):
            grouped[(item["id"], item["unit"])][item["stage"]].append(item)

    deltas: list[dict[str, Any]] = []
    warnings: list[str] = []
    for (metric_id, unit), stages in sorted(grouped.items()):
        before_values = stages["before"]
        after_values = stages["after"]
        if not before_values or not after_values:
            continue
        if len(before_values) != 1 or len(after_values) != 1:
            warnings.append(
                f"{metric_id}: multiple before/after values are not aggregated; use distinct metric ids"
            )
            continue
        before_item = before_values[0]
        after_item = after_values[0]
        before = float(before_item["value"])
        after = float(after_item["value"])
        before_kind = before_item["kind"]
        after_kind = after_item["kind"]
        declared = after_item.get("comparison") or before_item.get("comparison")
        if declared is not None:
            declared_quality = declared["quality"]
            comparison_quality = {
                "paired": "paired_observation",
                "implementation_bound": "implementation_bound",
                "directional": "directional_evidence",
            }[declared_quality]
        elif not legacy:
            comparison_quality = "undeclared_comparison"
        elif "inference" in {before_kind, after_kind}:
            comparison_quality = "derived_vs_observed"
        elif before_kind == "code_fact" and after_kind == "code_fact":
            comparison_quality = "implementation_bound"
        elif before_kind == "measurement" and after_kind in {"measurement", "acceptance"}:
            comparison_quality = "paired_observation"
        else:
            comparison_quality = "mixed_evidence"
        is_exact_comparison = comparison_quality in {"paired_observation", "implementation_bound"}
        delta = after - before if is_exact_comparison else None
        percent = (
            None
            if not is_exact_comparison or before == 0
            else (after - before) / abs(before) * 100
        )
        if not is_exact_comparison:
            warnings.append(
                f"{metric_id}: comparison quality is {comparison_quality}; exact delta suppressed"
            )
        deltas.append(
            {
                "id": metric_id,
                "unit": unit,
                "before": before,
                "after": after,
                "delta": delta,
                "percent_change": percent,
                "comparison_quality": comparison_quality,
                "comparison_note": declared["note"] if declared is not None else None,
            }
        )
    return deltas, warnings


def normalize_verification_gates(raw: Any) -> list[dict[str, str]]:
    gates: list[dict[str, str]] = []
    for index, item in enumerate(require_list(raw, "verification_gates")):
        source = require_object(item, f"verification_gates[{index}]")
        gates.append(
            {
                "name": require_string(source.get("name"), f"verification_gates[{index}].name"),
                "status": require_enum(
                    source.get("status"), GATE_STATUSES, f"verification_gates[{index}].status"
                ),
                "source_ref": require_string(
                    source.get("source_ref"), f"verification_gates[{index}].source_ref"
                ),
                "note": require_string(source.get("note"), f"verification_gates[{index}].note"),
            }
        )
    return gates


def build_report(document: dict[str, Any]) -> dict[str, Any]:
    input_schema = document.get("schema")
    legacy = input_schema in LEGACY_SCHEMAS
    if input_schema != SCHEMA and not legacy:
        accepted = ", ".join([SCHEMA, *sorted(LEGACY_SCHEMAS)])
        raise EvidenceError(f"schema must be one of: {accepted}")
    title = require_string(document.get("title"), "title")
    scope = require_object(document.get("scope"), "scope")
    normalized_scope = {
        require_string(key, "scope key"): require_string(value, f"scope.{key}")
        for key, value in scope.items()
    }
    if not normalized_scope:
        raise EvidenceError("scope must include at least one runtime qualifier")
    if not legacy:
        for key in ("platform_family", "runtime", "workload"):
            if key not in normalized_scope:
                raise EvidenceError(f"scope.{key} is required for {SCHEMA}")
    status_value = document.get("status", "diagnosed")
    status = require_enum(status_value, TERMINAL_STATUSES, "status")
    observations = normalize_observations(document.get("observations"), legacy=legacy)
    observation_ids = {item["id"] for item in observations}
    resources = [
        evaluate_resource(require_object(item, f"resources[{index}]"), index)
        for index, item in enumerate(require_list(document.get("resources", []), "resources"))
    ]
    resource_ids = [item["id"] for item in resources]
    if len(set(resource_ids)) != len(resource_ids):
        raise EvidenceError("resources[].id values must be unique")
    hypotheses = normalize_hypotheses(document.get("hypotheses", []), observation_ids)
    deltas, warnings = compute_deltas(observations, legacy=legacy)
    if legacy:
        warnings.insert(
            0,
            f"legacy input schema {input_schema} was normalized; migrate to {SCHEMA} with structured provenance",
        )
    verification_gates = normalize_verification_gates(document.get("verification_gates", []))
    evidence_gaps = normalize_string_list(document.get("evidence_gaps", []), "evidence_gaps")
    evidence_counts = Counter(item["kind"] for item in observations)
    verdict_counts = Counter(item["verdict"] for item in resources)
    return {
        "schema": REPORT_SCHEMA,
        "input_schema": input_schema,
        "title": title,
        "status": status,
        "scope": normalized_scope,
        "summary": {
            "observations": len(observations),
            "evidence_by_kind": dict(sorted(evidence_counts.items())),
            "resources": len(resources),
            "resource_verdicts": dict(sorted(verdict_counts.items())),
            "comparable_deltas": sum(item["delta"] is not None for item in deltas),
            "directional_comparisons": sum(item["delta"] is None for item in deltas),
            "hypotheses": len(hypotheses),
        },
        "observations": observations,
        "deltas": deltas,
        "resources": resources,
        "hypotheses": sorted(hypotheses, key=lambda item: (item["priority"], item["id"])),
        "verification_gates": verification_gates,
        "evidence_gaps": evidence_gaps,
        "warnings": warnings,
        "safety": "read_only_plan; no process termination or file deletion performed",
    }


def display_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def markdown_table_cell(value: Any) -> str:
    return display_value(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['title']}",
        "",
        f"Verdict: `{report['status']}`",
        "",
        f"Safety: `{report['safety']}`",
        "",
    ]
    lines.extend(["## Scope", ""])
    for key, value in report["scope"].items():
        lines.append(f"- **{key}:** {value}")
    lines.extend(["", "## Evidence ledger", "", "| Stage | Kind | Metric | Value | Source |", "| --- | --- | --- | ---: | --- |"])
    for item in report["observations"]:
        lines.append(
            "| {stage} | {kind} | {id} | {value} {unit} | {source} — {note} |".format(
                **{key: markdown_table_cell(value) for key, value in item.items()}
            )
        )

    lines.extend(["", "## Before/after comparisons", ""])
    if report["deltas"]:
        lines.extend(
            [
                "| Metric | Before | After | Delta | Change | Evidence quality | Contract note |",
                "| --- | ---: | ---: | ---: | ---: | --- | --- |",
            ]
        )
        for item in report["deltas"]:
            delta = "n/a" if item["delta"] is None else display_value(item["delta"])
            percent = "n/a" if item["percent_change"] is None else f"{item['percent_change']:.1f}%"
            lines.append(
                f"| {item['id']} | {display_value(item['before'])} {item['unit']} | "
                f"{display_value(item['after'])} {item['unit']} | {delta} | "
                f"{percent} | {item['comparison_quality']} | "
                f"{markdown_table_cell(item['comparison_note'] or 'inferred from evidence kinds')} |"
            )
    else:
        lines.append("No exactly comparable numeric before/after pair was supplied.")

    lines.extend(["", "## Reclamation plan", ""])
    if report["resources"]:
        lines.extend(["| Resource | Kind | Policy | Verdict | Reasons |", "| --- | --- | --- | --- | --- |"])
        for item in report["resources"]:
            lines.append(
                f"| {item['id']} | {item['kind']} | {item['policy']} | **{item['verdict']}** | "
                f"{', '.join(item['reasons'])} |"
            )
    else:
        lines.append("No resource cleanup plan was supplied.")

    lines.extend(["", "## Ranked hypotheses", ""])
    if report["hypotheses"]:
        for item in report["hypotheses"]:
            lines.append(f"- **{item['priority']} · {item['id']}:** {item['statement']}")
            lines.append(f"  - Supports: {', '.join(item['supports'])}")
            lines.append(f"  - Falsifier: {item['falsifier']}")
    else:
        lines.append("No causal hypothesis was supplied.")

    lines.extend(["", "## Correctness and release gates", ""])
    if report["verification_gates"]:
        for item in report["verification_gates"]:
            lines.append(
                f"- **{item['status']} · {item['name']}:** {item['note']} "
                f"(`{item['source_ref']}`)"
            )
    else:
        lines.append("No correctness or release gate was supplied.")

    lines.extend(["", "## Evidence gaps", ""])
    if report["evidence_gaps"]:
        lines.extend(f"- {gap}" for gap in report["evidence_gaps"])
    else:
        lines.append("No material evidence gap was declared.")

    if report["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report["warnings"])
    lines.append("")
    return "\n".join(lines)


def write_output(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Evidence JSON")
    parser.add_argument("--json-output", type=Path, help="Normalized report JSON")
    parser.add_argument("--markdown-output", type=Path, help="Human-readable report Markdown")
    args = parser.parse_args()

    try:
        document = json.loads(args.input.read_text(encoding="utf-8"))
        report = build_report(require_object(document, "document"))
        json_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.json_output:
            write_output(args.json_output, json_text)
        if args.markdown_output:
            write_output(args.markdown_output, render_markdown(report))
        if not args.json_output and not args.markdown_output:
            sys.stdout.write(json_text)
    except (OSError, json.JSONDecodeError, EvidenceError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
