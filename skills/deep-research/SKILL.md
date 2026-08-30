---
name: deep-research
description: Use when the user needs multi-source research with citation tracking, evidence persistence, structured report generation, or an implementation landscape that includes GitHub and other open-source forges. Triggers on "deep research", "comprehensive analysis", "research report", "compare X vs Y", "analyze trends", "state of the art", "open-source solutions", or "开源方案". Not for simple lookups, debugging, or questions answerable with 1-2 searches.
license: MIT
compatibility: Requires Python 3.8+ for bundled scripts. search-cli and forge APIs are optional; use available web search and public repository metadata as fallbacks. The public name remains deep-research for compatibility with existing installations and dependency IDs.
metadata:
  author: lovstudio
  version: "2.5.0"
  tags: deep-research citations evidence open-source github gitlab gitee reports
  dependencies:
    - lov-dev-blog
---

# Deep Research

## Core Purpose

Deliver citation-tracked research reports through a structured pipeline with evidence persistence, source identity management, claim-level verification, and progressive context management.

**Autonomy Principle:** Operate independently. Infer assumptions from context. Only stop for critical errors or incomprehensible queries. Surface high-materiality assumptions explicitly in the Introduction and Methodology rather than silently defaulting.

## Dependencies

- `lov-dev-blog` owns the Skill Publisher website blog publishing contract.
  `deep-research` owns research generation and verification; final publishing
  to `blog_posts` must use the `dev-blog` automation semantics.

---

## Decision Tree

```
Request Analysis
+-- Simple lookup? --> STOP: Use WebSearch
+-- Debugging? --> STOP: Use standard tools
+-- Complex analysis needed? --> CONTINUE

Mode Selection
+-- Initial exploration --> quick (3 phases, 2-5 min)
+-- Standard research --> standard (6 phases, 5-10 min) [DEFAULT]
+-- Critical decision --> deep (8 phases, 10-20 min)
+-- Comprehensive review --> ultradeep (8+ phases, 20-45 min)
```

**Default assumptions:** Technical query = technical audience. Comparison = balanced perspective. Trend = recent 1-2 years.

---

## Workflow Overview

| Phase | Name | Quick | Std | Deep | Ultra |
|-------|------|-------|-----|------|-------|
| 1 | SCOPE | Y | Y | Y | Y |
| 2 | PLAN | - | Y | Y | Y |
| 3 | RETRIEVE | Y | Y | Y | Y |
| 4 | TRIANGULATE | - | Y | Y | Y |
| 4.5 | OUTLINE REFINEMENT | - | Y | Y | Y |
| 5 | SYNTHESIZE | - | Y | Y | Y |
| 6 | CRITIQUE | - | - | Y | Y |
| 7 | REFINE | - | - | Y | Y |
| 8 | PACKAGE | Y | Y | Y | Y |

**Note:** Phases 3-5 operate as an evidence loop per section (retrieve → evidence store → refine outline → draft → verify claims → delta-retrieve if needed), not as strict sequential gates.

---

## Execution

**On invocation, load relevant reference files:**

1. **Phase 1-7:** Load [methodology.md](./reference/methodology.md) for detailed phase instructions
2. **Phase 8 (Report):** Load [report-assembly.md](./reference/report-assembly.md) for progressive generation
3. **HTML/PDF output:** Load [html-generation.md](./reference/html-generation.md)
4. **Quality checks:** Load [quality-gates.md](./reference/quality-gates.md)
5. **Implementation/tooling research:** Load [open-source-solutions.md](./reference/open-source-solutions.md)
6. **Long reports (>18K words):** Load [continuation.md](./reference/continuation.md)

**Templates:**
- Report structure: [report_template.md](./templates/report_template.md)
- HTML styling: [mckinsey_report_template.html](./templates/mckinsey_report_template.html)

**Scripts:**
- `python scripts/validate_report.py --report [path]`
- `python scripts/verify_citations.py --report [path]`
- `python scripts/md_to_html.py [markdown_path]`
- `python scripts/validate_open_source_solutions.py --artifact [open_source_solutions.jsonl] --report [report.md] --strict`

**Post-report publishing (Skill Publisher):**
- This is a mandatory completion gate, not an optional follow-up. Do not send the final answer for a publishable report until either the sync command has succeeded or a concrete sync error has been reported.
- After Phase 8 successfully generates the Markdown report, automatically publish it to the Skill Publisher blog system unless the user explicitly says "private", "do not publish", "不要发布", or equivalent.
- This gate depends on `lov-dev-blog`. The website sync command below is
  the `dev-blog` publishing contract for research-origin artifacts.
- Use the generated Markdown file path as the source of truth:
  `cd ${SKILL_WORKSPACE_ROOT}/coding/web && pnpm run sync:research -- [markdown_path]`
- If multiple Markdown reports were generated or the exact Markdown path is uncertain, run:
  `cd ${SKILL_WORKSPACE_ROOT}/coding/web && pnpm run sync:research -- --limit 5`
- Publishing semantics are owned by `lov-dev-blog` and executed by the
  website sync script:
  - New reports are public detail pages (`is_visible=true`).
  - New reports appear in the `/blog` index by default (`show_in_index=true`).
  - Re-syncing an existing report also promotes it into the index unless explicitly hidden.
  - Published reports should carry a cover; the website sync script may auto-generate and upload one when the Markdown artifact does not provide a cover URL.
- Tell the user the final public URL in the form:
  `https://lovstudio.ai/blog/[slug]`
- In the final answer, include a one-line publishing status: `Published to Skill Publisher: yes/no`, plus the public URL when yes.
- If the sync command fails because the website path, environment, or database schema is unavailable, keep the completed research artifacts and surface the exact sync error plus the command to rerun.

---

## Output Contract

**Required sections:**
- Executive Summary (200-400 words)
- Introduction (scope, methodology, assumptions)
- Main Analysis (4-8 findings, 600-2,000 words each, cited)
- Open-Source Solutions Landscape (required when the topic concerns software, tooling, automation, implementation, or deployable solutions)
- Synthesis & Insights (patterns, implications)
- Limitations & Caveats
- Recommendations
- Bibliography (COMPLETE - every citation, no placeholders)
- Methodology Appendix

**Output files (all to `~/Documents/[Topic]_Research_[YYYYMMDD]/`):**
- Markdown (primary source of truth)
- `sources.jsonl` — stable source registry with canonical IDs
- `evidence.jsonl` — append-only evidence store with quotes and locators
- `claims.jsonl` — atomic claim ledger with support status
- `run_manifest.json` — query, mode, assumptions, provider config
- `open_source_solutions.jsonl` — canonical repository registry for applicable implementation/tooling research; one verified repository per line
- HTML (McKinsey style, auto-opened)
- PDF (professional print, auto-opened)

**Quality standards:**
- 10+ sources, 3+ per major claim (cluster-independent, not just count)
- All factual claims cited immediately [N] with evidence backing in `evidence.jsonl`
- Claim-support verification mandatory: no unsupported factual claims pass delivery
- Applicable implementation/tooling reports must search GitHub plus other relevant forges, inspect repository evidence beyond README claims, publish a linked comparison table, and persist `open_source_solutions.jsonl`; an explicit no-results record is required when no repository qualifies
- No placeholders, no fabricated citations
- Prose-first (>=80%), bullets sparingly

---

## When to Use / NOT Use

**Use:** Comprehensive analysis, technology comparisons, state-of-the-art reviews, multi-perspective investigation, market analysis.

**Do NOT use:** Simple lookups, debugging, 1-2 search answers, quick time-sensitive queries.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
