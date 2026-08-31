# Article State Contract

Use this internal contract to separate article intelligence from browser implementation. Capture only fields required by the current task.

```json
{
  "source": {
    "url": "ARTICLE_URL",
    "state": "editable",
    "adapter": "ADAPTER_ID"
  },
  "metadata": {
    "title": "",
    "digest": "",
    "author": "",
    "source_url": ""
  },
  "body": {
    "text": "",
    "html": "",
    "word_count": 0,
    "headings": [],
    "images": []
  },
  "cover": {
    "url": "",
    "asset_name": "",
    "wide_preview_ok": false,
    "square_preview_ok": false
  },
  "blocks": {},
  "observed": {
    "saved": false,
    "reloaded": false
  }
}
```

## Snapshot rules

- Store the snapshot in a temporary task location unless the user requests an artifact.
- Redact cookies, tokens, account IDs, unpublished URLs, and private paths.
- Keep before and after snapshots structurally comparable.
- Record visible facts, not inferred editor state.
- Represent repeated content blocks with `count`, stable visible text, and relative anchor when relevant.

## Mutation plan

```json
{
  "operation": "insert|replace|delete|read|cover",
  "target": "blocks.prompt",
  "anchor": "before:blocks.brand_endcap",
  "allowed_changes": ["body.word_count", "blocks.prompt*"],
  "required_results": {
    "blocks.prompt.count": 1,
    "observed.saved": true,
    "observed.reloaded": true
  }
}
```
