« 2026-08-18 在真实投稿页实测（EP.01 `BV1vzbv6eERS`、EP.02 `BV1vrbv6AEYP`）。
平台前端会改版，这里的每条都要能被当场的快照推翻——以页面为准，本文只用来省掉从零摸索的那几轮。 »

# B 站投稿页结构与可复用探针

入口 `https://member.bilibili.com/platform/upload/video/frame`，编辑已投稿件走
`?type=edit&bvid=BVxxx`。

## 和视频号最大的差别：这是普通 Vue 应用

没有 shadow DOM，没有 wujie 微前端，`document.querySelector` 直接可用。
不要把视频号那套 `DOM.getDocument({ pierce: true })` 穿透遍历套过来，多余。

但**换来另一个坑**：Vue 的双向绑定不吃合成事件。

## 写值必须用原生 setter

`input.value = x` + `dispatchEvent(new Event('input'))` **不会**更新 Vue 的模型。
表现是页面上看得见字，但计数器不动、提交时报「还没有输入 XXX」。观测实例：
建合集连报三次「还没有输入合集标题」，计数器停在 `0/20`。

```js
const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set
setter.call(i, '')
i.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'deleteContentBackward' }))
setter.call(i, VALUE)
i.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: VALUE }))
i.dispatchEvent(new CompositionEvent('compositionend', { bubbles: true, data: VALUE }))
i.dispatchEvent(new Event('change', { bubbles: true }))
```

`inputType` 不能省——Vue 的 `v-model` 修饰符和平台自己的输入过滤都会读它。

### 标题字段是例外：原生 setter 写得进去，但会在 ~100ms 内被悄悄revert 回文件名

2026-08-19 EP.04 实测：标签、简介用上面的原生 setter 套路都稳定生效，唯独标题字段
（`input[placeholder="请输入稿件标题"]`）写入后**立即读回是对的，但过 100ms 再读就变回了
上传时的原始文件名**（定时读 0ms/100ms/1100ms 三个点位实测复现）。推测是这个输入框绑定了
「未被用户真正编辑过就用文件名兜底」的 watcher，只认真实用户交互，合成事件骗不过它。

唯一稳的写法是**真操作**：三击选中全部文本 → 真键盘删除 → `Input.insertText` 插入：

```js
const r = titleInput.getBoundingClientRect()
const x = r.x + r.width/2, y = r.y + r.height/2
await cdp('Input.dispatchMouseEvent', { type:'mousePressed', x, y, button:'left', clickCount:3 })
await cdp('Input.dispatchMouseEvent', { type:'mouseReleased', x, y, button:'left', clickCount:3 })
await cdp('Input.dispatchKeyEvent', { type:'keyDown', modifiers:2, key:'a', code:'KeyA' }) // Ctrl+A
await cdp('Input.dispatchKeyEvent', { type:'keyUp',   modifiers:2, key:'a', code:'KeyA' })
await cdp('Input.dispatchKeyEvent', { type:'keyDown', key:'Backspace', code:'Backspace' })
await cdp('Input.dispatchKeyEvent', { type:'keyUp',   key:'Backspace', code:'Backspace' })
await cdp('Input.insertText', { text: TITLE })
```

写完必须等 ≥1 秒再读一次确认没有反弹，不能只信写入瞬间的读回。这条坑只在标题字段观测到，
简介/标签/分区/合集用原生 setter 没有类似问题，不要不分青红皂白全改成真键盘（自定义标签的创建仍靠真回车，
见「标签」第 4 条）。

**2026-10-06 补充：`value` 对了，Vue 模型可能还是文件名。** 账号「手工川」发 15 分钟横版，照上面
三击 → 全选 → Backspace → `Input.insertText` 写完，`input.value` 读回是新标题，没有反弹；但标题计数器
停在 `30/80`，正是上传文件名的长度，也就是模型里还是文件名。补一组真按键再失焦，计数器才变成
`70/80`（与新标题长度一致）：

```js
const key = (type, k, code, extra = {}) => cdp('Input.dispatchKeyEvent', { type, key: k, code, ...extra })
await key('keyDown', 'End', 'End');             await key('keyUp', 'End', 'End')
await key('keyDown', ' ', 'Space', { text: ' ' }); await key('keyUp', ' ', 'Space')
await key('keyDown', 'Backspace', 'Backspace'); await key('keyUp', 'Backspace', 'Backspace')
await js(`document.querySelector('input[placeholder="请输入稿件标题"]').blur()`)
```

