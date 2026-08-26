---
name: lov-media-fetch
description: >
  Use when the user asks to find and download a film, series, or long video. 以 aria2 为默认传输后端，完成多源测速、续传、容量预检、版本核验与字幕验收；也适用于“帮我下载这部电影”。
license: MIT
compatibility: >
  Portable Agent Skills format; Python 3.9+, aria2 1.36+, and ffprobe recommended.
  qBittorrent 5.x Web API is an optional discovery, BitTorrent-management, and seeding adapter.
metadata:
  author: contributors
  version: "0.4.0"
  tags:
    - media-discovery
    - release-selection
    - download-orchestration
    - quality-control
    - aria2-primary
    - optional-qbittorrent
    - resumable-download
    - subtitle-handoff
  card_standard: "lovstudio/skill-card/v1"
  dependencies:
    - python
    - pyyaml
    - aria2
    - ffprobe
---

# Media Fetch

Turn one natural-language request into a verified local media file. Search broadly,
identify the actual cut, balance picture quality against size, check storage before
transfer, race viable sources, monitor the winner, recover from stalls, and inspect
the completed file.

## Triggers

### Activate when

- 用户说“帮我找并下载这部电影”“下载导演剪辑版，画质好一点但别太大”“找带中英字幕的完整版”。
- 用户给出片名、年份、版本偏好，或已有 Magnet/Torrent，希望自动完成选择、下载和验收。
- The user asks to find and download the best release, fetch an extended cut, or download a compact high-quality copy with Chinese and English subtitles.

### Do not activate when

- 用户只想了解影片资料、比较不同剪辑或获得观看建议，不要求取得本地文件。
- 用户只要下载普通网页文件、软件安装包、网页视频片段或直播流。
- 用户明确要求发布、上传、转码压制或制作字幕；这些是下载完成后的独立任务。

## Product contract

- One request should normally run end to end without repeated confirmation.
- Prefer an edition whose identity is supported by runtime, release metadata, or
  file-level evidence. A filename alone is weak evidence.
- “Best” means the highest useful viewing quality inside the user's size and disk
  budget, not the largest file or highest advertised resolution.
- Default to embedded Simplified Chinese plus English subtitles. Treat filename
  claims as hints until streams or synchronized external subtitles are inspected.
- Ask the user only when title identity is ambiguous, editions contain materially
  different content, or the top candidates are close enough that taste decides.
- Never begin payload transfer before the destination capacity check passes.
- Keep observing an active job. A task added to a client is not a completed result.
- Completion means that the final local payload exists and the verification report is
  written. A client-reported 100% is only an intermediate signal.
- Keep advertised seeders, observed peers, metadata readiness, received bytes, and
  sustained speed as separate evidence fields. A large seeder count is not a speed
  promise.
- Use aria2 as the default transfer backend for direct URLs, Metalinks, Magnets, and
  Torrent inputs. Enable qBittorrent only when its search plugins, queue UI, swarm
  inspection, or long-term seeding materially helps the task. Record every backend
  choice and switch; do not create a second full payload by accident.
- A missing `zh-Hans` stream is a recoverable subtitle gap, not a reason to mislabel
  the media. The subtitle branch may consult `lov-subtitle-freedom-skill` for
  timestamp-preserving UTF-8 SRT handling. Its English-learning gloss and ASS modes
  stay opt-in; plain Chinese subtitle delivery remains a separate, clearly named SRT.

## User configuration

Resolve defaults through `$KIT_DIR/references/user-config.md`. On first use, show the
resolved output directory and preferences before persisting them. Keep credentials in
environment variables or the operating system credential store.

## Skill Kit modules

Load the selected module completely before acting:

- `$SKILL_DIR/skills/media-discovery/SKILL.md` — identify the title and collect normalized candidates from several independent discovery paths.
- `$SKILL_DIR/skills/media-selection/SKILL.md` — verify editions and rank picture, codec, size, audio, subtitles, health, and evidence.
- `$SKILL_DIR/skills/media-acquisition/SKILL.md` — capacity preflight, parallel swarm probing, winner selection, progress observation, stall recovery, and cleanup.
- `$SKILL_DIR/skills/media-verification/SKILL.md` — inspect the downloaded files, edition runtime, streams, subtitle coverage, completeness, and final path.

`kit.yaml` defines the available pipelines. Shared schemas and decision rules live in
`$KIT_DIR/references/`.

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve runtime and select a pipeline

1. Resolve `SKILL_DIR`, `KIT_DIR`, configuration, aria2 availability, and `ffprobe`.
   Detect qBittorrent as an optional capability; its absence must not block discovery,
   transfer, resume, verification, or reporting.
2. On first use, bootstrap missing stable aria2 and ffprobe dependencies through the
   platform's native package manager. When qBittorrent is explicitly enabled, keep its
   WebUI on loopback and its credential in the operating system credential store. Do
   not put secrets in profile or reports.
3. Preserve existing client tasks. Every task created by this Skill must receive a
   unique job tag and an isolated probe directory.
