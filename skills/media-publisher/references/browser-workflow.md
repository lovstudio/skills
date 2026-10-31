# 浏览器工作流（ego-browser，跨平台）

本文只写**各平台都成立**的部分：helper 签名、控制权规则、任务空间生命周期、
以及发布流程的六个阶段骨架。平台各自的 DOM 结构与写值方式在
[视频号创建页结构](wechat-channels/page-anatomy.md)、
[B 站投稿页结构](bilibili/page-anatomy.md) 和
[小红书发布页结构](xiaohongshu/page-anatomy.md) 里，不要互相套用。

## 操作原则

- 使用 `ego-browser` 的 task space 执行：`const task = await useOrCreateTaskSpace('media publish')`，同一任务持续复用同一空间，避免反复切换上下文。
- 所有关键动作前后先 `await snapshotText()`，以稳定文本 ref/loc 重定向控件；每次重渲染后必须重新读取快照。
- 使用语义交互为主：`openOrReuseTab` / `snapshotText` / `click` / `fillInput` / `uploadFile`；仅在必要时使用 `js` 读取 DOM 或 `pageInfo` 辅助。
- 语义 ref 只对最近一次快照有效。元素不在视口时先 `DOM.scrollIntoViewIfNeeded` 或滚动后重新截图；不要用页面坐标点击视口外元素。
- 仅在有明确用户确认时操作 `pressKey('Enter')`；遇到文本输入时默认 `click -> typeText/fillInput` + 失焦回读。
  例外只有两处，各带前置条件：小红书第一个话题（见[小红书发布页结构](xiaohongshu/page-anatomy.md)「话题」）、
  B 站自定义标签（见 [B 站投稿页结构](bilibili/page-anatomy.md)「标签」第 4 条）。
- 避免复用旧句柄、旧 ref、旧 CSS 选择器和旧坐标，页面变化后全部重新识别。

## helper 签名：传 id，不传 task 对象

2026-08-17 / 08-18 实测，下面这些调用会直接抛错，各费一轮往返。它们都属于「看起来对但签名不同」，
所以照表写，不要凭直觉：

| 写法 | 结果 |
| --- | --- |
| `handOffTaskSpace(task)` | 抛 `task space not found: [object Object]` |
| `handOffTaskSpace(task.id)` | 正常，返回 `{ done: true }` |
| `waitForAgentControl()` | 抛 `requires a task space name or id` |
| `waitForAgentControl(task.id)` | 正常阻塞等待；用户归还控制权后 resolve 为 `undefined`（2026-10-02 观测），这个返回本身就是归还信号 |
| `captureScreenshot({ path: '/tmp/a.png' })` | 抛 `ERR_INVALID_ARG_TYPE`，它把对象当路径 |
| `captureScreenshot('/tmp/a.png')` | 正常，返回路径字符串 |
| `screenshot(...)` | `ReferenceError`，helper 名是 `captureScreenshot` |
| `mouseClick(x, y)` | `ReferenceError`，没有这个 helper。当前运行时可用 `click([x, y])`（2026-09-06 实测），或 `cdp('Input.dispatchMouseEvent', { type: 'mousePressed'/'mouseReleased', x, y, button: 'left', clickCount: 1 })`；坐标必须来自最新浏览器截图或节点 rect |
| `completeTaskSpace(task, opts)` | 抛 `requires a task space name or id`，和 `handOffTaskSpace` 同坑 |
| `completeTaskSpace(task.id)` | 抛 `completeTaskSpace requires { keep: boolean }`（2026-10-11 实测），第二个参数不能省 |
| `completeTaskSpace(task.id, { keep: false })` | 正常，返回 `{ done: true }`；用户要求保留页面时改传 `{ keep: true }` |
| `` await js(`[...nodes].map(...)`) ``（顶层直接返回数组） | 2026-10-12 在 B 站投稿页两次得到 `null`（字符串数组、对象数组各一次），后面一读 `.length` 就抛 `Cannot read properties of null`；同日视频号创建页顶层数组正常返回 |
| `` await js(`({ list: [...nodes].map(...) })`) `` | B 站投稿页正常，数组在对象里原样拿到 |
| 页面刚 `location.reload()` 就 `js()` 读 DOM | 视频号列表页 2026-10-12 重载后 6 秒读 DOM，`js()` 挂了十几秒后报 `Runtime.evaluate timed out`（距重载约 21 秒）：页面还在加载，不是脚本错。等一会儿再读，不要当成失败或「没有条目」 |