所以标题的验收**必须**是下一轮 `js()` 读到的计数器 `n/80` 中 `n === input.value.length`，只看 `value`
不算数。计数器的类名本次没有记下来，探针限定在标题输入框附近的叶子节点（不要扫全页，见下文
「计数器探针不要用 innerText 匹配」）：

```js
const t = await js(`(() => {
  const ti = document.querySelector('input[placeholder="请输入稿件标题"]')
  let box = ti.parentElement, tip = null
  for (let i = 0; i < 4 && box && !tip; i++, box = box.parentElement)
    tip = [...box.querySelectorAll('*')]
      .find(e => !e.children.length && /^\\d+\\s*\\/\\s*80$/.test(e.textContent.trim()))
  const n = tip ? Number(tip.textContent.split('/')[0]) : null
  return { value: ti.value, len: ti.value.length, counter: n, ok: n === ti.value.length }
})()`)
```

`ok` 为假时先补上面那组真按键，再隔一轮重读；找不到计数器（`counter: null`）就停下截图，不当成通过。
这段探针按本次读数整理，没有原样跑过。

## 同一次 `js()` 里读回的计数器是旧值

写完值在**同一个** `js()` 里读 `n/N` 计数器，拿到的是 Vue `nextTick` 刷新前的旧值。
`0/20` 因此是**假失败**：上面那三次「失败」里，第三次其实已经成功了，只是读得太早。

判据：写和读必须分成两轮 `js()` 往返。误判的代价是去改一个没坏的写入逻辑。
诊断办法是 dump 容器的 `outerHTML` 看真实的 `<p class="input-max-tip">8/20</p>`。

## 简介是 Quill，不是 contenteditable 裸写

`document.execCommand('insertText', false, 多行文本)` 会把多行**吞成首行**
（观测：736 字 → 22 字）。拿 Quill 实例以用户来源写入并主动失焦：

```js
const q = document.querySelector('.ql-container').__quill
q.setText(text, 'user')
q.blur()
```

实例挂在 `.ql-container` 的 `__quill` 双下划线属性上。写入必须下一轮读取
`.ql-editor > p` / `.ql-editor.innerText` 或 `q.getText()`，与冻结全文逐字比较；只看编辑器里
出现文字不代表提交模型已更新。2026-08-30 实测首次提交公开 `view.data.desc` 为空，按上述
`setText(text, 'user') → blur → 下一轮回读` 修正后才真正发布简介。

## 计数器探针不要用 innerText 匹配

用 `innerText.match(/\/2000/)` 扫全页会命中 `<style>` 标签里的 CSS 文本
（观测：读到 `51`，而编辑器里实际有 736 字；顺手 dump 出 1.4 MB 输出）。
直接读 `.ql-editor` 的 `innerText.length`，或把探针限定到计数器自己的容器。

## 标签：四个独立的坑

1. **平台会按账号名自动猜标签**。账号「手工川」自动带出 `手工`/`生活记录`/`记录`。
   填字段前先清空已有标签，不要在脏状态上追加。
2. **部分标签是话题专用、禁止自定义添加**。toast 原文「当前tag为话题专用，不允许自定义添加」。
   2026-08-18 实测被拒：`DeepSeekHarness`、`独立开发者`、`插件开发`。
   2026-10-06 实测被拒：`vibecoding`，换成 `AI编程` 被接受。
   优先点推荐 chip `.hot-tag-item`，那些一定能加。计划里的标签已经作为热门 chip 出现时，
   点 chip，不要手打（2026-10-06：`深圳`、`手工艺` 都是点 chip 加上的）。
3. **`svg.close` 和 `.hot-tag-item` 都不吃合成 click**。`.click()` 与
   `dispatchEvent(new MouseEvent('click'))` 都静默无效（观测：报告 `removed: 12`，标签一个没少）。
   必须真鼠标：

```js
const r = el.getBoundingClientRect()
const x = r.x + r.width / 2, y = r.y + r.height / 2
await cdp('Input.dispatchMouseEvent', { type: 'mousePressed',  x, y, button: 'left', clickCount: 1 })
await cdp('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 })
```

