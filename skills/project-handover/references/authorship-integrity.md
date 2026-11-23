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

## Handover documents

A handover document is factual prose for a reader who was not there. Build its ledger as:

- `project_facts`: what the project files show (path, version, date written in a delivery note);
- `channel_facts`: what people said in chats, meetings and documents, each with time and speaker;
- `inferences`: mappings the writer made (which section a screenshot-only comment refers to, which version was sent
  when the message itself is not readable), written as inferences in the text;
- `gaps`: channels, images, voice notes or documents that could not be read;
- `preserve_verbatim`: client wording of requests, numbers awaiting confirmation, product names, identifiers;
- `forbidden_inventions`: approvals the client did not give, deadlines nobody set, who the recipient is when nobody
  said so, reasons behind a decision that were never stated.

Correct stale status in the sender's own notes when the channel shows otherwise, and say in the handover which
source was newer.