### js() 返回数组时包成对象

`js()` 要返回数组时，一律包成对象再解构（`const { list } = await js(...)`）。顶层数组在哪些页面会变成 `null`
没有摸清（2026-10-12 B 站投稿页两次），返回对象的调用在三个平台上都正常。返回字符串、数字这类原始值时没见过问题。

heredoc 按 **ES module** 解析：`require` 报 "Cannot determine intended module format"，
要读本地文件用 `const { readFileSync } = await import('node:fs')`。

同一次 Ego Lite 运行内，跨 heredoc 轮次用 `task.id`（数字）复用同一空间：`useOrCreateTaskSpace(5)`。编号不跨重启，
停下等过用户回话之后先按下节核对。
`handOffTaskSpace` / `completeTaskSpace` 都要检查返回的 `done`——`{ done: false, skipped: ... }`
说明目标空间不是你的，此时报「已交出」是错的。

### 编号不跨重启：等过之后先按名称找当前编号（2026-10-30 实测）

2026-10-30 经作者同意升级 Ego Lite（0.6.1.13 → 0.6.2.5，日志「Update installed. Restarting ego lite to apply it.」）。
升级前 `listTaskSpaces()` 里是 `{ id: 5, name: "media publish bilibili", ownership: "user", … }`；重启后变成
`[{ id: 0, name: "", ownership: "user" }, { id: 1, name: "media publish bilibili", ownership: "user" }]`，同名空间从 5 变成了 1。
这次是升级带的重启，单纯重启会不会也重新编号没有分开试过，按会处理。重启后拿旧编号调 `useOrCreateTaskSpace(5)`、
`taskSpace(5)` 或 `claimTaskSpace(5)` 会报错、指到别的空间还是新建一个，也没有验证过；不要为了验证去跑会新建或接手空间的命令。

所以停下等过用户回话之后（等终稿确认、等用户归还控制权、按要求保留页面待 review 等），或者 Ego Lite 重启、升级过之后，
复用、`takeOverTaskSpace()` 或 claim 之前先核对编号：

1. 创建空间时把名称和编号一起记下来（任务启动那段已打印 `task.id`）；
2. `listTaskSpaces()` 按名称找空间，读它现在的 `id`；
3. 用 `recentTabTitles` 核对是不是原来那个页面；
4. 只有一个同名空间、编号与记下的一致、标签页标题对得上，才复用、takeOver 或 claim。编号对不上，或者有多个同名空间，
   停下问作者，不要自己挑一个。

## 控制权

交出控制权后不得自行收回。`handOffTaskSpace(task.id)` 之后，只能通过 `waitForAgentControl(task.id)` 等待用户主动归还；在用户仍持有控制权时调用 `takeOverTaskSpace()` 属于抢夺，即使看起来页面已经就绪、即使只是想读一次快照，也不允许。用户在对话里明确说「已登录」「好了」「继续」之后，才用 `takeOverTaskSpace(task.id)` 接手，接手前按上文「编号不跨重启」核对编号。

判断依据是控制权状态本身，不是页面长什么样。用户可能正在同一标签页里手工检查封面或核对文案，此时代理的任何点击都会落在用户的操作中途。

**代理侧的中断按同一规则处理**：任何命令报 `The user has taken control of this task space` 是硬停，
不重试、不 `takeOverTaskSpace()`。浏览器权限请求同理：2026-10-01 小红书提交视频后弹出定位
权限，ego-browser 报 `A browser permission prompt for location access has appeared. The user now
controls this task space` 并自动交出控制权。告诉用户按隐私优先处理（默认拒绝），等用户说继续再接手。

