# Implementation Notes

## Runtime contract

The Skill wraps the local `xiaohongshu-cli` executable. Before a search, verify
that login is active:

```bash
xhs status
```

Expected output contains `authenticated: true` and `guest: false`. When login is
missing or guest-only, ask the operator to run:

```bash
xhs login --qrcode
```

The CLI stores its session under the user home directory. The Skill never reads
or prints cookie values.

## Search-only discovery

The deterministic local CLI is:

```bash
python3 scripts/xhs_search.py "QUERY" [options]
```

Supported options:

| Option | Meaning |
|---|---|
| `--must-contain TEXT` | Require a term in the note title. Repeat for every required term. |
| `--pages N` | Fetch up to N pages before local filtering. Default: 1. |
| `--sort general\|popular\|latest` | Search ordering. Default: general. |
| `--type all\|video\|image` | Note type. Default: all. |
| `--limit N` | Limit the matched rows after filtering. |
| `--timeout N` | Per-request timeout in seconds. Default: 120. |
| `--output PATH` | Write the result JSON to a file. |

## Collection for report mode

Use the collector when the request is a topic, plan, comparison, or research question. It discovers notes, reads their bodies, and writes an evidence corpus for synthesis:

```bash
python3 "$SKILL_DIR/scripts/xhs_collect.py" "冈仁波齐线路规划" \
  --pages 3 \
  --sort popular \
  --max-notes 12 \
  --delay 1.8 \
  --output xhs-evidence.json
```

The collector is deliberately partial-safe: individual note-read failures are
recorded in `meta.errors`, while successful notes remain usable. Never treat an
empty or partial corpus as a complete report.

## Examples

Search one page without a title filter:

```bash
python3 scripts/xhs_search.py "转山" --sort popular
```

Require two terms in the title and scan three pages:

```bash
python3 scripts/xhs_search.py "转山" \
  --must-contain "冈仁波齐" \
  --must-contain "转山" \
  --pages 3 \
  --sort popular \
  --output xhs-result.json
```

After saving a file, the script prints a short confirmation with the saved path
and match count.

## Output format

The result envelope contains:

```json
{
  "ok": true,
  "meta": {
    "query": "转山",
    "pages_requested": 3,
    "items_fetched": 60,
    "title_terms": ["冈仁波齐", "转山"],
    "matches": 2
  },
  "items": [
    {
      "id": "note-id",
      "title": "含两个关键词的标题",
      "author": "作者昵称",
      "published_at": "09-10",
      "likes": 128,
      "comments": 9,
      "collects": 21,
      "shares": 3,
      "url": "https://www.xiaohongshu.com/explore/note-id"
    }
  ]
}
```

The agent may summarize, rank, or compare these rows. It must not invent titles,
interaction counts, authors, or URLs beyond what the JSON contains.

## Failure handling

| Symptom | Action |
|---|---|
| `xiaohongshu-cli not found` | Install with `uv tool install xiaohongshu-cli`; verify with `xhs --version`. |
| `ok: false` and login error | Run `xhs login --qrcode` once, then retry. |
| `xhs search failed` | Keep stderr output; do not hide the API error. |
| Locale or Chinese garbling | Set `LANG=en_US.UTF-8` and `LC_ALL=en_US.UTF-8` in the shell. The script sets these for its child process. |

## Operational care

- Do not run many searches in parallel. The upstream CLI applies deliberate
  delays and backoff to reduce risk-control triggers.
- Keep the session fresh with `xhs status`; expired sessions should be renewed
  by the operator.
- Treat Xiaohongshu search output as source material, not authorization to
  republish or redistribute private content.
- Optional downstream handoff: pass a selected note URL to `lov-media-crawler`
  only when the operator explicitly asks to download media.
