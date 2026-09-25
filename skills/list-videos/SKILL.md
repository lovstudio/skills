---
name: lov-list-videos
description: >
  用增量缓存扫描指定目录或全局（主目录与外接卷），秒级列出全部视频文件及大小、
  修改时间，可选 ffprobe 补时长、分辨率与编码。Use when 用户说“列出所有视频”
  “找视频文件”“哪些视频最大”或 “list all video files”。
license: MIT
compatibility: "Portable Agent Skills format. Requires Python 3.9+; macOS/Linux filesystem. ffprobe (FFmpeg) only for --probe. Standard library only."
metadata:
  author: contributors
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - video
    - file-search
    - incremental-cache
    - local-first
    - macos
---

# 视频清单 · Video Inventory

把一个目录或整台电脑里的视频文件列成一份可排序、可过滤的清单。核心是一个共享的
增量目录缓存：第一次扫描完整遍历，之后每次只对目录做 `stat`，未变化的目录直接复
用缓存，所以重复运行的成本接近“目录数 × 一次 stat”，与文件总数无关。

## Triggers

### Activate when

- “列出这个文件夹里所有的视频文件。”
- “全盘找一下我电脑上有哪些视频，按大小排。”
- “最近一周新增了哪些 mp4 / mov？”
- “哪些视频是 HEVC 编码，哪些是 H.264？”
- “List all video files under this project.”
- “Find every video on my Mac and show the biggest ones.”

### Do not activate when

- 找的是“上次 AI 对话里生成的那个文件”，需要会话证据 → `lov-search-file`
- 要从一个视频里抽帧、挑瞬间或做照片 → `lov-video-moments`
- 要转码、剪辑、加字幕或压缩视频 → `lov-media-creator` / `lov-media-preprocessor`
- 要把相机卡素材完整迁移到 SSD 并校验 → `lov-migrate-camera-media`
- 只是问某个视频格式或编码的知识，不需要扫描磁盘 → 直接回答

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

| 记录 | 含义 |
| --- | --- |
| `records.default_scope` | 不带参数时的默认范围：`current`（默认）或 `global` |
| `records.global_roots` | `--global` 使用的根目录列表；缺省为主目录加 `/Volumes` 下的外接卷 |
| `records.extra_excludes` | 追加跳过的目录名或路径后缀 |
| `records.extra_extensions` | 追加识别的视频扩展名 |
| `records.default_format` | 默认输出：`table`、`json`、`paths`、`csv` |
| `records.default_sort` | 默认排序：`mtime`、`size`、`path`、`name`、`duration` |

缓存文件与 Profile 同住：`<profile 目录>/lov-list-videos/cache.json`，默认即
`~/.lovstudio/skills/lov-list-videos/cache.json`。`LOV_LIST_VIDEOS_CACHE` 或
`--cache` 可以覆盖。缓存是可再生的派生数据，删掉只会让下一次变成全量扫描。

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
- 必须确认 `scripts/list_videos.py`、`scripts/profile_store.py`、
  `references/cache-design.md`、`references/skill-composition.md` 均存在。
- If a required resource is missing, name its expected relative path and stop
  before producing a partial result.

When running scripts manually:

```bash
export SKILL_DIR="/path/to/lov-list-videos"
```

Resolve `context.profile` on every invocation. The precedence is current request,
project context, Skill-specific profile records, shared preferences, shared
brand/user profile, then safe defaults. A direct user statement about a durable
preference or brand fact should be saved with `scripts/profile_store.py record`
using `--confirm`, followed by a concise saved-path report.

### Step 1: Understand the requested outcome

- 定范围。用户点名了目录就扫那个目录；说“全盘”“整台电脑”“所有地方”用
  `--global`；什么都没说时扫当前工作目录，并在结果里写明扫的是哪里。
- 定输出。用户要“看一眼”给表格；要交给下游脚本或再筛选给 `--format json`；
  只要路径列表给 `--format paths`。
- 定过滤。把“最大的”“最近的”“超过 1G 的”“mp4 的”直接映射到 `--sort`、
  `--since`、`--min-size`、`--ext`，不要先全量输出再人工筛。
- 只有用户问到时长、分辨率或编码时才加 `--probe`；它会调用 ffprobe，结果也会缓存。

### Step 1.5: Analyze nearby Skills before implementation

- 先读 `references/skill-composition.md`。本 Skill 只负责“有哪些视频、在哪、
  多大、多新”，下游的抽帧、剪辑、迁移各有归属，不要在这里顺手做。
- 用户要的是某次 AI 对话的产物而不是磁盘盘点时，交给 `lov-search-file`。

### Step 2: Execute the workflow

1. 运行 CLI。默认扫当前目录，输出按修改时间倒序的表格：

```bash
python3 "$SKILL_DIR/scripts/list_videos.py"
```

2. 指定一个或多个目录，或改为全局：

```bash
python3 "$SKILL_DIR/scripts/list_videos.py" ~/Movies ~/Downloads
python3 "$SKILL_DIR/scripts/list_videos.py" --global --sort size --limit 30
```

3. 常用过滤与输出：

```bash
# 最近 7 天、大于 200M、只看 mp4/mov，输出 JSON 给后续处理
python3 "$SKILL_DIR/scripts/list_videos.py" --global \
  --since 7d --min-size 200M --ext mp4 mov --format json

# 补时长/分辨率/编码，按时长排序（自动启用 --probe）
python3 "$SKILL_DIR/scripts/list_videos.py" ~/Movies --sort duration
```

4. 缓存控制。怀疑缓存过期用 `--full` 强制重新列目录；不想留痕用 `--no-cache`；
   `--clear-cache` 删除缓存文件。扫描设置（扩展名集合、是否含隐藏目录）改变时
   脚本会自动重新列目录，不需要手动清缓存。

5. 默认跳过 `node_modules`、`Library/Caches` 等噪音目录、`.app`/`.photoslibrary`
   等包目录、隐藏目录和外接卷上的 `._` 副本文件。用户明确要扫这些位置时加
   `--no-default-excludes` 或 `--hidden`；只想多跳过某些目录用 `--exclude`。

6. 用户说出长期偏好时写回 Profile，例如“以后默认全盘扫”：

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" record \
  --skill-id lov-list-videos \
  --path records.default_scope \
  --value '"global"' \
  --confirm
```

### Step 3: Validate the deliverable

- 回读 stderr 摘要：视频数、总大小、目录数、`scanned`/`reused` 比例、错误数与
  缓存路径。第二次运行 `reused` 应接近目录总数；不是就说明有大量目录变化或
  设置改变，向用户说明。
- 报告时先给结论（多少个、多大、最值得看的几个），再给范围和过滤条件；不把
  整份长清单贴进对话，超过二十条时写文件或给 `--format json` 路径。
- `errors` 不为零时说明是权限拒绝或读取失败，并指出受影响的根目录；macOS 上
  `~/Library` 部分子目录需要“完全磁盘访问”权限，这属于用户系统设置，不要绕过。
- Validate `skill-card.yaml`, `cases/cases.json`, and `pricing-card.yaml` as the
  standard trust bundle for this Skill.

## Dependencies

- Python 3.9+（仅标准库）
- ffprobe（FFmpeg），仅 `--probe` 与 `--sort duration` 需要
- 无外部 Skill 依赖；相邻 Skill 的交接见 `references/skill-composition.md`
