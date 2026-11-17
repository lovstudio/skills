# Changelog

## 0.5.1 — 2026-11-17

- 文档：CHANGELOG 与 pitfalls 里的实测说明改为不点名具体项目；脚本与起步工程没有变化。

## 0.5.0 — 2026-11-17

- 片尾默认改为所有视频 Skill 共用的作者品牌片尾（`lov-logo-sting` 0.2.0 的 media end，配置在共享 Profile `preferences.video_outro`）：作者 2026-11-17 要求用采访片结尾的 Logo 片段替换原来的关注卡。
- `build.py --outro work/sting`：读 `media_end.py make` 的产物，片尾时长取 `timing.json` 帧数，`spec`/`timing`/`intro` 写进 `timeline.end.sting`；帧率不一致时拒绝。不传 `--outro` 时保留旧关注卡。
- `mix.py --sting work/sting/sting.wav [--sting-gain 0.40]`：配乐在片尾起点前 1.2 秒淡出，音效按增益在 `end.from` 并进母带前混音；带片尾时限幅默认 −3 dBTP（0.95 增益曾让 AAC 编码成片真峰到 −0.0 dBFS）。
- 起步工程新增与 `lov-logo-sting` 0.2.0 同版的 `LogoSting.tsx`；`Short.tsx` 有 `end.sting` 时挂 `<LogoSting>`，否则画旧关注卡；`types.ts` 增加 `end.sting`。
- 文档：SKILL.md Step 6 与硬门禁 5、pipeline 新增 6b 片尾阶段、style-grammar §8、skill-composition、user-profile、script-format、pitfalls 同步；frontmatter `dependencies` 登记 `lov-logo-sting`。
- 实测：一条约 2 分钟的竖版口播样片用本版脚本端到端重建（setup_project --force → media_end make → build --outro → mix --sting），时间线 3771 帧（口播 3627 + 片尾 144），−16.1 LUFS / −2.9 dBTP，与手工接入结果一致。

## 0.4.3 — 2026-11-17

- 字幕不再拆开带点号的英文名：0.4.2 只保护数字，「Node.js 和 claude.ai」仍被切成「Node」「js 和 claude」「ai…」，「build.py」「e.g.」同理。`build.py` 改用一个 `JOINED` 规则：英文 `.` 两侧都是字母或数字（3.0、Node.js、v0.4.2），或英文 `,` `:` 两侧都是数字（1,000、10:30），都算同一个词，断句和超长句均分都不从中间切。后面跟空格或中文的英文句号照旧断句，所以句号后漏了空格的英文（works.Then）会连成一个词。
- 粘回的长词会让超长句均分切过头，留下单字尾巴（「claude.ai 都能」「用」）。现在只在含这类词的一段里，切出的段数超过计划、且末段并回前一段不超过字数上限时，把末段并回去。纯中文句子不走这条，均分结果不变。
- `tts.py` 的样片 `words.json` 也不再拆开这类词：新增 `phrases_of`，与字幕共用同一个 `JOINED` 规则，测试检查两边一致。原先「3.0」被切成「…3」「0」两个短语，「0」只占 0.1 秒左右，还会多出一个期望分句点。
- 测试：`tests/test_split_caption.py` 补点号名的短句、超长句，以及句号后跟中文或空格仍断句的用例；新增 `tests/test_tts_phrases.py`。同一份测试对 0.4.2 有 8 个子用例失败，另有 3 项因 0.4.2 没有 `phrases_of` 而报错。
- 回归：字幕方面，本机 11 份 `script.json` 共 1648 次切分，1646 次与 0.4.2 逐字一致；另外 2 次是一句含 3.0 的长句在 10 字上限下，原先从词中间切出的尾段并回了前一段。按默认 14 字上限，没有变化。TTS 方面，两集缓存样片（33 句与 22 句）重算 `words.json`：旧代码的结果与已落盘文件逐字节一致；新代码只改了含 3.0 的 4 句，其余 51 句不变。
- `references/pitfalls.md`：「画面」那条扩到点号名，「对齐与转写」补 TTS 短语拆数字。README 测试命令的注释同步更新。

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
