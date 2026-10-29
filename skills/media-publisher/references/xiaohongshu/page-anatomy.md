« 2026-10-01 一次真实视频笔记发布的记录（账号「手工川」，ego-browser / Chromium）；
2026-10-02 第二次发布（同账号，手工川-南头古城招募共创宣传片 v0.9）实测走通了封面上传，见「封面」节。
2026-10-12 第三次发布（同账号，《背包九讲》竖版，视口 900×765）：当前封面缩略图的结构变了；正文改为按 `<p>`
逐段比对；封面预览要临时放宽视口才截得到；其余步骤照旧走通。这次的读数在各节标「2026-10-12」。
2026-10-29 第四次发布（同账号，「超越之旅」宣传短片竖版）：话题 12 个超过上限，前四次点「发布」都被前端拦下，见
「发布按钮」节的「点了「发布」没反应」；这次读到的发布栏宿主属性、删话题的写法也记在「发布按钮」「话题」两节，标「2026-10-29」。
平台前端会改版，这里的每条都要能被当场的快照推翻——以页面为准，本文只用来省掉从零摸索的那几轮。
证据按条标：写明「本次读到 / 本次点过」的，指该节所标日期那次运行，没标日期的指 2026-10-01；标 **未实测**
的没有走通或没有走到。代码片段里为了更稳加的断言（命中点、容器边界、尺寸核对）是保守写法，除各节写明
2026-10-12 跑通的以外，本身没有在页面上跑过——断言失败就停下截图，不要放宽断言去迁就。 »

# 小红书视频发布页结构与可复用探针

入口 `https://creator.xiaohongshu.com/publish/publish?source=official`。
笔记管理 `https://creator.xiaohongshu.com/new/note-manager`（直链可用，和 B 站管理页不同）。

## 和另外两个平台的差别

- 表单是**普通 DOM 的 Vue 应用**：没有 wujie，没有 shadow root，`document.querySelector`
  直接可用。不要把视频号的 `DOM.getDocument({ pierce: true })` 穿透遍历套过来。
- **唯一的例外是底部发布按钮**：「暂存离开」「发布」在自定义元素 `XHS-PUBLISH-BTN` 的
  **closed** shadow root 里，DOM 查不到、`innerText` 为空、`shadowRoot` 为 `null`。
  只能按截图坐标点，见下文「发布按钮」。
- 正文是 tiptap / ProseMirror，不是视频号的 `.input-editor`，也不是 B 站的 Quill。
- 话题由联想列表生成 `a.tiptap-topic` 节点，节点上带 `data-topic` JSON；纯文本 `#` 不算话题。
- 没有「快捷登录」，登录只能交给用户。

## 登录：没有快捷登录，只能交接

未登录打开入口会被重定向到：

```text
/login?source=official&redirectReason=401&lastUrl=...
```

登录卡片只有两条路：「短信登录」（手机号 + 验证码）和卡片右上角图标切换的二维码。
没有视频号那种同机免扫的「快捷登录」，所以**不要找、也不要试**。

```js
const onLogin = await js(`location.pathname.startsWith('/login')`)
if (onLogin) await handOffTaskSpace(task.id)   // 传 id；随后 waitForAgentControl(task.id)
```

交接说明只写一个动作（「在小红书登录页用短信或扫码登录手工川」），代理**绝不**代填手机号或
验证码。用户归还后重新读快照，按页面右上角显示的账号名（本次为 `手工川`）逐字核对；侧边栏
可见 `首页 / 笔记管理 / 数据看板 ...` 也可作为已登录的旁证。

## 上传：只有一个 file input

上传页顶部 tab：`上传视频 / 上传图文 / 写长文 / 发播客`。确认处在「上传视频」
（是否默认选中 **未实测**，以快照为准）。

页面上**恰好一个**文件输入，在主文档里：

| 选择器 | `accept` |
| --- | --- |
| `input.upload-input[type=file]` | `.mp4,.mov,.flv,.f4v,.mkv,.rm,.rmvb,.m4v,.mpg,.mpeg,.ts` |

不必像视频号那样穿透，也不必像 B 站那样按祖先链区分；但仍要**断言唯一命中**再提交，
`nodeId` 每次重新取：

```js
const { root } = await cdp('DOM.getDocument', { depth: 0 })
const { nodeIds } = await cdp('DOM.querySelectorAll', {
  nodeId: root.nodeId, selector: 'input.upload-input[type=file]',
})
if (nodeIds.length !== 1) throw new Error('upload input count = ' + nodeIds.length)
await cdp('DOM.setFileInputFiles', { nodeId: nodeIds[0], files: [VIDEO_ABS_PATH] })
```

上传后页面出现 `视频文件 重新上传 <文件名> 检测为高清视频...`，下方挂出表单。

2026-10-12 读到上传中的原文（44.8 MB 的 MP4）：

```text
视频文件  取消上传  <文件名>  上传中 47%  当前速度：5.78MB/s  剩余时间：3s
```

这可以作为 `uploading` 的判据；此时表单（标题、正文输入框）已经挂出。这次读到时只剩约 3 秒，标题写入时
上传多半已经完成，上传进行中写字段没有单独验证。上传完成后变成
`重新上传 <文件名> 检测为高清视频…`，中间没看到单独的转码 / 解析文案，所以 `processing` 的页面判据
仍 **未实测**：看到什么文案就原文记录，不要套用视频号或 B 站的进度文案。

## 位置权限弹窗：立即停手，交给用户

提交视频文件后，Chromium 弹出了**地理位置权限**请求，ego-browser 当场抛错并把控制权交给用户：

```text
A browser permission prompt for location access has appeared. The user now controls this task space
```

这和「The user has taken control of this task space」同级，是**硬停**：

1. 不重试、不 `takeOverTaskSpace()`、不读页、不点击；
2. 告诉用户唯一动作：在浏览器的位置权限弹窗里做选择，**推荐「拒绝」**（隐私最小化的默认值）；
   按 [浏览器工作流](../browser-workflow.md)「控制权」节同步展示素材绝对路径、发通知并播报；
3. 等用户在对话里说「继续」，再 `takeOverTaskSpace(task.id)`，重新 `snapshotText()`。

证据边界：本次用户处理完弹窗后，表单可以继续填，`添加地点` 按文字搜索也能用；但用户在弹窗里
选的是「允许」还是「拒绝」**没有记录**。所以下面几条都 **未实测**，不要当成已知：

- 拒绝定位后能否正常发布；
- 拒绝定位后 `添加地点` 能否按名称搜到地点（见下文「添加地点」）；
- 用户选「拒绝」后同一 origin 下次是否还会弹。

拒绝后若地点搜不出来，不要为此去授权定位：跳过地点，在终稿确认里写明「地点未填，原因是定位
被拒后搜索不可用」，由用户决定（用户没要求地点时按平台默认不填；要求了而搜不到，Profile 为 `auto` 也要退回确认）。
也不要为了省一次交接而预先授权定位。

2026-10-12（同一 ego-browser 环境）提交视频后**没有**弹出定位请求，表单直接可填。是不是因为之前在弹窗里
做过选择、被浏览器记住了，**未实测**。所以仍按「可能弹」准备，弹了照上面硬停。

## 标题：真点击 + `Input.insertText`，隔 1.2 秒再读

`input.d-text[placeholder="填写标题会有更多赞哦"]`。本次用 CDP 真鼠标点进输入框，再
`Input.insertText` 写入，**1.2 秒后**再读 `value` 与写入值全等，确认持久化（B 站标题曾在
100ms 后被悄悄 revert，所以写入瞬间的读回不算数）。

```js
const SEL = 'input.d-text[placeholder="填写标题会有更多赞哦"]'
const t = await js(`(() => {
  const i = document.querySelector(${JSON.stringify(SEL)})
  i.scrollIntoView({ block: 'center' })
  const r = i.getBoundingClientRect()
  return { x: r.x + r.width / 2, y: r.y + r.height / 2, value: i.value }
})()`)
if (t.value) throw new Error('标题已有内容，先判断来源，不要追加：' + t.value)
await cdp('Input.dispatchMouseEvent', { type: 'mousePressed',  x: t.x, y: t.y, button: 'left', clickCount: 1 })
await cdp('Input.dispatchMouseEvent', { type: 'mouseReleased', x: t.x, y: t.y, button: 'left', clickCount: 1 })
await cdp('Input.insertText', { text: TITLE })
await new Promise(r => setTimeout(r, 1200))
const v = await js(`document.querySelector(${JSON.stringify(SEL)}).value`)
if (v !== TITLE) throw new Error('title readback: ' + v)
```

