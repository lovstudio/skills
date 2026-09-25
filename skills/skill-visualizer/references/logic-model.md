# Skill logic model

The deterministic extractor emits `lovstudio/skill-logic/v1`. Its purpose is
traceability: a reviewer should be able to move from every diagrammed rule back
to the source without treating model inference as authored Skill behavior.

## Input resolution

- A directory resolves to its top-level `SKILL.md`.
- A file input must be named `SKILL.md`.
- Symlinks resolve to the canonical local source before extraction.
- Output stores only paths relative to the Skill root.

## Extracted layers

### Routing

`routing.activate` and `routing.do_not_activate` come from list items under the
matching headings in `## Triggers`. Each item includes a source line. Routing is
classified as `external_activation_boundary`: it helps the host decide whether
to invoke the Skill, but it is not part of the internal runtime graph.

### Runtime workflow

`workflow.steps` comes from Step headings under `## Workflow`. When a Skill uses
an ordered list instead of Step headings, top-level numbered items become the
steps. Each step includes its number, title, first meaningful summary, source
span, explicit local resources, and conditional list items. Its `details`
preserve authored body blocks as line-bound `instruction`, `output`, `criterion`,
`decision`, `verification`, `guardrail`, or `command` evidence. These labels are
deterministic text classifications, not inferred success claims.

A conditional rule starts with an explicit marker such as `if`, `when`,
`unless`, `otherwise`, `如果`, `若`, `当`, or `否则`. A comma, colon, or semicolon
splits the condition from its declared action. Prose that merely sounds
conditional is not promoted to a decision node.

### Runtime context and composition

`runtime_context` reads the runtime and Profile declarations from `skill.yaml`.
Frontmatter dependencies stay separate from local resource links. If `kit.yaml`
is present, module and named-pipeline declarations are preserved in `kit` and a
third Mermaid diagram is added. Existing module `SKILL.md` files are parsed for
their own workflow steps and quality gates. A controller step receives
`module_ids` or `pipeline_ids` only when its authored body explicitly names that
module, path, Skill ID, or pipeline.

### Trust evidence

`trust.scope` is `internal_runtime`; `trust.routing_scope` is
`external_activation_boundary`. The remaining fields separate:

- source-bound steps and authored detail;
- steps supported by explicit modules or local resources;
- deterministic runtime scripts versus Agent-guided instructions;
- declared step/module verification rules and structural validation assets;
- packaged cases or artifacts, which remain `observed_unbound` unless a future
  contract can bind them to individual steps.

Every step also carries an `assurance` record. Static extraction never upgrades
a step to effect-proven merely because the package contains one unrelated case.

### Resources

The extractor follows local Markdown links and explicit paths under
`references/`, `scripts/`, `assets/`, and `skills/`. `--max-depth` controls only
recursive Markdown traversal. It also inventories packaged files so unlinked
logic does not disappear from the report. Missing declared files become error
diagnostics.

## Mermaid views

The Markdown report contains:

1. internal runtime flow, including explicit conditions but excluding host
   activation matching;
2. controller-to-resource and dependency relationships; and
3. Skill Kit module pipelines when applicable.

The JSON model is the stable handoff for custom SVG, graph database, or catalog
renderers. Presentation renderers remain optional downstream consumers.

## Standalone HTML review

When `--output path/report.md` is used, the extractor also writes
`path/report.html` unless `--no-html` is present. `--html` chooses another HTML
path. The page embeds its CSS, JavaScript, Mermaid source, and complete JSON
model; it makes no network requests and needs no hosted renderer.

The review page leads with a concrete situation in which the Skill is the right
choice, followed by Before → internal transformation → After, a fully visible
selected pipeline, its non-use boundary, deliverables, and trust limits. The
primary reading path contains no node selection, canvas dragging, zoom control,
diagram tabs, or synchronized inspector.

Runtime, resource, and optional Kit diagrams render as SVG inside one collapsed
technical-evidence section. They preserve the extracted graph for verification
and downstream reuse without becoming the navigation model. Source, routing,
resource inventory, diagnostics, raw Mermaid, and JSON stay in the same
secondary evidence layer.

Host activation rules are excluded from the internal graph and kept collapsed
under an explicitly external boundary. Raw Mermaid source, resource tables, and
JSON are also secondary. CSS must visually hide any element carrying `hidden`;
checking only the DOM property is insufficient when an authored `display` rule
can override the browser default.

Presentation localization is separate from extraction. For a Chinese review,
generated UI and known authored display phrases may be shown in Chinese, while
the JSON model, file paths, Skill IDs, commands, source code, and Mermaid syntax
retain their extracted form. A missing safe translation falls back to the source
text rather than inventing meaning.

The generator embeds the vendored Mermaid 11.12.2 browser runtime. Successful
HTML validation requires each declared diagram host to contain an SVG after a
real browser load; embedded source alone is insufficient. The HTML remains a
review surface over the same deterministic model, not a second source of
semantics and not proof that the target Skill succeeds at runtime.

## Diagnostic contract

- Exit `0`: extraction completed; warnings or informational findings may remain.
- Exit `2`: target resolution, file I/O, YAML, or CLI validation failed.
- Exit `3` with `--strict`: extraction completed and the model contains at least
  one error diagnostic.

Common error diagnostics are missing frontmatter name, activation examples,
workflow steps, or a declared local resource. A report with errors is useful
for repair, but it is not a complete runtime specification.

## Static-analysis boundary

The extractor does not execute a target Skill or Python script. It does not
infer decisions hidden in prose, imported code, model judgment, remote tools,
or undeclared files. A source span proves the instruction exists; a module or
resource proves support exists; a quality gate proves an acceptance rule is
declared. None of those proves the target Skill produced a good real-world
result. That claim requires a bound task, artifact, and observed readback.
