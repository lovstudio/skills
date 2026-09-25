# Changelog

## 0.1.0 (2026-09-12)

- 新增 `scripts/list_videos.py`：扫描指定目录或全局（主目录与 `/Volumes` 外接卷）
  列出视频文件，支持 table / json / paths / csv 输出，按大小、时间、路径、名称、
  时长排序，按大小、时间、扩展名、子串过滤。
- 增量缓存：以目录绝对路径为键存放于 Profile 同级目录
  `<profile 目录>/lov-list-videos/cache.json`；目录 mtime 未变即复用，已缓存视频
  重新 `stat` 捕获原地改写，消失的目录自动剪枝，扩展名集合或隐藏设置变化时自动
  重新列目录。
- `--probe` 通过 ffprobe 补充时长、分辨率、编码、帧率与码率，结果按
  `size:mtime` 绑定缓存。
- 默认跳过 `node_modules`、`Library/Caches` 等噪音目录、`.app`/`.photoslibrary`
  等包目录、隐藏目录、符号链接与 `._` AppleDouble 副本。
- 实测主目录加外接 SSD：首扫 147,794 目录 / 50,884 视频 20.9 秒，增量 2.7 秒。
- 附 `tests/test_list_videos.py` 七项回归测试与 `references/cache-design.md`。