- 标题 20 字是平台公开规则；2026-10-12 读到计数器叶子文本 `4 / 20`（斜杠两侧有空格，可用
  `/^\d+\s*\/\s*20$/` 找），1.2 秒后复读 `value` 也一致。超限时页面怎么表现 **未实测**。
- 字段非空时怎么清空 **未实测**（本次写入前为空）。非空先当作可能的用户手改处理，不要直接追加。

## 正文：ProseMirror，真点击 + `insertText`，按 `<p>` 逐段回读

编辑器 `.tiptap.ProseMirror`（contenteditable）。真鼠标点进编辑区后 `Input.insertText(body)`
生效；读回按编辑器的直接子 `<p>` 逐段取，`innerText` 只用来判断是否为空和做诊断；旁边计数器显示
`n /1000`（正文上限 1000，实测读到过）。

```js
const ED = '.tiptap.ProseMirror'
const p = await js(`(() => {
  const ed = document.querySelector(${JSON.stringify(ED)})
  ed.scrollIntoView({ block: 'center' })
  const r = ed.getBoundingClientRect()
  return { x: r.x + 24, y: r.y + 16, text: ed.innerText.trim() }
})()`)
if (p.text) throw new Error('正文已有内容，按描述冻结规则处理，不要重写')
await cdp('Input.dispatchMouseEvent', { type: 'mousePressed',  x: p.x, y: p.y, button: 'left', clickCount: 1 })
await cdp('Input.dispatchMouseEvent', { type: 'mouseReleased', x: p.x, y: p.y, button: 'left', clickCount: 1 })
await cdp('Input.insertText', { text: BODY })
```

下一轮 `js()` 按字段表那节的 `paragraphs` 与冻结全文 `split('\n')` 逐段比较，并读计数器（探针见字段表那节，
**不要**用整页 `innerText.match(/\/1000/)`，B 站同类探针命中过 `<style>` 文本）。

- 接手页面的第一个只读动作仍是读正文全文；非空且与代理上次写入不同即
  `description_source=user-edited`，冻结，不再进入上面的写入分支。
- 清空已有正文的写法 **未实测**。
- 多行正文（2026-10-12 实测）：`insertText('A\nB')` 生成 `<p>A</p><p>B</p>`，`innerText` 读回 `A\n\nB`。
  段间多出的空行是 `<p>` 的渲染，不是写进了空行，所以按编辑器的直接子 `<p>` 逐段比对，不要拿 `innerText`
  整串和冻结文本比（整串比会误判失败），写法见字段表那节的 `paragraphs`。冻结文本本身含空行时
  `insertText` 会不会生成空 `<p>` **未实测**，比对不一致就停下报告，不要现场改写法。
- 计数器把话题文本也算进去：2026-10-12 正文两句共 32 字，加 7 个话题后读到 `71 /1000`。换行和空格
  各算几个没有拆开核对，接近上限时以页面计数器为准；离线预检见 `check_copy.py` 的
  `description_with_topics_over_limit`。
- 话题插进来后 `innerText` 会多出 `#名称[话题]# `（隐藏的 `.content-hide` 文本）。`paragraphs` 连同
  `a.tiptap-topic` 一起去掉了；字段表里的 `bodyWithoutTopics` 只作诊断。

## 话题：`#` + 联想项**精确匹配**，生成 `a.tiptap-topic`

每个话题走一轮：

1. caret 收到正文末尾，断言焦点在编辑器里、联想列表没开着；**第一个话题前**按一次 Enter 起新段落，
   之后的话题不再按 Enter，末尾不是空白时才补一个空格（2026-10-12 第一个话题节点后平台已自动补了 `&nbsp;`）；
2. `Input.insertText('#' + 名称)`；
3. 约 1.5 秒后出现联想列表：元素 `.item`（第一项带 `is-selected`），`children[0]` 文本是
   `#名称`，`children[1]` 文本是热度（如 `1.4亿浏览`）或 `新建话题`；
4. 只点 `children[0]` 文本 **=== `'#' + 名称`** 的那一项，用 CDP 真鼠标；
5. 解析 `data-topic` 确认话题个数 +1、名称正确。

插入后的节点：

```html
<a class="tiptap-topic" data-topic='{"id":...,"link":...,"name":"名称"}' contenteditable="false">#名称<span class="content-hide">[话题]#</span></a>
```

**Enter 是限定范围的例外。** [浏览器工作流](../browser-workflow.md) 的通则是 `pressKey('Enter')`
要有用户明确确认；这里不需要逐次确认，但只在下面三个条件**同时**成立时才发：

- 同一轮 `js()` 刚断言过焦点在编辑器里：`document.activeElement === ed || ed.contains(document.activeElement)`；
- 页面上**没有可见的话题联想项**（`.item`，首个子元素以 `#` 开头）——联想开着时 Enter 会选中带
  `is-selected` 的那一项（通常是第一项），绕过下面的「名称全等」规则；
- 编辑器里还没有任何 `a.tiptap-topic`，即这是**第一个**话题。之后的话题用空格分隔，不再发 Enter。

不满足就停下截图，不要改用别的键或 `pressKey` 凑。表单其他地方（标题、地点搜索、原创弹窗）
一律不发 Enter。

```js
// 1：caret 到末尾，断言焦点与联想状态。下面用 Range 收 caret 的写法 2026-10-12 跑了 7 个话题，
// 每次都落在末尾；话题没落在末尾就停下截图，不要叠加重试。
const pre = await js(`(() => {
  const ed = document.querySelector('.tiptap.ProseMirror')
  if (!ed) return { error: 'no editor' }
  ed.focus()
  const r = document.createRange(); r.selectNodeContents(ed); r.collapse(false)
  const s = getSelection(); s.removeAllRanges(); s.addRange(r)
  const a = document.activeElement
  const openItems = [...document.querySelectorAll('.item')].filter(el => {
    const b = el.getBoundingClientRect()
    return b.width > 0 && b.height > 0 && el.children.length >= 2 &&
      el.children[0].textContent.trim().startsWith('#')
  }).length
  return { focused: a === ed || ed.contains(a), openItems,
           topicCount: ed.querySelectorAll('a.tiptap-topic').length,
           endsWithSpace: /\\s$/.test(ed.innerText) }
})()`)
if (pre.error || !pre.focused || pre.openItems > 0) throw new Error('not safe to type: ' + JSON.stringify(pre))

// 紧接着发键，中间不插别的动作
if (pre.topicCount === 0) {                            // 只有第一个话题前起新段落
  await cdp('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 })
  await cdp('Input.dispatchKeyEvent', { type: 'keyUp',   key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 })
} else if (!pre.endsWithSpace) {
  await cdp('Input.insertText', { text: ' ' })         // 后续话题只用空格分隔
}

// 2：输入 #名称
await cdp('Input.insertText', { text: '#' + NAME })
await new Promise(r => setTimeout(r, 1500))

// 3–4：联想项精确匹配
const pick = await js(`(() => {
  const want = ${JSON.stringify('#' + NAME)}
  const rows = [...document.querySelectorAll('.item')]
    .filter(el => el.getBoundingClientRect().width > 0 && el.children.length >= 2)
    .map(el => ({ el, tag: el.children[0].textContent.trim(), meta: el.children[1].textContent.trim() }))
    .filter(r => r.tag.startsWith('#'))
  const hit = rows.filter(r => r.tag === want)
  const list = rows.map(r => r.tag + ' | ' + r.meta)
  if (hit.length !== 1) return { error: 'exact match count = ' + hit.length, list }
  hit[0].el.scrollIntoView({ block: 'nearest', behavior: 'instant' })   // 只在联想列表内挪动
  const b = hit[0].el.getBoundingClientRect()
  const x = Math.round(b.x + b.width / 2), y = Math.round(b.y + b.height / 2)
  const at = document.elementFromPoint(x, y)
  if (!at || !(at === hit[0].el || hit[0].el.contains(at)))
    return { error: 'hit test failed', at: at && (at.tagName + '.' + at.className), list }
  return { x, y, meta: hit[0].meta, isNew: hit[0].meta === '新建话题', list }
})()`)
if (pick.error) throw new Error(pick.error + '\n' + pick.list.join('\n'))
await cdp('Input.dispatchMouseEvent', { type: 'mousePressed',  x: pick.x, y: pick.y, button: 'left', clickCount: 1 })
await cdp('Input.dispatchMouseEvent', { type: 'mouseReleased', x: pick.x, y: pick.y, button: 'left', clickCount: 1 })
```

