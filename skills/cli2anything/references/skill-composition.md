# Skill Group Composition

## Nearby Skills Inspected

| Skill | Routing contract | Decision |
|---|---|---|
| `lov-cli-creator` | Turns an existing local project/backend into a maintained CLI | Adjacent, not composed. It creates a CLI from source code; `lov-cli2anything` runs cli2anything++ against authorized observed web APIs. |
| `lov-api-creator` | Adds FastAPI gateway endpoints and a uni-app client layer | Not composed. It owns application gateway integration, not observed API discovery or SDK generation. |
| `lov-codeex-creator` | Creates Codeex runtime plugins | Not composed. Its output is a Codeex plugin rather than an API contract or generated CLI. |

## Atomic Handoffs

- Optional upstream artifact: an authorized discovery JSON file containing
  endpoint evidence. The provider owns authorization and redaction; this Skill
  accepts the file and owns generated artifact validation.
- Core artifact: cli2anything++ produces `manifest.json`, `openapi.json`,
  `api-graph.json`, a portable SDK, and optionally Swagger or a generated CLI.
- Optional downstream artifact: the verified OpenAPI document or generated CLI
  may be consumed by another project. No downstream Skill is invoked implicitly.

## Overlap Decisions

`lov-cli-creator` overlaps only at the word “CLI.” Its acceptance criterion is a
maintained command surface over a local project's real backend. This Skill's
criterion is a verified bundle derived from authorized observed API evidence, so
neither Skill should extend or silently call the other.

`lov-api-creator` creates application gateway code and therefore must not be used
as a substitute for discovery evidence or same-origin browser-session handling.

## Composition Decision

Single Skill. Target selection, scope filtering, OpenAPI/graph generation, SDK
packaging, Swagger generation, and CLI generation share one runtime and one
user-visible acceptance boundary. The internal Python wrapper only locates and
executes the bundled project safely; it does not justify a Skill Kit.
