« 2026-08-17 在真实创建页实测。平台前端会改版，这里的每条都要能被当场的快照推翻——
以页面为准，本文只用来省掉从零摸索的那几轮。 »

# 创建页结构与可复用探针

## 表单在 shadow root 里，不在主文档

创建页是 **wujie 微前端**：整个表单挂在 `<wujie-app>` 的 open shadow root 下。
后果是主文档的选择器**全部返回空**，且不报错：

```js
document.querySelectorAll('[contenteditable="true"]').length   // 0，不是编辑器不存在
document.querySelectorAll('input[type=file]').length           // 0，不是上传区不存在
```

这个空结果最容易被读成「素材还没解析完」或「控件还没渲染」，于是白等几轮。
所有 DOM 读写都先取 shadow root：

```js
const sr = document.querySelector('wujie-app').shadowRoot
```

文件输入连 shadow root 都查不到（它在更深的嵌套里），只有穿透遍历能看见：

```js
const doc = await cdp('DOM.getDocument', { depth: -1, pierce: true })
const files = []
function walk(n) {
  if (!n) return
  if (n.nodeName === 'INPUT') {
    const a = n.attributes || [], attrs = {}
    for (let i = 0; i < a.length; i += 2) attrs[a[i]] = a[i + 1]
    if ((attrs.type || '').toLowerCase() === 'file') files.push({ nodeId: n.nodeId, accept: attrs.accept })
  }
  for (const k of [].concat(n.children || [], n.shadowRoots || [], n.contentDocument ? [n.contentDocument] : [])) walk(k)
}
walk(doc.root)
```

两个文件输入按 `accept` 区分，都是 `display:none`，所以 `uploadFile` 的语义定位命中不了：

| accept | 用途 |
| --- | --- |
| `video/mp4,video/x-m4v,video/*` | 视频，创建页一开始就存在 |
| `image/jpeg,image/jpg,image/png` | 封面，**只在封面编辑器打开后才出现** |

提交路径用 `DOM.setFileInputFiles({ nodeId, files: [绝对路径] })`。先按 `accept` 断言唯一命中，
再提交；`nodeId` 每次重新取，不复用。

## 弹窗是预渲染的，必须按可见性过滤

页面把约 35 个弹窗全部预渲染进 DOM，只靠尺寸隐藏。读 `.weui-desktop-dialog` 的
`innerText` 会拿到与当前状态毫无关系的文案——观测到的实例：上传封面后读到
「将此次编辑保留? 不保存 保存」，而屏幕上根本没有这个弹窗，它属于另一条分支。
把它当成真实弹窗就会去点一个不存在的按钮，或误判流程走错了。

判定可见性，不要判定存在性：

```js
const visible = []
sr.querySelectorAll('.weui-desktop-dialog__wrp').forEach(el => {
  if (el.getBoundingClientRect().width > 100) visible.push(el)
})
```

隐藏节点的 `getBoundingClientRect()` 全部是 `0×0`。同一套过滤也用于「弹窗是否已关闭」的
回读——按钮消失不等于弹窗关闭。

## 控件定位表

`className` 比可读名称稳：快照里多数控件没有 accessible name。

