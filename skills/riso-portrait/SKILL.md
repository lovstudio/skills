---
name: lov-riso-portrait
description: >
  把单人照片用 gpt-image-2 重绘成身份保真的 Riso 头像，并检查五官、手指、饰品与圆形裁切。Use when the user asks“做成 Riso 人像”“生成孔版印刷头像”or “create a Riso portrait”。
license: MIT
compatibility: "Portable Agent Skills format. Requires image viewing and generative raster-image editing with gpt-image-2; no local image-processing dependency is required."
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio
  version: "0.2.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - riso
    - portrait
    - avatar
    - image-editing
    - identity-preservation
---

# lov-riso-portrait — Riso 人像

把一张单人照片直接重绘成适合头像使用的 Riso 插画：人物仍然一眼可认，画面使用
有限色墨、网点、纸张颗粒、粗线条和轻微套印偏移，而不是给原照片叠一层复古滤镜。

## Triggers

### Activate when

- 用户说“把这张照片做成 Riso 人像”“生成孔版印刷风格头像”“做成双色网点头像”。
- 用户要求保留人物身份、姿势和衣服特征，同时改成 Riso、Risograph 或孔版印刷视觉。
- The user asks to “create a Riso portrait”, “turn this photo into a Risograph avatar”, or “make an identity-preserving Riso profile picture”.

### Do not activate when

- 用户只想磨皮、提亮、换背景或制作职业照；使用 `lov-professional-portrait`。
- 用户要从多张样图提炼任意视觉风格，而不是生成 Riso 人像；使用风格分析能力。
- 用户要制作海报、信息图或带文字的传播物料；使用相应设计 Skill。
- 当前运行时无法调用 `gpt-image-2` 做图像编辑；不得用 Canvas、Sharp、CSS、双色映射或普通滤镜伪装成同等结果。

## User Profile (cross-session)

每次运行读取 `skill.yaml` 声明的 `user-profile/v1`，按当前请求、项目上下文、
`skills.lov-riso-portrait.records`、共享 Preferences 和安全默认值解析配色与裁切偏好。
只有用户直接声明的长期偏好才通过 `scripts/profile_store.py record --confirm` 保存；
照片、人物身份信息、临时 Prompt、访问凭据和生成结果不得写入 Profile。

## Skill Group Composition

运行前读取 `references/skill-composition.md`。本 Skill 独占“身份保真的 Riso 头像”
这一结果；相邻能力只通过原图或完成后的 PNG 可选交接，不构成隐藏依赖。

## Implementation paths are alternatives

读取 `references/implementation-options.md`。程序化滤镜、生成模型重绘和 AI 参数分析
结合确定性渲染是三种并列方案，不是必须依次执行的三个步骤。本 Skill 的默认交付仍是
`gpt-image-2` 直接重绘，因为它最能重新组织人物、色块、线条和网点；只有用户要求
研究实现方式、追求参数可控或批量一致性时，才讨论其他方案，不能把双色滤镜冒充默认
Riso 人像结果。

## Workflow (MANDATORY)

### Step 0: Resolve root and runtime

1. 解析 Skill 根目录，读取 `skill.yaml`、`references/riso-art-direction.md`、
   `references/quality-gate.md`、`references/implementation-options.md` 与
   `references/skill-composition.md`。
2. 确认运行时能查看输入图片，并能用 `gpt-image-2` 进行真正的栅格图像编辑。
3. 若模型不可用，明确停止并说明缺少 `gpt-image-2`；不能静默替换为程序化滤镜、
   其他模型或只交付 Prompt。

### Step 1: Inspect the source as the identity reference

- 把用户上传的照片视为编辑目标和人物身份的唯一事实来源。
- 确认输入是用户选择的原始照片或经核验的权威原图，而不是既有 Riso 结果、聊天缩略
  图、被错误裁切的中间产物。多张候选图时逐张记录来源与角色，不从成品反推原图。
- 检查脸型、五官比例、发型轮廓、神态、视线、姿势、衣服、饰品、手持物和手指。
- 识别图片是否适合头像裁切：人脸是否清晰，发顶是否完整，视线前方是否有留白。
- 多人照片默认不执行；先请用户明确主角或提供单人照片。
- 只裁头部或头像用途时，先比较圆形裁切后的辨识度、视线留白、背景噪音和缩略图对比，
  再决定源图；不能只按全图“最好看”排序。
