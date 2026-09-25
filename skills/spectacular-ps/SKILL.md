---
name: lov-spectacular-ps
description: >
  将旅行或户外照片修成保留本人特征的环境人像大片，兼顾微信头像裁切，按需附真实对比图与复刻 Prompt。用于“修成有气势的头像”“像参考图一样帅”或 “make a cinematic environmental portrait”。
license: MIT
compatibility: "Image viewing and native generative image editing. Python 3.9+ for Profile and validation; Pillow for optional exact comparison boards; PyYAML for validation."
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - portrait
    - photo-editing
    - identity-preservation
    - environmental-portrait
    - avatar
---

# 人像大片 · Spectacular Portraits

把旅行、户外或城市人像修成有环境气势、仍然像本人的照片。优先改善人物与环境的比例、
构图、光影和色彩。PS 指修图结果，不要求 Photoshop，也不承诺 PSD 图层或自动操作微信。

## Triggers

### Activate when

- “把这张旅行照修成有气势的微信头像，附对比图与可复刻 Prompt。”
- “没有参考图帅；保留我本人和动作，让环境更有气势。”
- “海边这张做出电影感，但保留原天气、灯塔、红色外套和姿势。”
- “Make a cinematic environmental portrait from my photo; keep my identity.”
- “Create a dramatic travel avatar and an accurate before/after comparison.”

### Do not activate when

- 申请文书或 personal statement 中的 PS；不把它解释为照片任务。
- 职业证件照、纯磨皮提亮或换发型；可交接 `lov-professional-portrait`。
- Riso、动漫或插画重绘；使用对应风格能力。
- 仅加 Logo、图注或边框；可交接 `lov-image-decorator`。
- 只询问方法或要求 Prompt：可给建议/提示词，不能声称已完成修图。

## User Profile (cross-session)

每次读取 [skill.yaml](skill.yaml) 和 [Profile 合同](references/user-profile.md)。
无专用运行时则调用 `scripts/profile_store.py read --skill-id lov-spectacular-ps`。
只使用声明的语言、时区、输出目录、比例、构图与调色偏好；当前请求与项目上下文优先，
其后是显式环境值、Skill records、共享 preferences/Profile、安全默认值。

只有用户直接声明“以后都这样”的偏好才通过 `scripts/profile_store.py record --confirm`
写入 `skills.lov-spectacular-ps.records`，并报告实际保存路径。原图、脸部信息、地点、
临时 Prompt、凭据和从单次满意结果推断的偏好都不写入 Profile。

## Skill Group Composition

读取 [能力边界](references/skill-composition.md)。本 Skill 对最终环境人像及比较交付负责；
不需要先跑职业照再重绘。相邻 Skill 只作可选制品交接。品牌审校只约束创作型说明与标签，
不改原始资料，也不向个人头像强加 Logo、水印或宣传文案。

## Workflow

### 1. Inspect and assign image roles

先实际查看每张输入图，再建立角色表：

- **original / edit target / identity source**：用户原照片，人物事实的唯一依据。
- **style reference**：只借鉴景别、人物/环境比例、光影层次、配色与气氛。
- **rejected output**：已否定版本，只记录错误；不再作为原图或新一轮身份来源。
- **approved output**：已选定成片，用于对比及定向修正，不能倒推替代原照片。

记录面部可见度、衣服/饰品、动作、身体比例、光线、天气、地标和画幅。不移植参考图
人物的脸、衣服、姿势或地点。多张照片无法确定编辑对象时只问一个聚焦问题。
缺原图时请求原图，不能用聊天缩略图、旧生成图或文字凭空复建身份。

### 2. Resolve the brief and scene boundary

从请求推断用途、画幅与效果；不要求用户选技术方案。

- 微信头像默认 1:1，但“头像”不自动等于胸部以上大头照。强调山海、旅行和气势时优先
  环境人像；没有头像用途时保持原比例，除非用户要求重裁。
- **写实后期（默认）**：裁切、曝光、局部提亮、对比与色彩调整；保留真实天气、地标、
  山脊、物件及空间关系，不新增云雾、不改变山体尺度、不删除物件。
- **艺术化环境处理**：仅在用户已要求或授权时，增强云雾、空间纵深、前景疏密或改背景。
  明确列出允许改变的元素。无授权且方案依赖场景重构时，先完成可独立的构图分析，
  再问是否允许该项改变。“更帅”或“像参考图”本身不等于任意换背景。

