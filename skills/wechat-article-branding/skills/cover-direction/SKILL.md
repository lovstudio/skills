---
name: lov-wechat-branding-cover-direction
description: >
  将文章主题和参考图转为成熟的公众号品牌封面，管理素材来源、Logo 完整性与双比例裁切；用于“重做封面”“不要 AI 味”、"create an editorial WeChat cover"。
license: MIT
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "0.6.4"
  tags:
    - cover-design
    - editorial-art-direction
    - brand-integrity
  compatibility: "Embedded module; image generation, editing, or licensed-media retrieval is selected per task."
  dependencies: []
---

# 封面艺术指导 · Cover Art Direction

把文章命题翻译为一个克制、可辨认并适合公众号真实裁切的视觉世界。

## Triggers

### Activate when

- 用户说“参考这个成熟账号重做封面”“封面不要像 AI”“加入品牌 Logo”。
- Branding 管线启用封面生成、重构或替换。
- The user asks to "create an editorial WeChat cover" or improve an AI-looking cover.

### Do not activate when

- 用户只要求提取参考图 Design DNA，不需要封面成品。
- 当前封面已经通过审美、品牌和裁切验收且用户未要求变化。

## Workflow (MANDATORY)

1. 读取文章命题、参考图和品牌 Profile。
2. 先检索与文章命题、构图比例和发布语境匹配的真实艺术作品，并核对馆藏页与权利状态；只有选择生成式方向时才读取 `$KIT_DIR/prompts/cover-hero-editorial-painterly.md` 并生成完整制作 Prompt。
3. 提取参考图的信息层级、焦点、留白、色彩、素材类型和品牌权重，不照抄其身份元素。
4. 解析 `wechat_article_branding.cover_composition.art_direction`；默认按“公共领域或授权明确的真实艺术作品 → 真实摄影 → 生成式画面”的顺序选择素材。深度文章在主题与构图匹配时优先使用博物馆开放馆藏，选择理由必须服务文章而非工具偏好。
5. 需要外部素材时记录作品、作者、来源、使用状态和原始 URL。
6. 从 `publication.cover_logo` 加载发布主体的封面专用 Logo；字段缺失时才回退到 `publication.logo`。同时传递 `publication.cover_logo_variant`，对 `white` 等显式变体做像素验收。保持字形、字距、拼写和透明区域，不用生成模型重画品牌标识。`brand` 工作室、母品牌与 `products` 产品资产均不得作为默认替代。
7. 先构图 `2.35:1`，同时保护中心 `1:1` 安全区。
8. 控制视觉焦点；默认避免模板化蓝紫渐变、机器人、代码 UI、霓虹和无意义科技粒子。
9. 使用真实作品时保存作品、作者、年代、馆藏页、原图 URL、权利状态与处理方式，并为正文生成“本期封面”；使用生成式画面时保存完整制作 Prompt，再派生读者 Prompt。
10. 启用 `opening_hero` 时，基于同一视觉世界制作独立正文首屏；默认采用 `3:4` 竖向构图、Logo 底部居中、导语之前，并避免继承导语卡片或正文容器样式。平台页面已展示文章标题时，正文不得在首图之前再输出同名一级标题。
11. 输出 PNG、上传用 JPG、裁切预览，以及与制作方法匹配的作品来源记录或 Prompt 记录。
12. 上传后检查平台实际预览和 CDN 成品，而不是只检查本地文件。

## Art direction contract

- `type: hero` 需要一个可识别的主视觉隐喻和宽画幅张力，不用零散装饰拼出“看起来像封面”。
- `style: editorial` 需要有作者感的构图、材质和留白；`rendering: painterly` 使用绘画、纸艺或版画肌理，避免未经选择的暖色桌面静物和图库式产品摄影。
- `palette: elegant` 可使用克制的珊瑚、灰蓝、墨色、奶油色和少量金属色，但不把整张图压成单一橙棕色。
- `text: none` 时，底图不得出现标题、字母、数字、伪文字、Logo 或水印；官方 Logo 由 `cover-composition` 在生成后分别合成。
- `center_safe_zone: true` 时，中心区域保持低细节和足够对比度，供横版 Logo 居中使用；`square_bottom_logo_safe_zone: true` 时，中心方形裁切的底部中央同样保持安静，供方版 Logo 使用。

## Artwork note or Prompt publication

真实艺术作品默认在结论后、品牌尾注前写“本期封面”，展示完整原作并介绍作品、作者、年代、馆藏背景、与文章命题的关系、来源页与权利状态。生成式封面才读取 `$KIT_DIR/references/cover-prompt.md` 与 `$KIT_DIR/prompts/cover-hero-editorial-painterly.md`，并按配置公开清理后的读者 Prompt。两种说明默认二选一，不把真实作品加工伪装成纯文本生成。

## Decision rule

当“生成得更精细”仍然保留明显模型审美时，优先改变素材策略和信息层级，不继续堆叠 Prompt。确定性裁切、调色和官方 Logo 合成可以优于再次生成。

## Validation

- 封面只有一个主要视觉焦点。
- 横版与方形裁切都保留主题和品牌。
- Logo 高对比且不变形。
- Logo 对应 `publication.name` 的发布主体，而不是工作室、母品牌或产品。
- 配置 `publication.cover_logo_variant` 时，最终像素与该变体一致；不得因 `publication.logo` 回退顺序而使用错误颜色。
- 素材来源可回溯。
- 真实作品有可回溯的作品背景与权利记录；生成式封面的制作 Prompt 与公开 Prompt 分离，公开版本不泄漏本地路径或内部上下文。
- 启用正文首屏时，首图位于导语之前并保持独立视觉容器。
- 竖向首图为 `3:4`，使用同一官方 `publication.logo`；它是正文第一块，之前没有重复的文章标题。
- 文章标题由平台叠加时，画面仍留有可读区域。

## Dependencies

按任务选择图像生成、图像编辑、公共素材检索和真实页面预览能力。

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