`waitForAgentControl(task.id)` 正常返回时值是 `undefined`（2026-10-02 观测）：没有 `{ done: true }`
之类的对象，不要因此判成失败、也不要再等一轮——resolve 就表示控制权已经回来，接着重新
`snapshotText()` 再继续。只有抛错才是没等到。

`waitForAgentControl(task.id)` 实测 600 秒超时会抛错退出，这不代表用户放弃，也不代表可以自己接手：
只看命令报错原因（不读页面、不截图、不 `takeOverTaskSpace()`），然后重新 `waitForAgentControl(task.id)`，
或等用户在对话里说「继续」。

按用户的常驻要求，交出控制权时同步做四件事：

1. 在对话中展示已冻结的视频/封面绝对路径，让用户可以直接点开或拖放；
2. 系统通知只写一个具体动作，不用「请处理一下」之类模糊说法；
3. `notify_user.py --tts-provider auto` 优先用火山 TTS 播报同一条指令，并说清是否可点发布；
4. 后台轮询等待归还，不停下要求用户回话。轮询只读控制权状态，不读页面、不点击。

## 等待终稿确认时任务空间被结束（2026-10-30 实测）

终稿确认要等用户真的回话，可能隔很久。其间任务空间可能被结束、归还给用户，要到用户回复后第一次动这个空间才暴露。
这和用户接管不是一回事：接管报 `The user has taken control of this task space`，任务还在，归还后 `takeOverTaskSpace()`
就能续上；任务结束后 `takeOverTaskSpace()` 接不回来，只能 `claimTaskSpace(id)`，而 ego-browser 使用指南（v2.1.0，升级后的 v2.2.0 未变）规定
user-owned 或 inactive 的空间只在用户明确要求时才能 claim。

观测（《易七猫对话手工川》B 站投稿）：10-30 04:50 前后填完表，停在「立即投稿」前等终稿确认（B 站 Profile 是 `auto`，
因标题、简介、标签改自用户写的视频号文本而退回确认）。约 16 小时后用户回「确认投稿」，接着那一轮 `useOrCreateTaskSpace(5)`
没报错，随后第一条读页的 `js()` 报：

```text
Error: listTabs: This task space is no longer assigned to the agent: its task has ended, either through task.finish() or by the user, so browser commands are paused.
This is a hard stop, not an obstacle to route around — do not retry and do not take ownership back on your own. takeOverTaskSpace() cannot resume an ended task.
Wait until the user explicitly asks you to continue in this space, then claim it and resume:
  const task = await claimTaskSpace(spaceId)

Offer the user choices like "Continue" or "Done" if your harness supports it; otherwise tell them: "This task has ended and the space is yours. Reply 'continue' if you want me to resume in it."
```

前缀 `listTabs:` 是出错的那个内部调用，换个命令会变，按 `no longer assigned to the agent` 认。代理上一轮没有调用
`finish` / `handOff`；空间是用户结束的、闲置被回收的还是 Ego Lite 重启所致，这次没有证据区分。原问句只问了
「按这张字段表投 B 站吗？」，用户答确认时不知道空间已经结束，所以又问了一轮，用户回「继续」才接手。接手后整表重读与
确认过的字段表一致，创作中心 `archives` 接口里也没有同标题稿件，只点了一次「立即投稿」；同样没弹「封面制作」确认框，
48 秒后开放浏览。

### 处理步骤

1. 硬停：不重试，不 `takeOverTaskSpace()`，不新建任务空间重传重填，也不换别的浏览器或工具去提交。
2. 只读确认归属：按上文「编号不跨重启」，`listTaskSpaces()` 按创建时的名称找原空间、读它现在的 `id`，记下 `ownership`、
   `recentTabTitles`。条目里只有最近标签页的标题，没有 URL；投稿页还在不在，接手后用 `task.tabs()` 才读得准。这次读到
   `"id": 5`、`"name": "media publish bilibili"`、`"ownership": "user"`，`recentTabTitles` 为
   `["创作中心 - 哔哩哔哩弹幕视频网 - ( ゜- ゜)つロ 乾杯~"]`。编号与记下的不一致，或者有多个同名空间：停下问作者。按名称找不到时
   表单可能已经没了：停下报告，重新上传要用户另行同意。
