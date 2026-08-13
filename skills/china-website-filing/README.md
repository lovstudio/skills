# lov-china-website-filing

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

中国大陆网站备案与上线 Skill Kit，覆盖 ICP、备案后域名切换、公安联网备案、安全评估分支和状态巡检。

## 本地安装

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILL_SKILLS_INSTALL_DIR/lov-china-website-filing"
```

当前 Creator 初始化流程会在指定安装目录创建同名软链接。

## 使用

- “给这个公司网站做 ICP 备案，域名在腾讯云，先检查准备条件。”输出场景分类、材料与实名/接入资源缺口、不能提前开放的门槛。
- “ICP 已通过，继续绑定域名并完成公安联网备案。”输出部署验收、公安表单字段、人工确认点、权威状态与巡检记录。
- “每天检查这个备案订单，没变化就静默。”追加台账并仅在状态变化或需要用户动作时报告。

## 自包含模块

1. `filing-readiness`
2. `icp-filing`
3. `domain-cutover`
4. `public-security-filing`
5. `filing-monitor`

组合关系见 [`references/skill-composition.md`](references/skill-composition.md)，机器可读流水线见 [`kit.yaml`](kit.yaml)。

## 台账 CLI

```bash
python3 scripts/filing_record.py --help
python3 scripts/filing_record.py check --path ./website-filing-record.md
```

## 可信度卡与用户案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)
- [`cases/cases.json`](cases/cases.json)
- [`pricing-card.yaml`](pricing-card.yaml)

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 -m unittest discover -s tests -v
```

## 依赖

- Python 3.8+
- PyYAML（仅源校验）
- 实时操作所需的浏览器控制与已登录权威页面会话

## License

MIT
