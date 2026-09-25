# 公众号排版 · WeChat Typesetter

![Version](https://img.shields.io/badge/version-0.2.1-CC785C)

把自然语言中的 Lovpen 排版需求路由到已验收的 `lovpen-cli`。默认生成与
Lovpen “微信公众号复制”共享同一浏览器提取链的内联 HTML，也可显式生成独立
HTML，并返回 JSON 诊断、资源解析、文件大小和 SHA-256 回读证据。

## 本地安装

发布到 Skills catalog 后的标准命令：

```bash
npx skills add lovpen-cli -g -y
```

在 Skill 源目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$SKILL_SKILLS_INSTALL_DIR/lovpen-cli"
```

源代码保持可移植，不保存个人项目路径。运行时可通过 `LOVPEN_CLI`、
`LOVPEN_PROJECT_ROOT`、共享 Profile 或当前项目上下文解析后端。

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`。可读取工作区根目录、CLI 路径、输出目录、
默认模板套装、主题与高亮；只有用户直接声明为长期偏好的值才写入
`skills.lovpen-cli.records`。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

```text
/lovpen-cli 把 article.md 用 Typora Newsprint 套装排版为微信公众号 HTML
/lovpen-cli 列出当前 Lovpen 可用的主题、代码高亮和模板
Use /lovpen-cli to render this Markdown as self-contained HTML.
```

Agent 会先执行 `doctor`，必要时读取 `resources`，再调用真实
`renderStandaloneArticle` 与 `composeStandaloneCSS`。微信公众号格式还会在
Chromium 内运行共享的 `applyPreviewRenderPlugins` 和
`extractWechatClipboardHTML`，然后完成回读校验。

## 命令契约

详见 [`references/cli-contract.md`](references/cli-contract.md)。核心命令为：

- `doctor`、`info`、`capabilities`
- `resources`
- `render INPUT --output OUTPUT --format wechat|standalone`
- `--template-kit` 原子选择 UI 套装；或单独选择主题、高亮、HTML 模板
- 可选标题、作者和 dry-run

## 原子组合

本源是 Single Skill。`lov-cli-creator` 是生成 CLI 的可选上游，
`lov-skill-publisher` 是验证后发布的可选下游；两者都不是运行时隐藏依赖。
完整判断见 [`references/skill-composition.md`](references/skill-composition.md)。

## 可信度卡与真实案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)
- [`cases/cases.json`](cases/cases.json)
- [`pricing-card.yaml`](pricing-card.yaml)

案例来自已安装命令的 neutral-cwd 真实验收：Lovpen README 使用 Typora
Newsprint 套装生成 173,311 字节微信公众号 HTML，SHA-256 为
`85d00a183b88e4c59506f2279aa8629780011b1cf43f1dce4875032e7fd1a4d6`；
完整 CLI 验收为 14/14 测试通过。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/run_lovpen_cli.py --project-root PROJECT_ROOT -- --json doctor
```

## 边界

`wechat` 使用 Lovpen UI 的默认设置、同一内置套装和共享浏览器复制算法；UI
额外保存但未提供给 CLI 的逐文档设置不在一致性声明内。`standalone` 仍是
DOM-free 路径，并显式返回禁用插件。本 Skill 不负责平台发布或 Skill 上架。

## 依赖

- Python 3.9+
- Node.js 20+
- Chrome/Chromium 109+（微信公众号格式）
- `lovpen-cli` 0.2.0，或状态为 `ready` 的 Lovpen `agent-harness`

## License

MIT
