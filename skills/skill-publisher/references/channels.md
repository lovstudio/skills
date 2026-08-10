# Channel Adapter Contract

Each publishing channel is an independent adapter. A multi-channel request runs
selected adapters separately and aggregates evidence only at the end.

## Required adapter fields

Before implementing or executing a new adapter, establish:

1. Stable channel ID and current official display name.
2. Official documentation and public product URL.
3. Whether the result is a package, personal-library import, private listing,
   public marketplace listing, or live hosted page.
4. Required account, credentials, source locator, metadata, icon, examples, and
   commercial fields.
5. Deterministic preparation and validation commands.
6. External actions such as repository creation, upload, review, or submission.
7. Observable completion evidence and rollback path.

## Adapter directory convention

Keep channel state outside canonical Skill source:

```text
<publisher-profile-root>/
└── <channel-id>/
    └── <skill-name>/
        ├── metadata.json
        ├── icon.svg
        └── release.json

<publisher-output-root>/
└── <channel-id>/<skill-name>/<version>/
```

Do not add platform frontmatter, credentials, upload state, or generated archives
to the source repository.

## Execution states

- `prepared`: metadata and artifacts exist locally and pass local validation.
- `uploaded`: bytes reached a target account or submission endpoint.
- `installed`: a personal library shows the Skill as usable.
- `listed`: a marketplace record exists.
- `live`: intended users can access the expected public version.
- `verified`: the adapter-specific completion gate passed.

Never collapse these states into a generic success label.

## Adding a channel

Use current official sources when platform names, URLs, schemas, review policies,
or APIs may have changed. Add one focused reference and deterministic helper only
after the official contract and completion signal are known. Illustrative user
names for a platform are discovery clues, not final identifiers.
