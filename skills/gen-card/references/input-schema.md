# Card input contract

`lov-gen-card` accepts one UTF-8 JSON object. The current bundled preset is
`art-system-card`, a 2:3 editorial knowledge card with one independent visual.

## Required fields

| Field | Type | Rule |
|---|---|---|
| `title` | string | Primary title; automatically fitted, never baked into the visual |
| `subtitle` | string | Secondary-language title |
| `visual.path` | string | Local image path, relative to the input JSON or absolute |
| `background` | string | Short context paragraph |
| `prompt` | string | Copyable generation prompt; use `[SUBJECT]` as the replaceable subject slot |
| `scenarios` | string list | One to six practical uses |
| `ratings` | object list | One to five editorial ratings; each score is an integer from 1 to 5 |

## Optional fields

- `series.name`, `series.subtitle`, `number`, `category`, and `language`.
- Visual alt text and two captions under `visual`.
- `brand.name`, `brand.site`, `brand.logo`, or `brand.enabled: false`.
- Three six-digit theme colors: `accent`, `accent_2`, and `accent_3`.
- English and secondary labels for Background, Prompt, Profile, and scenario.

The explicit input wins over the project context and shared Profile. Brand name,
site, and logo may fall back to `user-profile/v1`; the reusable source never
contains a private absolute path.

## Content limits

- Keep the background to roughly 45-110 Chinese characters or 35-80 English words.
- Keep the prompt to roughly 20-70 words plus model parameters.
- Use a 4:3 visual without text, badges, logos, or layout chrome.
- Ratings are editorial judgments, not objective facts. Label them accordingly.
- When cards are compared as a series, keep rating labels, order, and semantics identical
  across every card. Three to five shared dimensions are recommended for a radar chart.

The browser fit routine reduces title, body, prompt, and spacing within guarded
limits. If content still overflows, PNG export fails instead of silently clipping.
