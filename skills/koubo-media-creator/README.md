# 口播短片 · Talking-head Short

![version](https://img.shields.io/badge/version-0.3.1-orange)

输入一个主题，Agent 交付 AI 工具类竖版口播短片的全部前期：带出处的事实、按片型写好并过门禁的脚本、提词器、上屏证据截图、封面。
你照提词器竖拍一条口播（念错了停半拍整句重读即可），它自动挑出每句最后念对的一遍、剪掉停顿，排成「上半屏证据、下半屏出镜、字幕压在交界」的成片，配乐、封面、质检报告一起交。

复刻的是片型（结构、语速、换画面节奏、字幕与封面语法），不是人：出镜、声音、名字、Logo 都是你自己的。

## 安装

```bash
npx lovstudio skills add koubo-media-creator
```

以 MIT 协议开源，免费安装使用。

## 用法

- 「输入一个主题，帮我做一条口播短视频，上面放截图、下面露脸的那种。」
- 「这个选题写口播稿和提词器，我自己录，录完你剪。」
- 「我录好了 recording/take.mov，按脚本剪成竖版成片。」

流程与命令见 [references/pipeline.md](references/pipeline.md)，片型标准见 [references/style-grammar.md](references/style-grammar.md)，
脚本字段见 [references/script-format.md](references/script-format.md)。

## Profile

读取共享 `user-profile/v1`：账号名、官方 Logo、头像、形象照、默认片型、ASR、样片音色、命名规则、输出目录。
你直接说出的长期偏好会写回 `skills.lov-koubo-media-creator.records`，见 [references/user-profile.md](references/user-profile.md)。

## 依赖

- Python 3.9+：numpy、pillow、mlx-whisper、opencc-python-reimplemented、jieba；Playwright
- FFmpeg / FFprobe；Node 20+、pnpm、Remotion 4.0.517
- macOS swiftc + Vision（封面抠图）
- 可选：`VOICENGINE_API_KEY`（样片占位配音）、`OPENROUTER_API_KEY`（AI 配乐，约 0.08 美元/首）

## 质量门禁

```bash
python3 scripts/validate_skill.py .
python3 scripts/check_script.py work/script.json        # 脚本
python3 scripts/finish.py EPISODE --name … --version v0.x   # 成片：尺寸、帧数、bt709、响度、真峰、吃字率
```
