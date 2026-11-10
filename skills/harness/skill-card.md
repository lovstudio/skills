# Harness 驾驶舱 · Harness Cockpit · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

Harness 驾驶舱一次扫描看清本机 Agent harness 的三块内容：根 Prompt 怎样分发到各宿主、各宿主
装了哪些 Skill、自己维护的 Skill 源码处于什么状态；并提供先预览、后执行、可撤销的整理。
结果以本地驾驶舱、终端摘要或单文件快照呈现。

## Owner

Lovstudio.AI Skill maintainers — local source maintainers.

## License / Terms

MIT；按仓库内 `LICENSE` 使用、修改与再分发。

## Use Case

面向在一台机器上同时使用多个 Agent 宿主、并自己维护一批 Skill 的个人或小团队。规则文件、
Skill 安装目录和 Skill 源码散落在几十个位置时，用它看出哪里断了、重了、过期了，再安全地整理。
输入是本机的共享配置目录、各宿主目录、Skill 源码根目录与目录文件；不需要用户准备任何文件。

## Deployment Geography

全球；完全在本机运行，不联网，没有服务端。驾驶舱只监听回环地址。

## Requirements / Dependencies

无凭据。Python 3.9+（仅标准库）；git 可选，用于源码仓库状态；PyYAML 可选，用于目录对照与
严格的 frontmatter 校验；浏览器仅驾驶舱需要。已在 macOS 上验证，Linux 预期可用但尚未实测。

## Known Risks and Mitigations

- 整理改动了不想动的条目：默认只读；先出逐步计划并需要明确确认；只增删符号链接或移动条目，
  不删除实体文件；每个批次可撤销。
- 本地服务被其他网页或进程调用：只绑定回环地址并校验 Host；接口需要页面内的一次性令牌，
  写接口另需启动时显式开启；可读文件限定为本次扫描到的指令文件与 `SKILL.md`。
- 第三方 Skill 的名称或描述夹带脚本：界面只用纯文本写入动态内容，并用内容安全策略禁止内联
  脚本与样式。
- 快照、导出文件或截图带出私人配置：路径以家目录简写显示，远端地址只保留 owner/repo；
  导出位置与是否外发由用户决定。
- 依赖本地检出新旧的判断被当成事实：落后上游以上次 fetch 为准，目录与镜像以本地目录仓库为准，
  问题说明里写明了这一点。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [检查项与整理动作](references/checks.md)
- [Composition analysis](references/skill-composition.md)

## Skill Output

本地驾驶舱（HTML）、Markdown 摘要、快照 JSON、单文件只读 HTML 与整理记录 JSON。内容按
System Prompt、Skills、工作室三个区域给出现状、带稳定 ID 的问题清单和其中可自动整理的部分；
整理输出逐步计划、执行结果与可撤销的批次记录。验证方式是 `scripts/harness.py selftest`
与 `scripts/validate_skill.py`，整理的每一步在执行前还会重新核对前提。

## Skill Version

0.1.0

## Ethical Considerations

只读取用户自己机器上的 Agent 配置，不联网、不上传。规则正文与 Skill 列表属于用户的私人工作
环境，导出或截图前应由用户决定是否外发。整理只在用户明确同意后执行，且不替用户提交、推送或
发布任何内容。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)。目前有一个案例：创建当天在维护者本机的只读验收运行，
记录了输入规模、采用的最小 brief、真实的输出数字，以及除安装自身外没有执行整理这一事实。

### Dimension Map

| 维度 | 说明 | 证据 |
| --- | --- | --- |
| 覆盖面 | 一次扫描覆盖规则链路、已装 Skill 与 Skill 源码 | 本机 13 个宿主指令文件、共享目录与 64 个宿主 Skill 目录共 2883 个入口、239 个源码目录，用时 2.66 秒 |
| 识别准确 | 直接读取文件系统、frontmatter 与 Git，问题 ID 稳定 | selftest 核对 30 类问题；本机抽查 6 处与实际文件一致 |
| 可撤销 | 只增删符号链接或移动条目，逐批记录 | selftest 执行三个批次后依次撤销，布局还原 |
| 边界与只读性 | 默认只读，不触碰源码仓库与 Git 历史 | 只读模式下执行接口返回 403；本机验收除安装自身的 2 个链接外未执行整理 |

没有给出分数：目前只有一次本机验收，不足以支撑量化评分。

### Pricing Basis

见 [`pricing-card.yaml`](pricing-card.yaml)。官网目录免费条目（0 Credits），本地使用同样免费。
六维加权 2.7/5：证据只有一次维护者本机验收，同类检查有免费替代，先以免费入口积累使用证据。

### Distribution

免费渠道 `lovstudio`：官网目录的免费条目（0 Credits）。源码仓库是私有的，公开副本是
`lovstudio/skills` 里的镜像。`workbuddy`、`skillpay`：没有提出发布要求。