4. **自定义标签靠回车创建（2026-10-11 实测）**。推荐 chip 里没有的名字要手打。输入框是
   `.tag-container input`，placeholder 为「按回车键Enter创建标签」。顺序：按下文「窄视口」的写法真鼠标点中
   输入框 → `cdp('Input.insertText', { text: 名称 })` → 发一组 CDP `Enter`（`keyDown` / `keyUp`，
   `key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13`）→ 等约 1 秒，读 `.tag-container` 里每个 `svg.close`
   所在标签的文本，确认新名字出现。本次 7 个手打标签都这样加上。
   这是浏览器工作流「Enter 需用户确认」的限定例外，与小红书第一个话题同类：只在刚真鼠标点中标签输入框、
   焦点仍在输入框上时发，表单其他位置一律不发 Enter。名字被拒时按第 2 条换同义词，不要重复回车同一个名字。

## 投稿后标签回读：`view` 接口不含 tags

投稿页标签节点只证明编辑表单当时有值。发布后用标签专用公开接口回读：

```bash
curl -s 'https://api.bilibili.com/x/tag/archive/tags?bvid=BVxxx'
```

验收字段是 `data[].tag_name`。公开页的第二条证据是
`.video-tag-container a.tag-link`；链接应带 `from_source=video_tag`。B 站会重排标签顺序，
所以把预期值与两个来源都规范化成名称集合再比较，不按投稿顺序比较。

不要用 `/x/web-interface/view` 是否含 tags 判断——这个接口不返回标签；也不要因为简介里没有
`#AI #Agent ...` 就判断 tags 丢失，B 站把简介与标签作为两个独立字段展示。标签接口和公开页
节点都命中完整集合时，结论是 tags 已发布，无需重新编辑或投稿。

## 按钮落在视口外时，坐标点会静默丢

视口实测 1496×731，而这些按钮实测在视口下方：合集弹窗「完成」y=813、
「立即提交」y=1006、「立即投稿」y=1380。坐标点击打在视口外，不报错也不生效。
2026-08-19 EP.04 确认这条不止管主按钮：推荐标签 `.hot-tag-item`（如"原创"）在长页面
里同样会落到 y>1000 的视口外，用 `document.querySelector` 读到的 rect 一样是「看得见但点
不中」，现象和按钮完全一样——**任何要点的元素都先 `scrollIntoView` 再用刷新后的 rect**，
不要因为它是小标签就跳过这步。

```js
el.scrollIntoView({ block: 'center' })
// 必须重新读 rect，用**新**坐标点
const r = el.getBoundingClientRect()
if (r.y < 0 || r.y + r.height > window.innerHeight) throw new Error('still clipped')
```

上面这段写于视口 1496×731 时。2026-10-06 视频号观测到同一个 `js()` 里滚完立刻读 rect 会拿到滚动
中途的值（见 [视频号创建页结构](../wechat-channels/page-anatomy.md)「「发表」按钮」）；窄视口下 B 站还有
左侧导航遮挡，现在的完整写法见下文「窄视口：左侧固定导航会盖住表单」。

## 原创声明不是独立控件，是"原创"标签

skill 正文里「原创权益弹窗」那套写法是**视频号**的，B 站没有对应的独立「自制/转载」
勾选组件——2026-08-19 EP.04 实测整页搜「自制」「转载」「声明原创」「版权」全部
`indexOf === -1`。用户要求"原创要勾选"时，实际能做的操作是把推荐标签列表（标题正下方
「推荐标签：」那一行）里的 `原创` chip 点进正式标签，跟其他 `.hot-tag-item` 一样的坑
（真鼠标 + 视口内坐标）。不要因为找不到「原创声明」字样就报告缺失或去改创作声明
（那个是 AIGC 内容标注，跟原创无关，别混；2026-10-11 观测为必填，见下文「创作声明」；2026-10-01 观测到
创作声明下拉里另有非必选的授权声明，如「内容为转载」「内容为自制：未经作者允许，禁止转载」，默认不动）。

推荐标签会随稿件变化，**不一定有「原创」**：2026-10-11 发算法科普片时，那一行只有
算法 / 学习 / 全局 / 编程 / 数学。没有时不要自己敲一个「原创」普通标签，也不要拿授权声明顶替，
在终稿字段表里写「原创 chip：未出现」，需要终稿确认时由用户当次决定；Profile 为 `auto` 时不加，发布后报告写明
（见 SKILL.md「按 Profile 偏好免终稿确认」）。

