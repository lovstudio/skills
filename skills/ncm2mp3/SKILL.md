---
name: lov-ncm2mp3
description: >
  把网易云音乐 .ncm 解密成能播放、带标题封面的 MP3（可保留 FLAC），批量处理文件夹并修复转出来是杂音的旧结果；不管下载歌曲或普通音频转码。Use when “ncm 转 mp3”“网易云的歌放不了” or “convert NetEase NCM to MP3”.
license: MIT
compatibility: "Portable Agent Skills format. Requires Python 3.9+ with pycryptodome and mutagen (uv run installs them from the script header). FFmpeg is required to turn FLAC/M4A payloads into MP3 and checks non-MP3 outputs for completeness. Cover download uses network unless disabled."
metadata:
  author: contributors
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - audio
    - ncm
    - netease-cloud-music
    - mp3
    - id3
---

# 网易云 NCM 转 MP3 · NetEase NCM to MP3

把网易云音乐客户端下载的 `.ncm` 解密成普通播放器能直接打开的音频：默认输出
MP3，写入标题、歌手、专辑和封面；FLAC 这类无损内容可以按原格式保留。输出与
源文件同名放在旁边，已经有效的结果自动跳过，之前转坏的结果自动替换。

新版网易云文件在封面区后面有一段预留填充，`ncmdump-py 1.1.6` 与
`Johnserf-Seed/ncm2mp3 0.3.1` 都没有跳过它，转出来的是一整段噪声。本 Skill 的
解析按 taurusxin/ncmdump 的封面帧读法实现，并在写出前校验格式和时长，坏结果
不会落盘。细节见 [`references/ncm-format.md`](references/ncm-format.md)。

## Triggers

### Activate when

- “把这个 ncm 转成 mp3。”
- “网易云下载的歌在别的播放器里放不了。”
- “把网易云音乐下载目录里的 ncm 全部转一下，子文件夹也要。”
- “之前转出来的 mp3 打不开，帮我修一下。”
- “无损的保留 flac，不要转码。”
- “Convert these NCM files to MP3.”
- “Help me play the songs I downloaded from NetEase Cloud Music in any player.”

### Do not activate when

- 要从网易云或其他平台下载歌曲、视频 → 不在本 Skill 范围；视频平台链接交给 `lov-media-crawler`
- 普通音频互转（FLAC、WAV、M4A 转 MP3）或剪辑、降噪 → 直接用 ffmpeg 或对应媒体 Skill
- 要把音频转写成字幕或文字 → `lov-voice2srt`
- 要新建或修改 Finder 右键菜单本身 → `lov-finder-action`（本 Skill 只提供被调用的命令）
- 要批量分发、上传或售卖解密后的歌曲 → 拒绝；本 Skill 只服务用户对自己已下载曲目的个人格式转换

## User Profile (cross-session)

Every generated Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and this
Skill's `skills.<skill_id>` namespace at the start of every run. Keep the source
portable: resolved personal values belong in the shared profile, never here.

When the user directly states a durable preference or brand fact, persist it
through `scripts/profile_store.py` and report the saved profile path. Put
Skill-specific values under `records.<field>`; use `brand.<field>` or
`user.<field>` for shared values. Do not persist inferred secrets or credentials.
See `references/user-profile.md` for the complete contract.

本 Skill 读取的长期记录（都可选）：

| 记录 | 含义 | 对应参数 |
| --- | --- | --- |
| `records.output_format` | `mp3`（默认）或 `original`（无损保留原格式） | `--format` |
| `records.output_dir` | 固定输出目录，默认放在源文件旁边 | `--output-dir` |
| `records.download_cover` | `false` 时从不联网取封面 | `--no-cover-download` |

## Skill Group Composition

Read `references/skill-composition.md` before deciding whether to invoke or
extend any adjacent capability. The record distinguishes optional upstream and
downstream handoffs from embedded Kit modules. Do not silently depend on a
sibling Skill that is not shipped with this source.

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and runtime context

- Use `SKILL_DIR` if the environment provides it.
- Otherwise infer the installed skill directory from the current skill context.
- 必须确认 `scripts/ncm2mp3.py`、`scripts/profile_store.py`、
  `references/ncm-format.md`、`references/skill-composition.md` 均存在。
- 运行方式按优先级选择：
  1. 有 `uv`：`uv run "$SKILL_DIR/scripts/ncm2mp3.py" ...`，依赖由脚本头部的
     PEP 723 声明自动准备。
  2. 没有 `uv`：`python3` 需能导入 `Crypto` 与 `mutagen`；缺失时脚本会给出
     `python3 -m pip install pycryptodome mutagen` 的提示，征得同意后再安装。
- 只有需要把 FLAC、M4A 等非 MP3 内容转成 MP3 时才要求 `ffmpeg`；找不到时改用
  `--format original` 或让用户安装。
- If a required resource is missing, name its expected relative path and stop
  before producing a partial result.

When running scripts manually:

```bash
export SKILL_DIR="/path/to/lov-ncm2mp3"
```

Resolve `context.profile` on every invocation. The precedence is current request,
project context, Skill-specific profile records, shared preferences, shared
brand/user profile, then safe defaults. A direct user statement about a durable
preference or brand fact should be saved with `scripts/profile_store.py record`
using `--confirm`, followed by a concise saved-path report.

### Step 1: Understand the requested outcome

- 确认输入是 `.ncm` 文件或包含 `.ncm` 的文件夹；目录默认只看当前层，用户说
  “子文件夹也要”时加 `-r`。目录扫描自动忽略 macOS 在外置盘上生成的 `._*.ncm`
  旁路文件。
