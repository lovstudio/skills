# lov-npm-publisher

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

为新包和已有包建立可验证的 npm 自动发布链，兼容两种平级的认证方式：GitHub
Actions OIDC（trusted publishing，CI 免长期 token）与本地 granular NPM_TOKEN
（bypass，直接 `npm publish`）。首次引导一次，无需保存长期 token，也无需每次
执行 `npm login`。

## 本地安装

推荐 `npx skills add lov-npm-publisher -g -y`，或使用中间层安装，让不同 Agent
运行时解析到同一份源代码：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_AGENTS_DIR:?请设置共享 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$SKILL_AGENTS_DIR/lov-npm-publisher"
```

再从具体 Agent 的 Skills 目录创建指向共享层的相对链接。安装目标已存在时先检查，
不要覆盖其他 Skill。

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`。Skill 每次运行都会读取用户、工作区、偏好和
本 Skill 的记录；只有用户明确要求长期保留的非秘密设置才会通过
`scripts/profile_store.py` 写回。npm token、OTP、Cookie 和 OIDC assertion 永不保存。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

### 新包首次引导并切换到 OIDC

```text
帮我自动发布这个新的 npm 包，以后不要再次登录。
```

输出包括 registry 存在性判断、一次性 bootstrap 步骤、Trusted Publisher 配置、
无 token 的 `publish.yml`，以及首次版本的 npm registry 回读。

### 迁移已有包

```text
Publish this npm package from GitHub Actions without NPM_TOKEN.
```

输出包括现有工作流安全审计、保守迁移方案、OIDC 绑定命令和精确版本验证。

### 本地用 NPM_TOKEN 直接发布

```text
用 NPM_TOKEN 本地发布这个 npm 包，不要登录。
```

输出包括 granular NPM_TOKEN 检测、`auth.publish_command` 和精确版本验证；不会
生成 workflow，也不会打印 token 值。

先运行只读计划：

```bash
python3 scripts/publish.py /path/to/package --dry-run --json
```

确认后写入工作流（仅 oidc 模式；bypass 模式返回 `not-applicable`）：

```bash
python3 scripts/publish.py /path/to/package --write --json
```

## 原子组合

[`references/skill-composition.md`](references/skill-composition.md) 记录了与
`lov-release-via-cicd`、`lov-version-management` 和 `lov-skill-publisher` 的边界。
相邻 Skill 仅作为可选的制品交接，不是隐藏依赖。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md`：用途、风险、输出和维度证据。
- `cases/cases.json`：真实 Input → Prompt → Output 案例。
- `pricing-card.yaml`：免费策略、价值锚点和复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.9+
- Git、Node.js、npm
- GitHub Actions 托管 runner
- PyYAML（仅用于 Skill 源码校验）

## License

MIT