## 上传页有两个视频 file input

按祖先链区分，不要取第一个。判据只用一条：祖先链含 `upload-wrp`，且 `accept` 含 `mp4`，并断言恰好命中一个。

| 祖先链包含 | 用途 |
| --- | --- |
| `upload-wrp`（同时也含壳层类名） | **主上传区**，用这个 |
| 只有 `york_videoup_wrapper` / `micro-app` | 另一个视频框和字幕 `.txt` 框，传进去没反应 |

2026-10-11 实测：主上传框的祖先链**同时**含 `upload-wrp` 和壳层类名 `york_videoup_wrapper` / `micro-app`
（读到 `main:true, shell:true`）。壳层类名包住了全部输入，不能当排除条件，用「不含壳层」过滤会把主上传框
一起排掉。当天读到的 `accept` 也不是单独的 `.mp4`，而是 `.mp4,.flv,.avi,…,.asf` 长列表，按 `includes('mp4')` 判断。

## 封面是两个独立的槽

这是本平台最容易误报成功的地方。

| 槽 | 比例 | 渲染在哪 |
| --- | --- | --- |
| 首页推荐封面 | 4:3 | 首页推荐位 |
| 个人空间封面 | 16:9 | **合集列表、个人空间、信息流** |

一次上传**只落到当前激活的编辑画布**，另一个仍是平台自动抽的视频帧。
`.cover-img` 的 `backgroundImage` 只反映 4:3 那个，表单显示「封面设置」也只证明 4:3 有图。

**唯一可信验证**是投稿后拉一次公开接口，看 `pic` 字段并把图下载下来看：

```bash
curl -s 'https://api.bilibili.com/x/web-interface/view?bvid=BVxxx' | python3 -c \
  'import json,sys; print(json.load(sys.stdin)["data"]["pic"])'
```

`pic` 反映的是 **16:9 槽**。弹窗内的预览只代表当前槽，不是发布结果。
2026-08-18 就是靠这条抓到「两期封面都只改了 4:3」：EP.01 的 `pic` 是 1080×607 纯黑，
EP.02 的 `pic` 是随机抽的一帧。

补 16:9 必须激活对应的编辑画布 wrapper 后直传；具体结构和恢复顺序见下文。不要依赖同步弹窗，
`双比例同步改动` 应保持关闭。**重传同一个文件可能因哈希不触发变化；关掉封面弹窗也不等于提交**，
改完仍要重新点「立即投稿」。

## `captureScreenshot` 在封面编辑器里出全白图

改用页内 canvas 抠图再 `Read`：

```js
const c = document.createElement('canvas')
c.width = img.naturalWidth; c.height = img.naturalHeight
c.getContext('2d').drawImage(img, 0, 0)
return c.toDataURL('image/jpeg', 0.9)
```

## 管理页直链会被重定向

`upload-manager/all` 和 `/season` 直接 `goto` 都会跳回 `/platform/home`。
要从侧边栏点进去：「内容管理」→「合集管理」，落在 `/upload-manager/ep`。

## 合集选择要精确匹配

列表里可能同时存在多个同前缀合集（观测：`手工川DSH实战`、`科技与社会 | 手工川工作室`、
`技术分享 | 手工川工作室`）。用 `text === 目标名`，不要用 `includes`。

下拉是 `.season-list.season-dropdown`，每项名称读 `.season-item-title`，用它的文本做 `===` 匹配；同一项里的
`.title-tips` 会重复全称，不要算进候选。2026-10-11 列表的 `scrollHeight` 大于 `clientHeight`，但所有项都在 DOM 里，
读名称不用滚动；点列表下方的项要不要先滚列表自身**未实测**。

「创建合集」入口是 `div.season-add`，弹窗只有一个 20 字输入框和「创建并加入 / 取消」，写值见下文
「`Input.insertText` 进得了 DOM，进不了 Vue 模型」。**与视频号相反**：点「创建并加入」后 `.season-enter-text`
直接显示新合集名，不用再选一次；投稿成功的 toast 也带「已加入合集」。验收仍以 `.season-enter-text[title]` 回读为准。

## 表单控件的真实类名（自研组件库，不是 antd）