| 字段 | 定位 | 读什么算真值 |
| --- | --- | --- |
| 描述 | `sr.querySelector('.input-editor[contenteditable]')` | `innerText` 全文逐字比对 |
| 话题标签 | 描述内 `span.topic[data-type=topic]` | **节点个数与文本**，不是描述字符串里搜 `#` |
| `#话题` 按钮 | `.tag-inner` 里自身文本为 `#话题` 的那个，取 `.closest('.finder-tag-wrap')` | 点击后出现 `#`，选区停在它紧后面；之后不要再挪 caret |
| 短标题 | `sr.querySelector('input[placeholder*="短标题"]')` | `value`；`maxLength` 是 `-1`，长度靠动态校验：超 16 字报「标题超过16字限制」；不足 6 字报「标题至少6个字」（2026-10-12，从 `[class*=error]` 可见节点读到，所在 class 没记录） |
| 校验错误 | `sr.querySelectorAll('[class*=error]')` | `.error-title` 的文本 |
| 位置 | `.location-name` / 容器 `.place` | 清空后 `.location-name` 变 `null` |
| 位置选项 | `.location-item`，目标项文本 `不显示位置` | `.form-item` 文本变为「位置 不显示位置」 |
| 合集 | `.form-item` 前缀「添加到合集」 | — |
| 原创主框 | 「声明原创」`.form-item` 内 `input[type=checkbox]` | 同一 `.form-item` 内存在 `.ant-checkbox-checked` **且** `.checked` 为真；只读属性会误报（见下文「原创」） |
| 视频标注 | `.mark-tag-select` 打开，选项 `.mark-tag-option` | `.select-display` 文本 |
| 封面编辑入口 | `.edit-btn` | — |
| 主按钮 | `sr.querySelectorAll('button')` 按自身文本**全等**取 `发表` / `保存草稿`，并要求 `width > 0` | 点击后进入加载态（自身文本变空）；点法见下文「「发表」按钮」 |
| 账号 | 主界面不显示账号名；用页内只读接口，见下文「账号」 | `errCode === 0` 且 `nickname` 与预期逐字一致 |

取「自身文本」要排除后代文本，否则父容器也会匹配上：

```js
const own = el => Array.from(el.childNodes)
  .filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('')
```

### 按标签文本反查控件时，只认叶子节点 + 文本全等

上表给的是直接选择器，优先用它。表里没有的字段才按标签文字找，此时**不要**写
`sr.querySelectorAll('*')` 再 `innerText.includes('分区')` 这类判断：容器的 `innerText`
含整个表单的文本，第一个命中永远是最外层 `div`，`closest()` 从那里往上找会拿到
页面外的节点（B 站侧观测到 `y = -134`，CDP 照着负坐标点了出去，详见
[B 站投稿页结构](../bilibili/page-anatomy.md)「反模式」）。

```js
const label = [...sr.querySelectorAll('.form-item label, .form-item h3')]
  .find(el => el.textContent.trim() === '位置')   // 全等，不是 includes
const ctrl = label.closest('.form-item').querySelector('input, button')
```

同理，**读回值不要靠 `innerText.split('\n')` 取相邻行**：DOM 顺序与视觉顺序不一致，
读到的「下一行」经常是别的字段。用「一次读完整个字段表」那节的做法，按 `.form-item`
逐块取。

## 视频标注的选项集

`.mark-tag-option` 2026-08 实测四项；2026-10-01 复测已扩到七项，逐字如下（含换行的副标题）：

```
无需标注
含AI生成内容
内容为虚构剧情，仅供娱乐
个人观点，仅供参考
内容包含营销广告
内容为自行拍摄\n添加拍摄时间和地点
内容为转载\n添加转载来源(选填)
```

默认按作者偏好保持「无需标注」或不选，见 SKILL.md「生成内容标注默认不勾」。

按选项文本精确匹配后 `click()`，再读 `.select-display`。不要按序号点——顺序会变。

## 一次读完整个字段表

提交前的字段表用一次 `js()` 读完，比逐字段截图快一个数量级，且拿到的是真值而非外观：

```js
const state = await js(`
  (() => {
    const sr = document.querySelector('wujie-app').shadowRoot
    const ed = sr.querySelector('.input-editor[contenteditable]')
    const title = sr.querySelector('input[placeholder*="短标题"]')
    const item = p => {
      let r = null
      sr.querySelectorAll('.form-item').forEach(el => {
        const t = (el.innerText || '').replace(/\\s+/g, ' ').trim()
        if (t.startsWith(p)) r = t
      })
      return r
    }
    let origItem = null
    sr.querySelectorAll('.form-item').forEach(el => {
      if ((el.innerText || '').replace(/\\s+/g, ' ').trim().startsWith('声明原创')) origItem = el
    })
    const origCb = origItem && origItem.querySelector('input[type=checkbox]')
    const errs = []
    sr.querySelectorAll('[class*=error]').forEach(el => {
      const t = (el.innerText || '').trim(); if (t) errs.push(t)
    })
    return {
      shortTitle: title.value,
      shortTitleLen: title.value.length,
      desc: ed.innerText,
      topics: Array.from(ed.querySelectorAll('span.topic')).map(s => s.textContent),
      location: item('位置'), collection: item('添加到合集'),
      link: item('链接'), activity: item('活动'), markTag: item('视频标注'),
      // 两个都要读：2026-10-06 观测到属性为 true 而界面未勾，见下文「原创」
      originalClass: origItem ? !!origItem.querySelector('.ant-checkbox-checked') : null,
      originalChecked: origCb ? origCb.checked : null,
      schedule: Array.from(sr.querySelectorAll('input[type=radio]'))
        .map(r => ({ on: r.checked, label: (r.closest('label') || r.parentElement).innerText.trim() })),
      coverSlots: Array.from(sr.querySelectorAll('.cover-tips')).map(e => e.innerText.trim()),
      errors: errs,
    }
  })()
