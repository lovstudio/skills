# 增量缓存设计 · Cache Design

`scripts/list_videos.py` 用一个 JSON 文件记住每个目录的状态，让第二次及以后的
扫描只付出“目录数 × 一次 stat”的代价。本文说明缓存放在哪、长什么样、怎样判
断新旧，以及它明确不保证的事。

## 位置

优先级从高到低：

1. `--cache PATH`
2. 环境变量 `LOV_LIST_VIDEOS_CACHE`
3. `<profile 目录>/lov-list-videos/cache.json`

第 3 项里的 profile 目录与 `scripts/profile_store.py` 用同一套解析：
`SKILL_PROFILE_PATH` / `SKILLS_PROFILE_PATH`，否则依次找
`~/.lovstudio/skills/profile.json`、`~/.skill-publisher/skills/profile.json`、
`~/.config/agent-skills/profile.json`。这样缓存和用户 Profile 永远住在同一个
“Skill 通用位置”，不同宿主、不同扫描范围共用同一份索引。

写入用临时文件加 `os.replace`，中断不会留下半截文件。

## 结构

```json
{
  "schema": "lov-list-videos/cache/v1",
  "extensions": ["mov", "mp4", "..."],
  "hidden": false,
  "updated_at": "2026-09-12T08:17:00+08:00",
  "dirs": {
    "/abs/dir": {
      "m": 1757636220000000000,
      "d": ["sub1", "sub2"],
      "v": {"clip.mp4": [12500, 1757636220000000000]}
    }
  },
  "probe": {
    "/abs/dir/clip.mp4": {"key": "12500:1757636220000000000", "duration": 2.0, "width": 320, "...": "..."}
  }
}
```

- `dirs` 以目录绝对路径为键，与扫描根无关。先全局扫过再扫 `~/Movies`，后者直接
  命中同一批条目。
- `m` 是目录 `st_mtime_ns`；`d` 是全部子目录名（不经过排除规则，所以改排除规则
  不会让缓存失效）；`v` 只记录命中扩展名的视频文件及其 `[size, mtime_ns]`。
- `probe` 以文件路径为键，`key` 绑定 `size:mtime_ns`。文件一变，探测结果自动作废。

## 增量判定

对每个待访问目录：

1. `os.stat` 取目录 mtime。
2. mtime 与缓存相同且没有要求全量 → 直接复用 `d` 和 `v`，对 `v` 里的每个视频再做
   一次 `os.stat` 刷新大小与时间。这一步是必要的：文件原地追加或改写不会改变父
   目录 mtime。
3. 否则 `os.scandir` 重新列目录，写回缓存。
4. 子目录经过排除规则后入栈继续。

目录新增、删除、重命名都会改父目录 mtime，所以第 2 步不会漏掉结构变化。

扫描结束后做剪枝：所有位于本次扫描根之下、又没有被访问到的缓存目录，若其父目录
的最新列表里已经没有它，就删掉。按路径排序处理，父目录先于子目录，整棵消失的子
树一次清干净。被排除规则跳过的目录不会被剪，下次放开规则时仍能复用。

## 失效条件

以下情况脚本会重新列出每个目录（仍然不重复 stat 文件，只是不复用 `d`/`v`）：

- `--full`
- 本次扫描的扩展名集合不是缓存记录的子集（新增了 `--ext` 或 Profile 里的
  `extra_extensions`）
- `--hidden` 与上次不同

缓存 `schema` 不匹配或 JSON 损坏时整份重建，并在 stderr 说明。

## 明确不保证的事

- 不跟随符号链接，避免环路和重复计数。
- 不做内容哈希；判断依据只有大小和 mtime。
- 不记录非视频文件，所以不能当通用文件索引用。
- 没有“完全磁盘访问”权限时，macOS 会拒绝读取部分 `~/Library` 子目录，统计进
  `errors`，不会静默当作空目录缓存。
