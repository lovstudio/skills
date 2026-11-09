# media-creator · Linux 脚本层

- 日期：2026-11-06
- 环境：Debian 12 arm64（Docker）· Python 3.12 · FFmpeg 5.1 · 无 Agent，只跑脚本
- 方式：Skill 目录只读挂载进干净容器，直接运行 Skill 自带脚本，没有 Agent，也没有联网账号
- 素材：和 macOS 运行同一批合成素材

## 结果

- 通过：媒体探测脚本
- 通过：音频质检脚本

## 说明

这里只跑了不依赖转写的两个脚本。mlx-whisper 在同一容器里加载失败。
