# 视频清单 · Video Inventory

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

列出一个目录或整台电脑里的全部视频文件，带大小、修改时间，可选时长、分辨率与
编码。共享一份增量目录缓存，第二次起只对目录做 `stat`，未变化的目录直接复用。

实测（macOS，主目录加一块外接 SSD）：

| 运行 | 目录数 | 视频数 | 用时 |
| --- | --- | --- | --- |
| 首次全局扫描 | 147,794 | 50,884 | 20.9 s |
| 第二次全局扫描 | 147,794（复用 147,793） | 50,884 | 2.7 s |

## 本地安装

```bash
npx skills add lov-list-videos -g -y
```

或者在本仓库根目录手动链接：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$SKILL_SKILLS_INSTALL_DIR/lov-list-videos"
```

## 使用

```bash
# 当前目录，按修改时间倒序的表格
python3 scripts/list_videos.py

# 全局：主目录 + /Volumes 下的外接卷，按大小取前 30
python3 scripts/list_videos.py --global --sort size --limit 30

# 最近 7 天、大于 200M、只看 mp4/mov，输出 JSON
python3 scripts/list_videos.py --global --since 7d --min-size 200M --ext mp4 mov --format json

# 用 ffprobe 补时长 / 分辨率 / 编码（结果也缓存）
python3 scripts/list_videos.py ~/Movies --probe
```

示例输出：

```text
 SIZE  MODIFIED          PATH
24.7M  2026-08-14 09:25  ~/Movies/圆桌/圆桌-开头.mp4
1 videos, 24.7M total | dirs 5 (scanned 0, reused 5, pruned 0, errors 0) | 0.00s | cache: ~/.lovstudio/skills/lov-list-videos/cache.json
```

常用参数：

| 参数 | 作用 |
| --- | --- |
| `ROOT ...` | 要扫描的目录，默认当前目录 |
| `--global` | 扫主目录与外接卷（可用 Profile 的 `global_roots` 覆盖） |
| `--format table\|json\|paths\|csv` | 输出格式 |
| `--sort mtime\|size\|path\|name\|duration` / `--asc` / `--desc` | 排序 |
| `--since 7d` `--min-size 200M` `--max-size 2G` `--ext mp4 mov` `--match 课程` | 过滤 |
| `--limit N` | 只显示前 N 条，摘要仍报告匹配总数 |
| `--probe` / `--workers N` | 调 ffprobe 补充元数据 |
| `--hidden` / `--exclude NAME ...` / `--no-default-excludes` | 调整跳过规则 |
| `--full` / `--no-cache` / `--clear-cache` / `--cache PATH` | 缓存控制 |

默认跳过 `node_modules`、`Library/Caches` 等噪音目录、`.app`/`.photoslibrary` 等包、
隐藏目录、符号链接和外接卷上的 `._` 副本文件。

## 缓存

缓存与用户 Profile 同住：`<profile 目录>/lov-list-videos/cache.json`，默认为
`~/.lovstudio/skills/lov-list-videos/cache.json`；`LOV_LIST_VIDEOS_CACHE` 或
`--cache` 可覆盖。它以目录绝对路径为键，扫描范围之间共享；目录 mtime 未变即复用，
已缓存的视频只重新 `stat` 以捕获原地改写；消失的目录自动剪枝。设计细节见
[`references/cache-design.md`](references/cache-design.md)。

## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享
Profile 读取用户、品牌、工作区和本 Skill 的长期记录。用户直接说出的持久
偏好由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

本 Skill 的记录：`default_scope`、`global_roots`、`extra_excludes`、
`extra_extensions`、`default_format`、`default_sort`。例如把默认范围改为全局：

```bash
python3 scripts/profile_store.py record --skill-id lov-list-videos \
  --path records.default_scope --value '"global"' --confirm
```

详见 [`references/user-profile.md`](references/user-profile.md)。

## 原子组合

每个新 Skill 都带有 `references/skill-composition.md`。它记录已检查的相邻
Skills、可选的上游/下游交接、重叠处理，以及为何选择 Single Skill；外部
sibling Skill 不作为隐藏依赖。本 Skill 的下游是 `lov-video-moments`、
`lov-media-creator` 等，交接物是文件路径。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md`：用途、负责人、依赖、风险、输出与维度地图。
- `cases/cases.json`：真实的 Input → Prompt → Output 案例。
- `pricing-card.yaml`：价值锚点、交付边界和复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 -m unittest tests/test_list_videos.py
```

## 依赖

- Python 3.9+（脚本仅用标准库）
- ffprobe（FFmpeg），仅 `--probe` 与 `--sort duration` 需要
- PyYAML，仅 `validate_skill.py` 需要

## License

MIT
