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
| `#话题` 按钮 | `.tag-inner` 里自身文本为 `#话题` 的那个，取 `.closest('.finder-tag-wrap')` | 点击后描述末尾出现 `#` |
| 短标题 | `sr.querySelector('input[placeholder*="短标题"]')` | `value`；`maxLength` 是 `-1`，长度靠动态校验 |
| 校验错误 | `sr.querySelectorAll('[class*=error]')` | `.error-title` 的文本 |
| 位置 | `.location-name` / 容器 `.place` | 清空后 `.location-name` 变 `null` |
| 位置选项 | `.location-item`，目标项文本 `不显示位置` | `.form-item` 文本变为「位置 不显示位置」 |
| 合集 | `.form-item` 前缀「添加到合集」 | — |
| 原创主框 | 「声明原创」`.form-item` 内 `input[type=checkbox]` | `.checked` 真值 |
| 视频标注 | `.mark-tag-select` 打开，选项 `.mark-tag-option` | `.select-display` 文本 |
| 封面编辑入口 | `.edit-btn` | — |
| 主按钮 | `sr.querySelectorAll('button')` 按自身文本取 `发表` / `保存草稿` | 点击后进入加载态（自身文本变空） |

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

`.mark-tag-option` 实测四项，逐字如下：

```
无需标注
含AI生成内容
内容为虚构剧情，仅供娱乐
个人观点，仅供参考
```

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
    let origCb = null
    sr.querySelectorAll('.form-item').forEach(el => {
      if ((el.innerText || '').replace(/\\s+/g, ' ').trim().startsWith('声明原创'))
        origCb = el.querySelector('input[type=checkbox]')
    })
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
      originalChecked: origCb ? origCb.checked : null,
      schedule: Array.from(sr.querySelectorAll('input[type=radio]'))
        .map(r => ({ on: r.checked, label: (r.closest('label') || r.parentElement).innerText.trim() })),
      coverSlots: Array.from(sr.querySelectorAll('.cover-tips')).map(e => e.innerText.trim()),
      errors: errs,
    }
  })()
`)
```

`errors` 非空就停在提交前。这段同时是终稿确认要给用户看的内容来源。

## 描述与话题的写入顺序

### 用户手改后先冻结，不再进入写入分支

恢复发布页后的第一个动作先读 `.input-editor[contenteditable].innerText`。若非空且与 agent
上次写入值不同，记录 `description_source=user-edited` 与精确全文；后续封面、原创、合集、
位置等操作只允许回读描述，不允许执行本节下面的清空重建代码。每个无关写操作后逐字比较一次，
防止组件重渲染或旧脚本意外覆盖用户文本。

描述是 contenteditable，`fillInput` 不生效，连续输入会落在过期 caret 上。整体清空再一次性重建
（做法见 [浏览器工作流](../browser-workflow.md)），注意 `getSelection` 要取 shadow root 的：

```js
const sel = sr.getSelection ? sr.getSelection() : document.getSelection()
```

话题必须由平台生成节点。每加一个话题走一轮：把 caret 放到最后一个 `span.topic` 之后 →
插一个空格 → 点 `#话题` 按钮 → **再把 caret 收到编辑器末尾** → `typeText(话题名)` →
读 `span.topic` 个数确认 +1。

中间那步「再收一次 caret」不能省：点按钮本身会挪动选区，第二个话题实测把文字打在了 `#`
**之前**，末尾变成 `" #如何快速上手新项目 DeepSeekHarness#"`，个数不增。清理要用
`setStartAfter(最后一个 topic span)` + `setEnd(ed, ed.childNodes.length)` 再
`execCommand('delete')`，不要整体重建描述。

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
- 加话题的 caret 收尾（`range.selectNodeContents(ed); collapse(false)` 后点 `#话题` 再 `typeText`）会把正文末尾的空行吞掉，所以「话题前空行」靠事后 insertBefore 补，别指望加话题流程自己留空行。