`)
```

`errors` 非空就停在提交前。这段同时是终稿确认要给用户看的内容来源。原创只有
`originalClass && originalChecked` 都为真才记 `pass`，两者不一致时按未勾选处理并停下。
agent 合成写入过描述时，再按下文「合成写入后，手机预览可能还是旧文案」的读法读一次预览，作为字段表的
`preview` 行（对应 publish-gates「描述预览」），对不上就停在提交前。

## 账号（2026-10-11 实测）

创建页主界面不显示账号名：按 `name` / `nick` / `account` 类名查只拿到品牌名和菜单名；全文搜账号名只命中
合集名和下文的 `.no-permission-content`；悬停左下角头像也不弹名片。改用页内只读接口核对，和 B 站 `x/web-interface/nav` 同性质：

```js
await js(`fetch('/cgi-bin/mmfinderassistant-bin/auth/auth_data', { method: 'POST', credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ timestamp: String(Date.now()), _log_finder_uin: '', _log_finder_id: '', rawKeyBuff: null, pluginSessionId: null, scene: 7, reqScene: 7 }) })
  .then(r => r.json()).then(d => ({ errCode: d.errCode, nickname: d.data && d.data.finderUser && d.data.finderUser.nickname,
    adminNickname: d.data && d.data.finderUser && d.data.finderUser.adminNickname }))`)
```

`errCode === 0` 且 `nickname` 与预期逐字一致才算通过（本次 `nickname` 与 `adminNickname` 都是「手工川」）。
这组参数 2026-10-11、10-12 各跑通一次；登录态失效时返回 `errCode: 300333`（见下文「登录态失效」）。接口报错或
字段缺失时，退回 SKILL.md 第 6 步停下确认，不要猜。打开封面编辑器后，
弹窗里的「视频号 · <账号名>」是页面上可见的佐证，一并记进字段表。

shadow root 里还预渲染了 `.no-permission-content`，文案是「当前登录账号不是视频号「手工川」的管理员或运营者…」，
尺寸 0×0。它和预渲染弹窗一样按可见性过滤：不能当作账号不符的证据，也不能当作账号名的来源。

## 登录态失效：URL 可能先报创建页（2026-10-12 实测）

这次打开创建页时登录态已经失效，几处读数先后不一致，要按下面的顺序判断：

1. `openOrReuseTab(创建页, { wait: true })` 返回后，`pageInfo().url` 仍是 `/platform/post/create`，`snapshotText()` 只有
   `svg_root`——看上去和「表单在 shadow root 里所以快照为空」一模一样；
2. 约 10 秒后 `auth_data` 返回 `{ errCode: 300333 }`，`document.querySelector('wujie-app')` 为 `null`；
3. 约 20 秒后再读 `pageInfo().url` 才是 `https://channels.weixin.qq.com/login.html`，正文有「登录视频号助手」「加载失败，点击重试」。
   是 `openOrReuseTab` 返回后才重定向，还是返回时读数滞后，这次没有区分。

所以：`auth_data` 返回非 0（这次是 300333），或创建页上找不到 `wujie-app` 时，先重读 URL，确认是不是被重定向到了
`login.html`，不要当成表单还没渲染而空等。