5：按 `data-topic` 读名称，**这才是话题的真值**，不要在正文字符串里搜 `#`：

```js
// 返回值包一层对象：js() 顶层直接返回数组在 B 站页上读到过 null，见浏览器工作流「js() 返回数组时包成对象」
const { names: topics } = await js(`({ names: [...document.querySelectorAll('.tiptap.ProseMirror a.tiptap-topic')]
  .map(a => { try { return JSON.parse(a.dataset.topic).name } catch (e) { return null } }) })`)
```

证据边界：2026-10-01 记录的是每个话题前都「末尾 → Enter」。2026-10-12 按上面的顺序跑了 7 个话题
（联想项的 `scrollIntoView` 与命中断言是这次实跑用过、之后补进片段的）：

- 只在第一个前发了一次 Enter；
- 第一个话题插入后读到 `…</a>&nbsp;</p>`：平台在话题节点后自动补了 `&nbsp;`，所以第二个话题前
  `endsWithSpace` 为真、不用再插空格。后面几轮的 `endsWithSpace` 和是否补过空格没有逐轮记录，片段按
  `endsWithSpace` 自动处理；
- 第 2–7 个都是在上一个话题后直接 `insertText('#名称')`，联想每次都照常弹出，全等项都排在第一位
  （如 `#算法 | 5亿浏览`、`#背包九讲 | 37浏览`），7 个都是现成话题；
- 用 Range 把 caret 收到末尾的写法每次都落在了末尾（每轮 `data-topic` 的最后一项都是刚加的名字）。

没弹出联想、或话题个数没 +1，仍然停下截图，不要补 Enter 重试。

### 联想里只有「新建话题」

本次 `#AI` 的联想列表里只有一项，`children[1]` 是 `新建话题`——平台没有现成话题，点了会新建。
它的 `children[0]` 仍是 `#AI`，精确匹配会命中。处理规则：

- 照样只点那一项，但在终稿确认的「被平台改写」段里单独列出：
  `topic AI → 平台无现成话题，新建话题`，让用户看见；
- 新建话题生成的 `data-topic` 里 `id` / `link` 长什么样 **未实测**，验收只看解析出的 `name`；
- 离线脚本无法判断一个名字是否已有现成话题，只能在页面上看到。

### 不要碰的东西

编辑器下方的推荐话题 chip（`#生活美学` 之类）和 `# 话题 / @ 用户 / 表情` 按钮都忽略。
用 `# 话题` 按钮插话题的路径 **未实测**。话题最多 10 个（2026-10-29），超了只在点「发布」时闪一下提示，见「发布按钮」节的
「点了「发布」没反应」。

### 删掉已插入的话题（2026-10-29）

话题节点是 `contenteditable="false"` 的整块。这次没有试键盘删除，用的是挂在编辑器 DOM 上的 tiptap 实例
`document.querySelector('.tiptap.ProseMirror').editor`：按名称找到 `type.name === 'topic'` 的节点，连同它前面那个分隔
空格（空格或 `&nbsp;`）一起 `deleteRange`，每删一个都重新找位置。下面这段 2026-10-29 跑通，删了 2 个，随后读回 10 个
话题、正文三段逐段不变、计数器 `170 /1000`：

```js
const DROP = ['国沐青创', '全国高校创新创业联合体']     // 要删的话题名，按正文里的顺序从后往前列
const r = await js(`(() => {
  const ed = document.querySelector('.tiptap.ProseMirror').editor
  if (!ed) return { error: 'no tiptap editor instance' }
  const find = name => { let hit = null
    ed.state.doc.descendants((n, pos) => {
      if (n.type.name === 'topic' && (n.attrs.name || (n.attrs.data && n.attrs.data.name)) === name)
        hit = { pos, size: n.nodeSize } })
    return hit }
  const out = {}
  for (const name of ${JSON.stringify(DROP)}) {
    const t = find(name)
    if (!t) return { error: 'not found ' + name }
    const sep = ed.state.doc.textBetween(t.pos - 1, t.pos, '|', '|')
    if (!/^[\\s\\u00a0]$/.test(sep)) return { error: 'unexpected separator before ' + name, sep: JSON.stringify(sep) }
    out[name] = ed.chain().deleteRange({ from: t.pos - 1, to: t.pos + t.size }).run()
  }
  return { out }
})()`)
if (r.error) throw new Error(JSON.stringify(r))
```

- 下一轮按「一次读完整个字段表」重读 `topics`、`paragraphs` 和计数器，三样都对才算删完；
- 话题前面不是空格时（比如段首第一个话题）断言会拦下：停下截图，不要放宽断言去删；
- 这次名字取自 `n.attrs.name` 还是 `n.attrs.data.name` 没有分开记录，片段两个都认；
- 删话题改的是终稿：应在终稿确认之前减，按 [小红书约束](platform-constraints.md)「从其他平台继承文案」列进确认。

## 封面：默认第一帧；悬停「编辑封面」可上传批准封面（2026-10-02 实测，2026-10-12 复测）

页面事实：

- 「设置封面」区写着 `默认截取第一帧作为封面`；同区还有 `智能推荐封面`（带「应用」）和
  一个 `PK封面` 开关；右侧面板 tab `笔记预览 / 封面预览`。
- 鼠标悬停当前封面缩略图才浮出 `编辑封面` 浮层；**鼠标一离开就消失**，所以事后按文本搜 DOM
  什么都找不到——那不是控件不存在，是需要先 `Input.dispatchMouseEvent({ type: 'mouseMoved' })`
  移到缩略图上才会挂出来。
- 2026-10-01：对浮层做了两次 CDP 点击，**都没有打开封面编辑器**，当时只能接受默认第一帧。
  失败原因没有查明。
- 2026-10-02：按下面的顺序**点一次就打开了编辑器**，上传批准的 3:4 封面并确认成功。和 10-01 相比多了
  「先移到附近再移上去、等约 0.9 秒、断言命中 `.cover-edit-entry`」这几步，具体是哪一步起作用
  **没有单独对照**，所以整套照做，不要删步骤。

### 已实测的上传顺序

本次读到的结构：

| 部件 | 本次读数 |
| --- | --- |
| 当前封面缩略图 | 2026-10-12：`.cover-plugin-preview .cover > .default.column`（不带 `artistic-bg`），是用 CSS `background-image` 显示图的 `div`，约 113×151。同一行右侧「智能推荐封面」的卡片也是 `.default`，但带 `artistic-bg`（约 157×118），要排除。2026-10-02 读到的是区内第一个宽高都 > 60px 的 `img` / `canvas`，同样约 113×151 |
| 悬停浮层 | `.cover-edit-entry`，文字在 `span.cover-edit-entry-text`，文本 `编辑封面`；鼠标移上去约 0.9 秒后出现 |
| 编辑器 | 标题「设置封面」；tab `裁剪 / 模版 / 贴纸 / 文字 / 滤镜`；模版列表默认选中 `无模板`；帧条最右端有 `+ 上传` |
| 图片文件输入 | 编辑器打开后**恰好一个** `input[type=file][accept*="image"]`，`accept="image/png, image/jpeg, image/*"` |
| 完成按钮 | `button.d-button`，内含 `span.circle-button-content` 文本 `完成`；888px 宽视口里位于 x 840–908，**部分在视口外** |
| 成功判据 | 编辑器关闭，页面出现 `封面效果评估通过，未发现封面质量问题` |

一轮一步，步骤之间不插别的点击或滚动。下面的片段按 2026-10-02 的实测顺序与选择器整理，计数、命中点、
tab 文本断言是保守写法。2026-10-12 第 2–7 步原样跑通；第 1 步的旧写法（只找 `img` / `canvas`）报
`no thumbnail near 设置封面`，按 `.cover-plugin-preview .cover > .default.column` 找的新结构分支跑通。下面 1b 里
退回 `img` / `canvas` 的分支沿用 10-02 的写法，没在新页面上走到。断言失败就停下截图，不要放宽：

