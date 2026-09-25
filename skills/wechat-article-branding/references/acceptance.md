# Acceptance

Validate the final article at four layers.

## Content

- The article thesis and author position remain intact.
- 标题匹配发布账号在原创、受访或转载关系中的叙事身份，不照搬不合适的第三人称媒体标题。
- TOC labels match real sections and navigate or scan correctly for the target editor.
- New copy contains no working notes, private anecdotes, bracketed context, or unsupported claims.
- Optional polishing preserves facts, quotations, links, names, and intended meaning.

## Editorial and visual quality

- Headings, body, code or prompt blocks, and brand endcap have distinct but coherent hierarchy.
- 启用正文首屏时，首图是导语之前的独立出版组件，不继承导语卡片、正文边框或背景样式。
- 默认正文首图为 `3:4` 竖向构图并带官方发布主体 Logo；它是正文第一块，之前不得重复平台已展示的文章标题。
- The cover has one primary focal point and does not rely on generic AI-tech decoration.
- The cover visibly follows the resolved art direction (`type`, `style`, `palette`, `rendering`, and `mood`); an artistic-base request is not satisfied by an arbitrary warm still life.
- Wide and square sharing crops preserve the meaningful subject and brand mark.
- 分享封面以艺术主图为底；横版官方发布 Logo 位于画面中心，方版 Logo 默认位于底部中央。方版从未叠 Logo 的背景裁出，不得残留第二个居中 Logo；两个比例都不得使用品牌面板、卡片或贴纸。
- 封面与正文首图使用 `publication.name` 对应的官方 `publication.logo`；不得出现工作室、母品牌或产品 Logo 的误替换。
- 存在 `publication.cover_logo` 时，封面与正文首图必须使用该专用变体；`cover_logo_variant: white` 必须通过可见像素的白色验证，不得回退为橙色。
- 品牌区作为独立出版组件出现，通过位置与层级保持自然，不充当正文结论的续写。
- 真实艺术作品说明章节使用“本期封面”，并位于正文结论之后、品牌尾注之前。
- 启用封面 Prompt 时，区块位于正文结论之后、品牌尾注之前，内容可复制且与实际成图方法一致。

## Brand integrity

- Brand and product names, Logo geometry, public promises, colors, and URLs match the Profile.
- 品牌尾注默认不枚举产品；只有与正文主题直接相关或用户明确要求的产品才出现。被选中的产品最多出现一个主链接，且必须等于 `products[].url`；没有重复的仓库、下载或辅助链接。
- Only approved public facts appear.
- 核心品牌文案可跨不同文章主题复用，不依赖当前正文的人物、隐喻或结论。

## Persistence and regression

- Every intended block appears exactly once and at the intended anchor.
- `opening-hero` and `cover-prompt` are independently enabled and carry unique markers when published.
- No probe text, empty wrapper, duplicate image, or stale cover remains.
- Save succeeds and the same state survives a reload.
- Title, digest, body, images, cover, and word count change only where the mutation plan allows.
- Report observed platform state separately from generated local assets.
