# koubo-media-creator · Linux 脚本层

- 日期：2026-11-06
- 环境：Debian 12 arm64（Docker）· Python 3.12 · FFmpeg 5.1 · 无 Agent，只跑脚本
- 方式：Skill 目录只读挂载进干净容器，直接运行 Skill 自带脚本，没有 Agent，也没有联网账号
- 素材：和 macOS 运行同一批合成素材

## 结果

- 通过：脚本门禁
- 未过：封面抠图要的 swiftc
- 通过：align.py loads
- 通过：build.py loads
- 通过：finish.py loads
- 通过：mix.py loads
- 通过：teleprompter.py loads
- 通过：setup_project.py loads

## 说明

mlx-whisper 同样无法加载（见采访短片的记录），容器里也没有 swiftc。