```js
// 1a：把「设置封面」滚进视口（instant），这一轮不读 rect
const lab = await js(`(() => {
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 }
  const own = el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('')
  const labels = [...document.querySelectorAll('body *')].filter(el => vis(el) && own(el) === '设置封面')
  if (labels.length !== 1) return { error: '设置封面 label count = ' + labels.length }
  labels[0].scrollIntoView({ block: 'center', behavior: 'instant' })
  return { ok: true }
})()`)
if (lab.error) throw new Error(JSON.stringify(lab))
await new Promise(r => setTimeout(r, 700))

// 1b：下一轮取当前封面缩略图。先按 2026-10-12 的结构找，找不到再退回 2026-10-02 的 img / canvas
const th = await js(`(() => {
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 }
  const own = el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('')
  let hits = [...document.querySelectorAll('.cover-plugin-preview .cover > .default.column')]
    .filter(vis).filter(e => !e.classList.contains('artistic-bg'))   // 排除「智能推荐封面」卡片
  let via = 'div.default.column'
  if (hits.length === 0) {
    const label = [...document.querySelectorAll('body *')].find(el => vis(el) && own(el) === '设置封面')
    const big = el => [...el.querySelectorAll('img, canvas')].filter(m => {
      const r = m.getBoundingClientRect(); return r.width > 60 && r.height > 60 })
    let sec = label && label.parentElement             // 向上找最近一个含大图的祖先 = 这一区
    while (sec && sec !== document.body && big(sec).length === 0) sec = sec.parentElement
    hits = sec && sec !== document.body ? big(sec).slice(0, 1) : []
    via = 'img/canvas'
  }
  if (hits.length !== 1) return { error: 'current cover thumbnail count = ' + hits.length }
  const r = hits[0].getBoundingClientRect()
  return { via, x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
           w: Math.round(r.width), h: Math.round(r.height) }
})()`)
if (th.error) throw new Error(JSON.stringify(th))
// 10-02、10-12 两次都约 113×151；差得远（比如命中了右侧预览播放器或推荐卡片）就停下截图
if (Math.abs(th.w - 113) > 20 || Math.abs(th.h - 151) > 25) throw new Error('thumbnail size unexpected: ' + JSON.stringify(th))

// 2：真鼠标先移到缩略图外的附近一点，再移到缩略图中心，等约 0.9 秒
//    （附近点的具体偏移本次没记录；mouseMoved 不会点到任何东西）
await cdp('Input.dispatchMouseEvent', { type: 'mouseMoved', x: th.x - th.w, y: th.y })
await cdp('Input.dispatchMouseEvent', { type: 'mouseMoved', x: th.x, y: th.y })
await new Promise(r => setTimeout(r, 900))

// 3：断言浮层已挂出、且中心点命中它；鼠标此时仍停在缩略图上，不要再移
const en = await js(`(() => {
  const es = [...document.querySelectorAll('.cover-edit-entry')].filter(e => {
    const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 })
  if (es.length !== 1) return { error: 'visible .cover-edit-entry count = ' + es.length }
  const e = es[0], r = e.getBoundingClientRect()
  const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2)
  const at = document.elementFromPoint(x, y)
  if (!at || !e.contains(at)) return { error: 'entry centre is not inside .cover-edit-entry',
    at: at && (at.tagName + '.' + at.getAttribute('class')) }
  const t = e.querySelector('.cover-edit-entry-text')
  return { x, y, text: (t || e).textContent.trim() }
})()`)
if (en.error || en.text !== '编辑封面') throw new Error(JSON.stringify(en))
await cdp('Input.dispatchMouseEvent', { type: 'mousePressed',  x: en.x, y: en.y, button: 'left', clickCount: 1 })
await cdp('Input.dispatchMouseEvent', { type: 'mouseReleased', x: en.x, y: en.y, button: 'left', clickCount: 1 })
// 只点这一次
```

```js
// 4：下一轮确认编辑器开了，再找唯一的图片文件输入
const ed = await js(`(() => {
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 }
  const own = el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('')
  const leaf = [...document.querySelectorAll('body *')].filter(vis).map(own).filter(Boolean)
  return { tabs: ['裁剪', '模版', '贴纸', '文字', '滤镜'].filter(t => leaf.includes(t)),
           noTemplate: leaf.includes('无模板') }
})()`)
if (ed.tabs.length !== 5) throw new Error('cover editor not open: ' + JSON.stringify(ed))

const { root } = await cdp('DOM.getDocument', { depth: 0 })
const { nodeIds } = await cdp('DOM.querySelectorAll', {
  nodeId: root.nodeId, selector: 'input[type=file][accept*="image"]',
})
if (nodeIds.length !== 1) throw new Error('image input count = ' + nodeIds.length)
await cdp('DOM.setFileInputFiles', { nodeId: nodeIds[0], files: [COVER_3X4_ABS_PATH] })
```

5. 截图确认编辑器画布换成了批准封面；**保持 `无模板`**，模版、贴纸、文字、滤镜都不碰。
   本次没有动裁剪框，裁剪 tab 的拖动与比例行为 **未实测**。
6. 点 `完成`：用**语义 `.click()` 点 BUTTON 元素本身**，不要用坐标真鼠标。本次在 888px 宽视口里
   按钮横跨 x 840–908，CDP 真鼠标点 x=874 **没有关闭编辑器**，对按钮元素 `.click()` 才关掉。

   ```js
   const done = await js(`(() => {
     const bs = [...document.querySelectorAll('button.d-button')].filter(b => {
       const r = b.getBoundingClientRect(); const s = b.querySelector('span.circle-button-content')
       return r.width > 0 && r.height > 0 && s && s.textContent.trim() === '完成' })
     if (bs.length !== 1) return { error: 'visible 完成 button count = ' + bs.length }
     bs[0].click()
     return { clicked: true }
   })()`)
   ```

7. 下一轮回读：编辑器的 tab 已不可见，页面出现 `封面效果评估通过，未发现封面质量问题`；
   再切到右侧 `封面预览` 现拍截图，确认是批准封面、标题完整没被裁切或遮挡。评估出现别的文案时
   **未实测**：原文记录，停下给用户看，不要自己改图重传。

```js
const after = await js(`(() => {
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 }
  const texts = [...document.querySelectorAll('body *')].filter(vis).map(el =>
    [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('')).filter(Boolean)
  return { editorOpen: ['裁剪', '模版', '贴纸', '文字', '滤镜'].every(t => texts.includes(t)),
           evaluation: texts.filter(t => t.includes('封面效果评估')) }
})()`)
// 期望 editorOpen === false，evaluation 含「封面效果评估通过，未发现封面质量问题」；
// 文案若被拆成多个节点读不全，以截图为准
```

### 封面预览在视口外：临时放宽视口再截（2026-10-12）

视口 900×765 时，右侧 `笔记预览 / 封面预览` 两个 `.button-switch-item` 在 x≈937 / 1039，整块预览面板都在
视口外；`document.documentElement.scrollWidth` 也是 900，横向滚不过去。`Page.captureScreenshot` 加
`captureBeyondViewport: true` 和面板矩形做 clip，截出来只有底色，没有内容。

这次可行的做法（截完立即恢复，回读视口回到 900×765；之后又开了原创声明，再读全表时标题、正文、话题都与预期一致，
视口仍是 900×765。放宽前没有做逐字段快照，所以「放宽视口不影响表单」只到这个程度）：

1. 对文本为 `封面预览` 的 `.button-switch-item` 做语义 `.click()`：它只切换预览 tab，不改表单；
   回读 class 变成 `button-switch-item active`；
2. `Emulation.setDeviceMetricsOverride` 把视口放宽到 1440×900，等约 1.5 秒，现拍截图；
3. 立刻 `Emulation.clearDeviceMetricsOverride`，回读 `innerWidth / innerHeight` 回到原值；
4. 看图：信息流卡片里是批准封面、标题完整、没被裁切或遮挡，才算封面验收里截图那一半通过。