- 不把照片、结果或人物信息公开上传，除非用户另行授权。

### Step 2: Resolve the smallest sufficient brief

默认输出为 1:1 近景头像，适配圆形裁切。使用深炭黑、青绿、朱红和暖纸色；保留
纸张颗粒、网点、粗线条、不完全均匀的墨边与轻微套印偏移。当前请求可以覆盖配色、
景别或背景，但不能无声改变人物身份、年龄、姿势、服装或饰品。

只在缺失信息会明显改变人物或头像用途时问一个问题；普通配色与裁切由安全默认值补齐。

### Step 3: Build the identity-locked edit prompt

读取 `references/riso-art-direction.md`，让 Prompt 明确包含：

1. `style-transfer` 用例和 `1:1 social profile avatar` 资产类型；
2. 输入图是 edit target 和 identity reference；
3. 人物身份、姿势、视线、服装和关键物件保持不变；
4. Riso 的有限色墨、网点、纸张、手绘线条和轻微套印偏移；
5. 圆形头像安全区、完整发型轮廓和视线前方留白；
6. 禁止照片感、塑料皮肤、3D、普通动漫化、文字、Logo、水印和装饰边框。

用户的补充只作为 `Creator note` 加在模板末尾，不得覆盖身份锁和事实约束。

### Step 4: Edit directly with gpt-image-2

- 把原图作为 edit target 传给 `gpt-image-2`，使用高输入保真度和高质量方图输出。
- 让模型自己重组线稿、色块、网点与纸张关系；不在生成后追加灰度分版、双色映射、
  网角、噪点或套印滤镜。
- 非破坏性保存，建议使用“原文件名-riso-portrait-v1.png”。
- 第一轮只生成一个主版本，先验收再决定是否需要局部修正。

### Step 5: Inspect at three scales

按 `references/quality-gate.md` 检查：

1. 全图：人物、姿势、衣服和画面重心是否与原图一致；
2. 脸部近看：眼睛、鼻子、嘴唇、下颌、发际线和表情是否仍像本人；
3. 聊天列表与圆形裁切：缩小后是否仍可识别，发顶、下巴和视线是否被边缘吃掉。

另外逐项数清可见手指，检查耳饰、眼镜、项链、麦克风等高风险细节。整体氛围漂亮
不能替代事实检查。

### Step 6: Correct one fact at a time

- 身份漂移：重新强调脸型、五官比例、发型和神态，减少风格自由度。
- 太像滤镜：要求重新组织线稿与色块，禁止保留照片式连续明暗。
- 手指、饰品或物件错误：只修一个明确事实，并重复“其他人物特征、动作和风格不变”。
- 常识性错误：回到源图和真实世界事实确定正确数量、结构与空间关系，再做局部修正；
  不完全信任生成模型，也不因一个局部错误重做已经验收的整张图。
- 裁切不适合头像：只调整景别与安全区，不重做人物。

每轮只解决一个问题。修正后重新执行三尺度检查，避免修好手指却改坏脸。

### Step 7: Deliver

- 在运行时支持时直接展示最终 PNG，并报告保存路径。
- 简要说明采用的配色、裁切和有意修正；同时确认身份、姿势与关键物件被保留。
- 用户要求时另做原图/结果对照或迭代过程图，但不要把标签、水印或营销文字烘焙进头像。
- 过程图只展示真实发生且视觉上不同的阶段；删除重复结果，不补造畸形帧，并让局部
  问题在统一尺寸的小图中清楚可见。

## Completion Criteria

- 缩到头像大小仍能认出同一个人。
- 画面是重新设计的 Riso 插画，不是带颗粒的照片或双色滤镜。
- 五官、可见手指、饰品、衣服、姿势与视线没有事实错误。
- 圆形裁切不会切掉发顶、下巴或视线方向。
- 原图保持不变，最终 PNG 路径与模型边界已报告。

## Dependencies

- 可查看本地或上传图片的 Agent 运行时
- 可执行图像编辑的 `gpt-image-2`
- 生成服务可能产生模型调用费用；Skill 本身免费
