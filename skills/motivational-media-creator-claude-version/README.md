# 励志短片 · Claude 版

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

`lov-motivational-media-creator-claude-version` · Motivational Film (Claude edition)

把一个人或团队真实的倒下与起来做成 2–6 分钟励志短片。节奏规则来自对 8 条参考片的逐片测量，附带三个可复跑的脚本：拆参考片、体检时间线、复测成片。

## 安装

```bash
npx skills add lov-motivational-media-creator-claude-version -g -y
```

本地源码安装（共享入口 + 宿主相对链接）：

```bash
ln -s "$(pwd)" "$HOME/.agents/skills/lov-motivational-media-creator-claude-version"
ln -s ../../.agents/skills/lov-motivational-media-creator-claude-version \
  "$HOME/.claude/skills/lov-motivational-media-creator-claude-version"
```

## 用法

做新片：

> 做一条励志短片，讲我们工作室产品停服之后怎么重新上线的，用团队成员自己的话。

Skill 会先建证据账本，选片型（这里是多声部 `chorus`），给你批节拍表，再写旁白稿和 `timeline.json`，跑体检，交给剪辑执行器渲染，最后复测成片。

只体检：

> 体检一下这条励志片，对照参考片看哪里节奏不对。

```bash
python3 scripts/check_timeline.py timeline.json \
  --envelope assets/reference-envelope.json --forbid-black-cards
python3 scripts/study_reference.py final.mp4 --transcript voices.vtt \
  --envelope assets/reference-envelope.json --archetype single-arc
```

拆自己的参考片：

```bash
python3 scripts/study_reference.py ref.mp4 --transcript ref.vtt --out profiles/ref.json
python3 scripts/build_envelope.py profiles/*.json --member ref=chorus --out my-envelope.json
```

## 参考片里测出来的六条

1. 最响的 10 秒在片长 74%–98%；开场比峰低 12.5–25.8 LU。
2. 8 条里 6 条峰前有 ≥4.4 LU 的谷。
3. 8 条里 6 条把最响的地方交给一段 ≥8 秒的纯音乐。
4. 响度范围 LRA 10.9–18.8 LU。
5. 6 条越剪越快（后四分之一镜头长是前四分之一的 0.16–0.51 倍）；另一种收法是 40 秒长镜。
6. 关键时刻可以出现两次：先倒下，再起来。

详见 [references/reference-study.md](references/reference-study.md)。这些是描述性区间，偏出只提示，不判错。

## 用户 Profile（跨 session）

读共享 Profile 的 `user`、`brand`、`workspace` 与本 Skill 的记录：`black_title_cards`、`default_archetype`、`aspect`、`delivery_lufs`、`narration_voice`、`reference_envelope`。
用户直接说出的长期偏好用 `scripts/profile_store.py record ... --confirm` 保存。见 [references/user-profile.md](references/user-profile.md)。

## 与 `lov-motivational-media-creator` 的关系

两者基于同一组参考片，并行存在供比较。那一版交付原创制作包、到渲染前为止；这一版以实测为依据，带体检与复测脚本，覆盖到成片复测。见 [references/skill-composition.md](references/skill-composition.md)。

## 可信度卡与案例

- [skill-card.md](skill-card.md) / [skill-card.yaml](skill-card.yaml)
- [cases/cases.json](cases/cases.json)：参考包络的建立；《为什么是梅西》v1.0 体检
- [pricing-card.yaml](pricing-card.yaml)

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+（标准库）
- FFmpeg 与 ffprobe
- PyYAML（只用于 Skill 校验）
- `lov-branding-consistency`

## License

MIT。不授予参考视频或任何第三方素材的使用权。
