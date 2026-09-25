---
name: find-ebook
description: >
  用尽调式检索寻找指定书籍的合法授权电子书资源和获取路径，优先确认中文译本、
  非扫描电子版、GitHub/GitBook 明确授权仓库、PDF、EPUB、MOBI、Kindle、Markdown、在线阅读和图书馆借阅。
  Trigger when the user uses /find-ebook or find-ebook, asks to find an ebook, 电子书资源, epub, mobi, pdf,
  Kindle edition, downloadable book, 中文译本, or asks for a specific title
  such as 李飞飞自传 的电子版。
license: MIT
metadata:
  author: contributors
  version: "0.1.1"
  tags: ebook research books library isbn authorized-sources github open-access
---

# 电子书寻宝 · Ebook Finder

用这个 skill 帮用户寻找指定书籍的电子书资源时，目标不是“随便找一个下载链接”，而是确认书名、版本、语言、格式和合法获取路径。优先找中文译本和非扫描电子版；如果只有英文原版、在线阅读、图书馆借阅或付费购买，也要清楚标注。

## Core Principle

电子书查找要像事实校验一样做证据链，而不是只贴链接。

- 先确认目标书：中文名、英文原名、作者、ISBN、出版社、出版年份和版本。
- 优先合法授权来源：作者/出版社官网、GitHub/GitBook 明确授权仓库、官方电商、正规电子书店、图书馆平台、开放授权仓库、机构库。
- 优先非扫描电子版：EPUB、MOBI、Kindle、text-based PDF、HTML/Markdown；扫描 PDF 只能作为降级候选。
- 区分“可下载”“可在线读”“可借阅”“可购买”“只有预览”“未确认”。
- 不提供盗版资源站、网盘转载、BT/磁力、绕过 DRM/付费墙、破解下载、账号共享或规避地区限制的方法。
- 不把“没搜到免费版”写成“不存在”。只能写“未找到可验证的合法免费电子版”。

## Workflow (MANDATORY)

### Step 1: Restate the Target

把用户输入改写成一个可检索目标，并列出关键歧义。只有歧义会改变检索方向时才提问；否则直接检索。

需要确认的信息：

- 书名：中文名、英文名、别名、常见误写。
- 作者：中英文姓名、译者，如适用。
- 版本：原版、译本、再版、简体/繁体、注释版、合集。
- 标识：ISBN、出版社、出版年份。
- 偏好：按当前请求或个人配置选择语言；非扫描优先；格式遵循显式需求或个人配置。

Example:

```text
用户问：“找李飞飞自传电子书”

可检索目标：
1. 先确认“李飞飞自传”对应的英文原书名、作者和 ISBN。
2. 查是否有简体/繁体中文授权译本及其电子版。
3. 若中文电子版不存在或不可获取，查英文原版的 Kindle/EPUB/图书馆借阅/官方购买路径。
```

### Step 2: Build the Evidence Plan

按这个优先级查找：

1. `[一手]` 作者官网、出版社页面、版权页、官方新闻稿、ISBN/国家图书馆/WorldCat 记录。
2. `[开放仓库]` GitHub、GitBook、Codeberg、Gitee 等公开仓库；只接受作者/出版社/译者官方仓库，或仓库内有清晰 license、版权声明、公版依据、开放教材说明的版本。
3. `[授权销售]` Amazon Kindle、Apple Books、Kobo、Google Play Books、微信读书、京东读书、豆瓣阅读、得到、出版社自营店等正规平台。
4. `[图书馆/受控借阅]` WorldCat、OverDrive/Libby、Hoopla、Open Library、Internet Archive controlled lending、HathiTrust、学校/公共图书馆目录。
5. `[开放授权]` Project Gutenberg、Standard Ebooks、DOAB、OAPEN、arXiv、机构知识库、作者/出版社公开下载页等明确授权来源。
6. `[二手线索]` 豆瓣、Goodreads、媒体书评、书目数据库，用于确认译名、ISBN、出版时间和版本，不直接当下载来源。

### Step 3: Search Like Due Diligence

必须覆盖这些检索动作：

1. 确认书名和版本：
   - `<中文书名> 作者 ISBN 出版社`
   - `<英文书名> author ISBN publisher`
   - `<作者> autobiography memoir ebook`
   - `<英文书名> Chinese translation`
2. 查中文电子版：
   - `<中文书名> 电子书 epub mobi kindle 官方`
   - `<中文书名> 微信读书 京东读书 豆瓣阅读`
   - `<中文书名> ISBN 电子版`
3. 查英文原版：
   - `<英文书名> ebook epub kindle publisher`
   - `<英文书名> OverDrive Libby`
   - `<英文书名> Open Library`
4. 查 GitHub/GitBook 等开放仓库：
   - `<中文书名> epub OR pdf GitHub license`
   - `<英文书名> epub OR markdown GitHub license`
   - `<作者> <书名> GitBook`
   - 只有在仓库内能确认 license、版权声明、作者/出版社身份、公版依据或开放教材属性时，才把仓库列为候选。
