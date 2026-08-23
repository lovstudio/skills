# lov-yoda-automation

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

把 Yoda 内的一次性或周期自动化变成可验证、可停止且不重复通知的计划。

## 本地安装

```bash
ln -s "/path/to/yoda-automation-skill" \
  "/path/to/agent-skills/lov-yoda-automation"
```

## 用户 Profile

本 Skill 读取 `user-profile/v1` 中的语言、时区、工作区和自身记录。用户明确给出的长期默认值可通过 `scripts/profile_store.py` 原子保存；可移植源代码不写入个人路径、账户或凭据。详见 [用户 Profile](references/user-profile.md)。

## 使用

### 工作日催款提醒

输入：“在 Yoda 里每个工作日北京时间 10 点提醒我跟进活动款项，到账后停止。”

输出：一条活跃的 Yoda 原生自动化，使用 `0 10 * * 1-5`、`Asia/Shanghai`、未来的 `next_run_at` 与明确的收款后停用规则。

### 修复没有下次执行的自动化

输入：“这条自动化显示等待生成下一次计划，帮我修复并核验。”

输出：定位单次时间误写入 cron、缺失时区或过期 next run 等根因；保存修复后的记录，并回读计划字段和最新运行结果。

## 原子组合

本 Skill 的组合边界记录在 [skill-composition.md](references/skill-composition.md)。通用工作流设计、飞书投递和业务领域巡检保留为可选交接，不作为隐藏依赖。

## 可信度卡与用户案例

- [Skill Card](skill-card.md)
- [真实案例](cases/cases.json)
- [定价依据](pricing-card.yaml)

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/verify_automation.py --help
```

## 依赖

- Yoda 原生自动化能力
- Python 3.8+（只读验证脚本）

## License

MIT
