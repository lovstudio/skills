# 图片上云 · Image Uploader · Skill Card

## Description

`lov-upload-image` uploads existing local images through the user's configured PicGo
backend and returns public URLs. Given a Markdown document, it can preflight, deduplicate,
upload, and rewrite supported local image references into a new portable document.

## Owner

Maintained by the LovStudio Skills source repository maintainers.

## License / Terms

The source is MIT licensed. The user remains responsible for image rights, image-host
terms, storage cost, retention, and the consequences of making an image public.

## Use Case

The Skill serves writers, developers, documentation agents, and publishing workflows
that already use PicGo. Inputs are one or more local image paths or one Markdown file.
Outputs are public URLs, an ordered JSON mapping, or rewritten UTF-8 Markdown.

## Deployment Geography

It runs locally in any geography where the user's selected PicGo image host and returned
URLs are reachable.

## Requirements / Dependencies

- Python 3.8 or newer.
- A configured PicGo GUI/Core Server API or PicGo-Core CLI.
- Read access to input images and write access to the requested Markdown output.
- Image-host credentials remain inside PicGo. An optional Server secret comes only from
  an environment variable.

## Known Risks and Mitigations

- Private or unlicensed images can become public. The workflow uploads only explicit,
  user-authorized inputs and never crawls for additional files.
- A remote object may remain after verification or local-write failure. All local paths
  are validated first, and the result reports that remote rollback is unavailable.
- In-place edits can destroy content. New-file output is the default; explicit in-place
  mode creates a backup unless the caller explicitly disables it.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [PicGo integration](references/picgo-integration.md)
- [Markdown coverage](references/markdown-coverage.md)

## Skill Output

The CLI emits one plain URL, an ordered UTF-8 JSON mapping, or a UTF-8 Markdown document.
It verifies one-to-one input mapping, rejects non-HTTP(S) results, can check returned URLs,
and atomically writes Markdown only after complete upload success.

## Skill Version

0.1.0

## Ethical Considerations

The Skill does not inspect or persist PicGo credentials and does not treat possession of
a local path as proof that publication is allowed. Users control storage retention and
deletion in their configured image host.

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) records a real direct upload and a real Markdown
rewrite through the installed PicGo GUI Server. Both returned CDN URLs responded with
HTTP 200 during validation.

### Dimension Map

The machine-readable card records four named dimensions: URL/rewrite correctness, real
PicGo effectiveness, local document safety, and runtime portability. Evidence is present;
scores remain explicitly unassigned because no comparative benchmark was run.

### Pricing Basis

[`pricing-card.yaml`](pricing-card.yaml) keeps the Skill free because it is a local
orchestration layer over the user's existing PicGo and storage account. No hosted storage,
managed credential, or paid delivery channel is bundled.

### Distribution

- `lovstudio`: locally installed and verified.
- `github`: not published.
- `workbuddy`: not published.
- `skillpay`: not published.
