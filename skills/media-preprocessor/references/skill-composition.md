# Skill composition

## Nearby Skills Inspected

2026-09-06 检查真源与已安装入口的实际输入输出：

| 能力 | 分类 | 契约与边界 |
| --- | --- | --- |
| lov-video-moments | downstream atom | 从视频选照片；交接增强视频和源映射，下游验收组图 |
| lov-media-creator | downstream atom | 接收片段/轨道做精剪、字幕、动画和平台成片 |
| lov-video-chapter | downstream atom | 消费定稿视频时间线和字幕生成章节条 |
| lov-voice2srt | upstream atom，可选 | 输出同源时间戳字幕/JSON，本任务复核其内容 |
| FFmpeg Video Editor | not composed | 通用命令配方，不拥有质量/价值判断和素材库验收 |
| lov-media-preprocessor | core atom | 全片诊断、连续增强、语义取舍、视频导出和源映射 |
| lov-branding-consistency | microcopy 门禁 | 仅新增段名/说明，不改原课件和转录 |

## Atomic Handoffs

原片/独立轨道 + 同源转录 + 已认可参考 → 预处理计划。转录由宿主供应或使用包内 whisper-cli / MLX 适配，无外部 sibling 源码依赖。

增强 MP4 段 + manifest 源映射 → 照片精选或正式剪辑；本 Skill 验收质量、取舍依据和音画完整性，下游验收自己的成品。

`creator_handoff.py` 将完整已渲染任务导出为 `media-preprocess-handoff/v1` 与 MP4 链接列表，核验源身份、计划、文件哈希、连续区间映射与可选完整解码。`lov-media-creator` 按原片秒数选独立片段、复用增强画面、从原片读取人声。分段本地时间从 0 起，删除区间保留为原片映射缺口。

定稿视频 + 定稿时间线字幕 → 章节条；不能把原片字幕直接套到删减后的版本。

## Overlap Decisions

不扩展照片 Skill 到整片转码：后者额外承担帧间稳定性和音画同步。media-creator 的出版、包装和字幕审校会扩大素材准备范围；本 Skill 是其可选上游。

## Composition Decision

Single Skill + standalone CLI。模式共享同一 source/analysis/plan，服务同一份素材库；脚本多模式不构成 Kit。转录可替换，精选、章节和成片可选，不复制出版流程或创建隐藏依赖。

原生 Metal 渲染是同一 CLI 的可选后端，消费同一数值 grade 与源区间；不是独立 Skill，也不代替语义审阅。
