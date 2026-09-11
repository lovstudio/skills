# 反馈飞轮 · Feedback Flywheel

![version](https://img.shields.io/badge/version-0.3.0-blue)
![license](https://img.shields.io/badge/license-MIT-green)

把用户对 Agent 的情绪与判断变成可统计的反馈事件，再按最小作用域迭代系统提示词、
reference 与 Skill。被动情绪（“还是不行”“太失望了”）与主动 judge（`👍`、`👎`、
评分）走同一条闭环。源码公开，免费安装。

## 目录结构

```text
feedback-loop-skill/
├── SKILL.md                     # 唯一入口：评价、回扫、复盘、接入
├── skill.yaml
├── references/protocol.md       # 判定、作用域、状态机（自动链路单一真源）
├── references/store-schema.md
├── references/host-adapters.md
├── references/system-prompt.md
├── assets/system-prompt-block.md
├── scripts/
│   ├── feedback_store.py        # 账本：append / update / list / stats / verify
│   ├── scan_session.py          # 会话回扫
│   ├── report.py                # 满意度报告
│   ├── install_feedback_loop.py # 接入其他宿主
│   └── profile_store.py
├── cases/cases.json             # 真实用例
├── skill-card.yaml / skill-card.md
└── pricing-card.yaml            # 定价依据（公开价格在 catalog）
```

自动链路（情绪感知 → 落账 → 规则迭代）不经过 skill 路由，由根 Prompt 的
反馈与迭代规则驱动；Skill 只承载用户显式使用的能力。

## 安装

```bash
npx lovstudio skills add feedback-loop
```

本地开发直接使用源码：

```bash
cd feedback-loop-skill
python3 scripts/validate_skill.py .
python3 scripts/install_feedback_loop.py --host codex --dry-run
```

## 常用命令

```bash
python3 scripts/feedback_store.py append \
  --channel explicit --polarity positive --intensity 4 --kind praise \
  --evidence "做得很棒" --host codex --session-id demo --scope task
python3 scripts/scan_session.py --file ~/.codex/sessions/<日期>/<会话>.jsonl --last 40
python3 scripts/feedback_store.py stats --since 30d
python3 scripts/report.py --since 30d
```

账本默认在 `~/.feedback-loop/`，可用 `FEEDBACK_LOOP_HOME` 覆盖：

```text
~/.feedback-loop/
├── config.json
├── events.jsonl      # 追加式反馈事件
├── outcomes.jsonl    # 追加式处置与验证结果
└── reports/
```

## Profile 契约

声明共享 `user-profile/v1`：读取用户、品牌、工作区、偏好与
`skills.lov-feedback-loop`；长期偏好经 `scripts/profile_store.py record --confirm` 写回。

## 依赖

- Python 3.8+，仅标准库。
- `scripts/validate_skill.py` 需要 PyYAML。
- 不依赖外部服务；账本默认不上传。

## 质量门禁

```bash
python3 scripts/validate_skill.py .
python3 scripts/feedback_store.py verify
```

接入（`install_feedback_loop.py`）默认先 dry-run：显示将写入的宿主指令文件、
托管块校验和与技能链目标，确认后才落盘，并在改动前备份原文件。
