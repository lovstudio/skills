# Codex token semantics

Evidence checked on 2026-08-14. Runtime data and the installed Codex version can
change, so the inspector detects columns and event fields instead of assuming a
fixed database schema.

## Primary evidence

1. OpenAI Codex protocol defines `TokenUsage` and `TokenUsageInfo`. The total is
   accumulated by adding the last upstream usage; cached input is stored inside
   input, and reasoning output is stored inside output:
   [protocol.rs](https://github.com/openai/codex/blob/fdbab67c669a3176b13d08ab49493f30a806d2ba/codex-rs/protocol/src/protocol.rs#L2064-L2156).
2. Codex state extraction writes `info.total_token_usage.total_tokens` directly
   to `threads.tokens_used`. It does not add earlier values from another
   process:
   [extract.rs](https://github.com/openai/codex/blob/fdbab67c669a3176b13d08ab49493f30a806d2ba/codex-rs/state/src/extract.rs#L101-L106).
3. Codex TUI displays `non_cached_input + output` as its blended total and shows
   cached input separately:
   [token_usage.rs](https://github.com/openai/codex/blob/fdbab67c669a3176b13d08ab49493f30a806d2ba/codex-rs/tui/src/token_usage.rs#L20-L55).
4. The protocol explicitly describes `RawResponseCompletedEvent` as exact usage
   from one upstream Responses API completion, unlike the accumulated,
   estimated, or replayed `TokenCountEvent`:
   [protocol.rs](https://github.com/openai/codex/blob/fdbab67c669a3176b13d08ab49493f30a806d2ba/codex-rs/protocol/src/protocol.rs#L1829-L1836).

## Independent and local evidence

- A public Codex issue documents the same local `state_5.sqlite` and rollout
  JSONL surfaces, including `threads.tokens_used` and `token_count` events:
  [openai/codex issue #24510](https://github.com/openai/codex/issues/24510).
- The verified local case used Codex CLI 0.147.0. Its SQLite row contained
  `tokens_used = 104,545`, while the matching rollout contained five cumulative
  counter segments totaling 213,343,248 processed tokens. This directly proves
  that the latest SQLite snapshot can understate a resumed thread's history.

## Aggregation rule

Within one live Codex process, `total_token_usage` is cumulative. Repeated
`token_count` events must not be summed. The fallback historical method is:

1. stream token events in file order;
2. end a segment when `info` becomes null or `total_tokens` decreases;
3. retain the terminal cumulative snapshot of each segment;
4. sum only those segment terminals.

This is the best available thread-level reconstruction for legacy rollouts, not
an invoice. A first request after resume could theoretically exceed the prior
segment total without a null marker; the script cannot prove that unseen reset
and therefore reports the method and segment evidence rather than claiming
billing exactness.

## Interpretation

- `total_tokens = input_tokens + output_tokens` for ordinary provider-reported
  snapshots.
- `cached_input_tokens` is a subset of `input_tokens`.
- `reasoning_output_tokens` is a subset of `output_tokens`.
- `tui_style_total_tokens = max(input - cached, 0) + output`.
- Cached input can be discounted, but the discount depends on provider and
  product pricing; a token count alone cannot determine currency cost.
