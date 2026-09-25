# 网易云 NCM 转 MP3 · NetEase NCM to MP3

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

把网易云音乐下载的 `.ncm` 解密成任何播放器都能打开的 MP3，写好标题、歌手、专辑
和封面；无损内容可以保留为 FLAC。已经转好的跳过，之前被其他工具转坏的自动修复。

## 为什么需要它

2025 年后网易云下载的不少 `.ncm` 在封面区后面预留了一段填充。`ncmdump-py 1.1.6`
和 `Johnserf-Seed/ncm2mp3 0.3.1` 都没有跳过这段填充，转出来的 mp3 是一整段噪声，
播放器直接报错，工具本身却显示成功。本 Skill 按 taurusxin/ncmdump 的封面帧读法
解析，并在写出前校验文件头和时长，坏结果不会落盘。格式细节见
[`references/ncm-format.md`](references/ncm-format.md)。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$SKILL_SKILLS_INSTALL_DIR/lov-ncm2mp3"
```

## 使用

对 Agent 说“把这个 ncm 转成 mp3”或 “convert these NCM files to MP3”即可。直接运行
命令行：

```bash
# 单个文件，输出放在旁边
uv run scripts/ncm2mp3.py "许巍 - 蓝莲花.ncm"

# 整个下载目录（含子文件夹），先预览再执行
uv run scripts/ncm2mp3.py ~/Music/网易云音乐 -r --dry-run
uv run scripts/ncm2mp3.py ~/Music/网易云音乐 -r

# 无损保留 FLAC；输出到独立目录并给出 JSON 结果
uv run scripts/ncm2mp3.py album/ --format original -o out/ --json
```

| 参数 | 作用 |
| --- | --- |
| `-r` | 递归子文件夹 |
| `-o DIR` | 输出到指定目录，递归时保留子目录结构 |
| `--format original` | 不转码，FLAC/M4A 保持原格式（MP3 与 FLAC 写标签） |
| `--force` | 覆盖任何同名输出 |
| `--no-cover-download` | 不联网取封面 |
| `--ffmpeg PATH` | 指定 ffmpeg；无损转 MP3 时必需，也用于核对非 MP3 输出是否完整 |
| `--dry-run` | 只解析并列出计划 |
| `--json` | 输出结构化结果 |
| `--log FILE` | 追加每文件一行日志，适合无终端入口 |

默认行为：
- 同名输出有效且时长吻合 → 跳过；
- 同名输出无法播放（例如旧工具转出的噪声）→ 替换；
- 同名输出能播放但时长不符（你自己的文件或被截断的旧结果）→ 标为 `conflict`，
  不动它，需要 `--force` 才覆盖；
- 源 `.ncm` 永远不改动；写出后按磁盘上实际的音频核对时长，下载中断的文件会失败
  而不是被当成完整文件。

退出码：0 成功；1 有 `failed` 或 `conflict`；2 参数或日志路径错误。

## Finder 右键

本 Skill 只提供命令行。要在 Finder 里右键使用，用 `lov-finder-action` 生成快速
操作，让它调用：

```bash
uv run "<skill>/scripts/ncm2mp3.py" --ffmpeg "$(command -v ffmpeg)" --log "$HOME/Library/Logs/ncm2mp3.log" "$@"
```

快速操作的运行环境没有常规 PATH，`uv` 与 `ffmpeg` 请写绝对路径。

## 用户 Profile（跨 session）

在 `skill.yaml` 中声明 `user-profile/v1`，从共享 Profile 读取本 Skill 的长期记录：
`records.output_format`、`records.output_dir`、`records.download_cover`。用户直接
说出的长期偏好（例如“以后无损的都保留 flac”）由 `scripts/profile_store.py` 写回。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 原子组合

没有其他 Skill 负责 NCM 解密；Finder 入口交给 `lov-finder-action`，转写交给
`lov-voice2srt`，都是可选的下游交接。详见
[`references/skill-composition.md`](references/skill-composition.md)。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md`：用途、依赖、风险、输出与维度地图。
- `cases/cases.json`：真实修复案例与命令行行为案例。
- `pricing-card.yaml`：免费，写明价值锚点、交付边界和复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
uv run --with pycryptodome --with mutagen python3 tests/test_ncm2mp3.py
```

## 依赖

- Python 3.9+，pycryptodome，mutagen（`uv run` 自动安装）
- FFmpeg：把 FLAC/M4A/OGG/WAV 转成 MP3 时必需；也用于核对非 MP3 输出是否完整
- PyYAML：仅 `validate_skill.py` 需要

## License

MIT。仅用于对自己已下载曲目的个人格式转换。
