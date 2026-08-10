# Candidate and Decision Schema

All discovery adapters normalize into one UTF-8 JSON document. Unknown fields should
be omitted or set to `null`; do not invent zero values.

## Candidate manifest

```json
{
  "schema_version": "1.0",
  "query": {
    "title": "Example Title",
    "original_title": "Example Title",
    "year": 2026,
    "media_type": "movie",
    "season": null,
    "episodes": [],
      "requested_editions": ["director-cut", "extended"],
      "title_ambiguous": false,
      "edition_choice_required": false
  },
  "edition_facts": [
    {
      "edition": "director-cut",
      "duration_minutes": 132,
      "source_url": "https://example.com/release-record",
      "confidence": "primary"
    }
  ],
  "candidates": [
    {
      "id": "candidate-1",
      "name": "Example.Title.2026.Directors.Cut.2160p.HEVC",
      "uri": "magnet:?xt=urn:btih:0123456789ABCDEF0123456789ABCDEF01234567",
      "info_hash": "0123456789ABCDEF0123456789ABCDEF01234567",
      "transport_inputs": ["magnet"],
      "source": "adapter-name",
      "source_url": "https://example.com/result",
      "observed_at": "2026-08-08T00:00:00Z",
      "size_bytes": 12884901888,
      "seeders": 42,
      "leechers": 5,
      "resolution": "2160p",
      "video_codec": "hevc",
      "hdr": "hdr10",
      "edition": "director-cut",
      "duration_minutes": 132,
      "audio_languages": ["en", "zh"],
      "subtitle_languages": ["zh-Hans", "en"],
      "subtitle_verified": false,
      "source_health": {
        "advertised_seeders": 42,
        "observed_peers": null,
        "observed_at": "2026-08-08T00:00:00Z",
        "sustained_speed_bytes_per_second": null,
        "metadata_ready": false
      },
      "metadata_confidence": "filename",
      "trusted_source": false
    }
  ]
}
```

`source_url` may point to a description page while `uri` is the actual transfer input.
Never print private tracker query tokens in the user-facing result.

- `transport_inputs` may contain `magnet`, `torrent-file`, or `torrent-url`. Keep a
  Torrent URL or local path when `info_hash` is not available yet; fill the hash after
  metadata resolution instead of discarding the candidate.
- `source_health.advertised_seeders` comes from discovery. `observed_peers`,
  `metadata_ready`, and `sustained_speed_bytes_per_second` come from a live probe and
  must remain distinct.

## Normalization

- `edition`: `director-cut`, `extended`, `uncut`, `complete`, `theatrical`,
  `restored`, `regional`, or `unknown`.
- `resolution`: normalized vertical resolution such as `2160p`, `1080p`, `720p`.
- `video_codec`: `av1`, `hevc`, `h264`, `vp9`, or `unknown`.
- Language tags: prefer BCP 47 where available; normalize common `chs`/`zh-cn` to
  `zh-Hans`, `cht`/`zh-tw` to `zh-Hant`, and preserve `en`.
- `metadata_confidence`: `verified`, `release-record`, `filename`, or `unknown`.
- `info_hash`: uppercase hexadecimal when known. Deduplicate case-insensitively.
- `transport_inputs`: the inputs accepted by the acquisition layer; the same content
  can be resumed through qBittorrent or aria2 without changing release identity.

## Decision document

`scripts/rank_candidates.py` returns:

```json
{
  "schema_version": "1.0",
  "selected_id": "candidate-1",
  "choice_required": false,
  "reasons": [],
  "ranked": [
    {
      "candidate": {},
      "score": 118.4,
      "strengths": ["verified edition runtime", "efficient 2160p"],
      "warnings": []
    }
  ]
}
```

Acquisition must consume the complete `ranked` list so it retains tested fallbacks.