```js
const sw = await js(`(() => {
  const own = el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('')
  const t = [...document.querySelectorAll('.button-switch-item')].filter(el => own(el) === '封面预览')
  if (t.length !== 1) return { error: '封面预览 tab count = ' + t.length }
  t[0].click()
  return { ok: true }
})()`)
if (sw.error) throw new Error(JSON.stringify(sw))
await new Promise(r => setTimeout(r, 600))
// 下一轮：确认 tab 已切过去，并记下放宽前的视口
const vp0 = await js(`(() => {
  const own = el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('')
  const t = [...document.querySelectorAll('.button-switch-item')].find(el => own(el) === '封面预览')
  return { active: !!t && t.classList.contains('active'), vw: innerWidth, vh: innerHeight, dpr: devicePixelRatio }
})()`)
if (!vp0.active) throw new Error('封面预览 tab not active: ' + JSON.stringify(vp0))
await cdp('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: vp0.dpr, mobile: false })
try {
  await new Promise(r => setTimeout(r, 1500))
  await captureScreenshot(COVER_PREVIEW_SHOT)               // 绝对路径字符串
} finally {
  await cdp('Emulation.clearDeviceMetricsOverride', {})     // 截图失败也要恢复
}
await new Promise(r => setTimeout(r, 1000))
const vp = await js(`({ vw: innerWidth, vh: innerHeight })`)
if (vp.vw !== vp0.vw || vp.vh !== vp0.vh) throw new Error('viewport not restored: ' + JSON.stringify({ vp0, vp }))
```

- 预览面板本来就在视口内时不用放宽，切 tab 后直接截。
- 放宽期间拿到的任何坐标都作废。发布按钮的截图必须在恢复视口之后重新拍（见「发布按钮」）。

### 什么时候走上传、什么时候停下

1. 有本期批准的 3:4 封面文件（来源规则见 SKILL.md）就走上面的上传顺序；第一帧本来就是批准封面时
   也可以保留默认第一帧（离线抽一帧到 scratchpad **只用来看**，不拿它当封面素材）。2026-10-12 默认第一帧是全黑，这种情况必须上传批准封面；
2. **浮层没挂出、命中断言失败，或点一次 `编辑封面` 后编辑器没开**：不要重试、不要换点法，
   停下交接——把批准封面的绝对路径交给用户手动上传，交接后只回读 `封面预览` 截图；
3. 图片文件输入不是恰好一个、`.click()` 后编辑器仍开着，同样停下截图交接，不连点；
4. `智能推荐封面`、`PK封面` 一律不碰（行为 **未实测**），除非用户明确要求。

**小红书封面验收 = 「封面效果评估通过」回读 + 最新一张「封面预览」截图里批准封面的标题完整可读、
没被裁切或遮挡。** 截图要在封面相关操作之后现拍，旧图作废。本次缩略图约 113×151，与上传的 3:4
封面一致；横版等其他画幅的视频下缩略图比例 **未实测**，不要拿固定比例去预裁或判定。编辑器里的
裁剪框本次没有拿来验收，报告里照实写「封面按评估结果与封面预览截图验收」。

## 内容设置

区块内依次是：`添加章节`（`智能生成章节`）、`加入合集`（`创建合集`）、`原创声明`、
`添加内容类型声明`（下拉）。章节与合集本次没有操作，合集创建的字数上限与创建后能否改名
**未实测**——要用合集时先读页面上限，再按 SKILL.md 的合集口径询问用户。

2026-10-12 这一行是 `.collection-plugin-wrapper`：标题 `加入合集`、说明 `汇集系列视频，有利于连续性观看`，
右侧只有 `.collection-plugin-create`「创建合集」，没有下拉可选。由此推断账号当时没有小红书合集，没有另行核实
（没点开、没查合集列表）。其他平台的合集不会出现在这里；要建就先问用户，不要顺手建一个同名合集。

### 原创声明：开关 + 弹窗，两步都做完才算

开关在含文本 `原创声明` 的 `.custom-switch-card` 里，真正的状态在
`.d-switch .d-switch-simulator` 的 class：`unchecked` → `checked`。

**注意 `'unchecked'.includes('checked') === true`**，状态判断必须用
`classList.contains('checked')`，不能用字符串包含。

点开关会弹出固定定位的对话框，原文：

```text
笔记完成原创声明后，将获得以下权益 1. 获得原创笔记标记 2. 平台保护你的作品，识别并打击搬运
我已阅读并同意 《原创声明须知》 ，如滥用声明，平台将驳回并予以相关处置 声明原创
```

在**可见的**对话框里勾选协议复选框（`input[type=checkbox]` 读回 `checked === true`），
再点 `声明原创` 按钮；对话框关闭后开关仍是 `checked` 才算完成。只点开关、或只勾协议都不算。

```js
// a1. 只滚动，读当前状态；这一轮不读 rect
const sw0 = await js(`(() => {
  const cards = [...document.querySelectorAll('.custom-switch-card')].filter(c => c.innerText.includes('原创声明'))
  if (cards.length !== 1) return { error: '原创声明 card count = ' + cards.length }
  const s = cards[0].querySelector('.d-switch .d-switch-simulator')
  if (!s) return { error: 'no switch in 原创声明 card' }
  s.scrollIntoView({ block: 'center', behavior: 'instant' })
  return { on: s.classList.contains('checked') }
})()`)
if (sw0.error) throw new Error(JSON.stringify(sw0))
// sw0.on 已为 true 就到此为止，不要再点，否则会把它关掉
await new Promise(r => setTimeout(r, 800))

// a2. 下一轮重读 rect，断言命中点落在这张卡片的 .d-switch 里，再真鼠标点一次
const sw = await js(`(() => {
  const card = [...document.querySelectorAll('.custom-switch-card')].find(c => c.innerText.includes('原创声明'))
  const s = card.querySelector('.d-switch .d-switch-simulator'), box = card.querySelector('.d-switch')
  const r = s.getBoundingClientRect()
  const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2)
  const at = document.elementFromPoint(x, y)
  return { on: s.classList.contains('checked'), x, y, hit: !!at && box.contains(at),
           at: at && (at.tagName + '.' + at.className) }
})()`)
if (!sw.hit || sw.on) throw new Error('switch not clickable: ' + JSON.stringify(sw))

// b. 下一轮：只在「可见对话框」里找协议复选框与「声明原创」按钮
const dlg = await js(`(() => {
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 }
  const own = el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('')
  const center = el => { const r = el.getBoundingClientRect()
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) } }
  const btns = [...document.querySelectorAll('body *')].filter(el => own(el) === '声明原创' && vis(el))
  if (btns.length !== 1) return { error: 'visible 声明原创 count = ' + btns.length }
  const btn = btns[0]

  // 对话框容器：向上找 position:fixed / role=dialog / class 以 modal、dialog 结尾的祖先，
  // 且它包含「原创声明须知」；爬到 body 还没找到就失败，绝不在整页里找复选框
  const isDialog = el => getComputedStyle(el).position === 'fixed' ||
    el.getAttribute('role') === 'dialog' ||
    /(^|[\\s_-])(modal|dialog)(\\s|$)/i.test(el.getAttribute('class') || '')
  let box = btn.parentElement
  while (box && box !== document.body && !(isDialog(box) && box.innerText.includes('原创声明须知')))
    box = box.parentElement
  if (!box || box === document.body) return { error: 'no dialog container around 声明原创' }
  if (box.querySelector('.custom-switch-card')) return { error: 'container reaches the form, not a dialog' }

  // 排除对话框里任何开关卡片 / d-switch 自带的 checkbox（开关的 input 也是 type=checkbox）
  const cbs = [...box.querySelectorAll('input[type=checkbox]')].filter(c => {
    const k = c.closest('.custom-switch-card, .d-switch')
    return !k || !box.contains(k)
  })
  if (cbs.length !== 1) return { error: 'checkbox count in dialog = ' + cbs.length }
  const cb = cbs[0]

  // 点击目标：复选框可见就点它本身；否则点包住它的最小可见方块，绝不点文字行
  let target = vis(cb) ? cb : null
  if (!target) {
    const small = el => { const r = el.getBoundingClientRect(); return r.width <= 40 && r.height <= 40 }
    const area = el => { const r = el.getBoundingClientRect(); return r.width * r.height }
    const plain = el => vis(el) && small(el) && !el.textContent.trim() && !el.closest('a')
    let wrap = cb.parentElement                         // 包住复选框的最小可见祖先
    while (wrap && wrap !== box && !vis(wrap)) wrap = wrap.parentElement
    if (!wrap || wrap === box) return { error: 'no visible wrapper for checkbox' }
    // 它本身是无文字小方块就点它；若它已经是带文字的整行，只退到行内无文字的小方块（指示框），
    // 多个时取面积最大的那个，避免点到框里的勾号图标
    target = plain(wrap) ? wrap
      : [...wrap.querySelectorAll('*')].filter(plain).sort((a, b) => area(b) - area(a))[0] || null
    if (!target) return { error: 'no small text-free box for checkbox', wrapText: wrap.innerText.slice(0, 60) }
  }

  const c = center(target), b = center(btn)
  const atC = document.elementFromPoint(c.x, c.y), atB = document.elementFromPoint(b.x, b.y)
  const okC = !!atC && box.contains(atC) && !atC.closest('a') &&
    (atC === target || target.contains(atC) || atC.contains(cb))
  const okB = !!atB && (atB === btn || btn.contains(atB))
  if (!okC || !okB) return { error: 'hit test failed',
    atC: atC && (atC.tagName + '.' + atC.getAttribute('class')), atB: atB && atB.tagName }
  return { checked: cb.checked, cb: c, btn: b }
})()`)
if (dlg.error) throw new Error(JSON.stringify(dlg))
```

