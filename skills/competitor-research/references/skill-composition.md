# Skill Group Composition

Inspected on 2026-11-15 against the local Skill source root and the installed
Claude Code / shared agent skill catalogs, by routing description and actual
input/output contract.

## Nearby Skills Inspected

| Skill | Routing contract | Classification | Decision |
| --- | --- | --- | --- |
| `deep-research` | Multi-source research reports for broad analysis, X vs Y, trends, state of the art, open-source landscapes | upstream atom / partial overlap | Owns open-ended landscapes where targets are not yet named. Its candidate list can become this Skill's input. This Skill owns named head-to-head comparison, provenance and worth judgments, which `deep-research` does not cover with code-level evidence. |
| `market-research` (third-party) | Market sizing, competitor frameworks, free data sources | not composed | Adjacent topic; it estimates TAM/SAM and opportunity size. This Skill does not size markets and does not call it. |
| `autoglm-deepresearch` (third-party) | Deep topic research including 竞品分析 through a local token service | overlap, kept separate | General research engine without provenance evidence or a verifiable ledger. No handoff; users choose it explicitly. |
| `lov-fact-check` | Verify one factual claim with a source chain and confidence | downstream atom | When a report hinges on one disputed number (for example a funding amount), that single claim can be handed off. Artifact: the claim text plus its ledger entry. |
| `lov-dev-research` | Requirement-driven reuse strategy and technology selection | downstream atom | Consumes the comparison table when the user moves from "who is better" to "what should I build with". |
| `lov-solution-architect` | Research-backed solution and architecture plans | downstream atom | Same as above for full product or technical plans. |
| `lov-share-session` | Publish the session transcript as a LovStudio page | downstream atom | Optional: share the research session after delivery. |
| `lov-mobile-infographic`, `lov-gen-card` | Turn conclusions into mobile infographics or knowledge cards | downstream atom | Optional: visualize the final comparison table. Input is the delivered report. |
| `lov-article-creator`, `deep-tech-article` | Long-form article drafting and packaging | downstream atom | Optional: turn an accepted report into a publishable article. |
| `lov-gh-access`, `lov-repo-takeover`, `lov-better-github-desc` | GitHub repository administration | not composed | Share the GitHub topic only; no research handoff. |

## Atomic Handoffs

```text
optional upstream: deep-research
  candidate list of named targets
                |
                v
lov-competitor-research (core atom)
  evidence ledger + report with modules A comparison, B provenance,
  C worth, D investment view
                |
                v
optional downstream: lov-fact-check (one disputed claim),
  lov-dev-research / lov-solution-architect (build decision),
  lov-mobile-infographic / lov-gen-card (visual),
  lov-article-creator / deep-tech-article (article),
  lov-share-session (share the session)
```

- This Skill owns the acceptance criterion for the research report: every number
  traces to the ledger, provenance verdicts match the evidence ladder, and
  unverifiable items are listed.
- Downstream Skills own their own artifacts; they receive the delivered report or
  a single ledger entry, never hidden runtime coupling.

## Overlap Decisions

- `deep-research` stays the router for unnamed landscapes and trend reports. This
  Skill hands back to it when more than five targets or no named targets exist,
  instead of duplicating landscape search.
- `autoglm-deepresearch` and `market-research` overlap on the words 竞品分析 and
  competitor analysis. They are kept separate because this Skill's value is the
  evidence ledger and the deterministic open-source evidence script; the trigger
  list names provenance and worth questions explicitly to route accurately.

## Composition Decision

`lov-competitor-research` is a **Single Skill**. The four modules share one
evidence ledger and usually arrive as follow-up questions in the same
conversation, so splitting them into a Kit would force the ledger across module
boundaries without giving any module an independently useful input/output
contract. `scripts/repo_evidence.py` is implementation support for modules A–C,
not a separate stage. All adjacent Skills remain optional artifact-level handoffs.
