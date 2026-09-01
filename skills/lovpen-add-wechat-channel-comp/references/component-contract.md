# WeChat Channels Component Contract

## Accepted input

Exactly one of these forms is accepted:

1. A complete or partial HTML document containing exactly one
   `mp-common-videosnap` start tag.
2. One complete Lovpen directive beginning with `::wechat-channels`.

The CLI does not fetch WeChat preview URLs and does not execute scripts embedded in HTML.
Only the custom element's attributes are read.

## Canonical fields

| DSL field | Native HTML attribute | Rule |
| --- | --- | --- |
| `id` | `data-id` | Required, non-empty |
| `nonce-id` | `data-nonceid` | Required, non-empty |
| `username` | `data-username` | Required, non-empty |
| `nickname` | `data-nickname` | Required, non-empty |
| `description` | `data-desc` | Required field; value may be empty |
| `cover` | `data-url` | Valid HTTP or HTTPS URL |
| `avatar` | `data-headimgurl` | Valid HTTP or HTTPS URL |
| `width` | `data-width` | Positive integer |
| `height` | `data-height` | Positive integer |

HTML output also fixes `data-pluginname` to `mpvideosnap`, `data-type` to `video`,
and `draggable` to `true`. Editor-only selection classes are not retained.

## Markdown output

The Markdown result is one self-contained directive. Attribute order is stable, text is
UTF-8, and backslash, quote, carriage return, line feed, and tab characters are escaped.
This is the persistence format used by Lovpen.

## HTML output

The HTML result contains one native `mp-common-videosnap` with the 11 key WeChat
attributes and a compact declarative Shadow DOM template. The template includes isolated
preview styles for a centered card, cover, play control, and overlaid Channels identity row;
the nickname must not fall outside the cover. Values are HTML-escaped at the output boundary.
The component is a fragment; full article styling remains the responsibility of Lovpen and
`lovpen-cli`.

## Existing-file write rule

The default insertion marker is:

```html
<!-- lovpen-wechat-channel -->
```

For an existing target, the marker must occur exactly once. The marker is replaced atomically
with the rendered fragment. Zero or multiple matches are errors. A new target contains only
the rendered fragment plus a final newline.

## Error contract

CLI input and write failures exit with status 2. Plain output uses
`ERROR [context_id]: message`; `--json` returns `ok: false`, the same stable `context_id`, and
the diagnostic message. The implementation never logs the full DOM or DSL on failure.
