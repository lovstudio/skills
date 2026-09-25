# Skill Group Composition

This record is required for every generated Skill. It prevents adjacent Skills
from becoming accidental duplicates or hidden dependencies.

## Nearby Skills Inspected

| Skill | Routing contract | Classification | Decision |
| --- | --- | --- | --- |
| `lov-search-file` | 从本机 AI 对话记录追溯某次会话交付的文件，靠 transcript 证据定位 | not composed | 输入是“对话线索”，输出是带会话证据的候选路径；本 Skill 输入是“目录范围”，输出是磁盘盘点。两者互不替代，在 Triggers 里明确分流。 |
| `lov-video-moments` | 从一个视频抽帧、筛选、美化成照片组 | optional downstream atom | 用户先用本 Skill 找到“那段课程实录在哪、多大”，再把路径交给它。交接物是文件路径。 |
| `lov-media-creator` / `lov-media-preprocessor` | 剪辑、增强、分段视频 | optional downstream atom | 同上，本 Skill 只负责找到源文件，不做任何转码或剪辑。 |
| `lov-migrate-camera-media` | 相机卡整卡迁移与校验 | not composed | 它面向挂载的相机卷，带复制与校验；本 Skill 只读，不搬文件。迁移完成后可用本 Skill 复核目标盘上的视频清单，但不是必经步骤。 |
| `lov-ataru-indexing` / `lov-search-chat` | AI 会话记忆索引与检索 | not composed | 同为“本地索引”思路，但索引对象是对话，不是文件系统。缓存设计各自独立。 |
| `lov-media-fetch` | 从网络下载影视资源 | not composed | 下载完成后的文件会被本 Skill 扫到，但没有需要声明的接口。 |

## Atomic Handoffs

```text
用户指定目录 / --global
        |
        v
lov-list-videos
  清单（table / json / paths / csv）+ 共享增量缓存
        |
        v  文件路径（可附 size / mtime / ffprobe 元数据）
optional: lov-video-moments        抽帧与照片组
optional: lov-media-creator        剪辑成片
optional: lov-media-preprocessor   增强与分段
```

本 Skill 拥有“视频在哪、多少、多大、多新、什么编码”的验收；下游 Skill 各自拥有
其产物的验收。没有上游 Skill：范围来自用户或 Profile 记录，不来自其他 Skill 的输出。

## Overlap Decisions

- 与 `lov-search-file` 的重叠只在“最终都返回文件路径”。判据是用户线索的类型：
  记得的是一段对话就走它，记得的是目录或“整台电脑”就走本 Skill。
- 系统自带的 `mdfind`（Spotlight）也能列视频，但它依赖 Spotlight 索引范围与权限，
  外接卷和被排除路径常常缺失，且不能提供“上次以来变了什么”的可控增量。本 Skill
  自己维护缓存，不封装 `mdfind`。

## Composition Decision

`lov-list-videos` 是 **Single Skill**。扫描、缓存、过滤、排序、ffprobe 补充都是同
一个用户可见结果（一份视频清单）的实现细节，没有独立成立的中间阶段。相邻能力都
是可选的下游交接，交接物是文件路径，不作为运行时依赖。
