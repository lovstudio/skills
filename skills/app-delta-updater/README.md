# 应用更新助手 · App Update Assistant

![Version](https://img.shields.io/badge/version-0.2.1-CC785C)

为 Tauri 与 Electron 桌面应用实现并验证自动更新，同时如实区分签名完整包和真正的差分更新。

## 本地安装

当前仅提供已验证的本地源码安装；尚未发布到公共 registry，因此不要猜测或执行
`npx skills add` 的 registry 安装命令。

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$SKILL_SKILLS_INSTALL_DIR/lov-app-delta-updater"
```

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`。用户明确要求长期保存的更新渠道、自动检查偏好或
delta-only 策略写入本 Skill records；项目路径与签名秘密不进入 Skill 源码。

## 使用

- “给这个 Tauri app 加自动发现、下载、安装和重启更新。”
  输出运行时插件、权限、签名产物配置、更新中心 UI、发布门禁与验证报告。
- “Add a Sparkle delta updater and verify the appcast.”
  输出 macOS delta 契约、架构专属 feed、回退策略与旧版到新版回读证据。

静态审计：

```bash
python3 scripts/audit_updater.py /path/to/project
python3 scripts/test_audit_updater.py
```

## 原子组合

`references/skill-composition.md` 记录相邻 Skills 与明确的工件交接。该 Skill 是独立的
Single Skill，不依赖外部 sibling 才能完成核心结果。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md`：用途、风险、输出和证据维度。
- `cases/cases.json`：真实的 Ataru Tauri 更新器实现案例。
- `pricing-card.yaml`：免费边界与复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/audit_updater.py /path/to/project --format json
```

## 依赖

- Python 3.8+（静态审计与审计器测试）
- PyYAML（仅 `scripts/validate_skill.py` 的 Skill 源验证）
- 目标项目自己的桌面构建与签名工具

## License

MIT
