# LovStudio case collection

Public, independently identified cases for https://lovstudio.ai/cases.

- `cases.json` is the canonical registry. `skillIds` holds the many-to-many Skill relation.
- New contributions use the authenticated `https://lovstudio.ai/api/cases` API.
- `legacy` preserves previous Skill IDs, case IDs, titles, source URLs and content fingerprints for redirects and migration audits.
- Original per-Skill case files remain historical sources. Do not append the same case to several Skill repositories.
- Migration retained 122 legacy records as 114 distinct cases with 122 associations. Eight exact copies were consolidated. Distinct content with equal titles was preserved.
- Articles remain on their existing editorial surfaces. Existing public Session access terms are unchanged.

Images resolve to their original published sources unless they are new case assets under `assets/`. The website reads this repository dynamically.