依次：

1. `dlg.checked === false` 时真鼠标点 `dlg.cb` **一次**；已经是 `true` 就跳过，不要再点（会取消勾选）；
2. 下一轮**重跑同一段** `js()`：读回 `checked === true`，并拿这一轮新算出的 `btn` 坐标；
3. 真鼠标点 `dlg.btn`（对话框自己的「声明原创」按钮）；
4. 下一轮确认 `声明原创` 按钮已不可见、开关 `classList.contains('checked')`。

- 命中点断言保证点下去的不是 `<a>`、也不在 `<a>` 里：那一行有 `《原创声明须知》` 链接，点偏会跳走。
  断言失败就停下截图，不要改点文字行中心。
- 复选框的具体外观结构（原生 input 还是自定义外框）**未实测**，以 `checked` 读回为准；
  点了读回仍是 `false` 就停下截图，不连点。
- 2026-10-12 按 a1 / a2 / b 的顺序在页面上跑通（b 的第二轮用的是只读回 `checked` 与按钮坐标的精简版）：开关中心命中
  `SPAN.d-switch-indicator`（在 `.d-switch` 内），CDP 真鼠标点一次弹出对话框；对话框里恰好一个复选框，
  读到 `checked === false`，真鼠标点一次后读回 `true`；「声明原创」命中的是 `SPAN.circle-button-content`，
  点一次后对话框关闭、开关 `classList.contains('checked')`。900×765 视口里复选框与按钮在同一行（y≈525）。

### 内容类型声明：默认不选

`添加内容类型声明` 是下拉。作者偏好（2026-10-01）：**默认保持未设置**，不选「含 AI 生成内容」
一类标注，除非用户在当前任务里明确要求；平台自己加上的标识不得移除。判断依据见
[素材来源与生成内容标注](../publish-gates.md#素材来源与生成内容标注)。下拉选项原文 **未实测**
（本次没有展开）。

## 添加组件与添加地点

`添加组件` 网格：`添加地点`、`选择群聊`、`引用笔记`、`添加投票`、`关联直播预告`、
`标记地点或标记朋友`、`添加路线`；下面是 `关联活动` chip。除地点外全部忽略，用户要求才动。

`添加地点` 是**行内搜索**（下面是本次的读数；本次用户在定位弹窗里选了什么没有记录，所以拒绝
定位时这一节是否照样成立 **未实测**，见上文「位置权限弹窗」）：

1. 点该字段，先弹出附近 POI 列表（餐馆等），焦点落在行内搜索框；附近列表是否依赖定位授权 **未实测**；
2. `Input.insertText('南头古城')`，结果每项两行：名称 + 地址，例如
   `南头古城 / 深圳市南山区南头街道南头城社区深南大道12024号(南头古城地铁站C口)`，
   以及 `南头古城(南门)`、`南头古城(东门)`、`南头古城(地铁站)`；
3. 只选**名称全等**的那一项；点之前用 `document.elementFromPoint` 确认坐标命中的是这一项；
4. 真鼠标点一次，回读字段显示该地点名。

```js
const loc = await js(`(() => {
  const NAME = ${JSON.stringify(PLACE)}
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 }
  const hits = [...document.querySelectorAll('body *')].filter(el =>
    vis(el) && el.textContent.trim() === NAME &&
    ![...el.children].some(c => c.textContent.trim() === NAME))   // 取最深的那层
  if (hits.length !== 1) return { error: 'exact match count = ' + hits.length }
  const el = hits[0], r = el.getBoundingClientRect()
  const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2)
  const at = document.elementFromPoint(x, y)
  const ok = !!at && (at === el || el.contains(at) ||
    (at.contains(el) && at.getBoundingClientRect().height < 120))   // 允许命中行容器，不允许命中大容器
  return { x, y, ok, at: at && (at.tagName + '.' + at.className) }
})()`)
if (loc.error || !loc.ok) throw new Error(JSON.stringify(loc))
```

全等匹配会排除 `南头古城(南门)` 这类同前缀项。结果列表是否对关键词做高亮拆分 **未实测**——
若高亮导致命中数不是 1，脚本会停下，改看截图，不要放宽成 `includes`。
清除已选地点的方法 **未实测**。

## 更多设置：可见范围与定时发布

`更多设置` 下有 `公开可见`（可见范围）和 `定时发布` 开关（**默认关**）。提交前两项都要回读：
可见范围读到的文本应为 `公开可见`（除非用户另有要求），定时开关应为关。

- 可见范围的其他选项 **未实测**；
- 打开定时发布之后的时间选择器、时区显示与提交流程 **未实测**；
- 定时开关也是 `.d-switch-simulator`：2026-10-12 下文字段表的 `switchNear('定时发布')` 读到 `unchecked`。
  `switchNear` 只在「同一行/卡片里恰好一个开关、且那一行写着 `定时发布`、不含 `原创声明` / `PK封面`」
  时才给出状态；否则返回 `null`，表示**未核实**，不是「关」。读到 `null` 以截图为准。
- 草稿与定时的处理口径见 [小红书约束](platform-constraints.md)「可逆性未知」节：在证实之前都按
  `publish` 级动作对待。

## 隐藏的「请刷新试试」不是错误

预览播放器里预渲染了 `xgplayer-error` 节点，文本 `请刷新试试 / 刷新`，`getBoundingClientRect()`
宽度为 0。它们**不是表单校验错误**。和视频号的预渲染弹窗同理：判定可见性，不判定存在性。

```js
const { errors } = await js(`({ errors: [...document.querySelectorAll('[class*=error]')]
  .filter(el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 })
  .map(el => el.innerText.trim()).filter(Boolean) })`)   // 包一层对象，见浏览器工作流「js() 返回数组时包成对象」
```

本次没有触发过任何真实校验错误，表单错误的真实结构与文案 **未实测**；上面的探针只能保证
不被隐藏的播放器占位误导。

## 发布按钮：closed shadow root，只能按截图坐标点一次

底部栏「暂存离开」和「发布」都在自定义元素 `XHS-PUBLISH-BTN` 里，shadow root 是 **closed**：

- `document` 里按文本找 `发布` 返回空；
- `element.innerText` 为空；
- `element.shadowRoot` 为 `null`。

宿主自己的属性倒是读得到（2026-10-29）：`is-publish=true`、`is-save-draft=true`、`submit-text=发布`、
`save-text=暂存离开`、`submit-disabled=false`、`submit-loading=false`、`save-disabled=false`。点之前可以断言
`submit-disabled` 和 `submit-loading` 都是 `false`；被话题上限拦下那次，点完 5 秒读到 `submit-loading` 仍是 `false`。
这些属性分不清两个按钮谁在左谁在右，坐标照旧按截图取。

所以语义定位、`snapshotText()` 的文本 ref、`.click()` 都用不上。做法，顺序固定：

