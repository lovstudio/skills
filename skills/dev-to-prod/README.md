# 生产就绪助手 · Production Readiness

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

把开发态项目转化为经过真实构建与原生验证的生产制品，并在用户明确授权时完成可恢复的本地安装；它不会擅自把版本发布到外部渠道。

## 本地安装

在本仓库根目录执行：

```bash
python3 "$SKILL_CREATOR_DIR/scripts/init_skill.py" dev-to-prod \
  --path "$SKILL_SOURCE_ROOT" \
  --install-dir "$SKILL_SKILLS_INSTALL_DIR"
```

设置变量为你的 Skill Creator 源目录、Skills 源根目录和本地 Agent Skills 目录。安装后，`lov-dev-to-prod` 应解析到 `dev-to-prod-skill` 这个源目录。

## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享
Profile 读取用户、品牌、工作区和本 Skill 的长期记录。用户直接说出的持久
偏好或品牌事实由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

```text
把这个 Tauri 项目从 dev 转成 prod，先做生产就绪检查，再安装到本机应用程序。

Turn this dev app into a verified production build. Keep it local; do not publish it.
```

每次运行先使用 `scripts/production_audit.py` 生成基线，再按目标平台执行真实构建、测试、签名和安装验证。有关接受条件与平台边界，见 [`references/production-readiness.md`](references/production-readiness.md)。

## 原子组合

每个新 Skill 都带有 `references/skill-composition.md`。它记录已检查的相邻
Skills、可选的上游/下游交接、重叠处理，以及为何选择 Single Skill 或自包含
Skill Kit；外部 sibling Skill 不作为隐藏依赖。

## 可信度卡与用户案例

每个新 Skill 都必须随源代码提供：

- `skill-card.yaml` / `skill-card.md`：用途、负责人、依赖、风险、输出与维度地图。
- `cases/cases.json`：至少一个真实的 Input → Prompt → Output 案例。
- `pricing-card.yaml`：免费或付费都要写清价值锚点、交付边界和复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+
- 目标项目的构建工具与平台验证工具
- PyYAML 仅用于运行本源目录自带的验证器

## License

MIT
