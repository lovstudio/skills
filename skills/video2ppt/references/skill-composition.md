# Skill Group Composition

## Nearby Skills Inspected

| Skill | Routing contract | Relation |
|---|---|---|
| `lov-media-crawler` | 视频号、抖音、小红书、B 站等链接 → 已验证的本地媒体文件与 JSON 报告 | upstream atom |
| `video-frames` | 用 ffmpeg 抽取任意帧或短片段 | not composed：只抽帧，不做去重、分页和打包 |
| `slide-to-pptx` | 已有幻灯片图片 → PPTX/PDF | overlap（仅打包环节），见下文 |
| `lov-any2deck` / `baoyu-slide-deck` | 文字、Markdown、网页 → 新生成的幻灯片图片 | not composed：生成新内容，而本 Skill 还原视频里已有的幻灯片 |
| `lov-video-moments` | 视频 → 适合朋友圈的精选画面 | not composed：审美选图，不追求逐页完整 |
| `lov-video-chapter` | 字幕 + 视频 → 章节与章节条 | not composed：按语义分段，不输出幻灯片 |
| `lov-pdf2png` | PDF → 竖向拼接长图 | downstream atom（可选） |

## Atomic Handoffs

1. **上游 · 链接下载**：用户只给链接时，`lov-media-crawler` 产出 `status: verified` 的本地 MP4；
   本 Skill 只消费它报告中的 `output_path`。下载成败、授权与平台边界由 `lov-media-crawler` 验收。
   没有它时可用 `yt-dlp`，或请用户提供本地文件。
2. **核心 · 视频到幻灯片包**：本 Skill 负责采样、去重、代表帧选择、复核增删和打包。交付物是
   `OUTPUT_DIR` 下的 `frames/`、PPTX、PDF、`contact-sheet.jpg` 和 `manifest.json`，
   并以页数一致性和联系表复核作为验收标准。
3. **下游 · 长图分享（可选）**：需要一张长图发群时，把本 Skill 的 PDF 交给 `lov-pdf2png`。

## Overlap Decisions

- `slide-to-pptx` 也能把图片打包成 PPTX/PDF，但本 Skill 的 PPTX 要和 `manifest.json` 的
  时间戳备注、复核后的重新编号保持同步，所以打包逻辑内置在 `scripts/video2ppt.py` 里（基于
  python-pptx 和 Pillow，各几十行），不调用外部 Skill。
- `video-frames` 只负责抽帧；本 Skill 自己调用 ffmpeg，不依赖它。

## Composition Decision

做成 Single Skill：采样、比较、选帧、打包是同一结果的连续步骤，单独拆出来都没有独立价值。
链接下载作为可选的上游交接，不写入 `depends_on`，避免本地视频场景也被迫安装下载器。
