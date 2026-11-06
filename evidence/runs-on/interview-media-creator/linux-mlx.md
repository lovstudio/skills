# interview-media-creator · Linux 脚本层

- 日期：2026-11-06
- 环境：Debian 12 arm64（Docker）· Python 3.12 · FFmpeg 5.1 · 无 Agent，只跑脚本
- 方式：Skill 目录只读挂载进干净容器，直接运行 Skill 自带脚本，没有 Agent，也没有联网账号
- 素材：和 macOS 运行同一批合成素材

## 结果

- 通过：12 个 Skill 脚本能加载（运行 --help）
- 未过：配乐人声检查要的 swiftc
- 未过：杜比视界素材要的 avconvert
- 通过：pip install mlx-whisper
- 未过：用 mlx-whisper 转写

## 说明

mlx-whisper 能 `pip install`，但 `import` 时报 `libmlx.so: cannot open shared object file`，转写步骤过不去。
