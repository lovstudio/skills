# Selection Rubric

Use this rubric when ranking implementation options for each module.

## Priority Ladder

Rank options by this default ladder:

| Rank | Option type | Prefer when |
|---|---|---|
| 1 | Modern popular open-source DIY | Mature enough, active, good docs, avoids lock-in, can be integrated quickly |
| 2 | Legacy open-source DIY | Proven and stable, but only if modern choices are weaker or incompatible |
| 3 | From-scratch implementation | Core differentiator, unusual domain logic, strict privacy/security, or no adequate OSS |
| 4 | Commercial API | OSS/self-hosted quality is worse, or API materially reduces risk/time |
| 5 | Commercial product | Buying solves the whole workflow better than building/integrating |

## Scorecard

Score important candidates from 1 to 5:

| Dimension | Weight | What to check |
|---|---:|---|
| Fit to requirement | 25 | API coverage, extensibility, ecosystem compatibility |
| Developer experience | 15 | Docs, examples, type support, error quality, setup friction |
| Maintenance health | 15 | Recent releases, issue response, stars/downloads, bus factor |
| Output quality | 15 | Accuracy, rendering quality, performance, reliability |
| Cost and ownership | 10 | License, hosting/API fees, lock-in, migration path |
| Security and privacy | 10 | Data exposure, auth model, self-hosting, compliance |
| Operational complexity | 10 | Deployment, scaling, observability, failure recovery |

Recommend the highest weighted fit, not the highest raw popularity.

## Evidence Checklist

For recommended libraries or frameworks, gather:

- Official documentation URL.
- Repository URL when open source.
- License.
- Last meaningful release or recent commit activity.
- Adoption signal such as stars, downloads, community usage, or ecosystem default status.
- Known limitations and migration risk.

For commercial APIs/products, gather:

- Pricing URL.
- Data processing/privacy notes.
- Rate limits or quota model.
- Exit path if the service is replaced later.

## Decision Rules

- Prefer `modern-screenshot` over `html2canvas` for browser DOM screenshots unless compatibility evidence says otherwise.
- Prefer `FastAPI` over `Express` for API services when Python is acceptable and type/schema-first development matters.
- Prefer protocol-compatible providers over proprietary SDK-only integrations.
- Prefer self-hostable components when user data sensitivity is high.
- Prefer smaller focused libraries over full platforms unless the platform replaces substantial engineering work.
- Do not choose from-scratch work just because it is technically possible.
- Do not choose a commercial API before checking whether a current OSS stack can satisfy quality and timeline.