4. Select `full` for a title request, `choose` for comparison only, `download-known`
   for supplied links, `resume` for an existing job, or `verify` for a local file.
5. Read `$KIT_DIR/references/candidate-schema.md`, then validate all handoff JSON.

### Step 1: Resolve the requested work

Capture title, year, media type, season/episode when relevant, edition preference,
maximum size, destination override, audio/subtitle preference, and urgency. Infer
omitted values from the portable profile. Do not ask the user to choose tooling.

### Step 2: Discover independent candidates

Run the discovery module. Use at least two independent discovery paths when possible:
direct web or catalog research, a local DHT index such as Rats Search, user-supplied
links, or the optional qBittorrent search API. Deduplicate by info hash and canonical release identity. Preserve
a `.torrent` URL or local Torrent path even when its info hash is not known until
metadata resolution.

For title and edition truth, prefer distributor, studio, disc, catalog, or reliable
release metadata. Keep search-result claims separate from verified facts.

### Step 3: Rank releases and resolve genuine ambiguity

Run the selection module and `scripts/rank_candidates.py`. Apply
`$KIT_DIR/references/quality-policy.md`.

- Auto-select when one candidate clearly leads and its edition is supported.
- Show at most three concise choices when the output says `choice_required=true`.
- Explain only the user-facing tradeoff: edition/content, picture, size, subtitles,
  and current health. Do not expose internal scoring mechanics unless asked.

### Step 4: Preflight destination capacity

Resolve the destination, candidate size, probe concurrency, temporary probe budget,
fallback resume allowance, and free-space reserve. Run `scripts/storage_preflight.py`
before starting either backend.

If capacity is short, report available, required, and shortfall immediately. Offer the
best smaller candidate or a different destination, then wait for that user-facing
decision. Never silently consume the reserve.

### Step 5: Probe, select, and download

Run the acquisition module and `$KIT_DIR/references/acquisition-policy.md`.

1. Probe up to the configured concurrency in isolated per-candidate directories. Use
   aria2 by default and allocate distinct listen/RPC ports for concurrent jobs.
2. Observe warm speed, sustained speed, availability, peers, metadata readiness, and
   ETA; a short burst alone does not win.
3. Pause non-winners, move the winner to the final destination, and continue polling.
4. If the winner stalls beyond the configured threshold, pause it and first try the
   next proven candidate. Preserve the same aria2 job identity and `.aria2` state when
   restarting an input. Switch to qBittorrent only when it is enabled and measured
   evidence shows a healthier swarm or the user needs its queue/seeding behavior.
   Record the reason, backend, and observed rate for each switch.
5. If all candidates are slow, return to discovery for another wave.
6. Keep the terminal session alive and poll at intervals short enough to provide the
   user a progress update at least once per minute during active work.
7. Clean only exact job-tagged losing tasks and their isolated probe files after the
   final candidate is complete. Leave pre-existing client tasks untouched.

### Step 6: Verify the completed media

Run the verification module and `scripts/verify_media.py`.

- Confirm a readable video stream, non-zero duration, expected resolution and codec,
  audio tracks, subtitle streams, and duration close to the selected edition.
- Inspect every episode for episodic requests; a season folder is complete only when
  the requested episode set is present.
- When preferred subtitles are missing, search for a subtitle from the exact release
  or a synchronized subtitle checked against duration and scene boundaries. For a
  Simplified Chinese SRT handoff, preserve cue timing, UTF-8, source immutability,
  and adjacent naming as described in `references/subtitle-handoff.md`; do not create
  an English-learning gloss or ASS file unless explicitly requested.
- Recheck final free space and ensure no partial suffix remains on the primary file.

### Step 7: Report the result

Lead with completion status and the exact local path. Include title/edition, video and
audio summary, subtitle coverage, final size, advertised versus observed source
health, transport trace, elapsed time, and any remaining evidence gap. Distinguish
`download_status`, `verification_status`, and `subtitle_status`.

## References

- `$KIT_DIR/references/candidate-schema.md` — normalized candidate and decision JSON.
- `$KIT_DIR/references/quality-policy.md` — edition, picture, codec, size, language, and ambiguity rules.
- `$KIT_DIR/references/acquisition-policy.md` — capacity, probing, monitoring, switching, and cleanup rules.
- `$KIT_DIR/references/user-config.md` — portable defaults and secrets handling.
- `$KIT_DIR/references/subtitle-handoff.md` — Simplified Chinese SRT matching and the
  opt-in handoff to `lov-subtitle-freedom-skill`.

## Dependencies

- Python 3.9+ for deterministic helpers.
- aria2 1.36+ for primary HTTP(S), Metalink, Magnet, and Torrent acquisition.
- Optional qBittorrent 5.x with WebUI enabled for integrated search, BT management,
  queue visibility, or long-term seeding.
- Search plugins or another discovery adapter for title search.
- `ffprobe` from FFmpeg for final stream and duration inspection.
- Optional Rats Search for independent DHT discovery.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
