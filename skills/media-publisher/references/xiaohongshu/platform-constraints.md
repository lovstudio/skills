# 小红书发布约束

« 2026-10-01 一次真实视频笔记发布（账号「手工川」）的读数。证据按行标：「页面原文」「实测读到」
是这次运行里的读数，「平台公开规则」没有在页面上核对，标 **未实测** 的项本次没有证据——
不要把整份文档当成平台合同。 »

## 执行优先级

1. 当前账号发布页展示的限制、计数器与校验提示；
2. 本文里逐行标为「页面原文 / 实测读到」的 2026-10-01 读数（标 **未实测** 或「平台公开规则」的行不算）；
3. `scripts/check_video.py --platform xiaohongshu` / `scripts/check_copy.py --platform xiaohongshu`
   的保守默认值。

每次执行先读实时页面；页面文案与本文不同时，记录原文、账号和时间，以页面为准。

## 视频限制（页面原文）

上传页 2026-10-01 的原文：

```text
视频大小    支持时长4小时以内， 最大20GB的视频文件
视频格式    支持常用视频格式， 推荐使用mp4、mov
视频分辨率  超过1080P的视频用网页端上传画质更清晰
```

| 项目 | 值 | 证据 |
| --- | --- | --- |
| 文件大小 | ≤ 20GB | 页面原文；页面没写是 GB 还是 GiB 口径，**未实测** |
| 视频时长 | < 4 小时 | 页面原文「4小时以内」 |
| 推荐容器 | MP4 / MOV | 页面原文 |
| 可选文件类型 | `.mp4,.mov,.flv,.f4v,.mkv,.rm,.rmvb,.m4v,.mpg,.mpeg,.ts` | 文件输入的 `accept`；非推荐容器能否顺利转码 **未实测** |
| 分辨率 | 超过 1080P 走网页端画质更清晰 | 页面原文；本 Skill 本来就走网页端 |
| 视频码率 | **页面没有任何码率要求** | 同一页面只写大小、时长、格式、分辨率 |
| 最短时长 / 宽高比限制 | — | **未实测**，页面没写 |

页面对当前账号显示不同数值时，记录原文后用 `--max-gb` / `--max-hours` 覆盖重跑预检。

## 码率：页面没写，直接传批准母版

页面没有码率上限，也没有码率建议，所以重压没有平台依据：

- 直接上传本期小红书对应的**已批准平台成片**（渲染母版），不因码率或体积在上传前重压；
- 视频号的「≤ 10 Mbps」建议与「长视频先重压」只属于视频号，不搬到小红书；同一期视频号用了
  重压版时，小红书仍传母版；
- 母版是 MP4 或 MOV 时直接传，不为换容器重新封装；其他容器虽在 `accept` 里但不是推荐项，
  行为 **未实测**，遇到先在报告里列出，不擅自转码；
- 只有页面真的返回转码失败时，才按 [重压方案](../encoding-recipes.md) 处理。

## 文案限制

| 字段 | 上限 | 证据等级 |
| --- | --- | --- |
| 标题 | 20 字 | 平台公开规则；**本次没有读到标题计数器，未逐字撞过上限**；中英文、emoji 的计数口径 **未实测** |
| 正文 | 1000 字 | 计数器 `n /1000`，实测读到；话题文本是否计入 **未实测** |
| 话题 | 必须来自联想列表 | 实测点过联想项并读到 `a.tiptap-topic`；话题个数上限 **未实测** |
| 合集标题 | — | **未实测**（本次没有建合集） |

标题字段 `input.d-text[placeholder="填写标题会有更多赞哦"]`，写法与正文、话题的写入方式见
[发布页结构](page-anatomy.md)。

## 话题必须从联想列表里选

话题只有点联想项生成的 `a.tiptap-topic` 节点才算数（`data-topic` 里带 `name`），正文里的
纯文本 `#xxx` 不算。联想项每条右侧要么是热度（如 `1.4亿浏览`），要么是 `新建话题`。

- 一个名字有没有现成话题，**离线没法判断**：`check_copy.py` 只能查格式和长度，
  `新建话题` 只会在页面上出现；
- 本次 `#AI` 联想里只有 `新建话题`：没有现成话题，点了会新建。这种情况照常点选，但必须在终稿
  确认的「被平台改写」段单独列出，让用户决定是否换名；
- 只按 `'#' + 名称` 全等匹配联想项，不点第一项、不用 `includes`。

## 从其他平台继承文案

小红书常常是同期内容的第二、第三站，标题、正文、成片都从已冻结的别的平台终稿继承。继承时：

- **标题**：别的平台的标题（B 站 80 字、视频号短标题另有规则）不能直接搬。按同一表达核心重新
  压到 ≤ 20 字，过 `check_copy.py --platform xiaohongshu`，并在终稿确认里列为平台改写：
  `title <原平台标题> → <小红书标题>（平台限 20 字）`，让用户看到改了什么；
- **正文**：用冻结全文，只做一处改动——剥掉正文里的行内 `#话题` 纯文本（小红书不会把它们解析成
  话题）。话题改走 `--topic` 预检 + 页面联想选取。除此之外逐字不改；剥掉的话题在终稿确认里写明；
