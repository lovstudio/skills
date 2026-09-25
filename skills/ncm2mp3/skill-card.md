# 网易云 NCM 转 MP3 · NetEase NCM to MP3 · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

把网易云音乐客户端下载的 `.ncm` 解密成普通播放器能直接打开的音频。默认输出带
标题、歌手、专辑与封面的 MP3，可保留 FLAC 无损；支持文件夹批量处理，自动跳过
有效结果、替换损坏结果。

## Owner

Local skill contributors；联系本地 Skill 源目录维护者。

## License / Terms

MIT。被解密的音频及其版权归原权利人，本 Skill 只用于用户对自己已下载曲目的
个人格式转换。

## Use Case

- 受众：在网易云音乐下载了歌曲、想在其他播放器、车载或剪辑软件里使用的个人用户。
- 输入：单个 `.ncm`、多个文件或包含 `.ncm` 的文件夹。
- 任务：转成带封面的 MP3；递归处理下载目录；无损保留为 FLAC；修复旧工具转坏的结果。

## Deployment Geography

Global。本地运行，Python 3.9+（推荐 uv）；可选地由 Finder 快速操作包装调用。

## Requirements / Dependencies

- 无凭据。
- pycryptodome、mutagen（`uv run` 按脚本头部声明自动安装）。
- FFmpeg（含 libmp3lame）：把 FLAC/M4A/OGG/WAV 转成 MP3 时必需；也用于核对非 MP3 输出是否完整。
- 网络：仅在 NCM 内没有封面时下载网易云封面，可用 `--no-cover-download` 关闭。

## Known Risks and Mitigations

| 风险 | 缓解 |
| --- | --- |
| 解析错位写出噪声 mp3（旧工具的真实故障） | 按封面帧长度跳过填充；按文件头识别格式；实测时长与元数据相差超过 2%（0.5 到 3 秒）即丢弃 |
| 覆盖用户已有同名文件 | 只自动替换无法播放的输出；能播放但时长不符的标为 conflict 不动；同批次重名输出不互相覆盖；`--force` 仅在用户明确要求时使用；源文件只读 |
| 下载中断的文件被当成完整文件 | 按磁盘上实际音频核对时长（MP3 字节数与码率，其他格式 ffmpeg 解复用），不信任容器声明的总时长 |
| 中断或并发留下半成品 | 进程专属隐藏临时文件 + 原子替换；SIGTERM 清理并结束 ffmpeg |
| 下载的封面不是图片或网络缓慢 | 只接受 JPEG/PNG；8 秒超时；失败不影响音频；可关闭联网 |
| 被用于分发受版权保护的音乐 | 分发、上传、售卖请求不激活 |

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [NCM format and failure table](references/ncm-format.md)
- [Skill group composition](references/skill-composition.md)

## Skill Output

- 类型：可播放的音频文件，以及每文件处理结果与汇总。
- 格式：MP3（ID3v2.3 + 封面）；FLAC（Vorbis 标签 + 封面，`--format original`）；JSON（`--json`）。
- 参数：输出格式、递归与输出目录、覆盖策略、是否联网取封面、ffmpeg 路径与日志文件。
- 校验：解密后文件头为已知音频格式；按实际音频计算的时长与元数据相差不超过 2%（0.5 到 3 秒）；原子替换；退出码 1 表示有 failed 或 conflict，2 表示参数或日志路径错误。

## Skill Version

0.1.0

## Ethical Considerations

只读取用户指定的本地文件，源文件不改动；唯一的网络请求是访问 NCM 元数据里网易
云的封面地址，可关闭；不上传、不采集内容；只服务个人格式转换，不协助分发受版权
保护的音乐。

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json). Every case must show Input → Prompt → Output.

- 修复本机快速操作转出的 6 个无法播放的 mp3：10 个真实 `.ncm` 与独立实现逐字节
  一致，0 解码错误。
- Skill 命令行批量、跳过、修复、冲突行为与 13 个回归用例。

### Dimension Map

| 维度 | 证据 | 分数 |
| --- | --- | --- |
| 解密正确性 | 10/10 音频流 md5 与独立解码器一致，时长误差小于 1 毫秒 | 未评分 |
| 结果与源文件安全 | 错位与截断不产出、有效跳过、损坏替换、并发与中断回归 | 未评分 |
| 格式兼容 | MP3/FLAC 负载、dj 元数据、PNG 封面、原格式保留；合成 M4A/OGG/WAV | 未评分 |
| 处理速度与内存 | 6 个文件共 76.1 MB 含封面下载 0.75 秒；86 MB FLAC 负载峰值内存 30–57 MB | 未评分 |

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). 免费：纯本地工具，无托管与模型成本。

### Distribution

- 付费渠道（`workbuddy`、`skillpay`）：无。
- 免费渠道：MIT 源码。本地源已验证并安装到本机 Skills 目录；尚未发布到 `github`、
  `lovstudio` 或任何其他渠道。
