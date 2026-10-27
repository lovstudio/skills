---
name: lov-motivational-media-creator-claude-version
description: >
  按参考片实测节奏，把一个人或团队真实的倒下与起来做成 2–6 分钟励志短片：选片型、排节拍、写旁白、时间线体检、成片复测。用于“做励志短片”“按参考片节奏体检成片”；Make a measured motivational film.
license: MIT
compatibility: "Python 3.8+ standard library; FFmpeg/ffprobe on PATH for study and render checks; PyYAML only for Skill validation. Rendering uses the user's own Remotion or editing executor."
depends_on:
  - lov-branding-consistency
metadata:
  author: skill-publisher
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: authored-prose
  tags:
    - motivational-film
    - rhythm-analysis
    - narration
    - timeline-check
---

# 励志短片 · Claude 版

把一个真实的人或团队“倒下—起来”的经过做成 2–6 分钟的励志短片。先选片型和节拍，
再写旁白、排时间线，最后用参考片实测的节奏区间体检时间线和成片。
方案、时间线通过体检、已渲染、有人完整看过、已发布是五个不同状态，分开报告。

## Triggers

### Activate when

- “做一条励志短片，讲他怎么从低谷回来。”
- “按这几条参考片的节奏，给这条片子排结构和时间线。”
- “体检一下这条励志片，对照参考片看哪里节奏不对。”
- “拆一下这个励志频道 / 这几条参考片的节奏。”
- “Create a motivational film about how our team came back.”
- “Check this motivational cut against the reference rhythm.”

### Do not activate when

- 只下载、转写或翻译视频：交给 `lov-media-crawler`、`lov-voice2srt`。
- 把一场采访剪成竖版短片：交给 `lov-interview-media-creator`。
- 无实拍的动态图志或三维图志：交给 `lov-motion-media-creator` 或 `lov-3d-motion-media-creator`。
- 软件教程、录屏、课程切片：交给 `lov-media-creator`。
- 只发布已批准的成片：交给 `lov-media-publisher`。
- 想把参考片里的演讲音频、电影片段或配乐直接拿来拼新片：参考只提供节奏，不提供授权；说明后停下。
- 用户点名 `lov-motivational-media-creator`（同一参考集的另一版本）：用那个，不在一次任务里混用两套规则。

## 与另一版本的关系

`lov-motivational-media-creator` 与本 Skill 基于同一组 8 条参考片，按用户要求并行存在，
供比较。本版的不同在于：节奏规则来自对原片的逐片测量（切点、响度、语音覆盖、纯音乐段），
并附带可复跑的测量与体检脚本；它管到“成片复测”，渲染本身交给执行器。
详见 [Skill 组合记录](references/skill-composition.md)。

## User Profile (cross-session)

每次先读 [Manifest](skill.yaml) 和 [Profile contract](references/user-profile.md)：

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" read \
  --skill-id lov-motivational-media-creator-claude-version --pretty