3. 终稿确认那一问已经写明接手、用户直接答了确认，且满足下节「确认那一问顺带授权接手」的全部条件：直接到第 5 步。
4. 否则只问一次，一问说全：任务空间（名称和现在的编号；编号变了写明从几变成几，同名有多个就列出各自的编号和
   `recentTabTitles` 请作者指认）已被结束、归还给用户（附报错关键句）；投稿页标签页看起来是否还在；接手后只做
   第 6 步那几件事；另一个选择是用户自己在浏览器里点、agent 之后只做回读。宿主支持按钮时给「继续」「我自己点」两个。
   照常跑 `notify_user.py` 发通知与播报，然后停下等答复。这一问只问接手，不重新征求终稿确认：终稿已经确认过，
   第 6 步的重读就是用来证明表单没变的。
5. 有了用户的明确同意（确认那一问的直接确认，或这一问回「继续」）才 `claimTaskSpace(id)`，`id` 用第 2 步核对过、作者认可的
   当前编号；这次接手后 `task.ownership` 读到 `agent`。
6. 接手后先只读，再决定提交：
   - `task.tabs()` 按 URL 找原投稿页。这次只有一个标签页，`label: null`、`openedBy: "unknown"`，`task.adopt(tab.page)` 后
     拿到 `p1` 才能操作。找不到或不止一个就停下；
   - 一次读完整个字段表，逐项对照用户确认过的那张，连同上传状态、可见校验错误和账号；
   - 查有没有同标题稿件：B 站用创作中心 `archives` 接口，写法见 [B 站投稿页结构](bilibili/page-anatomy.md)「审核期间的回读」；
     视频号、小红书在另开的标签页查内容列表，投稿页不要导航走（表单会丢），这两个平台还没遇到过这种情况；
   - 都一致且没有同标题稿件，才按平台规则点一次主提交，之后照常回读列表。有任何出入就不写字段、不提交，停下把差异报给
     用户；要用户在浏览器里处理时 `task.handOff()`，不要 `finish()`。
7. 接手之后的轮次照这次跑通的 Page API 写（见下文）：`taskSpace(id)` + `task.page('p1')`，收尾 `task.finish({ keep: [] })`，
   用户要求保留页面时改成 `keep: ['p1']`。旧写法（`useOrCreateTaskSpace(id)` + 全局 `js()`）在 claim 之后没有试过；
   升级到 0.6.2.5 后新旧 helper 都还在。接手的投稿页是 `openedBy: "unknown"`，指南 v2.2.0 写明 unknown-origin 标签页受保护、
   `keep: []` 关不掉整个空间：这次 finish 之后空间还在、归用户（重启后编号成了 1）。这是正常结果，`finish()` 只调一次，
   不要再 finish，也不要逐个关标签页。
8. 发布后的报告写明：等待期间空间被结束，凭哪句答复接手，接手后重读与查重的结果。

别的长时间等待之后（交接登录、按要求保留页面待 review 等）遇到同一报错，也按这几步处理，只是没有第 3 步的现成授权。

### 确认那一问顺带授权接手

可以，问法见 SKILL.md「提交前由用户确认终稿」。ego-browser 要的是用户明确要求才 claim，报错原文也是让 agent 等用户
明确让它在这个空间继续。问句里写明了「任务空间 N 若已被结束，确认也算让我接手它」，用户对这一问直接答确认，就是明确
要求接手，接手出自用户，不是 agent 自己收回；这次空间也正是在等确认期间结束的，用户的答复在那之后。2026-10-30 要再问
一轮，只是因为原问句里没有这一层。

下面四条都满足才算授权，缺一条就回到第 4 步只问一次：

