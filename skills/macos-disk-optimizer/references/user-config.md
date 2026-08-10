# 用户配置

该 Skill 只保存跨任务仍有价值的磁盘优化默认值，不保存扫描结果、真实文件清单、迁移日志或目录内容。

## 解析顺序

1. 当前请求或显式 CLI 参数；
2. `SKILL_PREFERENCES_PATH` 指向的个人配置；
3. 个人配置的 `skills.macos_disk_optimizer`；
4. 安全默认值；
5. 仍缺少且会改变用户结果时，只问一个面向用户的问题。

默认个人配置路径：

```bash
${SKILL_PREFERENCES_PATH:-$SKILLS_CONFIG_DIR/preferences.json}
```

## 可持久化字段

```json
{
  "skills": {
    "macos_disk_optimizer": {
      "target_free_gb": 200,
      "buffer_gb": 15,
      "archive_volume": "/Volumes/ARCHIVE_VOLUME",
      "protected_paths": ["$HOME/PATH_TO_PROTECT"],
      "cleanup_policy": "balanced"
    }
  }
}
```

- `target_free_gb`：最低十进制 GB。
- `buffer_gb`：目标之上的稳定余量，默认 15 GB。
- `archive_volume`：可选；首次迁移时必须确认实际挂载和空间。
- `protected_paths`：额外保护目录，运行时展开 `$HOME`，不得提交解析后的个人绝对路径。
- `cleanup_policy`：`conservative`、`balanced` 或 `aggressive`；无论哪种策略都不越过保护边界。

## 初始化

先显示将保存的内容：

```bash
python3 "$SKILL_DIR/scripts/disk_optimizer.py" profile init \
  --target-free-gb TARGET_FREE_GB \
  --buffer-gb BUFFER_GB \
  --archive-volume ARCHIVE_VOLUME \
  --protected PROTECTED_PATH
```

用户确认后增加 `--write`。查看当前设置：

```bash
python3 "$SKILL_DIR/scripts/disk_optimizer.py" profile show
```

不要把访问凭据、浏览器资料、聊天内容、Git 远程地址或扫描得到的私人文件名写入个人配置。
