---
name: lov-media-fetch
description: >
  自动检索、比较并下载电影、剧集或其他长视频，结合 qBittorrent 与 aria2 做多源测速、可恢复续传、慢源切换、容量预检、剪辑版核验与字幕验收；适用于“帮我找并下载这部电影”、"find and download the best release"。
license: MIT
metadata:
  author: contributors
  version: "0.3.0"
  tags:
    - media-discovery
    - release-selection
    - download-orchestration
    - quality-control
    - transport-fallback
    - resumable-download
    - subtitle-handoff
  card_standard: "lovstudio/skill-card/v1"
  compatibility: "Portable Agent Skills format; Python 3.9+, qBittorrent 5.x Web API, aria2 optional, and ffprobe recommended."
  dependencies:
    - python
    - pyyaml
    - qbittorrent
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
- Use qBittorrent for discovery and first probes, then hand the same Magnet or Torrent
  input to aria2 when the source is healthier there. Reuse the `.aria2` continuation
  state and record every transport switch; do not create a second full payload by
  accident.
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

1. Resolve `SKILL_DIR`, `KIT_DIR`, configuration, qBittorrent and aria2 availability,
   and `ffprobe`. Treat aria2 as the resumable fallback transport.
2. On first use, bootstrap missing stable dependencies through the platform's native
   package manager. Keep qBittorrent's WebUI on loopback and its credential in the
   operating system credential store. Reuse an existing compatible client instead
   when present; do not put secrets in profile or reports.
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
the qBittorrent search API, a local DHT index such as Rats Search, direct web research,
or user-supplied links. Deduplicate by info hash and canonical release identity. Preserve
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

1. Probe up to the configured concurrency in an isolated job directory.
2. Observe warm speed, sustained speed, availability, peers, metadata readiness, and
   ETA; a short burst alone does not win.
3. Pause non-winners, move the winner to the final destination, and continue polling.
4. If the winner stalls beyond the configured threshold, pause it and first try the
   next proven candidate. When the same Magnet/Torrent is better served by another
   transport, run `scripts/aria2_acquire.py` with the same input and job identity so
   partial state can continue. Use DHT, PeX, LSD, configured trackers, and direct
   connections; record the reason, backend, and observed rate for each switch.
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
- qBittorrent 5.x with WebUI enabled for integrated search and first acquisition.
- aria2 1.36+ for resumable fallback acquisition; it is optional when qBittorrent is healthy.
- Search plugins or another discovery adapter for title search.
- `ffprobe` from FFmpeg for final stream and duration inspection.
- Optional Rats Search for independent DHT discovery.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