- **成片**：按 SKILL.md「平台成片映射门禁」选**小红书对应的已批准文件**。没有对应文件时状态记为
  `blocked-on-platform-variant`，交回渲染；只有用户在当前任务里明确同意复用别的平台文件，才能
  拿那个文件并给 `check_video.py` 加 `--allow-cross-platform-name`，并在报告里写明复用来源。

## 可逆性未知：按不可逆处理

发布后能否修改视频、标题、正文、话题、封面，本次**没有验证**。在证实之前按视频号口径处理：

- `publish` 前的终稿确认就是最后一道闸，出错的代价按「只能删了重发」说明；
- 报告里写「小红书笔记发布后是否可编辑未验证」，不要照 B 站口径说「发错了还能改」。

### 草稿与定时：在证实之前按 `publish` 对待

`draft`（「暂存离开」）的草稿落在哪里、能否继续编辑 **未实测**；`schedule` 的时间选择器、
时区显示与到点前能否撤销 **未实测**。在证实之前，两者都按 `publish` 级动作处理：

- 点 `XHS-PUBLISH-BTN` 里的**任何**按钮之前都先过终稿确认（`awaiting_confirmation` → 用户明确
  同意），或者直接把那一下交给用户点；
- 原因一：「暂存离开」和「发布」在同一个 closed shadow 宿主里，代码断言分不清两者，左右只能靠
  现拍截图——想存草稿时点偏一点就是发布；
- 原因二：定时一旦提交，无法证明到点前还能撤销，等同于一次延迟的发布；
- 点击纪律与「发布」相同：（需要时）滚动 → 现拍截图 → 尺寸与宿主断言 → 只点一次，见
  [发布页结构](page-anatomy.md)「发布按钮」；
- `draft` 交付时在报告里说明草稿位置与可编辑性未验证；`schedule` 交付时写明「到点前能否撤销
  未验证」。

## 作者偏好（2026-10-01）

- 创作声明 / 内容类型声明 / 视频标注：默认**不选**「含AI生成内容」一类标注，保持
  `无需标注` / 未设置；只有用户在当前任务里明确要求才设置；
- 平台自己加上的标识不得移除；
- 是否真含生成素材的判断方法见
  [素材来源与生成内容标注](../publish-gates.md#素材来源与生成内容标注)。

## 回读：笔记管理列表

点「发布」后跳到 `/publish/success?...` 只说明提交动作发生了，**不是发布证据**。
状态只认笔记管理列表：

- 入口 `https://creator.xiaohongshu.com/new/note-manager`，**直链可用**（不像 B 站管理页会被重定向）；
- tab：`全部`（本次读到 `全部 34`）/ `已发布` / `审核中` / `未通过`；
- 每条显示视频时长（如 `02:54`）、非公开时的状态标签（`审核中`，或 `未通过` + `查看修改建议`）、
  标题、发布时间（如 `2026-10-01 21:07`）和互动计数；
- **公开笔记在「全部」里没有状态标签**——没标签不等于已发布，必须切到「已发布」tab 找到它。

| 列表证据 | 状态 |
| --- | --- |
| 在「审核中」tab，或条目带 `审核中` 标签 | `platform_pending` |
| 在「未通过」tab，或条目带 `未通过` 标签 | `publish_failed`（附「查看修改建议」原文） |
| 确认「已发布」tab 已切过去（见下文探针）后，在列表里找到本期条目 | `published` |
| 成功页 URL、按钮消失、「全部」里无标签、点过「已发布」但没确认 tab 已激活 | 都不单独成立，保留最后已证实状态 |

匹配唯一条目用：标题 + 发布时间窗 + 视频时长；重发同一素材时时长相同，按
[发布门禁清单](../publish-gates.md)「重发场景下选对指纹字段」改用标题、话题组合和提交时间。
列表里转码中 / 处理中的状态原文、笔记 ID 与公开链接的取法、公开笔记页的字段回读都 **未实测**；
读到新的状态原文就照录，并按 SKILL.md 状态契约归类。

tab 文本带计数（`全部 34`），按前缀匹配，不要全等。分三步：定位并断言命中点 → 真鼠标点一次 →
下一轮确认 tab 已激活，再找条目。

```js
// 1. 定位「已发布」tab，点之前断言坐标命中的就是它
const tab = await js(`(() => {
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 }
  const own = el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('')
  const els = [...document.querySelectorAll('body *')].filter(e => own(e).startsWith('已发布') && vis(e))
  if (els.length !== 1) return { error: '已发布 tab count = ' + els.length }
  const el = els[0], r = el.getBoundingClientRect()
  const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2)
  const at = document.elementFromPoint(x, y)
  const ok = !!at && (at === el || el.contains(at) ||
    (at.contains(el) && at.getBoundingClientRect().height < 80))   // 允许命中 tab 外框，不允许大容器
  if (!ok) return { error: 'point not on tab', at: at && (at.tagName + '.' + at.getAttribute('class')) }
  return { x, y, text: own(el) }
})()`)
if (tab.error) throw new Error(JSON.stringify(tab))
// 2. 真鼠标点 (tab.x, tab.y) 一次，等列表刷新

// 3. 下一轮：确认 tab 已激活，或列表里已经没有可见的「审核中 / 未通过」标签
const act = await js(`(() => {
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 }
  const own = el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('')
  const el = [...document.querySelectorAll('body *')].find(e => own(e).startsWith('已发布') && vis(e))
  if (!el) return { error: 'tab gone' }
  let active = false
  for (let n = el, i = 0; n && i < 3; i++, n = n.parentElement) {
    const cls = n.getAttribute('class') || ''
    if (n.getAttribute('aria-selected') === 'true' ||
        /(^|[\\s_-])(active|selected|current|checked)($|[\\s_-])/.test(cls)) { active = true; break }
  }
  // tab 栏 = 同时包住「全部」「已发布」「审核中」「未通过」四个 tab 的最小祖先；它里面的字不算条目标签
  let bar = el.parentElement
  while (bar && bar !== document.body &&
         !['全部', '审核中', '未通过'].every(t => bar.innerText.includes(t))) bar = bar.parentElement
  const labels = [...document.querySelectorAll('body *')].filter(e =>
    vis(e) && /^(审核中|未通过)$/.test(own(e)) && !(bar && bar !== document.body && bar.contains(e)))
  return { active, entryStatusLabels: labels.map(e => own(e)), tabText: own(el) }
})()`)
```

