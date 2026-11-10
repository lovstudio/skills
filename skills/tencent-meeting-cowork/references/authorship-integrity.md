# Authorship Integrity Contract

Use this contract when `metadata.content_class` is `authored-prose`. It governs
essays, articles, reports, scripts, letters, and other prose where the writer's
reasoning and editorial choices are part of the deliverable.

## Authorship ledger

Before drafting, record:

- `source_question`: the real question or tension behind the piece;
- `author_positions`: claims explicitly supplied or approved by the user;
- `firsthand_evidence`: experiences, observations, decisions, and emotions that
  are safe to write in the first person;
- `editorial_decisions`: what to foreground, omit, defer, or leave unexplained;
- `counterevidence`: facts and interpretations that complicate the main claim;
- `open_questions`: uncertainty that should survive the draft;
- `preserve_verbatim`: quotations, transcripts, legal text, names, numbers, and
  identifiers that must not be paraphrased;
- `forbidden_inventions`: experiences, motives, facts, quotations, and causal
  links the Skill must not add.

## Discourse audit

Inspect the draft before surface polishing:

1. thesis provenance — trace each major claim to evidence or an explicit author
   decision;
2. causal compression — reject neat explanations that collapse a complex process
   without support;
3. counterevidence survival — preserve meaningful exceptions and alternatives;
4. closure pressure — do not resolve more than the evidence permits;
5. reader inference budget — leave room for readers to connect supported ideas;
6. structural asymmetry — let the material determine section size and order;
7. author decision trace — show why a fact, example, or boundary mattered.

## Boundaries

- Do not fabricate personal noise, false starts, typos, memories, or emotional
  confession to simulate humanity.
- Do not force every piece into conflict, reversal, open ending, or human-values
  uplift. Those are options only when the material supports them.
- Do not treat surface metrics or detector scores as authorship proof.
- For `verbatim`, preserve source text. For `microcopy`, optimize clarity and
  brand fit. For `deterministic-output`, validate correctness and completeness.

## Meeting follow-ups and cowork output

This Skill drafts text the user will send under their own name after a meeting,
working from notes an AI wrote about that meeting. The ledger is therefore
stricter than for an essay:

- Every sentence in the notes is second-hand. Treat s / c / n items as “the notes
  record that…”, never as a participant's direct quote. `preserve_verbatim`
  covers the wording of to-dos, table cells, names, and numbers as the notes give
  them; it does not turn them into verified facts.
- The assistant's commentary (「解读」) is neither `author_positions` nor
  `firsthand_evidence`. It may guide what to ask the user. It must not appear in
  a brief as a fact about someone's intent, and never in outward text.
- `author_positions` — what the user agrees to, refuses, prices, schedules, or
  promises — may come only from notes the user has confirmed in this
  conversation, statements in the current request, the user's own materials, or
  Profile records. Otherwise use a visible placeholder such as 【待确认：交付时间】.
- `firsthand_evidence` about the user's own track record (class sizes, prices,
  refunds, past work) requires the user's materials or confirmation. The notes
  may have misheard a number: cite the id and mark 【待核对】 until confirmed.
- Statements about the other party keep the strength the notes give them. An
  inquiry stays an inquiry; a suggestion stays a suggestion.
- `counterevidence`: conflicts between the summary, the cards, and the live notes
  are listed side by side with their ids. Unresolved objections and conditions
  stay visible instead of being folded into “双方达成共识”.
- `open_questions`: the meeting date, the verbatim wording, screen shares, the
  meeting chat, and anything said afterwards are unseen inputs. Say so whenever
  they could change the answer.
- Work products (outlines, proposals, quotes) take their substance from the
  user's materials. The notes only define what was asked for and what the other
  party cares about; do not expand a phrase from the notes into invented detail.