- 触发：报的是 `no longer assigned to the agent`（不是用户接管），而且是用户回复后第一次动原空间就报。回复后已经有命令
  在这个空间里成功、后来才报这个错，说明空间是在 agent 干活时被结束的，当作用户叫停，单独问；
- 目标：问句里写了空间编号，名称也已记下；`listTaskSpaces()` 按名称只找到一个，编号与问句一致，`ownership` 是 `user`，
  `recentTabTitles` 对得上该平台的投稿页。等待期间 Ego Lite 升级或重启过、编号变了，就不算；
- 答复：用户对这一问直接答确认（点确认按钮，或回「确认」「确认投稿」这类只表示同意的话），没有附带改字段或别的条件；
- 范围：只做第 6 步的只读核对和一次提交，表单一个字不改；只管这一个平台的这一次提交，不写进 Profile，不延到队列里的
  下一个平台，换平台要在那个平台的确认问句里另写。

授权省掉的只是那一问，第 6 步的重读、查重、单次提交一样不少。

### Page API 写法（2026-10-30 跑通）

第 1 轮只读，还没接手：按名称找当前编号。

```bash
ego-browser nodejs <<'EOF'
const spaces = await listTaskSpaces()
const same = spaces.filter((s) => s.name === 'media publish bilibili')
console.log(JSON.stringify(same.map((s) => ({ id: s.id, ownership: s.ownership, recentTabTitles: s.recentTabTitles }))))
EOF
```

第 2 轮在用户明确同意之后：接手，认领原投稿页，只读核对并截图。下面的 5 是第 1 轮按名称查到、与记下的一致的编号。

```bash
ego-browser nodejs <<'EOF'
const task = await claimTaskSpace(5)
const tabs = await task.tabs()
const hits = tabs.filter((t) => t.url.startsWith('https://member.bilibili.com/platform/upload/video/frame'))
if (hits.length !== 1) throw new Error('原投稿页不在或不唯一，停下问用户: ' + JSON.stringify(tabs.map((t) => t.url)))
const page = hits[0].label ? task.page(hits[0].label) : await task.adopt(hits[0].page)
console.log({ ownership: task.ownership, page: page.label, openedBy: hits[0].openedBy })
// 回调在页面里运行，读不到外层变量；字段读法与终稿确认时那次整表读取相同，照 page-anatomy 写全
const form = await page.evaluate(() => ({
  title: document.querySelector('input[placeholder="请输入稿件标题"]')?.value ?? null,
  desc: document.querySelector('.ql-container')?.__quill?.getText() ?? null,
  submitted: document.body.innerText.includes('稿件投递成功'),
}))
const archives = await page.evaluate(async () => {
  const d = await fetch('https://member.bilibili.com/x/web/archives?status=is_pubing%2Cpubed%2Cnot_pubed&pn=1&ps=10&coop=1',
    { credentials: 'include' }).then((r) => r.json())
  return { code: d.code, titles: ((d.data && d.data.arc_audits) || []).map((a) => a.Archive.title) }
})
await page.screenshot({ path: '/absolute/path/pre-submit.png' })
console.log(JSON.stringify({ form, archives }))
EOF
```

之后的轮次不再 claim，按 id 和 label 续上。主提交按钮用 CDP 真鼠标点，坐标取本轮读到的 rect，先断言 `elementFromPoint`
命中（这次命中的是 `SPAN.submit-add`）；不在视口内就先按下文「视口外的按钮」滚进来，下一轮再读：

```bash
ego-browser nodejs <<'EOF'
const task = await taskSpace(5)
const page = task.page('p1')
const p = await page.evaluate((text) => {
  const el = [...document.querySelectorAll('span')]
    .find((e) => !e.children.length && e.offsetParent && e.textContent.trim() === text)
  if (!el) return { ok: false, reason: 'missing' }
  const r = el.getBoundingClientRect()
  if (r.top < 0 || r.bottom > innerHeight) return { ok: false, reason: 'outside viewport' }
  const x = Math.round(r.left + r.width / 2), y = Math.round(r.top + r.height / 2)
  const hit = document.elementFromPoint(x, y)
  return { ok: !!hit && (hit === el || el.contains(hit)), x, y }
}, '立即投稿')
if (!p.ok) throw new Error('不点: ' + JSON.stringify(p))
await page.cdp('Input.dispatchMouseEvent', { type: 'mousePressed', x: p.x, y: p.y, button: 'left', clickCount: 1 })
await page.cdp('Input.dispatchMouseEvent', { type: 'mouseReleased', x: p.x, y: p.y, button: 'left', clickCount: 1 })
EOF
```

