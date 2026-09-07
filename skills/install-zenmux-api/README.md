# ZenMux API 接入

![Version](https://img.shields.io/badge/version-1.0.1-CC785C)

为应用接入 ZenMux 服务端代理，隔离密钥并验证请求链路。

## 安装

```bash
npx skills add lov-install-zenmux-api -g -y
```

## 使用

- 为应用接入 ZenMux 服务端代理，隔离密钥并验证请求链路。
- Integrate the ZenMux API through a secure backend.

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
