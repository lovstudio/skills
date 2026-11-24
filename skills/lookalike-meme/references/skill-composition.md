# Skill Group Composition

## Nearby Skills Inspected

- `lov-spectacular-ps`：把真人照片修成环境人像大片，可附对比图。同样处理真人照片，但目标是写实美化，不做卡通化和表情包排版。不组合。
- `lov-image-creator`：按用途生成通用图像和图文布局。能力更宽，但没有同意、版权、报价记账门禁，也没有本版式。可作为不限版式的退路，不组合。
- `lov-image-decorator`：给现有图片加底栏和 Logo。与本 Skill 输出风格冲突（本版式禁止 Logo 水印）。不组合。
- `lov-event-poster`、`lov-gen-card`：HTML 排版出 PNG 的海报和知识卡片，排版手法相近，受众和版式不同。不组合。
- `lov-media-creator`、`lov-group-interview-media-creator`：剪辑视频的上游，可产出视频帧；本 Skill 自带 `prep_photo.py` 取帧，不依赖它们。可选上游。
- `lov-branding-consistency`：受众可见文案门禁，用于大标题。声明为依赖。

## Atomic Handoffs

- 上游（可选）：任意剪辑工程提供视频文件或截帧 PNG → 本 Skill 的 `prep_photo.py` 取帧裁剪。验收归本 Skill。
- 核心：真人照片 + 参考形象图 + 标题 → 卡通 PNG + 1080×1440 对比图 PNG。验收归本 Skill。
- 下游（可选）：成品 PNG 可交给 `lov-media-creator` 作为视频插图，或由用户自行发到群里。本 Skill 不负责任何外发。
- 文案门禁：大标题交给 `lov-branding-consistency` 做语境检查。

## Overlap Decisions

与 `lov-image-creator` 有生图能力重叠，但本 Skill 的价值在固定的同意/版权/报价门禁、只上传真人照片的生成约束和作者认可版式，保持独立，不扩展进通用生图能力。

## Composition Decision

Single Skill。取帧、生图、排版是同一个结果的三个确定步骤，单独拆出来都没有独立价值；外部 Skill 只作可选交接，不作隐式依赖。