是登录页就按 [浏览器工作流](../browser-workflow.md)「视频号跨域 iframe 的快捷登录」点一次「微信快捷登录」。这次点完：

- 4 秒时 URL 还是 `login.html`，登录框里只有一个加载圈；
- 34 秒时 URL 已回到 `/platform/post/create`（中间没有看），`auth_data` 返回 `errCode: 0`、`nickname` 为「手工川」。

点完按约 2.5 秒间隔轮询 URL 约 40 秒，等到离开 `login.html` 再核对账号；40 秒还在登录页再交接，不要点第二次。

## 描述与话题的写入顺序

### 用户手改后先冻结，不再进入写入分支

恢复发布页后的第一个动作先读 `.input-editor[contenteditable].innerText`。若非空且与 agent
上次写入值不同，记录 `description_source=user-edited` 与精确全文；后续封面、原创、合集、
位置等操作只允许回读描述，不允许执行本节下面的清空重建代码。每个无关写操作后逐字比较一次，
防止组件重渲染或旧脚本意外覆盖用户文本。

描述是 contenteditable，`fillInput` 不生效，连续输入会落在过期 caret 上。整体清空再一次性重建
（做法见下文「描述换行与话题空行」），注意 `getSelection` 要取 shadow root 的：

```js
const sel = sr.getSelection ? sr.getSelection() : document.getSelection()
```

### 合成写入后，手机预览可能还是旧文案（2026-10-11 实测，一次观测）

用 `removeChild` / `insertBefore(textNode)` 加合成 `InputEvent` 改写描述、之后没有任何真键入时，
`.input-editor.innerText` 逐字正确，左侧手机预览却仍是改写前的文案；隔一分钟两次回读都没变。同一会话先用
`innerHTML` 写首版、随后用 `typeText` 加话题，预览是跟上的。
预览没更新时点「发表」会不会发出旧描述**未实测**，先按会发出处理。

修法：把 caret 放进正文文本节点（本次放在首行末尾、第一个 `\n` 之前，不碰 `span.topic`），`typeText(' ')`，
再发一组 CDP 真 `Backspace`（`keyDown` / `keyUp`，`windowsVirtualKeyCode: 8`），然后 `blur()`；约 2 秒后预览变成
新文案，编辑区全文不变。只有 agent 最后一次改描述用的是合成写入、之后没有真键入时才需要这一步；用户在页面上
手改的文本本来就是真输入，不要去补键。

验收：在 shadow root 内、`.input-editor` 之外，找**自身文本节点**含冻结描述首句的元素，它的文本必须以冻结描述的
首段开头；找不到或对不上就停在终稿确认之前。本次用的读法：

```js
const hits = []
sr.querySelectorAll('*').forEach(e => {
  const own = [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('')
  if (own.includes(HEAD) && !e.closest('.input-editor')) hits.push(own.slice(0, 60))
})
```

`HEAD` 取冻结描述首句的前十来个字；排查时可同时搜旧文案的开头，确认旧预览已经消失。

话题必须由平台生成节点。每加一个话题走一轮（2026-10-02 实测走通的顺序）：

1. caret 收到编辑器末尾；
2. 不是第一个话题时 `typeText(' ')` 补一个空格；
3. 点 `#话题` 按钮；
4. **不要再挪 caret**：按钮插入 `#` 后会把选区留在这个 `#` 紧后面（本次读到选区在文本节点
   `" #\n"` 的 offset 2）；
5. `typeText(话题名)`；
6. 等约 1 秒，读 `span.topic` 个数确认 +1。

不变量是「输入名称时 caret 紧跟着刚插入的 `#`」。第 5 步前先断言这一点，不成立就停下截图，
不要用收 caret 到末尾来凑：

```js
const at = await js(`(() => {
  const sr = document.querySelector('wujie-app').shadowRoot
  const ed = sr.querySelector('.input-editor[contenteditable]')
  const sel = sr.getSelection ? sr.getSelection() : document.getSelection()
  const n = sel.anchorNode, o = sel.anchorOffset
  return { inEditor: !!n && ed.contains(n), isText: !!n && n.nodeType === 3,
           prevChar: n && n.nodeType === 3 ? n.textContent.slice(0, o).slice(-1) : null,
           node: n && n.nodeType === 3 ? n.textContent : null, offset: o,
           topics: ed.querySelectorAll('span.topic').length }
})()`)
if (!at.inEditor || at.prevChar !== '#') throw new Error('caret is not right after #: ' + JSON.stringify(at))
```