判读：

- `act.active === true`，或 `entryStatusLabels` 为空，才算「已发布」tab 已切过去；之后再按标题 +
  发布时间窗 + 时长找唯一条目，找到才记 `published`；
- 两者都不满足（激活 class 认不出、列表里仍有 `审核中` / `未通过`）就**不判 `published`**：
  保留最后已证实状态（刚提交时通常是 `platform_pending`），截图附进报告，稍后重载再读；
- `entryStatusLabels` 为空只说明 tab 大概率切过去了；列表还没加载完时它也为空，所以必须同时
  找到本期条目，空列表不算发布证据。

tab 的具体 DOM 结构与激活态的 class 名 **未实测**，上面是按文本定位的保守写法；找不到就截图。

## 预检脚本

和另外两个平台一样，脚本**必须显式传 `--platform xiaohongshu`**，不能拿视频号或 B 站的默认值来卡：

```bash
python3 $SKILL_DIR/scripts/check_video.py <视频路径> --platform xiaohongshu \
  --expected-orientation "$EXPECTED_ORIENTATION" --json

python3 $SKILL_DIR/scripts/check_copy.py --platform xiaohongshu \
  --title "标题不超过二十字" --description "$(cat 正文.txt)" \
  --topic 南头古城 --topic AI --json
```

- `EXPECTED_ORIENTATION` 取自本期交付契约（`horizontal` / `vertical` / `square`），
  不从平台名称猜；
- 页面显示的大小/时长与脚本默认不同时，按页面值加 `--max-gb` / `--max-hours` 重跑；
- `--description` 传不含话题的正文，话题用多个 `--topic` 单独传。正文里还带行内 `#xxx` 时脚本报
  warn `description_inline_hashtag`（纯文本 `#` 在小红书不会变成话题）。warn 不阻断退出码，但对
  小红书要当成必须处理：从别的平台继承来的正文先剥掉行内 `#话题` 再传，话题改走 `--topic`
  + 页面联想（见上文「从其他平台继承文案」）；
- 小红书**不用合集时不要传 `--collection`**。合集上限未实测，传了脚本报 warn
  `collection_limit_unknown`——这不是放行，上限必须在页面上读（输入框 maxLength / 计数器），
  再按 SKILL.md 的合集口径询问用户；
- `check_copy.py` 通过不等于页面接受：标题计数口径、话题是否已存在都只能在页面上确认；
- 两个脚本的 `--platform` 都已列出 `xiaohongshu`；不要拿 `wechat-channels` 或 `bilibili` 的值替小红书
  做预检——那会得到另一平台的假结论。

## 来源

- [小红书创作服务平台 · 发布页](https://creator.xiaohongshu.com/publish/publish?source=official)：
  2026-10-01 读取；视频大小、时长、格式、分辨率原文，文件输入 `accept`，正文计数器 `n /1000`；
  页面无码率要求。
- [小红书创作服务平台 · 登录页](https://creator.xiaohongshu.com/login?source=official)：
  2026-10-01 读取；未登录重定向（`redirectReason=401&lastUrl=...`），只有短信与二维码两种登录。
- [小红书创作服务平台 · 笔记管理](https://creator.xiaohongshu.com/new/note-manager)：
  2026-10-01 读取；tab 与条目字段、状态标签原文。
- 发布成功页 `https://creator.xiaohongshu.com/publish/success?source=official...`：
  2026-10-01 观测到的跳转目标，仅说明提交动作发生。
- 标题 20 字：平台公开规则；本次没有记录对应的来源链接，也没有在页面计数器上核对，**未实测**。
