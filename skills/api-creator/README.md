# 网关工坊 · Gateway Studio

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

开发某个 app 需要 API 网关能力时，在 uni-api（FastAPI 聚合网关）后端为该 app 创建网关端点并
接入 /docs 分组，同时在对应 uni-app 前端封装统一调用层。Skill Kit 形态：backend 模块产出
网关端点清单，frontend 模块消费该清单封装前端调用层。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR"   "$SKILL_SKILLS_INSTALL_DIR/lov-api-creator"
```

## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享
Profile 读取用户、品牌、工作区和本 Skill 的长期记录。用户直接说出的持久
偏好或品牌事实由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

**示例一（完整流水线）**：开发某个 app 时需要网关能力，要求集成进 uni-api 并在 uni-app 前端封装调用层。
输入：app 名称、需要网关化的上游能力、uni-app 前端项目路径。输出：uni-api 内的网关端点与
/docs 分组、前端 api/ 调用层与用法示例。

**示例二（只做后端）**：后端已就绪，仅需为某 app 在 uni-api 里新增一组聚合接口。
输入：app 名称与上游能力。输出：网关端点清单（method + path + 说明）。

详细步骤见 [`SKILL.md`](SKILL.md) 与两个模块 `skills/backend`、`skills/frontend`。

## 原子组合

本 Skill 是自包含 Skill Kit：`backend`（网关端点创建）与 `frontend`（调用层封装）两个模块
各有独立输入/输出契约且可单独运行，也能以 `full` 流水线一次完成。相邻能力
`lov-install-zenmux-api`（Supabase 单一 AI 代理）与 `lov-refactor-api`（后端冗余重构）均保持
独立、不作为隐藏依赖。详见 `references/skill-composition.md`。

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

- 后端：uni-api（FastAPI）仓库与项目 poetry 环境；运行前提见仓库 AGENTS.md。
- 前端：DCloud uni-app 项目（含 pages.json 与 manifest.json）。
- 校验脚本：Python 3.8+、PyYAML。

## License

MIT
