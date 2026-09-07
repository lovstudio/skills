# 经验萃取 · Lesson Distiller

![Version](https://img.shields.io/badge/version-3.7.1-CC785C)

将真实解决过程整理为可复用经验文档并维护知识索引。

## 安装

```bash
npx skills add lov-distill -g -y
```

## 使用

- 将真实解决过程整理为可复用经验文档并维护知识索引。
- Distill a solved problem into reusable knowledge.

支持自然语言调用，具体执行步骤与边界见 [SKILL.md](SKILL.md)。分析、预览和实际修改分开处理。

## 配置与依赖

读取 [共享 Profile](references/user-profile.md)；项目路径、输出目录与品牌来自当前请求或用户配置。
业务工具和目标系统依赖见工作流；公开文案使用 lov-branding-consistency 审校。

## 质量与案例

```bash
python3 scripts/validate_skill.py .
```

[案例](cases/cases.json) 记录真实迁移输入和输出，仅证明所声明的验收范围。
[Skill Card](skill-card.md) 与 [定价依据](pricing-card.yaml) 说明使用边界；业务运行结果须逐次回读。

## License

MIT
