« 2026-10-01 一次真实视频笔记发布的记录（账号「手工川」，ego-browser / Chromium）。
平台前端会改版，这里的每条都要能被当场的快照推翻——以页面为准，本文只用来省掉从零摸索的那几轮。
证据按条标：写明「本次读到 / 本次点过」的是这次运行里的读数；标 **未实测** 的本次没有走通或
没有走到；代码片段里为了更稳加的断言（命中点、容器边界、尺寸核对）是保守写法，本身没有在
页面上跑过——断言失败就停下截图，不要放宽断言去迁就。 »

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
本次没有记录上传进度、转码/解析中的原文，所以 `uploading` / `processing` 的页面判据
**未实测**：看到什么文案就原文记录，不要套用视频号或 B 站的进度文案。

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
被拒后搜索不可用」，由用户决定。也不要为了省一次交接而预先授权定位。

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

- 标题 20 字是平台公开规则；本次**没有读到标题计数器**，超限时页面怎么表现 **未实测**。
- 字段非空时怎么清空 **未实测**（本次写入前为空）。非空先当作可能的用户手改处理，不要直接追加。

## 正文：ProseMirror，真点击 + `insertText`，读 `innerText`

编辑器 `.tiptap.ProseMirror`（contenteditable）。真鼠标点进编辑区后 `Input.insertText(body)`
生效；读回用 `innerText`，旁边计数器显示 `n /1000`（正文上限 1000，实测读到过）。

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

下一轮 `js()` 再读 `innerText` 与冻结全文逐字比较，并读计数器（探针见字段表那节，
**不要**用整页 `innerText.match(/\/1000/)`，B 站同类探针命中过 `<style>` 文本）。

- 接手页面的第一个只读动作仍是读正文全文；非空且与代理上次写入不同即
  `description_source=user-edited`，冻结，不再进入上面的写入分支。
- 清空已有正文的写法 **未实测**；多行正文里 `\n` 经 `insertText` 后的段落结构只做过
  `innerText` 整体比对，空行是否被折叠 **未单独核对**——比对不一致就停下报告，不要现场改写法。
- 话题插进来后 `innerText` 会多出 `#名称[话题]# `（隐藏的 `.content-hide` 文本），
  比对正文时先把这段剥掉，见字段表那节的 `bodyWithoutTopics`。

## 话题：`#` + 联想项**精确匹配**，生成 `a.tiptap-topic`

每个话题走一轮：

1. caret 收到正文末尾，断言焦点在编辑器里、联想列表没开着；**第一个话题前**按一次 Enter 起新段落，
   之后的话题只补一个空格分隔，不再按 Enter；
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
// 1：caret 到末尾，断言焦点与联想状态；本次记录的是「末尾 → Enter → insertText」这条序列，
// 下面用 Range 收 caret 的具体写法未单独实测，若话题没落在末尾就停下截图，不要叠加重试。
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
  const b = hit[0].el.getBoundingClientRect()
  return { x: b.x + b.width / 2, y: b.y + b.height / 2, meta: hit[0].meta, isNew: hit[0].meta === '新建话题', list }
})()`)
if (pick.error) throw new Error(pick.error + '\n' + pick.list.join('\n'))
await cdp('Input.dispatchMouseEvent', { type: 'mousePressed',  x: pick.x, y: pick.y, button: 'left', clickCount: 1 })
await cdp('Input.dispatchMouseEvent', { type: 'mouseReleased', x: pick.x, y: pick.y, button: 'left', clickCount: 1 })
```

5：按 `data-topic` 读名称，**这才是话题的真值**，不要在正文字符串里搜 `#`：

```js
const topics = await js(`[...document.querySelectorAll('.tiptap.ProseMirror a.tiptap-topic')]
  .map(a => { try { return JSON.parse(a.dataset.topic).name } catch (e) { return null } })`)
```

证据边界：本次记录的是每个话题前都「末尾 → Enter」；第二个起改成空格分隔是为了少发 Enter 的
保守写法，空格后输入 `#名称` 联想是否照常弹出 **未单独实测**。没弹出联想、或话题个数没 +1，
就停下截图，不要补 Enter 重试。

### 联想里只有「新建话题」

本次 `#AI` 的联想列表里只有一项，`children[1]` 是 `新建话题`——平台没有现成话题，点了会新建。
它的 `children[0]` 仍是 `#AI`，精确匹配会命中。处理规则：

