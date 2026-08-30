# Open-Source Solutions Landscape

Use this workflow when the research topic concerns software, tooling, automation, implementation, integrations, deployment, or a request for practical solutions. It is a conditional but mandatory completion gate.

## 1. Discovery coverage

Search GitHub and at least two other relevant forges or code indexes when they are available and likely to contain the topic. Candidate platforms include GitLab, Gitee, Codeberg, SourceForge, GitCode, Bitbucket public repositories, package registries, and domain-specific indexes. Do not add low-value platforms only to satisfy a count; record why a platform was applicable or unavailable.

Use multiple query forms:

- topic and product names in English and the user's language;
- action terms such as upload, publish, automate, scheduler, adapter, plugin, CLI, SDK, bot, or integration;
- implementation terms such as Playwright, Puppeteer, Selenium, API, browser extension, RPA, reverse engineering, or protocol;
- forge-native topic, language, filename, and code search when available.

Persist the attempted forge, query, retrieval date, and result count. Search snippets are discovery leads, not evidence.

## 2. Canonicalization and eligibility

Resolve each candidate to the canonical upstream repository. Treat mirrors, forks, renamed repositories, organization transfers, and vendored copies as one solution unless the fork has independent maintenance and material changes. Record the relationship instead of inflating the solution count.

An included repository must have:

1. a publicly reachable canonical URL;
2. topic-relevant implementation or documentation;
3. at least one inspected file, commit, release, or issue supporting the claimed mechanism;
4. enough metadata to state maintenance and license uncertainty honestly.

Archived, abandoned, unlicensed, proof-of-concept, or private-protocol projects may be included when decision-relevant, but must be labeled rather than presented as production-ready.

## 3. Evidence inspection

README claims alone are insufficient for core capability claims. Inspect the relevant adapter, uploader, workflow, manifest, package metadata, release, issue, or commit. Prefer immutable commit URLs for implementation evidence. Record which evidence was inspected and what it proves.

Use forge APIs or repository metadata pages for mutable facts such as stars, forks, archived status, license, default branch, and last push. Record a retrieval date. Never infer a license from language, repository visibility, or copied code.

For each repository, separate:

- **repository facts:** URL, forge, owner, license, metrics, dates, archived status, language;
- **verified mechanism:** how the implementation works and the exact evidence path/commit;
- **assessment:** maturity, security, maintenance, platform-policy, and adoption fit;
- **recommendation:** reuse, reference only, human-in-the-loop, research only, or reject.

## 4. Persistence contract

Write one JSON object per line to `open_source_solutions.jsonl` using these fields:

```json
{
  "name": "project-name",
  "canonical_url": "https://forge.example/owner/repo",
  "forge": "github",
  "upstream_url": null,
  "description": "one-sentence verified scope",
  "license": "MIT",
  "stars": 123,
  "forks": 12,
  "archived": false,
  "last_activity_at": "2026-08-30",
  "retrieved_at": "2026-08-30",
  "implementation_mechanism": "Playwright drives the official creator UI",
  "evidence_url": "https://forge.example/owner/repo/blob/commit/path/file",
  "evidence_locator": "function publishVideo",
  "verification_status": "code_verified",
  "fit": "reference",
  "risks": ["platform terms", "stored login state"]
}
```

Allowed `verification_status` values are `code_verified`, `release_verified`, `documentation_only`, and `unverified`. Allowed `fit` values are `reuse`, `reference`, `human_in_the_loop`, `research_only`, and `reject`.

If no repository qualifies, write one record with `status: "no_qualifying_repositories"`, plus `attempted_forges`, `queries`, `retrieved_at`, and `reason`.

## 5. Shareable report contract

The report must contain an **Open-Source Solutions Landscape** section with direct canonical links. Use a compact table covering project, forge, verified mechanism, activity, license, evidence inspected, fit, and risks. Follow it with prose explaining:

- the strongest reusable option and why;
- reference-only or research-only projects;
- excluded mirrors, forks, dead links, or marketing-only claims;
- coverage gaps on attempted forges;
- how mutable repository metrics may have changed since retrieval.

The table is a discovery and handoff artifact, not a substitute for evidence-backed analysis. Register repository pages and implementation evidence in `sources.jsonl` and `evidence.jsonl`, then cite the related report claims normally.
