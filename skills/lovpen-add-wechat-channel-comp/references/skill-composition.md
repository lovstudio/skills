# Skill Group Composition

## Nearby Skills Inspected

- `lovpen-cli` 接收完整 Markdown 并调用 Lovpen 的真实渲染器生成微信公众号内联 HTML
  或独立 HTML。它不接收原生视频号 DOM，也不负责把组件写入文章，因此是 Markdown
  结果的可选下游，不与本 Skill 重叠。
- `lov-publish-wechat-article` 接收已经准备好的文章与 Lovpen 微信复制态 HTML，负责草稿
  创建、回读和发布状态。它不拥有本地组件规范化，属于更下游的渠道能力。
- `baoyu-markdown-to-html` 把整篇 Markdown 排版为 HTML，但没有 Lovpen
  `::wechat-channels` 的输入、持久化和原生组件恢复契约，因此不组合。
- `lov-branding-consistency` 只审校本 Skill 的 README、错误提示等用户可见文本；根据
  依赖契约，它不得改写视频 ID、nonce、URL、描述或其他源数据。
- `lov-media-publisher` 和 `media-crawler` 面向媒体获取或视频号视频发布，不处理公众号
  文章中的 `mp-common-videosnap` 组件，属于相邻但不组合的能力。

## Atomic Handoffs

| Role | Owner | Input artifact | Output artifact | Acceptance owner |
| --- | --- | --- | --- | --- |
| Optional upstream | Lovpen Desktop/Obsidian or user | One native DOM or Lovpen DSL | Approved component input | Upstream owns component provenance and selection |
| Core | `lov-lovpen-add-wechat-channel-comp` | One DOM/DSL plus target format and optional marked file | Canonical DSL, native HTML fragment, or safely updated file | This Skill owns parsing, field fidelity, exact marker replacement and integrity evidence |
| Optional downstream | `lovpen-cli` | Markdown containing the canonical DSL | Full Lovpen HTML artifact | `lovpen-cli` owns article rendering and WeChat-copy fidelity |
| Optional downstream | `lov-publish-wechat-article` | Verified full article HTML and publication inputs | Draft or publication state | Publisher owns remote writes, readback and final channel state |

There is no required sibling-Skill call during the core transform.

## Overlap Decisions

The implementation does not copy Lovpen themes, article rendering, browser clipboard extraction,
or publishing transports. It owns only the small portable component contract. `lovpen-cli` remains
the canonical full-document renderer, and the publishing Skill remains the only owner of external
WeChat writes.

Generic Markdown-to-HTML Skills are intentionally not extended: their acceptance criterion is page
styling, while this Skill must preserve WeChat component identifiers and produce a native custom
element. Media acquisition and 视频号 publishing are separate because their artifact is a video,
not an Official Account article component.

## Composition Decision

This is a **Single Skill**. DOM parsing, DSL parsing, normalization, Markdown serialization, HTML
serialization and exact-marker insertion are modes of one deterministic transform and share one
field schema plus one acceptance criterion. Splitting them into embedded modules would add routing
without creating independently useful user outcomes. All external handoffs are optional and
artifact-based.
