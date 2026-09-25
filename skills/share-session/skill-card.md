# 会话分享 · Session Sharing · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

把一个 Agent 会话（Claude Code、Codex Desktop、Yoda 或任意 JSONL/JSON/markdown transcript）转成一条
免费公开或按 Credits 解锁的 LovStudio 分享页 URL。脚本负责读取并脱敏转录、归一化为合法
yodaSessionShareUpload 结构、登录 LovStudio 并上传，最后返回可复制链接或付费案例证据。

## Owner

- Team: Lovstudio
- Contact: https://lovstudio.ai

## License / Terms

MIT。可自由使用与分发；上传到 Lovstudio 的会话内容遵循 Lovstudio 服务条款。

## Use Case

- Audience: 需要把一个 Agent 对话分享给他人（微信、邮件、Twitter）的用户。
- Supported input: 自动探测当前会话，或显式 `--file` transcript / `--session-id`。
- Expected task: 拿到免费公开链接，或与目标 Skill / case 绑定的付费 Session。

## Deployment Geography

global。任何有 Python 3.10+ 的本地环境；上传走 LovStudio 线上端点。

## Requirements / Dependencies

- 运行时: Python 3.10+，标准库。
- 凭据: Lovstudio 账号。首次运行走 device-flow 授权，后续复用本地缓存的 refresh token；
  access/refresh token 只存本机 gitignore 文件，不写 durable profile records。
- 无第三方 pip / npm 包。

## Known Risks and Mitigations

- A one-off confirmation can be over-expanded, while an explicit reusable default can be ignored. Reuse standing authorization only when its trigger, target, sanitized payload, Lovstudio destination, and exclusions all match; otherwise ask for current consent.

1. 上传失败或命中 Cloudflare/TLS 指纹拦截。请求始终带浏览器风格 User-Agent 与 Accept
   头；报错保留服务器原始 message 与 HTTP status。
2. 会话含敏感信息。默认显示档 concise；内容级剥离被折叠进 `role=user` 消息的宿主
   上下文，发现异常残留时阻断上传，并脱敏主目录、明显 token、Authorization 和私钥；
   用户可显式指定 detail。
3. 严格 schema 校验失败。脚本先归一化到严格结构再上传；报错指明 invalid_session_share。
4. 付费附件绕过购买校验。付费模式拒绝附件，直到附件也走私有授权交付。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Skill Card standard](references/skill-card-standard.md)

## Skill Output

- Type: 一条 LovStudio 分享页 URL，可选结构化付费元数据。
- Format: text。
- Parameters: `--detail`（hidden/concise/detailed/verbose）、`--file` / `--session-id`、
  `--base-url` / `--token` / `--profile-path`，以及 `--paid-skill` / `--case-id` / `--json`。
- Validation: URL 可打开；payload 通过 strict schema；付费价格只来自服务端。
- Version: 0.4.1。

## Skill Version

0.4.1

## Ethical Considerations

只上传用户明确选择的会话内容；默认隐藏中间推理与工具正文。token 凭证不写 durable
records。不要把含密钥、密码的会话公开或付费分享。内容审核与撤回归 LovStudio 服务本身。

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json). Every case must show Input → Prompt → Output.

### Dimension Map

Machine-readable card records three dimensions — 结构正确性、端到端有效、一次成型 —
with named evidence and an explicit status per dimension. 结构正确性与一次成型为
verified；端到端上传已成功，公开页面正文仍需人工打开回读确认。

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). The Skill is free because it reuses
Lovstudio's hosted endpoint with no proprietary model or licensing cost.

### Distribution

Free channels: github, lovstudio. Paid channels declared but empty — nothing is
described as live when it is not.
