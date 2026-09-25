# 公众号排版 · WeChat Typesetter · Skill Card

## Description

`lovpen-cli` 把 Markdown 排版请求路由到已验收的 Lovpen CLI，默认输出与
Lovpen 微信公众号复制链一致的内联 HTML，也可输出独立 HTML，并同步返回
资源选择、文件大小、SHA-256 与运行边界。

## Owner

由 LovStudio contributors 维护。问题与产品上下文可通过
[Lovpen repository](https://github.com/markshawn2020/lovpen-obsidian) 反馈。

## License / Terms

Skill 指令与解析脚本采用 MIT License。用户仍需对输入文档、链接媒体和最终
输出的使用权负责。

## Use Case

适合希望在不操作图形界面的情况下检查 Lovpen 资源，或把 UTF-8 Markdown
稳定渲染为微信公众号内联 HTML/独立 HTML 的写作者、开发者与 Agent。输入是
Markdown、格式与套装/样式参数；输出是 HTML 或 `lov-cli/v1` JSON 诊断。

## Deployment Geography

全球本地部署。需要能够访问文件系统和启动子进程的 Agent runtime。

## Requirements / Dependencies

- `lovpen-cli` 0.2.0，或带有 ready `agent-harness` 的 Lovpen 源码目录
- Python 3.9+
- Node.js 20+
- Chrome/Chromium 109+（微信公众号格式）
- 源码模式需要 Lovpen 已安装的 workspace 依赖，包括 Vite
- 不需要凭证

## Known Risks and Mitigations

- 后端不可定位：先运行 resolver 与 `doctor`，返回带 `context_id` 的具体配置提示。
- 误解一致性范围：微信公众号格式回报共享 clipboard source 与解析后的 kit；
  未提供给 CLI 的 UI 持久化设置不冒充已复现。
- 覆盖已有文件：使用明确输出路径与 dry-run，写入由 CLI 原子完成并回读。
- 私密或受版权保护的输入：默认仅本地渲染，不在日志中复制全文，不代替用户作发布决策。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [CLI contract](references/cli-contract.md)
- [Skill composition](references/skill-composition.md)

## Skill Output

输出包括微信公众号内联 HTML、独立 HTML、Lovpen 资源目录或运行诊断。渲染
参数覆盖输入、输出、format、template kit/单项资源、标题、作者和 dry-run。
验收检查 `doctor`、输出文件、字节数、SHA-256、Lovpen article root、内联或
内嵌 CSS 契约、renderer/clipboard source、mode 和禁用插件列表。

## Skill Version

0.2.0

## Ethical Considerations

本 Skill 不上传内容或凭证；Chromium 只在本机处理临时渲染页，Skill 明确披露
一致性范围，并要求用户尊重输入内容及媒体的版权和授权范围。

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) 记录了实际 Lovpen README + Typora
Newsprint 微信复制渲染案例，包括 Prompt、解析后的 kit、字节数和回读 SHA-256。

### Dimension Map

- CLI contract correctness：14/14 测试与最终 validator 通过，1.0。
- Real backend fidelity：JSON 同时指向 Lovpen renderer 与共享 clipboard source，1.0。
- Artifact integrity：173,311 字节与 SHA-256 回读一致，1.0。
- Render-mode transparency：wechat/standalone 边界与设置范围完整披露，1.0。

### Pricing Basis

本地 Skill 免费：它是现有开源本地 CLI 上的意图路由与验收层，不包含托管算力。
详见 [`pricing-card.yaml`](pricing-card.yaml)。

### Distribution

- `lovstudio`：`local_installed`，已完成本地验证与链接安装。
- `github`：`not_published`，未创建远程仓库或 Release。
- `workbuddy`：`not_published`，未提供付费版本。
- `skillpay`：`not_published`，未提供付费版本。
