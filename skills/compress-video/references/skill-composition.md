# Skill Group Composition

This record is required for every generated Skill. It prevents adjacent Skills
from becoming accidental duplicates or hidden dependencies.

## Nearby Skills Inspected

| Skill | Routing contract | Classification | Decision |
| --- | --- | --- | --- |
| `lov-list-videos` | 增量缓存列出目录或全局的视频文件 | optional upstream atom | 批量压缩前先用它挑出“最大的 / 最近的”候选，交接物是文件路径列表（`--format paths` 或 JSON）。 |
| `lov-media-creator` / `lov-media-preprocessor` | 剪辑成片、增强分段 | optional upstream atom | 它们产出成片或素材库，本 Skill 只负责把成片压到分发体积，不参与剪辑。 |
| `lov-media-publisher` | 发布视频到视频号或 B 站 | optional downstream atom | 压缩后的 MP4 作为上传输入。平台各有大小上限，用 `--target-size` 对齐。 |
| `lov-migrate-camera-media` | 相机卡整卡迁移与校验 | not composed | 迁移强调原样保存与校验，压缩会破坏原样；两者不应串联，避免误把压缩件当备份。 |
| `ffmpeg-video-editor`（第三方） | 把自然语言翻译成 FFmpeg 命令 | overlap, kept separate | 它只生成命令、不执行、不校验；本 Skill 负责选参数、执行、进度、体积与时长门禁、VMAF 与替换安全。两者定位不同，不合并。 |
| `baoyu-compress-image` | 图片压缩 | not composed | 对象不同，只在 Triggers 里分流。 |

## Atomic Handoffs

```text
optional: lov-list-videos            候选文件路径
optional: lov-media-creator 等        成片路径
                |
                v
lov-compress-video
  <stem>-compressed.mp4（或替换模式下的 <stem>.mp4）+ JSON 结果
                |
                v
optional: lov-media-publisher        上传压缩后的文件
```

本 Skill 拥有“压缩后文件可播放、时长一致、体积更小、画质达到门禁”的验收。上游
Skill 拥有源文件是否正确的验收，下游拥有发布状态的验收。

## Overlap Decisions

- 与第三方 FFmpeg 命令生成 Skill 的重叠只在“最终都调用 ffmpeg”。判据是用户要的
  是一条命令还是一个压好的文件；后者走本 Skill。
- 不把“找视频”做进本 Skill：范围与缓存逻辑已由 `lov-list-videos` 承担。

## Composition Decision

`lov-compress-video` 是 **Single Skill**。参数选择、编码、两遍模式、VMAF 门禁、
替换安全都服务同一个用户可见结果（一个压缩好的文件），没有独立成立的中间阶段。
相邻能力都是可选的、以文件路径交接的上下游，不作为运行时依赖。
