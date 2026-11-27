# mono

单色印刷风：纸纹底 + 一种油墨 + 近黑，可编辑 PPTX，适合中文演讲投屏

## Design Aesthetic

像一份用单色油墨印出来的编辑出版物。纸面始终可见，所有图片都转成同一种油墨的单色调，排版不对称、左对齐，每页只有一个视觉焦点。视觉语言参考 [yanliudesign/mono-color-skill](https://github.com/yanliudesign/mono-color-skill)，默认取它 `examples/reference-04.png` 的锈橙配色。

## When to Use

- 中文为主的线下分享、讲座、闭门会，会议室投屏
- 需要现场改字、需要演讲者备注、需要在别人的 Windows 电脑上打开
- 想要比 bold-editorial 更克制、比 minimal 更有质感的整套视觉

## Production Mode（默认：原生排版）

mono 默认不走“每页整张生成图片”，而是：

1. 只让生图模型出**无文字**的主视觉插画（封面、章节、时代场景等），统一画风。
2. 标题、正文、数字全部用 python-pptx 原生文本框排版，可编辑、字不会画错。
3. 所有图片（插画、照片、截图、图标）在本地转成油墨单色调后再放入。
4. 讲稿写进每页演讲者备注。

用 `scripts/mono_pptx_kit.py` 组装，见文末。用户明确要“整页生成图片”时，才用下面的 STYLE_INSTRUCTIONS 走常规 any2deck 流程。

## Background

- Paper: 暖灰 `#E4E1DB`，叠一层很淡的印刷颗粒（高斯噪声 σ≈4.5，加一层低频斑驳）
- 纸纹和品牌 Logo 放进**母版**（版式层），不在每页重复放；满幅图片的页面会自然盖住 Logo
- 不加边框、卡片、阴影、渐变

## Color Palette

单色油墨 + 近黑。一页里油墨承担标题、数字、图片；近黑承担正文和第二强调。

| Role | Hex | Usage |
|------|-----|-------|
| Paper | `#E4E1DB` | 底色（带颗粒） |
| Ink（锈橙，默认） | `#A75D38` | 标题、大数字、图片单色调、结论句 |
| Dark | `#2C2C2A` | 正文、第二强调（例如“今天”对“过去”） |
| Soft | `#77716A` | 极少量注脚、出处 |
| Rule | `#BDB6AC` | 细分隔线 |

可替换的油墨（同一份 deck 只用一种）：钴蓝 `#2148B8`、植物绿 `#008A4B`、信号红 `#C83232`、炭灰 `#30343A`、茄紫 `#63365F`。

## Typography

只用 Windows 和 macOS 都自带的字体，保证会议室电脑上不走样：

- 中文：微软雅黑（标题加粗，正文常规）
- 大数字、年份：Impact
- 英文单词标题（产品名、人名、范式名）：Arial Black。**不要给英文单词用 Impact**，窄体字放单词会显得挤
- 代码、文件名、元信息：Consolas
- 字号：标题 36–44pt；问题页 52–80pt；大数字 100–220pt；正文 ≥18pt；注脚 13–16pt

## Page Types

| 类型 | 做法 |
|------|------|
| 封面 | 只留标题、副标题、讲者名和 Logo；右侧主视觉满幅。不放日期、地点、头衔等说明 |
| 问题页 | 一个问题单独一页，大字居中，底部一个小色点作唯一扰动；问题下的内容另起一页 |
| 大数字页 | 一个超大数字作焦点，配 2–3 个次级数字和一句结论 |
| 照片页 | 照片从页边出血，文字在另一侧左对齐 |
| 结论句 | 放页面底部的一行大字（油墨色），不加框 |
| 时间轴 | 一排等宽小图 + 年份（Impact）+ 一行说明 |
| 提前收集的问题 | 问答前一页列出问卷问题、提问人、在哪页回答 |
| Q&A | 讲者照片 + 微信与公众号二维码 + Logo；二维码保持原色以免扫不出 |
| 资料来源 | 两栏小字，写明“插画为 AI 生成的示意图”与照片来源 |

## Image Treatment

- 照片、截图、插画：按亮度映射到“油墨 → 纸色”的单色调，再加同样的颗粒；暗部满墨，高光露纸
- 带透明圆角的应用图标：先垫白底再转色，否则圆角会变成色块
- Logo：取 alpha 和暗度做蒙版，渲染成单色油墨，透明底
- 插画提示词：只要无文字的画面（screen-print / risograph 风、强剪影），明确写 “ABSOLUTELY NO text, letters, numbers, logos”

## Sourcing Photos

每个出现的人物、产品、书、事件都尽量配图，来源记到 `assets/sources.json`：

- 讲者本人的活动照：讲者授权的本地相册或本人社交动态（只取本人发布的）
- 应用图标：本机已装应用的 `.icns`（`sips -s format png`），资源包里的用系统接口导出；未安装的用 App Store 公开搜索接口 `itunes.apple.com/search?entity=software` 取 `artworkUrl512`，核对开发者名，防止取到同名应用
- 人物照：公开的 GitHub 头像（`github.com/<user>.png`）、维基百科主图；先看一眼是不是本人
- 书封：豆瓣 `book.douban.com/j/subject_suggest`，下载封面要带 `Referer`
- 产品/文章：网页 `og:image`

## Verification

1. 逐页渲染预览，检查溢出、重叠、换行孤字
2. 有条件就在 PowerPoint 或 Keynote 里实际打开看一遍；渐变遮罩、自由曲线等只能在真实软件里确认
3. 回读演讲者备注是否每页都有

## Pitfalls

- Impact 用在英文单词上显得挤；Georgia 的数字是老式数字（会下沉），做大数字不合适
- 中文标题若改用宋体等非系统字体，会议室电脑上会被替换；要宋体效果只能把标题渲染成图片（不可编辑）
- 用 AppleScript 让 Keynote 打开 PPTX 是异步的，`open` 会返回空值；后台等待也可能卡在需要手动点掉的弹窗上，不要为此抢前台或模拟点击
- 维基媒体对浏览器 UA 的脚本请求会返回 429，用带工具名的 UA
- zsh 不会拆分未加引号的变量，批量传多个同名参数要逐条调用或用数组
- 带颗粒的图片存 PNG 会很大，单色调图一律存 JPG（quality≈90）

## STYLE_INSTRUCTIONS（仅整页生图模式）

```
<STYLE_INSTRUCTIONS>
Design Aesthetic: one-ink editorial print on warm gray paper; asymmetric, left-aligned; one focal event per slide; generous empty paper.
Background: warm gray paper #E4E1DB with subtle print grain, edge to edge; no frames, cards or shadows.
Typography: bold geometric sans for CJK headlines; condensed heavy numerals for big numbers; wide heavy sans for English words.
Color Palette: ink #A75D38 for headlines, numbers and all imagery; near-black #2C2C2A for body text; nothing else.
Visual Elements: all imagery reproduced in the single ink as monotone print; thin rules; one small round mark as the only ornament.
Density: minimal to balanced; at most 3 text elements per slide.
Style Rules: Do keep paper visible and crop images decisively. Don't use gradients, a second chromatic color, full-color photos, or centered-everything layouts (except question slides).
</STYLE_INSTRUCTIONS>
```

## Using the Kit

```bash
python3 ${SKILL_DIR}/scripts/mono_pptx_kit.py --demo /tmp/mono-demo.pptx   # 自检：生成 5 页样张
```

```python
import sys; sys.path.insert(0, f"{SKILL_DIR}/scripts")
from mono_pptx_kit import MonoDeck, Theme

d = MonoDeck(Theme(), notes_md="讲稿.md", logo="logo.png", cache_dir="ink")
s = d.new(); d.title(s, "两次软件危机"); d.big(s, 0.9, 1.7, 5, 2.0, "1968", 150)
d.question("什么是产品？")
d.save("deck.pptx")
```

讲稿文件里用 `## P01 标题` 分段，`MonoDeck.new()` 按创建顺序把第 N 段写进第 N 页的备注。

## Best For

中文演讲与讲座、产品分享、行业闭门会、个人品牌介绍、需要现场修改的会议投屏 deck
