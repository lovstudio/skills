# Fit Analysis Rubric

How to decide whether an existing DSH plugin covers a goal or a new plugin
must be built. Every judgment cites gateway fields; no hard score threshold is
sufficient alone, because the gateway indexes community plugins of uneven
maturity.

## Five dimensions

Score each candidate qualitatively on each dimension and record the supporting
gateway fields.

1. 能力覆盖 capability coverage
   - Read the description, tags, category, and the localized intro and
     highlights from the detail endpoint.
   - Does the plugin name the goal's core verbs and objects? For example a
     goal of "读取图片做问答" needs explicit image input and Q&A wording,
     not just a screenshot tool.
   - Missing core verbs mean partial or no coverage, regardless of grade.

2. 成熟度 maturity
   - Use score (0-100), grade (S/A/B/C), stars, contributors, and pushed_at.
   - A null score or grade means unrated: fall back to stars, contributors,
     pushed_at, and description quality. An unrated plugin can still be a
     MATCH when coverage and integration are strong and the repo is active.

3. 健康与风险 health and risk
   - archived true disqualifies a MATCH. is_risky true with a risk_note means
     the match is at most PARTIAL and the note must be surfaced to the user.

4. 集成可行性 integration
   - install.kind order of preference: npm and release are the smoothest, git
     needs a source mount, build-required needs a local build,
     not-installable means the repo is not a plugin package at all.
   - npm_published true strengthens an npm path; install.cmd gives the
     canonical command when present.
   - is_plugin false with install.kind not-installable means the repo is an
     app or web UI, not a candidate plugin.

5. 来源可信 provenance
   - is_official and is_featured signal catalog placement; is_insider marks
     community insider projects. These raise confidence but do not override
     weak coverage or integration evidence.

## Verdict rules

- MATCH: core capability covered, no health disqualifiers, acceptable
  maturity, and a usable install path (npm, release, or git).
- PARTIAL: covers part of the goal, or is usable with real caveats (unrated,
  build-required, stale push, risk_note, or missing core verbs). Present the
  trade-off and ask the user one focused question.
- NO-MATCH: no candidate covers the core capability, or every covering
  candidate is archived or not-installable. Produce a new-plugin brief.

## Decision guidance

- At least one MATCH: adopt the strongest one; give the usage path derived
  from install fields and state the acceptance check the user can run.
- Only PARTIAL candidates: options are compose existing candidates, extend the
  closest one (base for a new plugin), or accept the caveats. Ask one focused
  question before committing.
- NO-MATCH: the create path. Base the new plugin on the closest open-source
  implementation: the candidate whose coverage and architecture most overlap
  the goal becomes the base, even when its own coverage is partial.

## New-plugin brief shape

The brief handed to dsh-plugin-creator contains: goal, required capabilities,
closest base implementations (full_name, repository_url, why each is the
base), the gaps to implement, and the constraints from the request. The brief
must not claim capabilities that lack gateway evidence.
