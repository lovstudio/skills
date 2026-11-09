# voice2srt · 三种转写引擎的字错率

- 日期：2026-11-06
- 环境：macOS 26.6 arm64，没有 Agent，直接跑引擎
- 素材：`talk-zh.mp4`（58.56 秒合成语音，sha256 01983c722495674c），文本真值已知
- 口径：去掉标点和空白，繁体先转简体，再算编辑距离除以真值长度

| 引擎 | 字错率 | 耗时 | 备注 |
| --- | --- | --- | --- |
| mlx-whisper large-v3-turbo | 0% | 12.9 秒 | 只能在 Apple 芯片上用 |
| mlx-whisper large-v3 | 0% | 18.4 秒 | 只能在 Apple 芯片上用 |
| whisper.cpp ggml-base | 3.5% | 约 2 秒 | 输出繁体；把「未验证」听成「为验证」，「但」听成「蛋」 |
| DashScope qwen-audio-3.0-asr-flash | 没测成 | | 接口返回 `InvalidApiKey: API-key is blocked`，预估费用 0.0129 元 |

这是发音清楚的合成语音，只能比较引擎之间的差距，不代表真实录音的绝对水平。