保留脸型、五官比例、表情、肤色、年龄感、衣服、饰品与姿态。不能把“有气势”执行成
换脸、瘦脸、换装或健美化。用户授权改其中某项时只放开那一项。

### 3. Direct composition before retouch

明确前/中/后景、视觉重心和尺度关系，让环境有空间，同时让人物缩小后仍可识别。
不要机械套用“人物居中偏下”，也不要一律换成冷色。

雪山张臂案例可参考头部位于画面高度约 45%–50%、展示至大腿/膝部、山体占上半部；
这是案例参数，不是通用硬规则。脸和躯干应落在圆形头像安全区；全手臂入方图与全部
落在圆形范围可能冲突，先保脸/躯干，再调整景别，禁止拉伸肢体。

自然肤色、黑衣材质、雪地高光和一致光向约束调色。背景整理优先压低杂色与局部对比；
删减前景或改结构必须属于已授权的艺术化范围。

### 4. Build and execute the edit prompt

读取 [Prompt 模板](references/prompt-template.md)；雪山场景另读
[真实雪山案例](references/mountain-example.md)。写清角色、保留项、允许改动、构图、
光影和避免项。不把示例的黑衣、经幡或雪山带入其他照片。

使用宿主原生图像编辑能力，遵循当前工具协议。不硬编码模型、私有端点或密钥。
无图像编辑能力时说明缺失；只有用户接受 Prompt 交付或原本只要 Prompt，才以文本完成，
不能把文本建议、SVG 或普通滤镜当成已修好的照片。

本地原图先查看后传给编辑工具；全部目标有本地路径时用路径机制，否则用宿主支持的
最小近期图片集合。逐一说明多图角色；具体参数以当前工具协议为准。
保留原文件；第一轮生成一张主版本，避免连续重绘导致身份漂移。

### 5. Review and iterate

按 [质量门禁](references/quality-gate.md) 查看全图、脸部细节、缩略图和圆形裁切。
检查脸、手、眼镜、头灯、背包带、衣服边缘、光向与场景事实。不能凭 Prompt 写过
“保真”就报告身份已保留。

将反馈落到可观察维度：

- “没有人家帅”：比较景别、人物/环境比例、姿态呈现、光影与色彩，保留本人。
- “脸不像”：回到原图身份源，减少风格自由度，优先纠正脸部。
- “山没气势”：先放宽景别、恢复环境层次，未经授权不换山、不捏造尺度。
- “太假”：减少 HDR、过锐、塑料肤质与不一致的边缘光。

每轮只做必要的定向修正，并复查保留项；不自动反复生成直到某个主观分数达标。

### 6. Deliver the selected result

默认交付选定成片及简短改动说明；用户要求时另交付：

1. **真实对比图**：按 [对比规范](references/comparison.md) 用原图和选定成片排版。
   禁止让生图模型重新画“原图”。缺少可回读的原始像素文件时分别展示已有图片或说明
   无法完成精确拼接，不把生成式对比示意冒充真实前后对比。
2. **可复刻 Prompt**：附实际使用的场景化 Prompt、图片角色、可用时的模型与规格、
   有意改动范围。复刻的是处理方向，不保证像素一致；不编造 seed、参数或模型名。

宿主支持时直接展示图片，提供实际可访问的文件路径。艺术化处理的天气、地形、前景
单独说明；未亲自检查的事实不写成已验证。不要自动替换头像、公开上传照片或发布案例。

## Output Contract

- 成片：一张已查看的栅格照片；头像模式为 1:1，默认无文字、Logo、边框、水印。
- 可选对比 PNG：左原图、右成片，保留两图完整画面和比例；标注缩放事实。
- 可选 Prompt 文本：身份源、风格参考、保留项、允许变化、构图光影、负面约束。
- 验收状态：区分已生成、已回读、待确认，以及写实调整和艺术化改动。

## Dependencies and Validation

- 原生看图与栅格图像编辑；不依赖 Photoshop、Computer Use 或外部 sibling 流程。
- Python 3.9+ 用于 Profile、源校验和对比；Pillow 仅用于用户要求的真实文件拼接，
  不替代生成式修图；PyYAML 用于源校验。不自行安装全局依赖。
- `lov-branding-consistency` 审校说明、标签与交付文本，保留源引用及标识符。
- 源包验证：`python3 scripts/validate_skill.py .`。
- 必须完成真实制品质量门禁；格式校验和历史案例不能替代本次照片检查。