这个断言按本次的选区读数整理，是保守写法，没有原样在页面上跑过。

**caret 问题的两次观测，都保留**——它们是同一个不变量的两种破法：

- 2026-08：当时的做法是「caret 放到最后一个 `span.topic` 之后 → 插空格 → 点 `#话题` →
  **再把 caret 收到编辑器末尾** → `typeText`」。不收那一下时，点按钮挪动了选区，第二个话题
  把文字打在了 `#` **之前**，末尾变成 `" #如何快速上手新项目 DeepSeekHarness#"`，个数不增；
  所以当时补上了「再收一次 caret」。
- 2026-10-02：照上面那条做法加第二个话题失败。描述的 innerHTML 末尾多了一个 `"\n"` 文本节点，
  点完按钮再把 caret 收到编辑器末尾，caret 落在这个换行**之后**，离开了 `#`，打进去的名称只是
  纯文本（末尾成了 `" #深圳"`），没有生成 `span.topic`。改成点按钮后不动 caret 就成功了。

也就是说「点完按钮再收到末尾」只在 `#` 恰好是编辑器最后一个字符时碰巧成立，不能当规则用；
以第 5 步前的断言为准。

失败一轮后的清理：选中最后一个 `span.topic` 之后到编辑器末尾的内容并删除，不要整体重建描述：

```js
const r = document.createRange()
r.setStartAfter(lastTopicSpan)                 // ed 里最后一个 span.topic
r.setEnd(ed, ed.childNodes.length)
sel.removeAllRanges(); sel.addRange(r)
document.execCommand('delete')
```

第一个话题就失败时没有 `span.topic` 可当起点，这种清理写法 **未实测**，停下截图交给用户。

少了空格，新话题会粘在上一个标签里；不读回个数，就无法区分「插入成功」和「只留了个 `#`」。

## 封面槽位数量会变，不要写死几个

同一天的两次会话读到了**不同的槽位数**：一次是一个槽（标签「个人主页和分享卡片(3:4)」，
两个预览由同一张 3:4 裁出，4:3 图没有上传入口），一次是两个槽
（`["个人主页卡片","3:4","分享卡片","4:3"]`，4:3 图有自己的入口）。所以这个数字既不能写死
两个，也不能写死一个——每次现场数。

```js
Array.from(sr.querySelectorAll('.cover-tips')).map(e => e.innerText.trim())
```

读到几个就传几张并各自验安全区；确认只有一个时才在报告里写 4:3 无入口、留作备用件。

### 4:3 槽的交互与 3:4 槽不同

点 4:3 槽的 `.edit-btn` **不开弹窗**（可见弹窗读回 `[]`），而是弹一个浮层
「使用此素材作为封面? / 直接编辑 / 使用素材」。浮层里那张图要探一下真实像素：

```js
const im = /* 浮层内的 img */; ({ nw: im.naturalWidth, nh: im.naturalHeight })
// 观测到 810×1080 —— 这是 3:4，平台想把竖图复用到横槽
```

`810×1080` 意味着点「使用素材」会把 3:4 封面塞进 4:3 槽并裁掉标题。要传真正的 4:3 图必须走
「直接编辑」进编辑器（弹窗标题「编辑分享卡片」），编辑器打开后图片文件输入才出现。

## 描述换行与话题空行（2026-08-20 EP.05 实测补充）