2026-08-18 在 EP.03 投稿时因为**猜类名**把分区、合集、封面三项全填不进去，
最后靠用户手填收场。这里把实测的结构钉死。

| 字段 | 容器 | 入口（点这个） | 当前值读这里 |
| --- | --- | --- | --- |
| 分区 | `.video-human-type` | `.select-controller` | `p.select-item-cont` 的文本 |
| 合集 | `.video-season` | `.season-enter` | `.season-enter-text` 的 **`title` 属性** |
| 封面 | `.cover-main` | `.cover-main .edit-text` | `.cover-main .cover-img` 的 `background-image`（仅证明 4:3） |

不存在的东西（我全试过）：`.choose-btn`、`.ant-select-*`、`.ant-cascader-menu-item`、
`.ant-form-item`、`[role="combobox"]`、`.category-item`。B 站创作中心是自研组件库 +
`data-v-*` scoped CSS，套 antd 选择器一个都命中不了，而且**查不到不报错**，
表现为「点了没反应」，很容易被误读成时机没到而空等几轮。

编辑页（`?type=edit&bvid=`）的分区控件带 `select-controller-disabled`：**已投稿件不能改分区**，
不要在编辑页重试分区，那不是定位失败。

### 反模式：`querySelectorAll('*')` + `innerText.includes(标签名)`

这是上面三项全灭的直接原因。祖先容器的 `innerText` 含整页文本，所以第一个命中永远是
最外层 `div`，`closest()` 从那里往上找必然拿到导航栏。观测实例：找「分区」拿到
`y = -134`、文本 `"主站\n试试更多AI创作工具吧…"`，CDP 就照着负坐标点了出去。

定位一律走**叶子节点 + 文本全等**，拿到 label 之后**用上表的容器类名**，不要靠 `closest()` 猜：

```js
const label = Array.from(document.querySelectorAll('h3.section-title-content-main'))
  .find(el => el.textContent.trim() === '分区')          // 全等，不是 includes
const ctrl = label.closest('.video-human-type').querySelector('.select-controller')
```

同理，**读回值不要用 `innerText.split('\n')` 取相邻行**：DOM 顺序与视觉顺序不一致，
同一次会话里把合集依次读成「商业推广」「付费合集协议」「手工川-dsh-ep03-…-v0.1」（视频文件名），
三次全错且都不像错的。合集读 `.season-enter-text[title]`。

### 封面的 file input 在弹窗打开前不存在

主文档里 `input[type=file]` 只有 3 个：两个视频输入（见上文「上传页有两个视频 file input」）和一个 `.txt`
（字幕）。**没有任何 `accept=image` 的输入**，`DOM.getDocument({pierce:true})` 也一样查不到——
不是藏起来了，是还没挂载。必须先点 `.cover-main .edit-text` 打开封面编辑器，
弹窗里才会出现图片输入。

而 `span.edit-text` 不是 `<button>`，`querySelectorAll('button')` 按文本找「添加封面」找不到；
它和 `.hot-tag-item` 一样只吃 CDP 真鼠标。顺序固定为：
`scrollIntoView` → 按新 rect 发 CDP mousePressed/mouseReleased → 等弹窗 → 再查 file input。

### 封面素材去 `output/covers/<ep>/` 拿，不要抽视频首帧

项目里每期都有 `lov-channels-cover` 产出的 `cover_3x4.png` / `cover_4x3.png`，
另有 `output/deliverables/手工川-dsh-<ep>-封面-1440x1080-v*.png`。找不到 16:9 时
正确动作是**指出缺口**（那套只产 3:4 和 4:3），不是 `ffmpeg -vframes 1` 抽首帧顶上——
首帧是片头静帧，当封面等于没有封面。EP.03 线上 16:9 是 1440×810 的正式封面（人像 + 标题），
和抽帧完全是两回事。

## 封面 16:9 槽切换的正确入口（2026-08-30 EP.04 纠正）

右侧「首页推荐 / 个人空间」两个 `div.button` **只切换右侧效果预览，不切换上传目标**；
`button active` 只能证明预览卡片变了，把它当编辑槽证据会让 16:9 仍保留视频抽帧。

