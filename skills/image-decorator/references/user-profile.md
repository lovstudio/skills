# User Profile contract

`lov-image-decorator` reads the shared `user-profile/v1` context on every run.

## Resolution order

1. Current CLI flags and request.
2. Current project context.
3. `skills.lov-image-decorator.records`.
4. Shared preferences and brand Profile.
5. Bundled safe defaults.

Supported Skill records are `default_caption`, `logo_path`, and
`default_format`. `logo_path` must resolve to a local raster image; the CLI does
not fetch remote logos. When no usable Profile Logo exists, the bundled verified
LovStudio mark remains the default.

## Persistence

Only a directly stated durable choice may be written:

```bash
python3 scripts/profile_store.py record \
  --skill-id lov-image-decorator \
  --path records.default_caption \
  --value '"Powered by lovstudio.ai/skill/image-decorator"' \
  --confirm
```

The command writes atomically and reports the canonical Profile path without
echoing secrets. Do not persist image contents, captions that belong to only one
asset, remote credentials, or inferred private paths.
