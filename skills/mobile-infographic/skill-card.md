# Skill Card — lov-mobile-infographic

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

把已有结论的内容重排成 1080 宽竖屏可读的证据型信息卡，交付可编辑 HTML、2× PNG 与可复核的
移动可读性审计报告；支持单卡与三到五张的系列。

## Owner

LovStudio Skills · https://lovstudio.ai/skills/mobile-infographic

## License / Terms

MIT。源码可自由使用与修改；用户提供的素材、引文与数据版权仍归原权利人。

## Use Case

读者是需要把结论发到手机渠道的创作者、产品与运营人员。典型任务：把一段结论做成一张竖屏卡、
把一组要点做成三到五张可连续滑动的系列卡、为已有卡片补口径与来源标注。

## Deployment Geography

global。运行在本地 Agent 会话；没有浏览器时只能使用 `scaffold` 与 `init-brand`。

## Requirements / Dependencies

- Python 3.8+，标准库即可运行 `scaffold` 与 `init-brand`。
- `render` 与 `audit` 需要 Playwright for Python 以及 Chromium 或 Google Chrome。
- 需要中文字体之一：PingFang SC、Hiragino Sans GB、Microsoft YaHei。
- 无必需凭据；不访问网络。

## Known Risks and Mitigations

| 风险 | 缓解 |
| --- | --- |
| 为塞进一屏而缩小字号或删掉口径 | 字号下限、行宽上限与口径检查进入机器审计，低于阈值即失败 |
| 把机器审计当成“好看”的证据 | audit 自述为代理指标，发布前必须做原图与 320px 缩略图复核 |
| 数字缺少单位、周期或分母被误读 | `metric-focus` 强制单位与对比基准，`evidence_linkage` 要求编码元素挂在来源上 |
| 品牌强调色直接用于文字导致对比度不足 | 文字强调统一使用 `accent_ink`，按 4.5:1 与 3:1 分档检查 |

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [手机可读性标准](references/mobile-reading-standard.md)
- [模板语法](references/template-grammar.md)
- [HTML 契约与 audit 字段](references/spec-schema.md)
- [系列与导出](references/series-and-export.md)
- [品牌与用户配置](references/user-config.md)

## Skill Output

可编辑 `card.html`（内联 CSS 与 data URL 品牌 Logo）、2× PNG（默认 2160 宽，`3:4` 时为
2160×2880）、`brief.md`、`source.md`、`audit.json`，系列另附 `manifest.json`。
参数：`ratio` 取 `3:4`、`4:5`、`9:16`、`1:1`、`long`；`scale` 默认 2；`series-index` 与
`series-size` 控制页码范围。校验：字号下限、行宽上限、对比度、安全区、裁切与越界、单一结论、
证据挂载、品牌页脚、系列页码、骨架文案残留。

## Skill Version

0.1.0

## Ethical Considerations

只处理用户有权使用的材料；引用、转录与标识符保持原样，不改写事实。审计报告与卡片内不得写入
凭据、Cookie 或私密路径。涉及金融、医疗或法律判断的卡片必须保留口径与来源，不用视觉确定性
掩盖不确定的前提。

## User Cases

See [`cases/cases.json`](cases/cases.json). 已记录一个真实案例：三张 `3:4` 的 harness 行动指南系列，
机器审计 3/3 通过（各 100/100），附原图与 320px 缩略图复核结论。

## Dimension Map

| 维度 | 含义 | 证据 | 当前状态 |
| --- | --- | --- | --- |
| 移动可读性 | 真实观看距离下能读完 | 字号下限 72/50/36/26px、行宽上限、对比度 4.5:1 | 100 |
| 证据完整性 | 数字与判据可追到来源、口径、单位 | `evidence_linkage` 检查与 brief 证据表 | 100 |
| 竖屏版式正确性 | 不越界、不裁切、系列一致 | `canvas`、`overflow`、`out_of_bounds`、`safe_area`、`series_page` | 100 |
| 品牌一致性 | Logo、署名与强调色可用 | `brand_footer`、`accent_ink` 对比度、`brand_origin` | 100 |

## Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). 免费；价值在于降低重复返工并让每张卡自带可复核报告。
不包含内容写作、事实核查、生图与平台发布。

## Distribution

- 免费渠道：`github`、`lovstudio`（本地源码已就绪，尚未发布）。
- 付费渠道：暂无计划。
