# Verified Case: Codex Banked Reset Screenshot

## Input

The real input was a 1200 by 888 screenshot showing two Tibo posts and one
quoted post. English source text appeared next to automatic Chinese translations.
The visible machine translation rendered `banked reset` as “银行重置”, `by 8pm
PST` as “太平洋标准时间下午 8 点到达”, and `Do with this information what
you may` as “请自行处理这些信息”.

The user's acceptance criteria were:

1. communicate the correct translation;
2. make readers notice how poor the automatic translation was; and
3. keep the original layout and formatting substantially unchanged.

The user then clarified that strikethroughs already communicate correction, so
an additional “勘误” label should not appear by default.

## Evidence and judgment

OpenAI's Codex documentation describes a banked reset as a saved Codex
rate-limit reset that can be applied later. This rules out the dictionary sense
of a financial bank. The product behavior supports “可储备的用量重置” as a
clear Chinese rendering for this audience.

`By 8pm PST` is a deadline, so “晚上 8 点前到账” preserves both the time and
the `by` boundary. The final sentence is playful permission or suggestion, not
a formal instruction to process information.

Primary reference:

- [Using Codex with your ChatGPT plan](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)

## Correction map

| Old fragment | Replacement | Reason |
|---|---|---|
| 银行重置已到达 | 可储备的用量重置已经到账 | Product term and account-credit metaphor, not a bank operation |
| 银行重置 | 可储备的用量重置 | Same product-term error in repeated blocks |
| 太平洋标准时间下午 8 点到达 | 太平洋时间晚上 8 点前到账 | Restores the deadline expressed by `by` and uses natural account wording |
| 请自行处理这些信息 | 知道这个消息后该怎么做，就看你们了 | Restores the playful pragmatic force rather than a bureaucratic instruction |

## Complete corrected readings

Top post:

> 可储备的用量重置已经到账。我再说一遍，可储备的用量重置已经到账。祝大家周末愉快。

Quoted and lower post:

> 可储备的用量重置将在太平洋时间晚上 8 点前到账，面向 ChatGPT Work 和 Codex
> 的所有付费用户。知道这个消息后该怎么做，就看你们了。

## Visual iteration evidence

The first generated image replaced the translation cleanly and therefore failed
the requirement to expose the old machine error. The second retained old
fragments under red strikethroughs and placed corrected fragments in dark red,
but added a repeated “勘误” heading. Direct user feedback established that the
heading was redundant. The reusable default is therefore unlabeled inline track
changes with the original screenshot as the immutable base.

The real iterations verified semantic correctness and the communication model.
Exact pixel-diff layout verification remains a future deterministic enhancement,
so the Skill Card marks that dimension as provisional rather than complete.