真正的两个编辑目标是 `.cover-editor-panel-canvas > div` 包住的 `#editor_4_3` 与
`#editor_16_9`。wrapper 的 `active / inactive` 才是当前上传目标状态：上传 4:3 前确认第一个
wrapper active；再点击第二个 inactive wrapper / canvas，回读其 class 变 active 后上传 16:9。
弹窗可能只有一个可见 `span.upload-text`，图片 file input 也只有打开编辑器后才挂载，因此每次
上传都必须先证明正确 wrapper 已激活，不能按第几个上传按钮猜槽位。

`双比例同步改动` 保持关闭。两张图上传后同时截图 `#editor_4_3` 与 `#editor_16_9` 的 canvas，
再点 `div.button.submit`「完成」。如果先前把素材传错槽，最安全的恢复是点「取消」丢弃本次未保存
图层，重新打开编辑器，按 4:3 wrapper → 上传 → 16:9 wrapper → 上传 → 双 canvas 截图 → 完成
的顺序重做；不要在未知激活状态上继续叠图。

投稿后仍用 `view.data.pic` 验收 16:9，并下载目视核对。投稿成功落地页会遮住编辑表单；需要修正时
从内容管理进入同一 BV 的编辑页，修完再次「立即投稿」，不得新建重复稿件。

## 立即投稿提交：先做一次语义点击，遮挡时再交用户（2026-08-30 修订）

- 点「立即投稿」会弹「封面制作」弹窗（4:3 / 16:9 封面效果确认），点「确定」后提交。
- 「立即投稿」按钮常被预渲染 `bcc-dialog`、视频预览 `canvas`/`vp-nd-b`、素材容器 `materials` 遮挡，
  `elementFromPoint` 命中遮挡元素，CDP 真鼠标点击落到遮挡上，按钮的 React onClick 不触发。
- **不要 `display:none` 弹窗/预览容器去「透传」**——那会破坏 React 状态，导致「立即投稿」的
  onClick 彻底失效（本 EP 踩过：隐藏弹窗后点「立即投稿」无任何反应，页面停留投稿页）。
- 终稿确认后先把主按钮滚入视口，刷新 rect，按可见名称做一次语义/直接点击；出现加载、跳转、
  成功页或提交态后立刻停止点击，只进入回读。
- 只有检查 `elementFromPoint` 后确认真实遮挡、且一次点击没有触发任何提交态时，才把「立即投稿」
  与封面确认弹窗交给用户。不要无条件手动交接，也不要隐藏遮挡层或盲目重复点击。

## 创作声明是必填的 `bcc-select`，下拉有展开动画（2026-10-01 实测，2026-10-11 观测为必填）

**2026-10-11 观测到「创作声明」已是必填项（标签前有红色星号），初始为空；2026-10-01 时还默认「内容无需标注」。**
留空点「立即投稿」会被 toast「请添加创作声明」拦下，下拉自动展开，页面停在表单，没有生成稿件。
这一下不算提交：确认 URL 仍是 `/platform/upload/video/frame`、没有「稿件投递成功」、可见 toast 是「请添加创作声明」
之后，补选并回读 `input.value`，再按原流程点一次。正常做法是在终稿确认**之前**就主动选好并回读，字段表不能写「未添加」。

选项是隐藏的 `li.bcc-option`（`ul.bcc-select-option-list`），
观测到：内容无需标注 / 含AI生成内容 / 含虚构演绎内容 / 内容含营销信息 / 个人观点，仅供参考 /
内容为转载，下方另有非必选的授权声明（如「内容为自制：未经作者允许，禁止转载」）。页面提示
「添加创作声明后该文案会在视频播放时展示，添加后不可再次编辑」——选错代价高，按常驻偏好选
「内容无需标注」。

操作：从目标 `li.bcc-option` 向上找 `class` 恰为 `bcc-select` 的祖先，真鼠标点它的输入区展开；
**等动画结束再读选项 rect**——展开过程中读到的各项 `y` 会重叠（实测两项都是 401），照它点会落在
别的选项上。确认 `document.elementFromPoint(x, y)` 命中目标 `li` 的文字后再真鼠标点击，读回
所属 `bcc-select` 内 `input.value`。

## 改标题后分区会被重新猜（2026-10-01 实测）

上传后平台先按文件名猜分区（观测「游戏」），写完标题后又被改成「vlog」。分区要在标题写完之后
选，并在提交前的全表回读里再读一次 `.video-human-type p.select-item-cont`。