列表回读完的最后一轮里收尾，`finish()` 之后不再操作任何 Page：

```js
await task.finish({ keep: [] })
```

## 任务启动

```bash
ego-browser nodejs <<'EOF'
const task = await useOrCreateTaskSpace('media publish')
await openOrReuseTab(ENTRY_URL, { wait: true })
await snapshotText()
cliLog(task.id)
EOF
```

`ENTRY_URL` 按平台取：

| 平台 | 入口 |
| --- | --- |
| 微信视频号 | `https://channels.weixin.qq.com/platform/post/create` |
| Bilibili | `https://member.bilibili.com/platform/upload/video/frame` |
| 小红书 | `https://creator.xiaohongshu.com/publish/publish?source=official` |

## 页面阶段

### 1. 登录与账号

- 读取快照后确认是否处于登录页（二维码、登录按钮、账号选择器）。
- 登录受阻时，不要改造登录流程，不要手工绕过验证。
- **视频号：本机微信已登录时优先点「快捷登录」再选账号，不要交接去扫二维码。** 二维码这条路
  多一次交接、还会遇到 `加载失败，点击重试`；快捷登录是同机免扫的。
- 视频号快捷登录点一次后要多等：2026-10-12 4 秒时还在登录页（登录框转圈），34 秒时已回到创建页。按约 2.5 秒
  间隔轮询 URL 约 40 秒再判断，等不到再交接，不要点第二次。
- 只有免扫路径也不可用时才 `handOffTaskSpace(task.id)` 交给用户，并等待用户完成后续。
- 回到代理可控后，重新 `snapshotText()`，读取导航区/账号展示文本并逐字核对。

### 2. 上传

- 从快照中定位「上传视频」「选择文件」「上传」语义控件，优先使用 `loc` 或 `@ref`。
- 文件提交优先使用 `uploadFile`，并使用绝对路径。
- 上传后读取进度文案与页面状态；仅 `progress=100` 不代表入库完成，需等待 `封面生成/解析中/转码中` 等消失。
- 上传观察和字段写入是两条独立通道：不要用一个阻塞的「等上传完」调用占住整个流程。
  若标题、描述、话题、合集、原创、标注等独立字段已经挂载并连续两次回读稳定，立即填写；
  只在字段操作的空档低频回读上传状态。素材解析结束后再全量回读一次。
- 封面编辑器若明确显示「上传中，等待完成后再编辑」，只把封面通道记为 blocked；
  不得因此暂停标题、描述、标签或合集。封面自动写入确定失败时，立即交付封面绝对路径和唯一需要点击的槽位。
- 封面、转码错误检查和最终提交仍等待素材解析完成。
- **同一页面上可能有多个 `accept` 相同的 file input**，必须锚定到主上传区再提交，
  不能取第一个（视频号按 shadow 穿透 + `accept` 区分，B 站按祖先链含 `upload-wrp` 区分）。
  不复用旧 `nodeId`/`backendNodeId`。

### 3. 发布信息与封面

- 按 [发布门禁清单](publish-gates.md) 逐项回读该平台字段表里的每一项。
- 写值方式**按平台走**，各平台完全不同：视频号的描述是 contenteditable、话题必须由平台按钮生成；
  B 站的输入框要用原生 setter，简介是 Quill；小红书正文是 tiptap，话题从 `#` 候选点选。照各自的 page-anatomy 写。
- 封面槽位数按页面实测，不写死；每个槽独立验安全区。B 站的 16:9 槽必须用公开接口的 `pic` 回读。
- 原创/声明类复选框要读真实 `checked` 属性，不能合并成一次点击假设。