```

本 Skill 的长期记录放在 `skills.lov-motivational-media-creator-claude-version.records`：

| 字段 | 含义 | 用在哪 |
|---|---|---|
| `black_title_cards` | `avoid` 或 `allow` | `avoid` 时体检加 `--forbid-black-cards` |
| `default_archetype` | `single-arc` 或 `chorus` | 用户没说时的默认片型 |
| `aspect` | 如 `16:9`、`9:16` | 时间线与渲染画幅 |
| `delivery_lufs` | 交付整体响度，如 `-16` | 成片复测 |
| `narration_voice` | 已批准的旁白音色名 | 合成旁白前不再重复问 |
| `reference_envelope` | 自建包络 JSON 的位置 | 替换内置包络 |

用户直接说出的长期偏好，用 `scripts/profile_store.py record ... --confirm` 保存并报告路径。
品牌名、Logo、语气从共享 `brand.*` 读，不写进源文件；推断出的值只用于本次。

## 参考片告诉我们什么

8 条 TheMiro0r 视频（5 条多声部拼贴、3 条单人逆转），逐片测量，详见
[参考片研究](references/reference-study.md)。能直接指导制作的结论：

1. **安静开场，晚到的峰。** 最响的 10 秒全部落在片长的 74%–98%；开场比峰低 12.5–25.8 LU。
2. **扬之前先抑。** 8 条里 6 条在峰之前有一段比前面高点低 4.4 LU 以上的谷。
3. **峰留给音乐。** 8 条里 6 条，最响的 10 秒挨着（≤2 秒）一段 8 秒以上的纯音乐段：人声说完最后一句，音乐自己把情绪推到顶。
4. **宽动态。** 响度范围 LRA 10.9–18.8 LU。压成一条平线，前三条都会失效。
5. **越到后面切得越快，或者干脆一镜到底。** 6 条最后四分之一的平均镜头长是第一个四分之一的 0.16–0.51 倍；另一种收法是用一个 40 秒左右的长镜头收尾。
6. **关键时刻可以出现两次。** Tyson Fury 那条把倒地画面先作为“倒下”放一次，一分钟后配着解说再作为“起来”放一次。

这些是描述性区间，不是硬指标。偏出区间是提示你去看，不是判错。

## Workflow (MANDATORY)

### Step 0：定位与上下文

- 用 `SKILL_DIR`；没有就从已安装 Skill 目录推断。核对 `scripts/`、`assets/reference-envelope.json`、`references/` 都在。
- 读 Profile。确认本次是哪种模式：**拆参考片**（study）、**做新片**（make）、**体检**（check）。

### Step 1：证据账本（make 模式）

开写之前先建账本，见 [权利、事实与安全](references/rights-and-safety.md)：

- 主人公是谁；那次真实的“倒下”是什么；决定性的时刻是哪一个、有没有影像。
- 主人公本人的原话录音有哪些（时间、出处、原文、译文）。
- 每条事实的状态：`verified`、`single-source`、`disputed`。
- 每个素材的权利：`owned`、`licensed`、`permitted`、`public-domain`、`unclear`、`risk-accepted`。
  `risk-accepted` 只能来自用户本人在对话里的明确表态，且片子状态最高到 `review`。
- 是否涉及自杀或自伤。涉及时按安全报道规则处理，片尾必须有核实过的求助信息。

### Step 2：选片型与声音来源

| 材料 | 片型 | 声音 |
|---|---|---|
| 一个主人公，有本人原话或比赛/现场解说 | `single-arc` 单人逆转 | 本人原话为主；原创旁白只做桥 |
| 一个主人公，原话很少 | `single-arc` | 原创旁白贯穿，转折处放本人原话 |
| 一个主题，多位真实人物（团队、用户、社区）各有一段 | `chorus` 多声部 | 多人原话接力，旁白最少或没有 |

不确定时用 Profile 的 `default_archetype`，仍不确定就问一个问题。

### Step 3：节拍表 → 用户批

按 [片型与节拍](references/archetypes-and-beats.md) 排节拍：每拍写角色、起止时间、这拍要让观众知道什么、用哪段原话、强度 1–10。
把节拍表给用户看，**批了再写稿**。用户最在意的是叙事：贯穿的矛盾、层层加码、转折配本人原话、首尾呼应；不要“日期 + 一句话”的碎片字幕。

### Step 4：写稿

- 先读 [作者性约束](references/authorship-integrity.md)。旁白只写账本里有的事；不替主人公编内心独白、不编“那一刻他想到了……”。
- 中文旁白每秒 4–5 字；一句一个意思，写给耳朵听。
- 原话出现时旁白停。转折、决定性时刻、结尾，优先用本人原话。
- 峰值段落旁白收声，让音乐和画面走；收尾最多一句话。
- 做品牌片时读 `lov-branding-consistency`，品牌只在片尾出现一次。

### Step 5：时间线与体检

按 [时间线格式](references/timeline-format.md) 写 `timeline.json`（可从 `assets/timeline.template.json` 起步），然后：

```bash
python3 "$SKILL_DIR/scripts/check_timeline.py" timeline.json \
  --envelope "$SKILL_DIR/assets/reference-envelope.json" \
  [--forbid-black-cards] --out check-report.json