## 分区下拉的列表自己会滚，被裁掉的项也有正常 rect（2026-10-12 实测）

分区下拉展开后是 `.drop-list-v2-container.human-type-list`（高约 264），选项在会滚动的
`.drop-list-v2-content-wrp`（高约 250）里，每项是 `.drop-list-v2-item > .drop-list-v2-item-cont > .item-cont-main`。
900×765 视口下 30 个一级分区排成一列，**被列表裁掉的项 `getBoundingClientRect()` 照样有正常的宽高和坐标**
（观测：「知识」读到 y=341，看上去在视口内）。对这个 rect 的中心做 `elementFromPoint`，命中的是外层表单容器，
不是这一项（这次在点击前被文本断言拦下，没有点出去）。命中检查若允许「命中节点包含目标」（`hit.contains(el)`），
外层容器也会通过，所以要断言命中节点的文本就是目标名。

做法：先只滚列表自身，再下一轮重读 rect、断言在列表可见区内且命中文本全等，最后真鼠标点一次：

```js
// 第 1 轮：只滚列表自身（不要 scrollIntoView，那会带着整页滚）
await js(`(() => { const wrap = document.querySelector('.video-human-type .drop-list-v2-content-wrp')
  const el = [...wrap.querySelectorAll('.item-cont-main')].find(e => e.textContent.trim() === ${JSON.stringify(NAME)})
  wrap.scrollTop = Math.max(0, el.closest('.drop-list-v2-item').offsetTop - 60) })()`)
await new Promise(r => setTimeout(r, 600))
// 第 2 轮：重读 rect，断言在列表可见区内、命中的就是这一项
const p = await js(`(() => { const wrap = document.querySelector('.video-human-type .drop-list-v2-content-wrp')
  const el = [...wrap.querySelectorAll('.item-cont-main')].find(e => e.textContent.trim() === ${JSON.stringify(NAME)})
  const r = el.getBoundingClientRect(), w = wrap.getBoundingClientRect()
  const x = Math.round(r.left + r.width / 2), y = Math.round(r.top + r.height / 2), hit = document.elementFromPoint(x, y)
  return { x, y, inside: r.top >= w.top - 1 && r.bottom <= w.bottom + 1,
           hitText: hit ? (hit.textContent || '').trim() : null } })()`)
if (!p.inside || p.hitText !== NAME) throw new Error('分区项未命中: ' + JSON.stringify(p))
// 真鼠标点 (p.x, p.y) 一次，下一轮读 .video-human-type p.select-item-cont
```

回读时注意：本次选「知识」，`p.select-item-cont` 读到「知识」；投稿后创作中心 `archives` 接口给的是
`tid: 122`、`typename: 野生技能协会`，公开 `view` 的 `tid` 也是 122、`tname` 为空。下拉显示一级分区名，接口给的是
落库分区，两者对不上不是选错，不要据此重选或重投。

## 审核期间的回读（2026-10-01 实测）

本次点「立即投稿」后**没有**出现「封面制作」确认弹窗，直接落到「稿件投递成功」页；两种情况都要
兼容，出现成功页后只做回读。稿件「审核中」时公开 `x/web-interface/view` 返回 `-404 啥都木有`，
不是失败。此时用带登录态的创作中心接口：

```js
// 包成对象：B 站投稿页上 js() 顶层返回数组读到过 null，见浏览器工作流「js() 返回数组时包成对象」
const { list } = await js(`fetch('https://member.bilibili.com/x/web/archives?status=is_pubing%2Cpubed%2Cnot_pubed&pn=1&ps=10&coop=1',
  { credentials: 'include' }).then(r => r.json())
  .then(d => ({ list: (d.data.arc_audits || []).map(a => ({ bvid: a.Archive.bvid, title: a.Archive.title,
    state_desc: a.Archive.state_desc, tag: a.Archive.tag, cover: a.Archive.cover })) }))`)
```

按标题找唯一条目，`state_desc` 原文写进状态（「审核中」→ `platform_pending`）；下载 `cover`
目视核对是否为批准的 16:9 封面。`/x/tag/archive/tags?bvid=` 审核期间已可回读。公开 title / desc /
pic 过审后再补读。账号用 `api.bilibili.com/x/web-interface/nav`（带登录态）读 `uname` / `mid` 逐字核对。