- 把用户话语直接映射到参数，不要先跑一遍再问：
  - “转成 mp3 / 默认” → 不加参数
  - “无损的保留 flac / 不要转码” → `--format original`（网易云负载实际只有 MP3
    与 FLAC；若遇到 M4A/OGG 也会原样保留，但不写标签）
  - “输出到某个目录” → `--output-dir <dir>`（递归时保留子目录结构）
  - “别联网 / 离线” → `--no-cover-download`（封面不在文件里时就不写封面）
  - “之前转的放不了 / 修复” → 默认命令即可：有效结果跳过，损坏结果替换
  - “全部重新转、覆盖掉” → `--force`
- 同名旧输出按三种情况处理：无法播放（例如旧工具转出的噪声）→ 直接替换，这正是
  修复场景；有效且时长吻合 → 跳过；能播放但时长不符（用户自己的文件或被截断的
  旧结果）→ 标为 `conflict` 不动它，向用户说明后由用户决定是否 `--force`。
- `--force` 会覆盖任何同名输出，只在用户明确要求重转时使用。
- 源文件 `.ncm` 永远只读，不移动、不删除。

### Step 1.5: Analyze nearby Skills before implementation

- 先读 `references/skill-composition.md`。本 Skill 只负责“NCM → 可播放音频”；
  Finder 右键入口由 `lov-finder-action` 生成，它调用本 Skill 的命令行契约。
- 不要在这里做下载、剪辑、转写或上传。

### Step 2: Execute the workflow

1. 批量或不确定时先看计划：用与正式运行**完全相同的参数**，只多加 `--dry-run`。
   预演不写任何文件（包括日志与输出目录），缺 ffmpeg 等会导致正式运行失败的问题
   在预演里同样报 `failed`。

```bash
uv run "$SKILL_DIR/scripts/ncm2mp3.py" ~/Music/网易云音乐 -r --format original --dry-run
```

2. 转换（输出放在源文件旁边）：

```bash
uv run "$SKILL_DIR/scripts/ncm2mp3.py" "许巍 - 蓝莲花.ncm"
uv run "$SKILL_DIR/scripts/ncm2mp3.py" ~/Music/网易云音乐 -r
```

3. 常见变体：

```bash
# 无损保留原格式（FLAC 仍是 FLAC，写 Vorbis 标签与封面）
uv run "$SKILL_DIR/scripts/ncm2mp3.py" album/ --format original

# 输出到独立目录，结构化结果供后续统计
uv run "$SKILL_DIR/scripts/ncm2mp3.py" in/ -r -o out/ --json

# 离线，不下载封面
uv run "$SKILL_DIR/scripts/ncm2mp3.py" song.ncm --no-cover-download

# 给 Finder Quick Action 等无终端入口用：额外写一份日志
uv run "$SKILL_DIR/scripts/ncm2mp3.py" "$@" --log ~/Library/Logs/ncm2mp3.log
```

4. 用户说出长期偏好时写回 Profile，例如“以后无损的都保留 flac”：

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" record \
  --skill-id lov-ncm2mp3 \
  --path records.output_format \
  --value '"original"' \
  --confirm
```

### Step 3: Validate the deliverable

- 脚本自带门禁：解密后的文件头必须是 MP3/FLAC/M4A/OGG/WAV；写出后按磁盘上实际
  存在的音频计算时长（MP3 用字节数与码率，其他格式用 ffmpeg 解复用），与网易云
  记录相差超过 2%（至少 0.5 秒、至多 3 秒）即判失败，下载中断的文件因此不会被当成
  完整文件；结果先写同目录隐藏临时文件，校验通过才原子替换，失败不留下任何输出。
- 每个输入一行：`状态: 文件名 -> 输出路径 {详情 JSON}`，最后一行是汇总。状态有
  `converted`、`planned`（预演）、`skipped`（已有有效输出）、`conflict`（同名文件
  内容不同或同批次两个输入写同一输出）、`ignored`（非 `.ncm`）、`failed`。详情里
  `duration` 是实测时长；`cover` 为 `embedded` / `downloaded` / `existing` /
  `none` / `will download`（预演）；可能出现 `replaces`、`transcode`、
  `completeness: unchecked without ffmpeg`（无 ffmpeg 时非 MP3 输出未做完整性核对）。
- 退出码：0 全部成功或跳过；1 至少一个 `failed` 或 `conflict`；2 参数错误或日志
  无法写入（此时不处理任何文件）。文本模式下 `failed` 与 `conflict` 行写 stderr，
  `--json` 模式全部在 JSON 里。首次运行时 `uv` 可能在 stderr 打印依赖安装信息。
- 向用户报告：转换数、跳过数、失败数与原因、输出位置；抽查一个结果可用
  `ffprobe -v error -show_entries format=duration <file>` 或 macOS 的
  `afplay -t 3 <file>`。
- 失败原因的含义与处理见 [`references/ncm-format.md`](references/ncm-format.md)
  的“故障对照”。同一原因不要原样重试。
- 维护本 Skill 时（不是每次转换）校验可信记录与回归测试：
  `python3 "$SKILL_DIR/scripts/validate_skill.py" "$SKILL_DIR"`，
  `uv run --with pycryptodome --with mutagen python3 "$SKILL_DIR/tests/test_ncm2mp3.py"`。

## Dependencies

- Python 3.9+，`pycryptodome` 与 `mutagen`（`uv run` 按脚本头部声明自动安装）
- FFmpeg：把 FLAC/M4A/OGG/WAV 转成 MP3 时必需；`--format original` 时用于核对
  非 MP3 输出是否完整，缺失时照常输出并标注未核对
- 网络：仅在 NCM 内没有封面时访问元数据里的网易云封面地址，可用 `--no-cover-download` 关闭
- 无外部 Skill 依赖；交接见 `references/skill-composition.md`