- 描述（`.input-editor[contenteditable]`）设置换行**必须用 `<br>`，不能用 `<div>`**：`<div>` 会被编辑器剥离成纯文本 `\n`，空行（`\n\n`）折叠成单个换行，段落挤在一起。设法 `desc.split('\n').map(l => l + '<br>').join('')`，空行由连续 `<br>` 表示。
- 话题标签前要留一个空行：正文设置完后，在第一个 `span.topic` 前 `insertBefore(document.createElement('br'), firstTopic)`，否则话题和上一行黏在一起（读 `innerText` 末尾几行确认有空行）。
- 正文里的 `#` 会被平台识别成话题标签：模板里「#公众号：手工川、官网：https://…」整串会被当成一个 topic。模板的「#公众号」要写成纯文本「公众号」，真话题只用 `#话题` 按钮生成。
- 加话题的 caret 收尾（`range.selectNodeContents(ed); collapse(false)` 后点 `#话题` 再 `typeText`）会把正文末尾的空行吞掉，所以「话题前空行」靠事后 insertBefore 补，别指望加话题流程自己留空行。（这是 2026-08 的旧顺序；2026-10-02 起点按钮后不再收 caret，见上文「描述与话题的写入顺序」。新顺序下末尾空行还会不会被吞 **未单独核对**，仍按事后 insertBefore 补并读 `innerText` 确认。）

## 合集下拉：列表自己会滚，`scrollIntoView` 会把下拉关掉（2026-09-09 EP.01 实测）

`.option-list-wrap` 实测高 220px，6 个 `.option-item` × 40px = 240px，最后一项**只露出 20px**。
坑有三个，都表现为「点了没反应」或「点到别的东西」：

- 直接按第一次读到的 rect 点最后一项，y 会落在 wrap 下沿之外，实际命中的是下面的
  「创建新合集」——于是又弹一次创建弹窗，而不是选中。
- 对目标 `.option-item` 调 `scrollIntoView` 会滚动祖先（页面），下拉当场关闭；紧接着的
  `getBoundingClientRect()` 全部返回 `top === bottom` 的塌陷值（实测 6 项全是 384/384），
  看起来像「元素在同一个位置」，其实是列表已经不在了。
- 只能滚列表**自己**：同一个 `js()` 里 `wrap.scrollTop = wrap.scrollHeight` 之后再读 rect，
  并对「目标行完全落在 wrap 内」下断言，然后用 CDP 真鼠标点。

```js
const t = await js(`(() => {
  const sr = document.querySelector('wujie-app').shadowRoot
  const wrap = [...sr.querySelectorAll('.option-list-wrap')].find(e => e.getBoundingClientRect().width > 50)
  wrap.scrollTop = wrap.scrollHeight                       // 只滚列表，不碰页面
  const el = [...wrap.querySelectorAll('.option-item')].find(e => e.innerText.trim().startsWith(NAME))
  const r = el.getBoundingClientRect(), w = wrap.getBoundingClientRect()
  return { x: Math.round(r.left + 60), y: Math.round(r.top + r.height/2),
           inside: r.top >= w.top - 1 && r.bottom <= w.bottom + 1 }
})()`)
if (!t.inside) throw new Error('目标行仍在可视列表外，不点')
```

**新建合集不等于已选中**：`创建` 成功后只弹「已创建合集」，`.post-album-display` 仍是
「选择合集」。必须关掉提示、重开下拉、再选一次，并回读 `.post-album-display` 的文本。

**用户说「合集沿用上一条」（2026-10-11 实测）。** 内容列表的卡片不显示所属合集，创建页下拉也只给
「名称 共N个内容」。做法：另开标签页打开内容列表（创建页不要导航走），列表顶部有「合集 (N)」分页，
按自身文本匹配 `/^合集\s*\(\d+\)$/` 后 `.click()` 进入，找包含上一条（按发表时间，跳过置顶）的那个合集。
确定名称后回到创建页，按上文选中并回读。

只想读候选、暂不选择时：下拉按 `Esc` 关不掉，再点一次 `.post-album-display` 就能收起（它是开关），
收起后回读 `.post-album-display` 仍应是「选择合集」。

## 原创：主复选框的 `.checked` 会和界面不一致（2026-10-06 实测）

账号「手工川」发 15 分钟横版时观测到：点创建页「声明原创」主复选框 → 弹出「原创权益」弹窗 →
按「取消」。弹窗关掉后界面上主复选框**没勾**，`input[type=checkbox].checked` 却仍读回 `true`。
只读属性的字段表会把这个状态报成「原创：已勾选」。