### 4. 提交分支

- `draft`：定位「保存草稿」主语义动作，提交后进入草稿列表。小红书的「暂存离开」与「发布」同在封闭 shadow 宿主里，
  草稿流程未实测，先走终稿确认或交用户点。
- `schedule`：打开定时区，读取页面时区与时间控件；确认完整年月日时分后提交。
- `publish`：定位主提交动作（视频号「发表」/ B 站「立即投稿」/ 小红书「发布」，后者在封闭 shadow 的
  `XHS-PUBLISH-BTN` 里，只能按现拍截图坐标点，见小红书 page-anatomy），提交前输出完整字段表；全部必填项通过，且用户确认终稿（或该平台 Profile 为 `auto` 且没有触发退回条件，见 SKILL.md「按 Profile 偏好免终稿确认」）后仅提交一次。点击后按钮加载或页面跳转即记录为已尝试提交。
- `status`：跳过上传/编辑，仅进入内容列表用于回读并刷新验证。

### 5. 回读与防重

- 提交（或进入状态页）后必须重载到内容列表并完成一次全量快照读取。
- 匹配条目顺序优先（首次发布场景）：账号 → 视频文件名或页面标题 → 文案前缀 → 时间窗口 → 封面特征 → 条目链接/ID。
- 重发同一素材时上面的顺序会命中旧条目：文件名、时长、首帧在两次之间完全相同，不具区分度。改用提交时间、标题、话题组合或新封面，详见 [发布门禁清单](publish-gates.md) 的重发指纹表。
- 只允许唯一匹配作为 `draft_saved` / `scheduled` / `platform_pending` / `published` / `publish_failed` 的证据。
- 若出现多条候选、无匹配、或页面状态跳转失败，保留最后确认状态并报告候选，不重复点击提交。
- **管理页可能拒绝直链**：B 站 `upload-manager/all` 与 `/season` 会被重定向到首页，要从侧边栏点进去。

### 6. 错误与回退

- 若返回重复确认、网络抖动、页面卡住：优先回到列表重读，不重复发布动作。
- 每次错误记录必须包含：最后快照摘要、文件名、执行时间窗、账号信息、当前 URL、上传/解析阶段文本、列表回读结果。

## 两个通用的点击坑

### 视口外的按钮

主提交与弹窗确认键常落在视口外（视频号观测 y=726/视口高 727；B 站观测 y=813、1006、1380 而视口高 731）。
坐标点击会打在视口外，表现为「点了但没反应」，而且不报错。

不要重试坐标点击。先让元素滚进视口，**再按新 rect** 操作：

```js
el.scrollIntoView({ block: 'center' })
const r = el.getBoundingClientRect()
if (r.y < 0 || r.y + r.height > window.innerHeight) throw new Error('still clipped')
```

2026-10-06 修正：上面那段把滚动和读 rect 放在同一轮，视频号上读到的是**滚动中途**的 rect，「发表」
点空且没有任何提示。坐标点击一律改成：`scrollIntoView({ block: 'center', behavior: 'instant' })` →
等约 1 秒 → 下一轮 `js()` 重读 rect → 断言 `elementFromPoint(x, y)` 命中目标（shadow DOM 里用
`shadowRoot.elementFromPoint`）→ 只点一次。视口尺寸也会变：同一天视口约 900×765，比别处记录的
1496×731 窄，B 站左侧固定导航会盖住表单。每次现读 `innerWidth` / `innerHeight`，不照搬历史坐标。
平台写法见 [视频号创建页结构](wechat-channels/page-anatomy.md)「「发表」按钮」与
[B 站投稿页结构](bilibili/page-anatomy.md)「窄视口」。

拿到节点后让元素自己滚动并点击也可以（视频号那边这条路走通过）：

```js
await cdp('Runtime.callFunctionOn', {
  objectId,
  functionDeclaration: `function () { this.scrollIntoView({ block: 'center' }); this.click() }`,
})
```

