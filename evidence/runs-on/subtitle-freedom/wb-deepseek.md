# subtitle-freedom · WorkBuddy + DeepSeek V4 Pro

- 结果：通过
- 日期：2026-11-06
- 环境：macOS 26.6 arm64 · WorkBuddy 内置 CodeBuddy CLI 2.115.0 · deepseek-v4-pro
- Skill 版本：1.4.0（e683f49）
- 入口：WorkBuddy 自带的命令行，不是图形界面；图形界面没有单独测
- 隔离：清空环境变量后运行，用 macOS 沙箱禁止读取密钥和个人目录，只给合成素材，配置目录为空，模拟一个新用户
- 运行：62 轮，2.1 分钟，输入 728765 tokens（缓存命中 692608），输出 7065 tokens

## 范围

同样的素材，时间轴完全一致，13/13 个难点短语标注，字幕解析通过。

## 差距与没覆盖的部分

12 条短对白上和另外两个模型没有差距。长片和人物卡没测。

## 给 Agent 的原话

```text
给当前目录的 dialogue-en.srt 生成 CET4 水平的英文学习字幕。不需要人物卡。
这是一次无人值守运行：不要向我提问，按默认决策做完；完成后告诉我输出路径、标注条数和你做过的校验。
```

## 素材

- `dialogue-en.srt`（sha256 3237e8255dc92fa4）：12 条原创英文对白，埋了 13 个难点短语

## 独立验收

下面的检查不看模型自述，由验收脚本直接读产物。

- 通过：Skill 确实被调用（工具调用或读取 SKILL.md）
- 通过：Agent 正常结束
- 通过：原文件没动：dialogue-en.srt
- 通过：有学习字幕 SRT 和 ASS（['dialogue-en.cet4.glossed.srt', 'dialogue-en.cet4.glossed.watermarked.ass']）
- 通过：时间轴和原字幕完全一致（12 vs 12）
- 通过：有注释（13）
- 通过：埋的 13 个难点短语至少标了 8 个（13/13）
- 通过：SRT 能被 FFmpeg 解析
- 通过：ASS 能被 FFmpeg 解析

实测值：`{"notes": 13, "planted_recall": "13/13"}`
