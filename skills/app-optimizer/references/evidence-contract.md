# App runtime evidence contract

The contract keeps a plausible performance story from becoming a false result. It is
platform-independent; platform adapters contribute measurements and lifecycle facts.

| Kind | Meaning | Minimum support |
| --- | --- | --- |
| `measurement` | Value observed from the actual runtime | source reference plus timestamp or sample window, unit, build and workload when available |
| `code_fact` | Behavior established from source/configuration | file/symbol/commit or equivalent immutable reference |
| `inference` | Derived count or causal interpretation that can still be wrong | source reference, explicit formula, inputs, assumptions and a falsifier through the hypothesis |
| `acceptance` | Post-change result evaluated against a threshold declared before measurement | threshold, frozen workload contract, actual-runtime provenance and result |

Tests, lint, typecheck and builds belong in `verification_gates`; they are not
`acceptance` observations unless the performance target itself is a test threshold.

## JSON input

`scripts/evidence_report.py` accepts `app-runtime-evidence/v1`. It also reads legacy
`electron-runtime-evidence/v1`, adds a migration warning and emits the new report schema.

```json
{
  "schema": "app-runtime-evidence/v1",
  "title": "Foreground list scroll",
  "status": "partially_verified",
  "scope": {
    "platform_family": "mobile",
    "runtime": "React Native on iOS",
    "workload": "release build, fixed dataset, 10 scripted scrolls"
  },
  "observations": [
    {
      "id": "slow-frame-rate",
      "stage": "before",
      "kind": "measurement",
      "value": 18.2,
      "unit": "percent",
      "source": "real-device frame trace",
      "note": "Ten runs after one warm-up.",
      "provenance": {
        "source_ref": "trace-before-001",
        "build_ref": "release commit abc123",
        "observed_at": "2026-08-10T10:00:00+08:00",
        "sample_window": "10 scripted scrolls",
        "sampler": "Instruments Core Animation",
        "workload_id": "list-scroll-v1"
      }
    },
    {
      "id": "slow-frame-rate",
      "stage": "after",
      "kind": "acceptance",
      "value": 4.1,
      "unit": "percent",
      "source": "real-device frame trace",
      "note": "Same device, build mode, data and script.",
      "provenance": {
        "source_ref": "trace-after-001",
        "build_ref": "release commit def456",
        "observed_at": "2026-08-10T11:00:00+08:00",
        "sample_window": "10 scripted scrolls",
        "sampler": "Instruments Core Animation",
        "workload_id": "list-scroll-v1",
        "acceptance": {
          "threshold": "slow frames <= 5%",
          "workload_contract": "list-scroll-v1 on the same device and OS"
        }
      },
      "comparison": {
        "quality": "paired",
        "note": "The frozen workload and sampler match."
      }
    }
  ],
  "resources": [],
  "hypotheses": [],
  "verification_gates": [
    {
      "name": "target repository tests",
      "status": "passed",
      "source_ref": "CI run 123",
      "note": "Correctness gate; not the frame-rate result."
    }
  ],
  "evidence_gaps": ["No field/RUM sample exists for this release."]
}
```

## Observation rules

- `id`, `stage`, `kind`, `value`, `unit`, `source`, `note` and `provenance` are required
  for new-schema observations.
- New-schema `scope` must identify `platform_family`, `runtime` and the reproducible
  `workload`; add host, build and adapter qualifiers when available.
- `stage` is `before`, `after`, or `context`.
- A measurement provenance must include `source_ref` and `observed_at` or
  `sample_window`. Add `build_ref`, `workload_id` and `sampler` whenever they exist.
- An inference provenance must add `derivation.formula`, an `inputs` object and an
  `assumptions` array. Never replace the formula with an unexplained approximate count.
- An acceptance provenance must add `acceptance.threshold` and
  `acceptance.workload_contract`. Thresholds are frozen before the after sample.
- Do not merge mean, peak, p95, p99, cold and warm values under one metric ID.
- Do not include secrets, message bodies, private device identifiers or unnecessary
  absolute paths in provenance.

## Comparison rules

Numeric before/after records with the same `id` and `unit` are classified as:

- `paired_observation`: same metric, workload, boundary and sampler; exact delta allowed;
- `implementation_bound`: exact configuration or code bound; delta describes the bound,
  not runtime impact;
- `derived_vs_observed` or `directional_evidence`: useful direction, no exact delta;
- `mixed_evidence`: incompatible kinds without an explicit stronger contract.

Set `comparison.quality` on one record in every numeric pair to `paired`,
`implementation_bound`, or `directional`. New-schema pairs without this declaration are
reported as `undeclared_comparison` and exact changes are suppressed. The helper also
suppresses percentage changes for directional/mixed pairs.
Different RPC payload shapes, single cache-hit versus cold full reads, simulator versus
device, lab versus field, and development versus release are not strict paired A/B.

## Resource rules

The helper evaluates a plan only; it never terminates or deletes a resource.

Required resource fields:

- `id`, `kind` and `policy` (`inventory_only`, `orphan_only`, `idle_resumable`);
- `owner_state` (`active`, `archived`, `missing`, `unknown`);
- `activity_state` (`working`, `awaiting_input`, `idle`, `unknown`);
- `resumable`, `attachments`, `registration_active`, `operation_active`, `cwd_in_use`;
- `dirty`, `identity_state`, `evidence_state`, `retention_state`.

`null` means not applicable only when the resource truly has no such concept. Unknown
dirty state on a filesystem resource is protection, not permission.

## Run status and output

Allowed terminal statuses are `diagnosed`, `implemented_not_runtime_verified`,
`partially_verified`, `verified`, and `blocked`. Audit-only work normally ends at
`diagnosed` or `blocked`; `verified` requires comparable runtime evidence meeting the
declared thresholds.

The helper always emits `app-runtime-report/v1` containing normalized observations,
comparison quality, resource verdicts, ranked hypotheses, correctness gates, evidence
gaps and warnings. The Markdown report mirrors the same facts and emits no destructive
commands.
