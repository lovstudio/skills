# 视频清单 · Video Inventory · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

列出指定目录或整台电脑里的全部视频文件，带大小、修改时间与可选的时长、分辨率、
编码。一份共享的增量目录缓存让重复扫描只花秒级时间：目录 mtime 未变就复用，
已缓存的视频只重新 stat，消失的目录自动剪枝。

## Owner

Local skill contributors；联系本地 Skill 源目录维护者。

## License / Terms

MIT。扫描到的视频文件及其元数据归用户所有，缓存只保存在本机 Profile 目录。

## Use Case

面向在本机和外接盘上积累大量视频素材的创作者、剪辑者与开发者。输入是一个或多个
目录，或 `--global`；输出是可过滤、可排序的视频清单，供清理、迁移、剪辑或抽帧前
决策使用。

## Deployment Geography

全球；本地运行，无网络请求。

## Requirements / Dependencies

- Python 3.9+，脚本仅使用标准库
- ffprobe（FFmpeg），仅 `--probe` 与 `--sort duration` 需要
- PyYAML，仅本地校验脚本需要
- macOS 读取部分 `~/Library` 子目录需要“完全磁盘访问”权限，脚本不绕过

## Known Risks and Mitigations

- 缓存过期漏掉原地改写：未变目录里的视频仍逐个 stat，`--full` 可强制重列。
- 全局扫描误入系统或应用内部目录：默认排除噪音目录、包目录、隐藏目录，不跟随符号链接。
- 缓存记录目录结构：仅存本机 Profile 目录，权限 0600，不进入源与发布渠道。
- `._` AppleDouble 副本被当成视频：一律跳过，测试覆盖。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Cache design](references/cache-design.md)

## Skill Output

table / JSON / paths / CSV 四种格式的视频清单；每条含路径、大小、修改时间，
`--probe` 时附时长、分辨率、编码、帧率、码率。stderr 摘要给出匹配总数、总大小、
目录访问数、复用数、剪枝数、错误数、用时与缓存路径，可用于复核增量是否生效。

## Skill Version

0.1.0

## Ethical Considerations

只读扫描，不移动、删除或上传任何文件；不采集视频内容，只记录路径与文件属性；
不绕过操作系统权限。

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json). Every case must show Input → Prompt → Output.

### Dimension Map

增量速度、结果正确、可移植、元数据深度四个维度，证据分别来自真实全局扫描计时、
回归测试、脚本依赖检查与 ffprobe 探测结果；分数状态见机器可读卡片。

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). 免费：纯本地只读工具，价值在于省去
每次全盘查找的等待。

### Distribution

免费渠道：MIT source。目前只完成本地源验证，尚未发布到 `github`、`lovstudio`、
`workbuddy` 或 `skillpay` 任一渠道。