和界面一致的是同一 `.form-item` 里有没有 `.ant-checkbox-checked`。这是现场读到的类名，不是按
antd 猜的（SKILL.md 说「套 antd 猜类名命中不了」，指的是没观测过的选择器）。

最终验收两者都要成立：

```js
const orig = await js(`(() => {
  const sr = document.querySelector('wujie-app').shadowRoot
  const item = [...sr.querySelectorAll('.form-item')]
    .find(el => (el.innerText || '').replace(/\\s+/g, ' ').trim().startsWith('声明原创'))
  if (!item) return null
  const cb = item.querySelector('input[type=checkbox]')
  return { cls: !!item.querySelector('.ant-checkbox-checked'), prop: !!(cb && cb.checked) }
})()`)
if (!orig || !(orig.cls && orig.prop)) throw new Error('原创未生效: ' + JSON.stringify(orig))
```

- 判断「现在要不要点主复选框」也以 `.ant-checkbox-checked` 为准：属性为 `true` 不代表已勾，照它跳过就漏勾了。
- `cls` 为假、`prop` 为真就是本次的取消残留态，按未勾选处理。在这个状态下再点主复选框会怎样 **未单独核对**：
  点一次后先确认可见弹窗是「原创权益」再继续，没弹出来就停下截图，不连点。
- 2026-08 起的「弹窗关闭后读主复选框 `checked=true`」仍是必要条件，只是不再充分。

## 「发表」按钮：滚动和读 rect 分两轮，命中断言后只点一次（2026-10-06 实测）

同一次发布，浏览器视口约 900×765，比文档里别处记录的 1496×731 窄，按钮更容易落在视口外。

- 在同一个 `js()` 里 `scrollIntoView({ block: 'center' })` 后立刻 `getBoundingClientRect()`，读到的是
  **滚动中途**的 rect。按这个坐标点「发表」，页面没有任何变化，内容列表里也没有新条目，点空了且不报错。
- 修正后的做法：`scrollIntoView({ block: 'center', behavior: 'instant' })` → 等约 1 秒 → 下一轮 `js()`
  重读 rect → 断言 `shadowRoot.elementFromPoint(x, y)` 就是这个按钮 → 只点一次。

还有一个预渲染干扰项：某个隐藏弹窗里有「直接发表」按钮（原创权益的推销分支），宽度为 0。
按 `includes('发表')` 找按钮会先命中它。只认自身文本**全等** `发表` 且 `width > 0` 的那个，并断言唯一。

```js
const FIND = `
  const sr = document.querySelector('wujie-app').shadowRoot
  const own = el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('')
  const btns = [...sr.querySelectorAll('button')]
    .filter(b => own(b) === '发表' && b.getBoundingClientRect().width > 0)  // 排除宽 0 的「直接发表」
`
// 第 1 轮：只滚动，不读 rect
await js(`(() => { ${FIND}
  if (btns.length !== 1) return btns.length
  btns[0].scrollIntoView({ block: 'center', behavior: 'instant' }); return 1
})()`)
await new Promise(r => setTimeout(r, 1000))
// 第 2 轮：重读 rect，用 shadow root 的 elementFromPoint 断言命中
const t = await js(`(() => { ${FIND}
  if (btns.length !== 1) return { ok: false, count: btns.length }
  const b = btns[0], r = b.getBoundingClientRect()
  const x = Math.round(r.left + r.width / 2), y = Math.round(r.top + r.height / 2)
  const hit = sr.elementFromPoint(x, y)
  return { ok: !!hit && (hit === b || b.contains(hit)), x, y, vw: innerWidth, vh: innerHeight,
           hit: hit ? hit.tagName + '.' + hit.getAttribute('class') : null }
})()`)
if (!t.ok) throw new Error('「发表」未命中，不点: ' + JSON.stringify(t))
await cdp('Input.dispatchMouseEvent', { type: 'mousePressed',  x: t.x, y: t.y, button: 'left', clickCount: 1 })
await cdp('Input.dispatchMouseEvent', { type: 'mouseReleased', x: t.x, y: t.y, button: 'left', clickCount: 1 })
```

