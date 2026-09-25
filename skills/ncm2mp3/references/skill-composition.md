# Skill Group Composition

This record is required for every generated Skill. It prevents adjacent Skills
from becoming accidental duplicates or hidden dependencies.

## Nearby Skills Inspected

检索范围：本地 Skill 真源目录与已安装目录（共享安装位和宿主入口）。用 `ncm`、
`ncmdump`、`网易云`、`netease`、`cloudmusic`、ID3、`.lrc` 检索 SKILL.md 与正文，
均无命中；以下按路由契约和实际输入输出判断。

| Skill | 分类 | 依据 |
| --- | --- | --- |
| `lov-finder-action` | 可选下游 atom | 负责创建 Finder Quick Action（按参数接收的脚本 + workflow plist）。本 Skill 只提供被调用的命令行。 |
| `lov-voice2srt` | 弱关联可选下游 | 接收音频路径产出字幕。歌曲人声不适合 ASR，也不能当歌词来源，仅在用户明确要求时交接。 |
| `ffmpeg-video-editor` | 不组合 | 通用 ffmpeg 命令生成，只与转码子步骤重叠；不能解密 NCM、不写标签、不校验。本 Skill 直接调用 ffmpeg。 |
| `lov-media-crawler` | 不组合 | 平台矩阵不含网易云，不产出 `.ncm`。 |
| `lov-media-fetch` | 不组合 | 影视长视频下载，明确不做转码。 |
| `lov-media-preprocessor` | 不组合 | 实录视频增强与分段，只共享 ffmpeg。 |
| `lov-compress-video` | 不组合 | 视频压缩；借鉴了其输出放原文件旁、`--dry-run`、`--json`、时长不符即丢弃输出的门禁形态。 |
| `lov-migrate-camera-media` | 不组合 | 相机素材整卡复制；借鉴了临时文件写完再原子改名的写法。 |
| `lov-app-generator` | 不组合 | 其 Finder Quick Action 合同是签名 App 内的 Action Extension，面向可分发 App，个人 Automator 工作流不需要。 |
| `hyperframes-audio`、`media-use` | 不组合 | HyperFrames 合成内的混音与素材导入，不负责获取或转换音频文件。 |

## Atomic Handoffs

```text
用户已下载的 .ncm 文件或文件夹
        |
        v
lov-ncm2mp3（core atom）
  输出：源文件旁（或 --output-dir）同名 .mp3 / 原格式音频，带标签与封面；
        每文件 converted / skipped / planned / failed 与原因；退出码 0/1
        |
        +--> 可选：lov-finder-action
        |      输入：本 Skill 的命令行契约
        |        uv run <skill>/scripts/ncm2mp3.py [--ffmpeg <abs>] [--log <file>] "$@"
        |      说明：Quick Action 运行环境 PATH 很窄，ffmpeg 与解释器用绝对路径；
        |            菜单对任意文件可见时由脚本按 .ncm 后缀过滤（ignored）。
        |      验收归属：菜单出现与实际触发由 lov-finder-action 按其门禁验收。
        |
        +--> 可选：lov-voice2srt（用户明确要求转写时）
               输入：转换后的音频路径
```

本 Skill 的验收边界止于“可播放、标签正确的音频文件已原子写出”。

## Overlap Decisions

- 没有已有 Skill 负责 NCM 解密，不存在需要扩展或合并的重叠能力。
- 转码只作为内部步骤直接调用 ffmpeg，不依赖通用 ffmpeg Skill。
- 右键菜单的创建、修改、注册与回退属于 `lov-finder-action`；本 Skill 不内置
  workflow 模板，避免绕开其“不强制重启 Finder、不覆盖同名动作”等门禁。
- 歌词 `.lrc` 不在 NCM 文件内，需要访问网易云接口，当前不做。

## Composition Decision

`lov-ncm2mp3` 是 **Single Skill**。解析、解密、格式识别、可选转码、写标签、
校验与批处理共享同一份文件上下文，服务同一个用户结果：一个能播放的音频文件。
Finder 入口与转写都是独立可选的下游交接，不作为运行时依赖。
