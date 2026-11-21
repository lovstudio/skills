# 共绩算力 CLI · Suanli CLI · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

在对话里安全地查询与操作共绩算力（suanli.cn）的 Open API 与大模型云服务：随附由官方公开文档生成的 `lov-suanli-cli`、SDK 与本地 Swagger 代理，
共 83 个接口；默认只读，写操作与计费调用逐次征得用户同意，密钥只从环境变量或钥匙串读取。

## Owner

LovStudio（lovstudio.ai）。

## License / Terms

MIT。接口定义来自共绩算力公开文档与官方 Apifox 公开分享，版权归平台方；调用受平台服务协议约束，费用由用户账户承担。

## Use Case

使用共绩算力 GPU 云的开发者与运营者：查任务、存储、账单、可购资源；在确认后执行创建、停止、扩缩、下单；打开本地 Swagger 调试。

## Deployment Geography

全球；本地 macOS / Linux（钥匙串回退仅 macOS）。

## Requirements / Dependencies

Node.js 20+、Python 3.8+；用户本人的 Open API 密钥（大模型接口另需大模型 API Key 与账户余额）；无 Skill 运行依赖，接口变化时由 `lov-cli2anything` 重新生成。

## Known Risks and Mitigations

- 误执行写操作或产生费用 → `gjkj_cli.py` 发出前拦截，必须带用户对这一次调用的原话同意；先 dry-run。
- 密钥泄漏 → 只从环境变量或钥匙串读，doctor 只报长度，dry-run 只显示是否提供。
- 接口与文档不一致 → 每个操作标证据等级，未实测接口如实报告差异。

## References

`SKILL.md`、`references/commands.md`、`references/auth.md`、`references/errors.md`、`references/regenerate.md`、`references/skill-composition.md`。

## Skill Output

接口查询结果摘要（JSON / Markdown）、写操作的 dry-run 请求与执行后回查、本地 Swagger 页面。

## Skill Version

0.1.0

## Ethical Considerations

只用用户本人的账号与密钥；不代填、不保存、不复述密钥；不绕过鉴权或权限；产生费用的操作先说明并取得同意。

## User Cases

- 从公开文档生成共绩算力 CLI 并只读实测：83 个命令，14 个只读接口实测成功，两类真实错误的处理写入参考资料（`cases/cases.json`）。

## Dimension Map

| 维度 | 说明 | 证据 |
| --- | --- | --- |
| 接口与调用正确 | 命令、参数与签名与平台一致 | 14 个只读接口实测 0000；随附 CLI 再调 storage-get-regions 成功 |
| 写操作与费用可控 | 未经同意不执行 | 未带 --approved 的写操作被拒；Swagger 代理默认拒绝写操作 |
| 错误可诊断 | 鉴权、余额、密钥问题能快速定位 | A003 与 insufficient_quota 的定位过程写入 references/errors.md |

## Pricing Basis

免费入口（作者决定）。六维加权约 2.28 / 5：单一平台、接口来自公开文档、可由 cli2anything 重新生成（`pricing-card.yaml`）。

## Distribution

- 本地：已安装（三层链接解析到源码目录）。
- GitHub：私有仓库 lovstudio/gjkj-cli-skill。
- LovStudio 官网：已上架（live，免费）。lovstudio.ai 详情页显示 0.1.0，隔离试装通过；lovstudio.cn 待国内镜像同步。WorkBuddy、SkillPay：未发布。

## LovStudio Evidence

- 只读实测与 Swagger 调试通过；从本 Skill 随附副本再次只读调用成功，写操作拦截生效。