- 照样只点那一项，但在终稿确认的「被平台改写」段里单独列出：
  `topic AI → 平台无现成话题，新建话题`，让用户看见；
- 新建话题生成的 `data-topic` 里 `id` / `link` 长什么样 **未实测**，验收只看解析出的 `name`；
- 离线脚本无法判断一个名字是否已有现成话题，只能在页面上看到。

### 不要碰的东西

编辑器下方的推荐话题 chip（`#生活美学` 之类）和 `# 话题 / @ 用户 / 表情` 按钮都忽略。
用 `# 话题` 按钮插话题的路径 **未实测**；话题个数上限 **未实测**。

## 封面：默认第一帧；换封面的入口本次没打开

页面事实：

- 「设置封面」区写着 `默认截取第一帧作为封面`；同区还有 `智能推荐封面`（带「应用」）和
  一个 `PK封面` 开关；右侧面板 tab `笔记预览 / 封面预览`。
- 鼠标悬停当前封面缩略图才浮出 `编辑封面` 浮层；**鼠标一离开就消失**，所以事后按文本搜 DOM
  什么都找不到——那不是控件不存在，是需要先 `Input.dispatchMouseEvent({ type: 'mouseMoved' })`
  移到缩略图上才会挂出来。
- 本次对浮层做了两次 CDP 点击，**都没有打开封面编辑器**。所以上传自定义封面的路径（编辑器
  结构、图片 file input、裁切与确认）全部 **未实测**。

本次能走通的做法：成片第一帧本来就是设计好的封面，于是接受平台默认（第一帧），并在
`封面预览` 里截图确认缩略图完整显示标题。缩略图的比例和裁切方式按「封面预览」实际显示的去核对；
具体比例（是不是 3:4、会不会随视频画幅变）**未实测**，不要拿一个固定比例去预裁或判定。

**小红书封面验收 = 最新一张「封面预览」截图里标题完整可读、没被裁切或遮挡。** 其他平台那种
「进封面编辑器逐个槽位回读」在这里做不到（编辑器本次没打开），所以不能声称逐槽位核对过；
报告里写「封面按封面预览截图验收，未经编辑器逐槽位核对」。

规则：

1. 上传前先离线确认成片第一帧是否就是本期批准的封面（抽一帧到 scratchpad **只用来看**，
   不拿它当封面素材——封面素材来源规则见 SKILL.md）；
2. 是：接受默认第一帧，切到 `封面预览` 重新截图，按页面实际显示的比例与裁切核对标题完整、
   没被裁切或遮挡；截图要在封面相关操作之后现拍，旧图作废；
3. 不是：**不要猜着点**。把批准封面的绝对路径交给用户，请他手动上传，交接后只回读
   `封面预览` 截图；
4. `智能推荐封面`、`PK封面` 一律不碰（行为 **未实测**），除非用户明确要求。

## 内容设置

区块内依次是：`添加章节`（`智能生成章节`）、`加入合集`（`创建合集`）、`原创声明`、
`添加内容类型声明`（下拉）。章节与合集本次没有操作，合集创建的字数上限与创建后能否改名
**未实测**——要用合集时先读页面上限，再按 SKILL.md 的合集口径询问用户。

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
// a. 点开关
const sw = await js(`(() => {
  const card = [...document.querySelectorAll('.custom-switch-card')].find(c => c.innerText.includes('原创声明'))
  const s = card && card.querySelector('.d-switch .d-switch-simulator')
  if (!s) return null
  s.scrollIntoView({ block: 'center' })
  const r = s.getBoundingClientRect()
  return { on: s.classList.contains('checked'), x: r.x + r.width / 2, y: r.y + r.height / 2 }
})()`)
// sw.on 已为 true 就不要再点，否则会把它关掉

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
- 上面的容器边界、尺寸阈值与命中断言是保守写法，**未在页面上跑过**；本次点开关和复选框
  用的具体点击方式也未记录，统一用 CDP 真鼠标是按 B 站经验的保守写法。

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
- 定时开关是否和原创一样用 `.d-switch-simulator` **未实测**——下文字段表的 `switchNear` 按这个
  假设去找，只在「同一行/卡片里恰好一个开关、且那一行写着 `定时发布`、不含 `原创声明` / `PK封面`」
  时才给出状态；否则返回 `null`，表示**未核实**，不是「关」。读到 `null` 以截图为准。