5. 查开放授权：
   - `<英文书名> PDF official`
   - `<作者> <书名> pdf site:publisher-or-author-domain`
   - 仅当书籍可能是公版、开放教材、学术报告或作者公开发布时，才把免费 PDF/EPUB 作为强候选。
6. 查反例和限制：
   - 是否只有纸书或有声书。
   - 是否只有扫描版、预览、摘录、地区限定、馆藏限定、排队借阅。
   - 是否存在同名书、伪书名、错误译名或非授权转载。

搜索时优先打开候选页面核验，不要只依赖搜索结果摘要。对会随时间变化的获取状态，写明检索日期。

### Step 4: Verify Each Candidate

每个候选资源都要检查：

- **Title match**: 是否是同一本书，而不是书评、摘要、采访、课程讲义或同名作品。
- **Language/edition**: 简体中文、繁体中文、英文原版、译本、节选、预览。
- **Format**: EPUB/MOBI/Kindle/HTML/MD/text PDF/scanned PDF/audio/unknown。
- **Access**: 直接下载、在线读、借阅、购买、预览、需要机构登录、地区限制。
- **Authorization**: 来源是否来自官方、正规平台、图书馆、开放授权库或明确许可页面。
- **Text layer**: 对 PDF，尽量确认是文字 PDF 还是扫描图像。不能确认时写“PDF 类型未确认”。
- **Quality**: 是否完整、是否含 OCR 错误、是否只有样章、是否为旧版。

丢弃或不输出这些候选：

- 没有授权说明的免费下载站、聚合下载站、转载网盘、论坛附件、BT/磁力、破解电子书站。
- Z-Library、Library Genesis 等以未授权商业书下载为主的资源站，以及镜像站、代理站和导流页。
- 要求绕过 DRM、付费墙、验证码、登录限制或地区限制的来源。
- 文件名像目标书但页面无法证明来源、版本或完整性。

### Step 5: Rank Results

默认排序：

1. 授权中文非扫描电子版。
2. GitHub/GitBook 等仓库中的明确授权中文非扫描版本。
3. 授权英文原版非扫描电子版。
4. GitHub/GitBook 等仓库中的明确授权英文非扫描版本。
5. 图书馆可借阅电子版。
6. 官方在线阅读或预览。
7. 授权纸书/有声书信息，作为“未找到电子版”的替代。
8. 扫描版或未确认格式，仅在合法且用户可接受时列为降级候选。

同一层级内，优先：官方/出版社 > 明确授权仓库 > 正规电子书店 > 图书馆 > 开放授权库 > 书目数据库线索。

## Output Format

默认中文输出。不要只给链接列表，必须解释每个来源证明了什么。

```markdown
**结论**
[一句话说明是否找到可验证的合法电子版；最推荐的获取路径是什么。]

**目标书目确认**
- 书名：[中文名 / 英文原名]
- 作者：[作者]
- 版本：[中文译本/英文原版/ISBN/出版社/出版年，如已确认]
- 检索日期：[YYYY-MM-DD]

**已确认资源**
| 优先级 | 语言/版本 | 格式/访问方式 | 来源 | 费用/限制 | 证据质量 |
|---|---|---|---|---|---|
| 1 | 中文译本 | EPUB/在线读/购买 | [平台名](URL) | 付费/会员/借阅 | [授权销售] 证明了什么 |

**未找到或已排除**
- [例如：未找到可验证的合法免费中文 EPUB。]
- [例如：某类结果只有扫描版、预览或无法确认授权，因此不推荐。]

**获取建议**
[给用户下一步：购买、借阅、用图书馆账号查询、接受英文版、设置到货提醒等。不要提供绕过限制的方法。]

**置信度**
[高/中/低]：[说明证据充分性和未确认点。]
```

## Practical Notes

- 现代受版权保护的商业书通常不会有合法免费完整 PDF/EPUB。找到“免费完整下载”时要更严格核验授权。
- 中文译本可能晚于英文原版，且不一定有电子版；先确认译名和 ISBN，再查电子书平台。
- “PDF”不等于非扫描版。若用户明确要非扫描版，EPUB/Kindle/HTML/MD 通常比 PDF 更可靠。
- 如果无法联网或无法打开关键来源，明确说“暂未核验”，并降低置信度。

## Runtime context

运行前读取同目录 `skill.yaml`，由宿主的 `skill-runtime` 按“当前请求、项目上下文、个人配置、品牌 Profile、安全默认值”的顺序注入，只使用 manifest 声明的字段。

- 缺少 `required: true` 字段时，按 `questions` 向用户提出一个聚焦问题；回答只用于本次运行，除非用户明确要求保存。
- Profile 只用于公开品牌事实；个人配置只用于决策，不自动写入产物或源码。
- 调试报错提供可复制的 `context_id`、字段路径和来源，不输出秘密、完整私人路径或原始内容。

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
