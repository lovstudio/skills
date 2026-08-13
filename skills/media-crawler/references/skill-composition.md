# Skill Group Composition

## Nearby Skills Inspected

- `lov-media-fetch`：输入是片名、版本偏好、Magnet/Torrent 或长视频检索需求；输出是经过版本、字幕和文件流验证的电影/剧集。它不处理普通网页或社交媒体单链接，因此不是重叠能力。
- `lov-media-creator`：输入是已经存在的录屏、视频、音频和剪辑 brief；输出是剪辑成片、封面、EDL 和质检报告。它消费本 Skill 的本地视频，但不负责来源解析。
- `lov-video-chapter`：输入是本地视频与 SRT/VTT；输出是章节工程、透明叠加层或压制成片。它是可选下游。
- `lov-publish-wechat-channels`：输入是已质检的本地成片；输出是视频号发布状态与线上回读。它与下载方向相反，不组成默认流水线。
- `media-use`：提供通用媒体处理知识；没有“单链接 → 已验证本地文件”的完整验收，不作为依赖。

## Atomic Handoffs

| Classification | Owner | Input artifact | Output artifact | Acceptance boundary |
| --- | --- | --- | --- | --- |
| core atom | `lov-media-crawler` | one authorized public media URL | local media file + JSON report | payload exists and container/stream checks pass |
| upstream atom | user/browser session | platform login or Yuanbao authorization | reusable local session/credential | credential works without being printed or placed in Profile |
| downstream atom | `lov-media-creator` | verified local video | publish-ready edited video | editing, audio and render QC pass |
| downstream atom | `lov-video-chapter` | verified local video/subtitles | chapter project/overlay | timeline and render checks pass |
| downstream atom | `lov-publish-wechat-channels` | publish-ready video | platform publication + readback | real platform readback exists |

No sibling Skill is required at runtime. Handoffs are explicit local files or login/session artifacts.

## Overlap Decisions

- Keep `lov-media-fetch` focused on title discovery, edition selection, swarm transport and subtitle verification. A supplied social-media URL belongs here, even though both workflows end in a local video.
- Do not absorb editing, transcription, chaptering or publication; successful download is a stable boundary.
- MediaCrawler is an optional upstream engine and external checkout, not an embedded module. The video号 adapter is owned here because the open-source MediaCrawler platform list does not include WeChat Channels.

## Composition Decision

This is a **Single Skill**. Platform detection, authorization, resolution, transfer and verification are stages of one user-visible outcome and share one report contract. They are not independently useful agent outcomes that justify a Skill Kit. MediaCrawler and optional downstream Skills remain artifact-level integrations rather than hidden sibling dependencies.
