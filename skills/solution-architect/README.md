# lov-solution-architect

![Version](https://img.shields.io/badge/version-0.2.0-CC785C) ![Free](https://img.shields.io/badge/Free-green) ![Category](https://img.shields.io/badge/category-business-blue)

把产品或技术需求转成有调研依据、开源优先的可执行解决方案。

Part of [skill-publisher/skills](https://example.com/skills/skills) — by [example.com](https://example.com)

## Install

```bash
npx skills add solution-architect -g -y
```

## Use Cases

- 技术方案：架构、模块拆分、部署、运维和风险控制。
- 产品方案：用户流程、数据模型、功能边界和交付路线。
- 技术选型：对比开源库、商业 API、商业产品和自研方案。
- 客户方案：按 Skill Publisher.ai / 品牌工作室品牌预设生成解决方案内容。

## Usage

```text
/lov-solution-architect 我想做一个 AI 合同审阅产品，请给我技术方案
/lov-solution-architect 帮我比较一下自建 RAG 和商业知识库 API 的方案
```

Skill 会先确认真正阻塞的信息；如果没有阻塞，会直接给出假设并继续。输出包含结论摘要、需求理解、模块拆分、推荐架构、技术选型、实施路线、成本估算、风险应对和下一步。

## Principle

默认优先级：

1. 现代、活跃、体验好的开源 DIY 方案。
2. 仍然稳定可靠的传统开源方案。
3. 只有在差异化、隐私、安全或开源缺口明确时才自研。
4. 开源方案明显不如商业 API 时才选商业 API。
5. 只有买比集成或自建更合适时才选商业产品。

## References

- [Output template](references/output-template.md)
- [Selection rubric](references/selection-rubric.md)

## License

MIT
