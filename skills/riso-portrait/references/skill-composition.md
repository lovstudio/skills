# Skill Group Composition

## Nearby Skills Inspected

- `lov-professional-portrait`：保留照片媒介，负责职业照精修、提亮、去帽和背景整理；
  它不生成 Riso 插画，因此不是重叠实现。
- `lov-image-creator`：通用生图、代码渲染和 Prompt 工程框架；它可以提供图像工具，
  但不拥有身份保真的 Riso 头像验收。
- `lov-style-clone`：从文章提炼写作文风并改写文本；输入输出都不是人像图片，不组合。
- 运行中的 Imagine `Riso 人像工坊`：产品内的真实实现证据，使用 `gpt-image-2`、
  高输入保真度和同一视觉基准；它不是安装式 sibling Skill。

## Atomic Handoffs

- 上游输入由用户或照片选择能力提供一张获得授权的单人图片；本 Skill 从身份检查开始负责。
- 核心原子是 `lov-riso-portrait`：输入原图和最小 brief，输出通过人物、Riso 媒介、
  事实细节与头像裁切验收的 PNG。
- 下游 `lov-image-decorator`、文章排版、社交发布或头像上传能力可以消费最终 PNG；
  它们不能替代本 Skill 的身份与解剖检查。
- `lov-professional-portrait` 可在用户明确要求时先修复曝光或背景，但其输出必须重新
  作为本 Skill 的唯一 identity reference，不能在两项能力之间隐式混合身份。

## Overlap Decisions

没有发现拥有同一结果契约的独立 Skill。通用生图不能保证采用 `gpt-image-2`，职业照
保持照片媒介，Imagine 则是产品运行实现。新 Skill 复用已验收的视觉契约和质量门，
不复制 Imagine 的任务持久化、鉴权或服务端代码。

## Composition Decision

本源是 Single Skill。原图检查、Prompt 约束、直接重绘、三尺度验收和局部修正共同
服务一个头像结果，拆成 Kit 会增加身份漂移风险。相邻能力均通过图片文件可选交接。