点击后必须回读页面状态确认弹窗真的关闭、状态真的改变；按钮存在不等于点到了。

### 横向滚不过去的区域：只为截图临时放宽视口

要看的东西在视口外、而页面横向滚不过去（`document.documentElement.scrollWidth === innerWidth`）时，
`Page.captureScreenshot` 加 `captureBeyondViewport: true` 和区域 clip 可能只截出底色（2026-10-12 小红书封面预览）。
这时可以只为截图临时放宽视口：

1. 先记下 `innerWidth / innerHeight / devicePixelRatio`；
2. `Emulation.setDeviceMetricsOverride` 放宽到能装下目标的宽度，等约 1.5 秒后截图；
3. 截图放在 `try`、`Emulation.clearDeviceMetricsOverride` 放在 `finally`，截图失败也要恢复；
4. 恢复后重读视口，与第 1 步的值不一致就停下。

放宽期间只截图，不点击、不写字段；期间读到的坐标全部作废，之后要点的东西在恢复后重新截图、重读 rect。
页面本身比视口宽、能横向滚动时（B 站投稿页 2026-10-12 页面宽 1324、视口宽 900）不需要放宽，用 `scrollLeft` 或
`scrollIntoView({ inline: 'center' })` 把目标滚进来。写法见 [小红书发布页结构](xiaohongshu/page-anatomy.md)
「封面预览在视口外」。

### 有些控件只吃真鼠标

B 站的标签删除 `svg.close` 和推荐 chip `.hot-tag-item` 对 `.click()` 与
`dispatchEvent(new MouseEvent('click'))` 完全无反应，且不报错（观测：报告删了 12 个，一个没少）。
这时用 CDP 真鼠标：

```js
const r = el.getBoundingClientRect()
const x = r.x + r.width / 2, y = r.y + r.height / 2
await cdp('Input.dispatchMouseEvent', { type: 'mousePressed',  x, y, button: 'left', clickCount: 1 })
await cdp('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 })
```

判据是「点了没反应且没报错」，不是「按钮长得特殊」。

## 任务收尾

完成后如无明确保留需求，执行 `completeTaskSpace(task.id, { keep: false })` 关闭任务空间（**传 id，传对象会抛 `requires a task space name or id`**）。用户在任务任意阶段提出保留 review 页面时，该要求持续到明确撤销；清理无效 scratch tab 后，在独立最终命令中执行 `completeTaskSpace(task.id, { keep: true })`，并检查返回值 `done=true`。

## 视频号跨域 iframe 的快捷登录（2026-09-06 实测）

视频号登录组件位于 `open.weixin.qq.com` 的跨域 iframe。`snapshotText()` 可能读到账号名和
「微信快捷登录」文本，却没有可点击 ref；顶层 DOM / accessibility 查询失败或语义点击
报 `Element not found`，只能说明当前定位方式不适用，不能据此判定代理无法点击。

在代理仍持有任务空间控制权、本机微信已登录且目标账号明确时：

1. 用 `captureScreenshot(SCREENSHOT_PATH)` 保存当前浏览器页面截图，路径取本轮独立文件，
   确认账号与可见的快捷登录按钮。
2. 从这张最新截图确定按钮中心，以 `click([x, y])` 执行一次浏览器坐标点击；也可使用
   浏览器 CDP 的 `Input.dispatchMouseEvent`。不要照搬历史坐标，不调用系统级鼠标或切换前台应用。
3. 轮询页面 URL 约 40 秒（见上文「登录与账号」），确认进入创建页，并逐字核对已登录账号。2026-09-06 本轮按此
   流程一次点击后进入创建页，回读账号为「手工川」；这是本次证据，不是其他账号的默认值。
4. 只有当前截图无法确认控件、一次点击后确认仍失败，或页面要求额外用户授权时，才按控制权
   规则 `handOffTaskSpace(task.id)`，说明唯一待完成动作并等待归还；不连续盲点，也不绕过验证。

以上操作全部发生在浏览器任务空间内；用户已接管时仍须停止读页与点击，等待控制权归还。