- 草稿与定时的处理口径见 [小红书约束](platform-constraints.md)「可逆性未知」节：在证实之前都按
  `publish` 级动作对待。

## 隐藏的「请刷新试试」不是错误

预览播放器里预渲染了 `xgplayer-error` 节点，文本 `请刷新试试 / 刷新`，`getBoundingClientRect()`
宽度为 0。它们**不是表单校验错误**。和视频号的预渲染弹窗同理：判定可见性，不判定存在性。

```js
const errors = await js(`[...document.querySelectorAll('[class*=error]')]
  .filter(el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 })
  .map(el => el.innerText.trim()).filter(Boolean)`)
```

本次没有触发过任何真实校验错误，表单错误的真实结构与文案 **未实测**；上面的探针只能保证
不被隐藏的播放器占位误导。

## 发布按钮：closed shadow root，只能按截图坐标点一次

底部栏「暂存离开」和「发布」都在自定义元素 `XHS-PUBLISH-BTN` 里，shadow root 是 **closed**：

- `document` 里按文本找 `发布` 返回空；
- `element.innerText` 为空；
- `element.shadowRoot` 为 `null`。

所以语义定位、`snapshotText()` 的文本 ref、`.click()` 都用不上。做法，顺序固定：

1. 先过终稿确认（`awaiting_confirmation` → 用户明确同意）；
2. （需要时）滚动，让底部栏完整出现在视口里；**滚动只能发生在截图之前**；
3. **截图**（本轮独立文件名），看图找红色的 `发布`，它在 `暂存离开` 右侧，读出它在**原图像素**
   里的坐标 `IMG_X, IMG_Y`。参考：888×734 视口里 `暂存离开` 在 (496, 689)、`发布` 在 (640, 689)
   ——只是参考，**每次都从最新截图取坐标**；
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
（或直接把这一下交给用户点）→（需要时）滚动 → 现拍截图 → 尺寸与宿主断言 → 只点一次。草稿流程
验证之前，点「暂存离开」按 `publish` 级动作对待，不当成「反正只是存草稿」的低风险操作。

**绝不点第二次。** 加载、跳转、无反应都一样：先去笔记管理回读。

## 成功页 URL 不是发布证据

点「发布」后约 1.5 秒内 URL 变成：

```text
https://creator.xiaohongshu.com/publish/success?source=official&bind_status=not_bind...
```

这只说明提交动作发生了，不证明笔记已发布，也不代表审核通过。`bind_status=not_bind` 的含义
**未实测**，不要解读。状态只按 [小红书约束](platform-constraints.md)「回读」节的笔记管理列表判定：
点「已发布」tab 前断言命中点，点完先确认 tab 真的切过去了（激活态，或列表里没有可见的
`审核中` / `未通过` 标签），再找本期条目；确认不了就保留最后已证实状态（通常是
`platform_pending`）并截图，不要因为「点过已发布」就判 `published`。

## 视口会在同一轮里变

同一次运行中两张截图之间视口从 1512×765 变成了 888×734。任何坐标——地点项、发布按钮、
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
  // 定时开关的结构未实测。返回 null = 未核实（不是「关」）；只有确定是这一行自己的开关才给状态
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
    bodyWithoutTopics: raw && raw.replace(/#[^#\\n]+?\\[话题\\]#\\s?/g, '').trimEnd(),
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
- `original` 必须是 `checked`，且 `originalDialogOpen === false`（弹窗没收尾就不算完成）。
- `bodyWithoutTopics` 与冻结正文逐字比较；`bodyCounter` 应能读到唯一一条 `n /1000`。
  计数是否把话题文本算进去 **未实测**，以页面计数器为准。
- `location.expectedShown` 只证明页面上能看见这个地名，选中后字段的容器结构 **未实测**，
  所以同时附一张截图；`placeholderShown` 在选中后是否消失也 **未实测**。
- `visibility` 预期含 `公开可见`。
- `schedule` 预期 `unchecked`。读到 `null` 是**未核实**，不能当成「没开定时」写进终稿确认：
  截图看定时开关那一行，图上能确认是关的才算；图上也确认不了就把「定时发布状态未核实」列进
  终稿确认，由用户决定。读到既不是 `checked` 也不是 `unchecked` 的 class 串同样按未核实处理。
- 封面不在这张表里：按上文「封面」节用最新的 `封面预览` 截图验收。
