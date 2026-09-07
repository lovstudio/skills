# Website case contract

The service contract is `GET https://lovstudio.ai/api/skills/<id>/cases`.
Free and paid targets have the same contribution auth. The server owns the
canonical `cases/cases.json` array and its assets.

## Public case input for prepare

```json
{
  "id": "accepted-reading-handbook",
  "type": "case",
  "title": "A readable workshop handbook",
  "description": "Organized public workshop notes into a checked reading handbook.",
  "input": {"text": "Public workshop notes, 12 pages."},
  "prompt": "Keep the original text and organize headings and page numbers.",
  "output": {"items": ["A handbook with consistent sections and page numbers."]},
  "evidence": {
    "acceptance": "user-confirmed",
    "verified_at": "2026-09-07",
    "method": "The author checked every page against the original notes.",
    "privacy": "Only public workshop material is included.",
    "artifact_type": "other"
  }
}
```

This is a format example, not evidence of a real run. Replace factual fields with
the accepted result. Input/output objects contain text and/or items. Prompt is a
string. Artifact type is required: visual or other. Images, posters, charts and
slides require their final artifact as cover; gallery holds up to 3 more variants.

Optional case fields are author, cover and gallery. Unsupported fields are
rejected, including legacy session objects, translations, transcripts and prices.
A legacy record needs deliberate preparation and review; never silently convert
its paid Session.

## Submission envelope

`prepare` emits `{case: PUBLIC_CASE, images: [], consent: false, dryRun: true}`.
Optional `sessionUrl` is an existing public
`https://lovstudio.ai/yoda/session/yss_*` URL owned by the submitter; supported
detail parameters are concise and full. The server checks ownership and public
access. A well-formed URL alone proves neither. Linking does not upload a Session.

Local images become `{contentType, dataBase64}` entries; cover uses `upload:0`
and gallery references subsequent indices. Otherwise images must be public HTTPS
URLs without embedded credentials. Local paths and private image URLs are not
public evidence. The server persists uploaded images with the case.

Limits: ID 3–100 characters, title 2–120, description 5–1200, prompt/text up to
8000, up to 20 input/output items of 2000 characters each, author up to 80,
verification/privacy text 2–1200, image URLs up to 2000. At most 4 images,
1 MiB each, 2 MiB combined, 3 MiB request. Acceptance uses a real YYYY-MM-DD date.
The authenticated server remains authoritative for validation, image decoding,
target availability and quotas.

## Privacy and consent

Acceptance refers to this exact output. Use factual Input → Prompt → Output and
reviewable images. Never present planned work as completed. Redact credentials,
private paths, personal identifiers and unpublished customer material. Transcripts
do not belong in this JSON. Pattern checks do not replace explicit review.

Prepare/check never publish. Saved consent flags are ignored.
`publish --confirm SHA256` binds consent to the reviewed payloadFingerprint,
covering case content, image bytes and optional Session. Transport flags are
excluded. A fresh server preflight runs before the consent-bearing POST.

## Retries and completion

- Retry unchanged bytes and ID: timeout may follow a successful source commit.
  Duplicate success is safe; another payload under an existing ID is rejected.
  There is no website `--replace-existing` path.
- prepared: local import file only; offline form URLs are not yet verified.
- validated: authenticated server dry-run passed, no case written.
- published: source commit confirmed; report cacheRefreshed separately and retain
  the response's server fingerprint.
- live-verified: source JSON matches that server fingerprint, parent and case
  pages render the result, all images return non-empty image content, and any
  public Session is accessible without login.

Approval and server fingerprints differ. The latter covers the complete stored
case including server metadata. A dry-run's source fingerprint is transient;
only the published response is used for final source readback. If source JSON is
private, report verified public surfaces and partial verification without asking
for GitHub credentials.
