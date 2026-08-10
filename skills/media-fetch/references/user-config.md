# User Configuration

Media Fetch keeps portable preferences across runs while leaving passwords and private
tokens outside the profile.

## Resolution order

1. Current request or explicit CLI flag.
2. `MEDIA_FETCH_*` and `QBITTORRENT_*` environment variables.
3. `media_fetch` in the shared profile.
4. Defaults below.
5. One focused user question only when a remaining choice changes the output.

Shared profile:

```bash
${SKILL_PROFILE_PATH:-$HOME/.skill-publisher/skills/profile.json}
```

## Defaults

```json
{
  "media_fetch": {
    "output_dir": "$HOME/Downloads/Media",
    "quality_mode": "balanced",
    "max_movie_size_gib": 24,
    "max_episode_size_gib": 6,
    "reserve_free_gib": 15,
    "parallel_probes": 3,
    "probe_seconds": 180,
    "warmup_seconds": 60,
    "probe_budget_mib": 512,
    "slow_speed_mib_s": 1.0,
    "stall_seconds": 180,
    "max_search_waves": 3,
    "preferred_audio": ["original", "zh", "en"],
    "preferred_subtitles": ["zh-Hans", "en"],
    "preferred_editions": [
      "director-cut",
      "extended",
      "uncut",
      "complete",
      "theatrical"
    ],
    "transport_backends": ["qbittorrent", "aria2"],
    "aria2_binary": "aria2c",
    "aria2_listen_port": 53555,
    "aria2_max_peers": 200,
    "aria2_max_restarts": 2,
    "subtitle_repair": "match-exact-release",
    "qbittorrent_url": "http://127.0.0.1:8080",
    "qbittorrent_username": "admin"
  }
}
```

The default size cap is a guardrail, not a target. Explicit per-request values win.
Series packs use the aggregate requested episode size when that is known.

## First-run initialization

1. Run `python3 scripts/media_config.py show`.
2. Show the resolved output directory, caps, language preferences, and probe policy.
3. If the user already requested different values, pass them as flags.
4. Run `python3 scripts/media_config.py init --write` only after the values are visible
   in the conversation.
5. Preserve all unrelated profile keys.

## Environment overrides

```bash
export MEDIA_FETCH_OUTPUT_DIR="$HOME/Downloads/Media"
export MEDIA_FETCH_MAX_MOVIE_SIZE_GIB="24"
export MEDIA_FETCH_MAX_EPISODE_SIZE_GIB="6"
export MEDIA_FETCH_RESERVE_FREE_GIB="15"
export MEDIA_FETCH_PARALLEL_PROBES="3"
export MEDIA_FETCH_SLOW_SPEED_MIB_S="1.0"
export MEDIA_FETCH_TRANSPORT_BACKENDS="qbittorrent,aria2"
export MEDIA_FETCH_ARIA2_BIN="aria2c"
export MEDIA_FETCH_ARIA2_LISTEN_PORT="53555"
export MEDIA_FETCH_ARIA2_MAX_PEERS="200"
export MEDIA_FETCH_ARIA2_MAX_RESTARTS="2"
export QBITTORRENT_URL="http://127.0.0.1:8080"
export QBITTORRENT_USERNAME="admin"
export QBITTORRENT_PASSWORD="read-from-a-secure-source"
```

Do not place `QBITTORRENT_PASSWORD`, cookies, private tracker keys, or provider tokens
in committed Skill source or the shared profile.