## `Input.insertText` 进得了 DOM，进不了 Vue 模型（2026-09-09 EP.01 实测）

创建合集弹窗里用 CDP `Input.insertText` 打字，`input.value` 读回是对的（`川言川语`），
但计数器**下一轮**读仍是 `0/20`——不是「读得太早」那个坑，是 Vue 的 `v-model` 压根没更新，
点「创建并加入」会当成空标题。换成本文开头那段原生 setter + `InputEvent(inputType)` 序列，
下一轮计数器立刻变 `4/20`。

判据：`insertText` 之后**隔一轮**再读计数器，还是 0 就换原生 setter，不要反复重打。
反过来，标题字段必须用真键盘（见上文「标题字段是例外」），自定义标签也要靠真回车创建（见上文「标签」
第 4 条）——标题和合集两个字段的正确写法恰好相反，不要互相套用。

## 封面：空封面时入口是 `.add-text`，不是 `.edit-text`

`.cover-main .edit-text` 只存在于**已有封面**的状态。首次投稿时封面是空的，DOM 里是
`.cover-slot > .cover-empty`，可点的叶子节点文本是「添加封面」、类名 `.add-text`。
按 `.edit-text` 找会直接抛「no .edit-text」，而这不是时机问题，等多久都不会出现。

`captureScreenshot` 在封面编辑器里出全白图（已知），验收改成把两个 wrapper 的 canvas
各自 `toDataURL` 落盘再看图：4:3 传完再点 16:9 wrapper，回读 class 变 `active` 之后传第二张，
最后两张 canvas 都截图确认——本期确认 4:3 没有被第二次上传覆盖。

## 窄视口：左侧固定导航会盖住表单（2026-10-06 实测）

浏览器视口约 900×765（比上文记录的 1496×731 窄）。左侧固定导航 `.cc-nav-wrp` 盖住表单左边约 200px，
页面还能横向滚动；横向滚过之后，标签的关闭图标 `svg.close` 正好落在导航底下，CDP 真鼠标的点击
落到了导航上，标签没删掉。

每一次 CDP 点击前都做两件事：

1. 先 `document.scrollingElement.scrollLeft = 0` 把页面横向滚回原位；目标在最右边（例如热门 chip
   `.hot-tag-item`）放不进视口时，改用 `scrollIntoView({ inline: 'center' })` 把它横向居中。
2. 下一轮 `js()` 重读 rect，断言 `document.elementFromPoint(x, y)` 命中目标本身，再点。

```js
// TARGET() 换成这次要点的元素，例如某个标签的 svg.close 或某个 .hot-tag-item
await js(`(() => {
  document.scrollingElement.scrollLeft = 0
  const el = TARGET(), r = el.getBoundingClientRect()
  if (r.left < 0 || r.right > innerWidth || r.top < 0 || r.bottom > innerHeight)
    el.scrollIntoView({ block: 'center', inline: r.right > innerWidth ? 'center' : 'nearest', behavior: 'instant' })
})()`)
const p = await js(`(() => {
  const el = TARGET(), r = el.getBoundingClientRect()
  const x = Math.round(r.left + r.width / 2), y = Math.round(r.top + r.height / 2)
  const hit = document.elementFromPoint(x, y)
  return { x, y, ok: !!hit && (hit === el || el.contains(hit)),
           underNav: !!(hit && hit.closest('.cc-nav-wrp')),
           hit: hit ? hit.tagName + '.' + hit.getAttribute('class') : null }
})()`)
if (!p.ok) throw new Error('目标被遮挡，不点: ' + JSON.stringify(p))
await cdp('Input.dispatchMouseEvent', { type: 'mousePressed',  x: p.x, y: p.y, button: 'left', clickCount: 1 })
await cdp('Input.dispatchMouseEvent', { type: 'mouseReleased', x: p.x, y: p.y, button: 'left', clickCount: 1 })
```

`svg.close` 被命中时 `hit` 常是里面的 `path`，所以按 `el.contains(hit)` 判断。读 SVG 的类名用
`getAttribute('class')`，`className` 是对象。代码按本次修正的步骤整理，没有原样跑过；断言失败时
先看 `underNav`，不要换成语义 `.click()`，这些控件本来就不吃合成点击（见上文「标签：四个独立的坑」）。