1. 先过终稿确认（`awaiting_confirmation` → 用户明确同意）；Profile 把小红书登记为 `auto` 时，改为确认字段表
   全项 `pass` 且没有触发退回条件（见 SKILL.md「按 Profile 偏好免终稿确认」）；
2. （需要时）滚动，让底部栏完整出现在视口里；**滚动只能发生在截图之前**；
3. **截图**（本轮独立文件名），看图找红色的 `发布`，它在 `暂存离开` 右侧，读出它在**原图像素**
   里的坐标 `IMG_X, IMG_Y`。参考：888×734 视口里 `暂存离开` 在 (496, 689)、`发布` 在 (640, 689)；
   2026-10-12 的 900×765 视口（`devicePixelRatio` 2，`captureScreenshot` 出图仍是 900×765，换算系数 1）
   里是 (496, 720) 与 (640, 720)——只是参考，**每次都从最新截图取坐标**；
4. 下一轮先断言：截图像素尺寸与当前 `innerWidth × innerHeight`（× `devicePixelRatio`）对得上，
   换算后的点落在恰好一个 `xhs-publish-btn` 宿主里，且 `elementFromPoint` 就是这个宿主；
5. 断言通过立即 CDP 真鼠标点**一次**，然后只做回读。

截图与断言、断言与点击之间不插任何滚动、输入、等待或别的点击；插了就回到第 2 步重拍。

```js
// 轮 A：（需要时先滚动）→ 截图，到此为止
const SHOT = '/绝对路径/xhs-before-publish-<时间戳>.png'
await captureScreenshot(SHOT)                       // 传字符串路径，不传对象
```

```js
// 轮 B：看完轮 A 的图、读出 IMG_X / IMG_Y 后执行；中间不做任何别的动作
const SHOT = '/绝对路径/xhs-before-publish-<时间戳>.png'           // 与轮 A 同一个文件
const { readFileSync } = await import('node:fs')
const png = readFileSync(SHOT)
if (png.toString('ascii', 1, 4) !== 'PNG') throw new Error('screenshot is not a PNG: ' + SHOT)
const SHOT_W = png.readUInt32BE(16), SHOT_H = png.readUInt32BE(20)   // PNG IHDR 里的原图宽高
const chk = await js(`(() => {
  const W = ${SHOT_W}, H = ${SHOT_H}, dpr = devicePixelRatio
  const k = [1, dpr].find(s => Math.abs(W - innerWidth * s) <= 1 && Math.abs(H - innerHeight * s) <= 1)
  if (!k) return { error: 'screenshot size != viewport', shot: [W, H], vw: innerWidth, vh: innerHeight, dpr }
  const x = Math.round(${IMG_X} / k), y = Math.round(${IMG_Y} / k)
  const hosts = [...document.querySelectorAll('xhs-publish-btn')].filter(h => {
    const r = h.getBoundingClientRect()
    return x >= r.left && x <= r.right && y >= r.top && y <= r.bottom
  })
  if (hosts.length !== 1) return { error: 'hosts containing point = ' + hosts.length, x, y }
  const at = document.elementFromPoint(x, y)
  if (at !== hosts[0]) return { error: 'elementFromPoint is not that host', at: at && at.tagName, x, y }
  return { x, y, scale: k, vw: innerWidth, vh: innerHeight, dpr }
})()`)
if (chk.error) throw new Error('publish click aborted: ' + JSON.stringify(chk))
await cdp('Input.dispatchMouseEvent', { type: 'mousePressed',  x: chk.x, y: chk.y, button: 'left', clickCount: 1 })
await cdp('Input.dispatchMouseEvent', { type: 'mouseReleased', x: chk.x, y: chk.y, button: 'left', clickCount: 1 })
// 从这里开始只读，不论发生什么都不再点
```

尺寸不对、宿主不唯一、命中的不是宿主：都回到第 2 步重新截图，不要按比例硬换算旧坐标。
坐标必须按截图**原图像素**读；看的是缩放过的预览时，先换回原图像素再填 `IMG_X / IMG_Y`。

**这些断言只能证明点在发布栏宿主上，区分不了「暂存离开」和「发布」**——两者在同一个 closed
shadow 宿主里，`tagName`、宿主矩形、`elementFromPoint` 对两个按钮返回的都一样。左右之分只能靠
那张刚拍的截图，所以截图必须是点击前、断言前最后一个动作。点错成「暂存离开」的后果（草稿
是否保存、存在哪里）**未实测**。

**「暂存离开」同样按这套纪律。** 它和「发布」共用一个宿主，所以任何小红书草稿动作都要：终稿确认
（或直接把这一下交给用户点；Profile 的 `auto` 只针对「发布」，不覆盖这里）→（需要时）滚动 → 现拍截图 → 尺寸与宿主断言 → 只点一次。草稿流程
验证之前，点「暂存离开」按 `publish` 级动作对待，不当成「反正只是存草稿」的低风险操作。

**绝不点第二次。** 加载、跳转、无反应都一样：先去笔记管理回读。

### 点了「发布」没反应：先抓瞬时提示（2026-10-29）

这次前后点了 4 次「发布」（每次之前都回读过笔记管理，没有重复笔记）：URL 不变，截图里页面也没有变化，于是前三次
被判成「点击没生效」，其间交给过用户。第四次之前装上记录器，才读到真实原因：话题 12 个、超过上限 10 个，点击后
约 0.1 秒（记录器读到 87 ms）出现提示「最多支持添加10个话题」，很快消失，事后截图看不到；这次只发出了埋点请求
（`t2.xiaohongshu.com/api/v2/collect`），没有发布请求。

所以：

1. 话题数先过预检（`check_copy.py` 超过 10 个报 error），字段表里 `topics` 不超过 10 个才点；
2. 轮 A 截图之前先装下面的提示与请求记录器，让每一次点击都留下记录。它只包住 `fetch` / `XMLHttpRequest`，
   记 URL、方法、状态和前 200 字返回，不改请求；
3. 点完约 5 秒读记录，按读到的东西走：
   - `toasts` 里有提示原文（如「最多支持添加10个话题」）：被前端拦下了。按提示改字段，重读整张字段表；
     改的是用户写的文本时，按 SKILL.md 的退回条件停下确认；
   - `reqs` 里有 `POST …/web_api/sns/v2/note`、返回 `success: true`：提交成功，`data.id` 是笔记 ID，再去笔记管理回读状态；
   - 两样都没有：去笔记管理回读，确认没有新笔记后截图交接，交接说明里写明记录器什么也没读到；
4. 「点了没反应」先当成被前端拦下，不当成没点上：不换点法连点，也不在读记录之前交接。「绝不点第二次」照旧：
   回读确认没有新笔记、按记录改完之后，才按同一套纪律再点一次。

```js
// 轮 A 截图之前装上；装过就不重装
const log0 = await js(`(() => {
  if (window.__pubLog) return { already: true }
  window.__pubLog = { toasts: [], reqs: [] }
  new MutationObserver(ms => { for (const m of ms) for (const n of m.addedNodes) {
    const t = (n.innerText || n.textContent || '').trim()
    if (t && t.length < 120) window.__pubLog.toasts.push(Math.round(performance.now()) + ' ' + t) } })
    .observe(document.body, { childList: true, subtree: true })
  const of = window.fetch
  window.fetch = function (u, o) {
    const url = String(u && u.url || u), p = of.apply(this, arguments)
    p.then(r => r.clone().text().then(t => window.__pubLog.reqs.push({ url: url.slice(0, 120),
        method: (o && o.method) || 'GET', status: r.status, body: t.slice(0, 200) })))
      .catch(e => window.__pubLog.reqs.push({ url: url.slice(0, 120), err: String(e) }))
    return p }
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send
  XMLHttpRequest.prototype.open = function (m, u) { this.__u = String(u).slice(0, 120); this.__m = m; return oo.apply(this, arguments) }
  XMLHttpRequest.prototype.send = function () {
    this.addEventListener('loadend', () => window.__pubLog.reqs.push({ url: this.__u, method: this.__m,
      status: this.status, body: String(this.responseText || '').slice(0, 200) }))
    return os.apply(this, arguments) }
  return { installed: true }
})()`)

// 轮 B：断言通过后、点击之前，在同一个 js() 里清空记录并记下时间（2026-10-29 就是这样做的）：
//   window.__pubLog.t0 = Math.round(performance.now()); window.__pubLog.toasts = []; window.__pubLog.reqs = []
// 点完约 5 秒再读（埋点请求多时可按 /collect/ 过滤掉）：
const log = await js(`(() => {
  if (!window.__pubLog) return { gone: true }
  const h = document.querySelector('xhs-publish-btn')
  return { url: location.href, t0: window.__pubLog.t0,
    toasts: window.__pubLog.toasts.slice(-12), reqs: window.__pubLog.reqs.slice(-12),
    loading: h ? h.getAttribute('submit-loading') : null }
})()`)
```

