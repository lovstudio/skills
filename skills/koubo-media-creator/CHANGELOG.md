# Changelog

## 0.4.2 — 2026-11-17

- `build.py` 字幕切分不再拆开数字：`split_caption` 原先在每个英文 `,` `.` `:` 后断句，「3.0」被拆成以「3」结尾、以「0」开头的两条字幕；句内清理还会把「1,000」「10:30」写成「1 000」「10 30」，超长句按词均分时也可能从数字中间切开（jieba 把「1,000」「10:30」分成三个词，无 jieba 时逐字切）。现在英文 `,` `.` `:` 两侧都是数字时算作数字本身，断句、清理、均分三处都不拆；中文标点和其余英文标点照旧断句，配音与对齐不受影响。
- 新增回归测试 `tests/test_split_caption.py`（标准库 unittest，有无 jieba 两种分词都测）：3.0、1,000、10:30 的短句与超长句，以及中英文句号、逗号、冒号、分号、问叹号的原有断句。同一份测试对 0.4.1 有 12 个子用例失败。
- 回归：本机 11 份 `script.json`、412 句，按两种分词、14 与 10 两个字数上限共 1648 次切分，1632 次与 0.4.1 逐字一致；其余 16 次全是含「3.0」的 4 句，改为「3.0」完整显示。
- `references/pitfalls.md`「画面」：补「英文标点断句把 3.0、1,000、10:30 拆开」。README 质量门禁补测试命令。

## 0.4.1 — 2026-11-15

- `tts.py` 写 `<out>.words.json` 时不再取句内最长的 N−1 个停顿当分句点：按字重（中文 1、拉丁字母与数字 0.5）算期望分句点，只在 ±max(0.3 s, 句长 12%) 内吸附 ≥ 60 ms 的停顿，按「停顿长 ×（1 − 距离/窗口）」取最高分，窗口内没有就落在期望点，且不早于上一个分句点。Seed-TTS 在英文词前后、句中强调处的停顿常比逗号长，旧算法会把字幕与 b-roll `at` 切偏 1–2 秒。
- 回归（同一集改稿后的 41 句样片，全缓存、0 请求）：wav 与真值 JSON 字节不变；91 个短语与本集已验证的修法逐条一致；38 个多分句句子里同句分句语速差超过 2 倍的由 8 句降到 3 句，最差由 7.8 倍降到 2.5 倍。
- `references/pitfalls.md`：补「TTS 句中停顿长于逗号停顿，最长停顿法会切错」。

## 0.4.0 — 2026-11-15

来自 2026-11-15 样片（37 句见闻类口播）的回归修复；同一工程用 0.4.0 重跑 tts → align → build → mix → finish，时间线、字幕、人声与成片画面逐帧一致，质检全过。

- 样片对齐改走 TTS 真值：`tts.py` 同时写出 `<out>.words.json`（每句按标点分短语、边界取句内最长停顿），pipeline 与 SKILL 第 4 步默认 `align.py --words recording/tts-take.words.json`，不调用任何 ASR。
- 起步工程 `Short.tsx`：占位出镜在 `face` 布局下改为顶对齐（`paddingTop: 560`），头像不再压住胸口大标注（`CALLOUT_Y.face = 1050`）。
- `align.py` / `finish.py`：Whisper 模型已在 Hugging Face 缓存时直接从本地快照目录加载，环境有 SOCKS `all_proxy` 且缺 `socksio` 时不再报 ImportError（`HF_HUB_OFFLINE=1` 也绕不过）。
- 吃字率去误报：标点表补「」『』〈〉〔〕；`finish.py` 复用 `align.py` 的归一化（繁转简、全角转半角），口语数字转换补〇、千与逐位读法（二〇二六 → 2026）；2026-11-15 样片同一份转写由 2.1% 降到 1.1%。
- `references/pitfalls.md`：补 TTS 真值对齐、引号误报、转写漏听要先核切点再归因、SOCKS 与本地快照、经代理 `uv run --with` 卡住改用持久 venv、Seed-TTS 默认语速约 7.7 字/秒高于片型上限、占位头像压标注。

## 0.3.1 — 2026-10-30

- README 安装命令改回官方的 `npx lovstudio skills add koubo-media-creator`（免费直接安装）。

## 0.3.0 — 2026-10-30

- 以 MIT 协议开源，源码仓库公开；停止付费销售。
- README 安装说明改为直接克隆；`pricing-card.yaml` 与 Skill Card 的定价、分发改为免费开源。

## 0.2.1 — 2026-10-29

- `skill.yaml` 版本号补齐（0.2.0 发布时仍写 0.1.0）。
- README 安装说明与官网现状对齐：付费 Skill 当前随 VIP 会员解锁，不再写单项购买价。

## 0.2.0 — 2026-10-28

- 首发上架 Lovstudio.AI 官网：一次性付费 1,394 Credits，源码私有（2026-10-29 定价）。
- 调用 ID 改为 `lov-koubo-media-creator`（源目录 `koubo-media-creator-skill`，Profile 命名空间 `skills.lov-koubo-media-creator`）；展示名「口播短片」与数据格式名 `talking-head-*/v1` 不变。

## 0.1.0 — 2026-10-28

- 首版：片型语法（7 条代表作转写、上半屏切点与 30 张封面量化）、五种片型公式、`script.json` 规范。
- 脚本：`check_script.py`（结构、估时、证据覆盖、事实出处、AI 腔与借用口头禅）、`teleprompter.py`、`capture.py`（网页 / 终端输出 / 批量）、
  `tts.py`（样片占位配音与重读回归）、`align.py`（最后一遍选择 + 最长静音缝落刀，可接外部 ASR）、`build.py`、`mix.py`、`finish.py`、`gen_bgm.py`。
- 起步工程：Remotion 4 竖版三布局（分屏 / 全脸 / 全素材）、红框与焦点推近、标黄字幕、Logo 水印、片尾关注卡、3:4 与 16:9 封面；Vision 抠图工具。
- 首个案例：`2026-10-28-topic-to-short` 样片 v0.2。