```

- 有 error 就改，直到 `valid: true`。
- warning 逐条判断：是有意为之就在交接记录里写一句理由，否则改。

### Step 6：素材与花费 → 用户批

下载素材、合成旁白、买配乐、开渲染之前，列清单和花费估算给用户，等批准。
开子 Agent 或 workflow 前先报 token 费用估算。下载他人素材前先列候选让用户挑。

### Step 7：渲染（交给执行器）

本 Skill 不自带渲染引擎。把 `timeline.json`、旁白稿、[节奏与声音规则](references/rhythm-and-sound.md) 交给用户的 Remotion 工程或 `lov-media-creator`。
执行时守住：每首歌只挂一次、整段连续；原话下压低配乐；峰值段旁白停；结尾按节拍表收。

### Step 8：成片复测

```bash
python3 "$SKILL_DIR/scripts/study_reference.py" final.mp4 \
  --transcript final-voices.vtt \
  --envelope "$SKILL_DIR/assets/reference-envelope.json" \
  --archetype single-arc --out final-profile.json
```

- `comparison.outside` 里的每一项都要解释：有意为之，还是要回到混音或剪辑。
- 另外核对交付响度（Profile 的 `delivery_lufs`）、真峰值、抽帧总览、成片旁白转写与稿子是否一致。
- 机器复测通过不等于有人看过。没人从头到尾看过、听过，就写“未经人审”。

### Step 9：报告

报告用这五个状态，一个一个说清楚：方案（节拍表/稿）、时间线体检、渲染、人审、发布。
发布交给 `lov-media-publisher`，只在用户要求时做。

## Study 模式：拆参考片

```bash
python3 "$SKILL_DIR/scripts/study_reference.py" ref.mp4 --transcript ref.en.vtt \
  [--ignore-cue "字幕组署名的正则"] --out profiles/ref.json
python3 "$SKILL_DIR/scripts/build_envelope.py" profiles/*.json \
  --member <stem>=chorus --member <stem>=single-arc --label "<参考集名>" \
  --out my-envelope.json
```

- 下载参考片只在用户授权范围内做，cookies 不保存、不展示。
- 再配一张联系表实际看画面（每 4 秒一帧、带时间码）：
  `ffmpeg -i ref.mp4 -an -vf "fps=1/4,scale=200:-2,tile=8x8" -fps_mode vfr sheet_%02d.jpg`
- 证据分级：实测数字、看过的联系表、字幕文本、推断，分开写。联系表不等于完整看片，响度不等于听感。
- 自建包络的位置用户要长期用时存进 Profile 的 `reference_envelope`。

## Check 模式：只体检

用户只给一条已有的片子或时间线时，跑 Step 5 和/或 Step 8 的命令，按“偏出了什么、可能为什么、要不要改”回报。
只读：不改用户工程里的任何文件，建议写在报告里。

## 硬规则

- 参考片只提供节奏和手法，不搬运其中的演讲、电影画面或音乐。
- 不编造原话、内心独白、因果；`disputed` 的事实不进旁白，`single-source` 的要软化措辞。
- 旁白不压在原话上；两段原话之间最多交叉淡化 0.15 秒。
- 每首歌一条连续音乐床，全片最多换一次歌。
- 涉及自杀或自伤：不出现方式、地点、速度等细节；写求助，不写意志力战胜一切；片尾求助信息每次从官方来源核实。
- 不羞辱观众（不用“你们大多数人就是懒”的腔调）、不歌颂透支（不熬夜、不过劳当美德）、不承诺成功。
- 未清权素材的片子最高到 `review`，不能叫“可发布”。

## Dependencies

- Python 3.8+ 标准库：`study_reference.py`、`build_envelope.py`、`check_timeline.py`。
- FFmpeg / ffprobe：测量与复测。
- 渲染执行器（可选）：用户的 Remotion 工程或 `lov-media-creator`。
- `lov-branding-consistency`：读者可见文案（旁白、字幕、片名、片尾）的品牌门禁。
- PyYAML：只用于 `scripts/validate_skill.py`。