- 跳到 `/publish/success` 是前端路由切换：2026-10-29 跳转之后记录器还在，提示「发布成功」和发布请求都读了出来。
  读到 `gone: true`（整页刷新或离开了）就以笔记管理为准，不要为了读记录再点；
- `reqs` 的返回里可能带账号 ID 等个人信息，报告里只写需要的字段（`success`、笔记 ID）。

## 成功页 URL 不是发布证据

点「发布」后约 1.5 秒内 URL 变成：

```text
https://creator.xiaohongshu.com/publish/success?source=official&bind_status=not_bind...
```

这只说明提交动作发生了，不证明笔记已发布，也不代表审核通过。`bind_status=not_bind` 的含义
**未实测**，不要解读。2026-10-29 跳转时还弹出提示「发布成功 / 5 秒后将返回发布页 / 立即返回」，发布请求的返回里
有笔记 ID（见上文「点了「发布」没反应」），两者同样只说明提交动作发生了。状态只按 [小红书约束](platform-constraints.md)「回读」节的笔记管理列表判定：
点「已发布」tab 前断言命中点，点完先确认 tab 真的切过去了（激活态，或列表里没有可见的
`审核中` / `未通过` 标签），再找本期条目；确认不了就保留最后已证实状态（通常是
`platform_pending`）并截图，不要因为「点过已发布」就判 `published`。

## 视口会在同一轮里变

同一次运行中两张截图之间视口从 1512×765 变成了 888×734。2026-10-12 全程 900×765；为截封面预览临时放宽到 1440×900，截完即恢复（见「封面」）。任何坐标——地点项、发布按钮、
原创开关——都只能来自**最新**截图或当轮 `getBoundingClientRect()`，旧坐标一律作废。
按截图取坐标的点击（目前只有发布栏）必须把截图像素尺寸传进同一个 `js()` 和
`innerWidth / innerHeight` × `devicePixelRatio` 比对，对不上就抛错重拍，写法见上文「发布按钮」。

## 一次读完整个字段表

提交前用一次 `js()` 读完，结果直接作为终稿确认的内容来源。占位变量在 node 侧替换：

```js
const state = await js(`(() => {
  const EXPECT = ${JSON.stringify({ account: ACCOUNT, place: PLACE, file: FILE_NAME })}
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 }
  const own = el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('')
  const all = [...document.querySelectorAll('body *')].filter(vis)
  const leafTexts = all.map(own).filter(Boolean)
  const sw = s => !s ? null : s.classList.contains('checked') ? 'checked'
    : s.classList.contains('unchecked') ? 'unchecked' : s.className
  // 定时开关同为 .d-switch-simulator（2026-10-12 读到 unchecked）。返回 null = 未核实（不是「关」）；只有确定是这一行自己的开关才给状态
  const switchNear = label => {
    const labels = all.filter(el => own(el) === label)
    if (labels.length !== 1) return null
    let n = labels[0]
    for (let i = 0; n && n !== document.body && i < 6; i++, n = n.parentElement) {
      const ss = n.querySelectorAll('.d-switch-simulator')
      if (ss.length > 1) return null                     // 爬到了包住多个开关的容器，停
      if (ss.length === 1) {
        const rowText = n.innerText
        if (!rowText.includes(label) || /原创声明|PK封面/.test(rowText)) return null
        return sw(ss[0])                                 // sw 用 classList.contains，不用字符串包含
      }
    }
    return null
  }
  const title = document.querySelector('input.d-text[placeholder="填写标题会有更多赞哦"]')
  const ed = document.querySelector('.tiptap.ProseMirror')
  const raw = ed ? ed.innerText : null
  const card = [...document.querySelectorAll('.custom-switch-card')].find(c => c.innerText.includes('原创声明'))
  const counterRe = /^\\d+\\s*\\/\\s*1000$/
  const counter = all.filter(el => counterRe.test(el.textContent.trim()) &&
    ![...el.children].some(c => counterRe.test(c.textContent.trim()))).map(el => el.textContent.trim())
  const errNodes = [...document.querySelectorAll('[class*=error]')]
  return {
    account: leafTexts.includes(EXPECT.account),
    uploadedFile: leafTexts.some(t => t.includes(EXPECT.file)),
    title: title ? title.value : null,
    titleLen: title ? [...title.value].length : null,
    body: raw,
    bodyWithoutTopics: raw && raw.replace(/#[^#\\n]+?\\[话题\\]#\\s?/g, '').trimEnd(),   // 只作诊断
    // 逐段真值：直接子 <p> 去掉话题节点、NBSP 换空格（2026-10-12：innerText 段间会多一个空行）
    paragraphs: ed ? [...ed.querySelectorAll(':scope > p')].map(p => {
      const c = p.cloneNode(true); c.querySelectorAll('a.tiptap-topic').forEach(a => a.remove())
      return c.textContent.replace(/\\u00a0/g, ' ').trim() }) : [],
    bodyCounter: counter,
    topics: ed ? [...ed.querySelectorAll('a.tiptap-topic')]
      .map(a => { try { return JSON.parse(a.dataset.topic).name } catch (e) { return null } }) : [],
    original: sw(card && card.querySelector('.d-switch .d-switch-simulator')),
    originalDialogOpen: all.some(el => own(el) === '声明原创'),
    location: { expectedShown: leafTexts.includes(EXPECT.place), placeholderShown: leafTexts.includes('添加地点') },
    visibility: leafTexts.filter(t => /可见/.test(t)),
    schedule: switchNear('定时发布'),
    errors: errNodes.filter(vis).map(e => e.innerText.trim()).filter(Boolean),
    hiddenErrorNodes: errNodes.filter(e => !vis(e)).length,   // xgplayer 占位，只作诊断
    viewport: [innerWidth, innerHeight],
  }
})()`)
```

判读：

- `errors` 非空就停在提交前；`hiddenErrorNodes` 只是诊断信息，不是失败。
- `topics` 与预期名称集合比较；有「新建话题」的单独列进被改写字段。
- `topics` 不超过 10 个：超了点「发布」会被前端拦下，只闪一下提示（2026-10-29，见「点了「发布」没反应」）。
- `original` 必须是 `checked`，且 `originalDialogOpen === false`（弹窗没收尾就不算完成）。
- `paragraphs` 去掉末尾的空串（话题单独成段，剥掉后为空）后，与冻结正文 `split('\n')` 逐段相等才算通过。
  `bodyWithoutTopics` 只作诊断：段间会多出一个空行（2026-10-12 读到 `A\n\nB`），整串比会误判。
- `bodyCounter` 应能读到唯一一条 `n /1000`；计数包含话题文本（2026-10-12：正文 32 字 + 7 个话题读到
  `71 /1000`），以页面计数器为准。
- `location.expectedShown` 只证明页面上能看见这个地名，选中后字段的容器结构 **未实测**，
  所以同时附一张截图；`placeholderShown` 在选中后是否消失也 **未实测**。
- `visibility` 预期含 `公开可见`。
- `schedule` 预期 `unchecked`。读到 `null` 是**未核实**，不能当成「没开定时」写进终稿确认：
  截图看定时开关那一行，图上能确认是关的才算；图上也确认不了就把「定时发布状态未核实」（定时是必填项，未核实即不是 `pass`，Profile 为
  `auto` 也不能直接提交）列进
  终稿确认，由用户决定。读到既不是 `checked` 也不是 `unchecked` 的 class 串同样按未核实处理。
- 封面不在这张表里：按上文「封面」节，用「封面效果评估通过」回读加最新的 `封面预览` 截图验收。