`hit` 允许是按钮的后代节点。代码按本次修正的步骤整理，没有原样在页面上跑过。

### 点了没反应：先在另一个标签页看列表，再决定要不要重试

- 按钮没进加载态、页面没跳转也没提示时，不要马上再点。**另开一个标签页**打开内容管理列表并重载，
  按标题、描述前缀和提交时间找本次条目。
- 不要把创建页标签导航到列表：离开创建页表单就丢了，描述、话题、封面、原创都得重来。
- 列表里已有本次条目，就只做回读，不再点。确认没有条目后才回到创建页，重读字段表（描述冻结照样生效），
  按上面的两轮流程重试一次；仍然没反应就停下交给用户，不继续换点法。
- 列表最前面可能是**置顶**的旧作品，卡片上有「取消置顶」。2026-10-11 发表后重载，新条目排在两条置顶之后的
  第三位（状态「原创审核中」）。所以读列表时不要只取前几张卡片，也不要把第一张当成最新：跳过带「取消置顶」
  的卡片，再按描述前缀加提交时间找唯一条目。只扫前 N 张就判「没有条目」，会走进上一条的重试分支，在不可逆的
  视频号上重复发表。

### 列表页重载后要等 wujie 挂出（2026-10-12 实测）

「发表」进入加载态后页面自己跳到 `/platform/post/list`（点击后 3 秒仍是创建页，17 秒时已跳到列表页，中间没看）。在列表页
`location.reload()` 之后：

- 6 秒时读 DOM，`js()` 挂了十几秒后报 `Runtime.evaluate timed out`（页面还在加载，不是脚本错）；
- 30–60 秒之间再读，`wujie-app` 还不存在，主文档里按卡片类名自然读到 0 张；
- 约 85 秒时 `wujie-app` 已挂出（中间没看，截图已能看到卡片）；约 120 秒时从 shadow root 读到本条卡片全文。

卡片的 class 选择器（`[class*=post-feed-item]`）只在 `wujie-app` 挂出前跑过，对不对没有核实。这次挂出后用的是按描述
前缀找文本节点的写法，读到了本条卡片全文（状态、发布时间、操作栏）；同一张卡片可能读出外层与内层两份，取带操作栏的那份：

```js
const card = await js(`(() => {
  const w = document.querySelector('wujie-app')
  if (!w) return { mounted: false }
  const want = ${JSON.stringify(DESC_PREFIX)}
  const hits = [...w.shadowRoot.querySelectorAll('*')].filter(e => {
    const t = e.innerText || '', h = e.getBoundingClientRect().height
    return t.includes(want) && t.length < 400 && h > 60 && h < 200
  }).map(e => e.innerText.replace(/\\s+/g, ' ').trim())
  return { mounted: true, hits: [...new Set(hits)] }
})()`)
// mounted 为 false、js() 超时或 hits 为空：等一会儿再读，不要判「没有条目」
```

轮询到 `wujie-app` 挂出、shadow root 里有内容再下结论。`js()` 超时、没挂出、没读到卡片都不等于没有条目——当成没有，
就会走进上一节的重试分支，在视频号上重复发表。

### 内容列表卡片上的操作（2026-10-12 观测）

本次条目（状态「原创审核中」）的卡片文本末尾是一排操作：

```text
置顶 分享 弹幕管理 评论管理 修改描述和封面 可见权限 删除
```

（置顶卡片上有「取消置顶」，见上一节 2026-10-11 的记录；10-12 没读置顶卡片的操作栏。）「修改描述和封面」说明描述和封面至少有事后修改的入口，和以前「发布后
不可撤改」的记录不同；但这次**只读到入口、没有点过**，下面几点都未实测：

- 能改的范围（话题、短标题、合集、位置是否也在里面）；
- 改完是否重新进入审核、原创声明是否保留。

所以门禁口径不变：视频本身换不了，发表前的终稿确认仍是最后一道闸。要用这个入口改已发条目，先当成
一次新的 `publish` 级动作：读现值 → 冻结要改的文本 → 终稿确认 → 只点一次保存 → 回列表重载回读。
