# Skill Group Composition

## Nearby Skills Inspected

2026-09-23 检查本地真源 SKILL.md，并核对共享、Codex、Claude 安装入口的真实指向。
以下按实际输入/输出合同分类。

| Skill | 输入 → 输出 | 关系与边界 |
| --- | --- | --- |
| lov-spectacular-ps | 原照片、可选参考 → 环境人像、可选对比/Prompt | core atom；拥有最终照片验收 |
| lov-professional-portrait | 单人照 → 职业形象照 | not composed；职业近景不是环境尺度目标 |
| lov-riso-portrait | 单人照 → Riso 插画头像 | not composed；介质和结果不同 |
| lov-image-creator | brief/参考图 → 通用图像或 Prompt | overlap（执行部分）；复用宿主能力，不复制 API/云脚本 |
| lov-image-decorator | 图片、caption、Logo → 有底栏的包装图 | downstream atom（可选）；仅在另要传播装帧时交接 |
| lov-branding-consistency | 场景、受众、文本 → 在位审校的说明/标签 | 横切文本门禁；不向头像加入品牌资产 |

## Atomic Handoffs

- 输入原子是用户选定、可实际查看的原图和可选参考图，以及角色表。不是上一 Skill
  生成的近景头像；本 Skill 负责身份与环境保真验收。
- 图像执行边界是宿主原生编辑工具；交接具名图片与场景化 Prompt，返回真实成片。
  本 Skill 检查照片，不能委托 API 成功状态代替验收。
- 可选下游 `lov-image-decorator` 接收已验收的 PNG/JPEG 与用户要求的 caption/Logo。
  它负责附加版式；无字成片独立保留。未经要求不自动调用。
- 品牌门禁接收即将交付的说明/标签及媒介上下文；不接管身份判断或原文引用。

## Overlap Decisions

没有发现已安装 Skill 以“环境尺度人像 + 参考身份隔离 + 真实对比”拥有相同完整结果。
通用造图和职业照部分重叠，复用图像工具与事实约束，保留本 Skill 独立的构图与场景验收
合同，不创建重复模型 SDK 或 Photoshop 自动化。

## Composition Decision

Single Skill：看图、构图、编辑、校验与对比围绕同一张照片，不形成独立业务产品。
对比 CLI 是局部确定性排版，不足以拆成 Kit。除品牌文本门禁外，不引入外部 sibling
硬依赖，不要求先运行职业照或装帧 Skill。
