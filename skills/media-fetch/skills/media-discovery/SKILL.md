---
name: lov-media-discovery
description: >
  识别电影或剧集并从多个独立渠道收集、去重、归一化可下载候选；适用于“帮我找这部片的不同版本”、"search releases for this title"，输出可审计的候选清单。
license: MIT
metadata:
  author: contributors
  version: "0.4.0"
  tags:
    - media-search
    - dht
    - candidate-normalization
  compatibility: "Agent runtime with web research; optional qBittorrent search API, Rats Search, and Torrent inputs."
  dependencies:
    - python
---

# Media Discovery

Identify the requested work before collecting releases, then return normalized,
deduplicated candidates with evidence kept separate from search-result claims. Keep
Magnet, local Torrent, and remote `.torrent` inputs usable for later transport choice.

## Triggers

### Activate when

- 用户说“帮我找这部片的不同版本”“找导演剪辑版的下载候选”。
- 用户希望比较同一影片的多个 Magnet、Torrent 或发布版本。
- The user asks to search releases for a title or find several downloadable candidates.

### Do not activate when

- 用户已经给出唯一链接且只要求立即下载。
- 用户只询问剧情、影评、演员或上映日期。
- The user asks only to verify an existing local media file.

## Workflow (MANDATORY)

### Step 0: Load the shared contract

- Resolve `KIT_DIR` and read `$KIT_DIR/references/candidate-schema.md` plus
  `$KIT_DIR/references/user-config.md`.
- Establish the output JSON path before searching.

### Step 1: Disambiguate the work

Resolve canonical title, original title, year, media type, season/episode, and likely
alternate spellings. Ask only if two different works remain plausible after research.

### Step 2: Establish edition truth

Collect reliable evidence for known cuts and their runtimes: theatrical, original,
director's cut, extended, uncut, complete, restoration, or regional variants. Record
the source and confidence; do not treat a release filename as authoritative.

### Step 3: Search independent paths

Use at least two available paths:

1. direct web research or catalog/index queries;
2. a local DHT index such as Rats Search;
3. user-supplied Magnet, Torrent, hash, or URL inputs;
4. optional `scripts/qbittorrent_search.py` across enabled, reviewed search plugins.

Run independent searches in parallel when the environment supports it. Use title,
original title, year, edition terms, resolution, and subtitle markers as separate
queries; avoid one over-constrained query that hides viable candidates.

### Step 4: Normalize and deduplicate

- Emit UTF-8 JSON matching `$KIT_DIR/references/candidate-schema.md`.
- Deduplicate Magnet entries by normalized info hash, then by release identity. A
  Torrent URL may have a null hash until metadata is resolved; preserve the input.
- Preserve `source`, `source_url`, observed time, and edition evidence.
- Preserve advertised seeders separately from live observation fields; discovery data
  never counts as sustained download health.
- Infer filename features conservatively; mark inferred values with
  `metadata_confidence: filename`.
- Retain at least three healthy candidates when available so acquisition can race
  independent swarms.

### Step 5: Validate handoff

Check that each candidate has `id`, `name`, `uri`, source, size when known, and current
health fields when available. Report discovery gaps instead of inventing metadata.

## Dependencies

No mandatory external search service. qBittorrent search plugins and Rats Search are
optional adapters; direct web research remains available when configured adapters are
absent.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
