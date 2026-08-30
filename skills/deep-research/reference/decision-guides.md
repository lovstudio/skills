# Decision Guides for Selection Research

Use this workflow when the report compares options or asks the reader to select, procure, adopt, deploy, or architect a solution. The goal is to convert analysis into a deterministic first-pass decision rather than leave the reader to interpret a score table.

## 1. Identify decision-changing gates

Start with constraints that can invalidate an option regardless of its aggregate score. Typical hard gates include:

- legal, policy, authorization, or licensing permission;
- whether an irreversible action may run unattended;
- data, credential, or deployment boundary;
- required acceptance evidence or auditability;
- minimum scale, latency, reliability, or budget threshold;
- whether the organization can operate and maintain the solution.

Do not begin with soft preferences such as UI polish or star count when a hard gate changes the recommendation.

## 2. Build the branch flow

Use three to seven decision nodes. Each node must ask one answerable question with mutually exclusive branches. Every path must end at one of:

- a named recommended option;
- a prerequisite action before selection can continue;
- a fallback option;
- an explicit rejection or stop condition.

Keep the diagram near the front of the report, after the Introduction and before detailed findings. Cite source-backed gate conditions in the accompanying prose; the diagram itself may use short labels.

## 3. Preserve non-compensable risks

Do not let a weighted score offset a hard prohibition. For example, stronger automation, lower cost, or higher popularity cannot compensate for missing authorization, an incompatible license, or an unverifiable final state. Use those constraints as branches before any scoring table.

## 4. Choose a renderer-safe format

Use Mermaid only after verifying the target renderer executes Mermaid. Otherwise use one of:

- responsive inline SVG with `role="img"`, a `<title>`, a `<desc>`, and readable text;
- semantic HTML/CSS flow blocks supported by the target renderer;
- a stable monospace text tree when rich rendering is unavailable.

Never deliver an image-only decision. Follow the visual with a compact `### Outcome Map` or `### 选择结果` section that repeats every terminal recommendation in text.

## 5. Acceptance checklist

- The first question changes the recommendation.
- Every branch reaches a terminal result.
- Terminal results use the same option names as the recommendation section.
- Hard gates appear before weighted preferences.
- The text fallback contains every terminal result.
- Mobile and print output remain readable.
- The guide can answer the reader's scenario in under one minute.
