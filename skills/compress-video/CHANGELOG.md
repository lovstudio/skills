# Changelog

## 0.1.0 (2026-09-12)

- 新增 `scripts/compress_video.py`：默认 libx265 CRF 28、保留分辨率帧率、AAC 96k，
  输出 `<原名>-compressed.mp4`，原文件不动。
- 质量档 `smallest` / `small` / `balanced` / `high` 对应 CRF、preset、音频码率与
  长边上限；`--crf`、`--preset`、`--max-edge`、`--fps`、`--audio-bitrate` 可细调。
- `--codec hevc|h264|av1`，`--fast` 切 VideoToolbox 硬件编码；硬件解码默认开启并在
  失败时回退软件解码。
- `--target-size` 两遍码率模式；`--vmaf` 测分，`--min-vmaf` 不达标自动降 CRF 重编
  最多两次。
- `--replace` 替换模式：写 `<原名>.mp4`，原文件移到废纸篓（Finder，失败回退
  `~/.Trash`），`--permanent` 才直接删除。
- 门禁：输出时长偏差超过 0.5 秒或 1% 丢弃；输出不比源小丢弃（`--force` 保留）；
  临时 `.part.mp4` 失败即清理。
- 实测 1080p HEVC 26 秒片段：24.7 MB → 2.2 MB，VMAF 93.5，24 秒。
- 附 `tests/test_compress_video.py` 七项回归测试与 `references/encoding-guide.md`。
