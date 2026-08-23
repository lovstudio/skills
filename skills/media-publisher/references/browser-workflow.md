# 浏览器工作流（ego-browser，跨平台）

本文只写**两个平台都成立**的部分：helper 签名、控制权规则、任务空间生命周期、
以及发布流程的六个阶段骨架。平台各自的 DOM 结构与写值方式在
[视频号创建页结构](wechat-channels/page-anatomy.md) 和
[B 站投稿页结构](bilibili/page-anatomy.md) 里，不要互相套用。

## 操作原则

- 使用 `ego-browser` 的 task space 执行：`const task = await useOrCreateTaskSpace('media publish')`，同一任务持续复用同一空间，避免反复切换上下文。
- 所有关键动作前后先 `await snapshotText()`，以稳定文本 ref/loc 重定向控件；每次重渲染后必须重新读取快照。
- 使用语义交互为主：`openOrReuseTab` / `snapshotText` / `click` / `fillInput` / `uploadFile`；仅在必要时使用 `js` 读取 DOM 或 `pageInfo` 辅助。
- 语义 ref 只对最近一次快照有效。元素不在视口时先 `DOM.scrollIntoViewIfNeeded` 或滚动后重新截图；不要用页面坐标点击视口外元素。
- 仅在有明确用户确认时操作 `pressKey('Enter')`；遇到文本输入时默认 `click -> typeText/fillInput` + 失焦回读。
- 避免复用旧句柄、旧 ref、旧 CSS 选择器和旧坐标，页面变化后全部重新识别。

## helper 签名：传 id，不传 task 对象

2026-08-17 / 08-18 实测，下面这些调用会直接抛错，各费一轮往返。它们都属于「看起来对但签名不同」，
所以照表写，不要凭直觉：

| 写法 | 结果 |
| --- | --- |
| `handOffTaskSpace(task)` | 抛 `task space not found: [object Object]` |
| `handOffTaskSpace(task.id)` | 正常，返回 `{ done: true }` |
| `waitForAgentControl()` | 抛 `requires a task space name or id` |
| `waitForAgentControl(task.id)` | 正常阻塞等待 |
| `captureScreenshot({ path: '/tmp/a.png' })` | 抛 `ERR_INVALID_ARG_TYPE`，它把对象当路径 |
| `captureScreenshot('/tmp/a.png')` | 正常，返回路径字符串 |
| `screenshot(...)` | `ReferenceError`，helper 名是 `captureScreenshot` |
| `mouseClick(x, y)` | `ReferenceError`，**没有按坐标点击的 helper**。要按坐标点用 `cdp('Input.dispatchMouseEvent', { type: 'mousePressed'/'mouseReleased', x, y, button: 'left', clickCount: 1 })` |
| `completeTaskSpace(task, opts)` | 抛 `requires a task space name or id`，和 `handOffTaskSpace` 同坑。写 `completeTaskSpace(task.id, { keep: true })` |

heredoc 按 **ES module** 解析：`require` 报 "Cannot determine intended module format"，
要读本地文件用 `const { readFileSync } = await import('node:fs')`。

跨 heredoc 轮次统一用 `task.id`（数字）复用同一空间：`useOrCreateTaskSpace(5)`。
`handOffTaskSpace` / `completeTaskSpace` 都要检查返回的 `done`——`{ done: false, skipped: ... }`
说明目标空间不是你的，此时报「已交出」是错的。

## 控制权

交出控制权后不得自行收回。`handOffTaskSpace(task.id)` 之后，只能通过 `waitForAgentControl(task.id)` 等待用户主动归还；在用户仍持有控制权时调用 `takeOverTaskSpace()` 属于抢夺，即使看起来页面已经就绪、即使只是想读一次快照，也不允许。用户在对话里明确说「已登录」「好了」「继续」之后，才用 `takeOverTaskSpace(task.id)` 接手。

判断依据是控制权状态本身，不是页面长什么样。用户可能正在同一标签页里手工检查封面或核对文案，此时代理的任何点击都会落在用户的操作中途。

**代理侧的中断按同一规则处理**：任何命令报 `The user has taken control of this task space` 是硬停，
不重试、不 `takeOverTaskSpace()`。

按用户的常驻要求，交出控制权时同步做三件事：发系统通知、语音播报、然后在后台轮询等待归还，不要停下来要求用户回话。轮询只读控制权状态，不读页面、不点击。

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

## 页面阶段

### 1. 登录与账号

- 读取快照后确认是否处于登录页（二维码、登录按钮、账号选择器）。
- 登录受阻时，不要改造登录流程，不要手工绕过验证。
- **视频号：本机微信已登录时优先点「快捷登录」再选账号，不要交接去扫二维码。** 二维码这条路
  多一次交接、还会遇到 `加载失败，点击重试`；快捷登录是同机免扫的。
- 只有免扫路径也不可用时才 `handOffTaskSpace(task.id)` 交给用户，并等待用户完成后续。
- 回到代理可控后，重新 `snapshotText()`，读取导航区/账号展示文本并逐字核对。

### 2. 上传

- 从快照中定位「上传视频」「选择文件」「上传」语义控件，优先使用 `loc` 或 `@ref`。
- 文件提交优先使用 `uploadFile`，并使用绝对路径。
- 上传后读取进度文案与页面状态；仅 `progress=100` 不代表入库完成，需等待 `封面生成/解析中/转码中` 等消失。
- **同一页面上可能有多个 `accept` 相同的 file input**，必须锚定到主上传区再提交，
  不能取第一个（视频号按 shadow 穿透 + `accept` 区分，B 站按祖先链含 `upload-wrp` 区分）。
  不复用旧 `nodeId`/`backendNodeId`。

### 3. 发布信息与封面

- 按 [发布门禁清单](publish-gates.md) 逐项回读该平台字段表里的每一项。
- 写值方式**按平台走**，两边完全不同：视频号的描述是 contenteditable、话题必须由平台按钮生成；
  B 站的输入框要用原生 setter，简介是 Quill。照各自的 page-anatomy 写。
- 封面槽位数按页面实测，不写死；每个槽独立验安全区。B 站的 16:9 槽必须用公开接口的 `pic` 回读。
- 原创/声明类复选框要读真实 `checked` 属性，不能合并成一次点击假设。

### 4. 提交分支

- `draft`：定位「保存草稿」主语义动作，提交后进入草稿列表。
- `schedule`：打开定时区，读取页面时区与时间控件；确认完整年月日时分后提交。
- `publish`：定位主提交动作（视频号「发表」/ B 站「立即投稿」），提交前输出完整字段表；全部必填项通过且用户确认终稿后仅提交一次。点击后按钮加载或页面跳转即记录为已尝试提交。
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

拿到节点后让元素自己滚动并点击也可以（视频号那边这条路走通过）：

```js
await cdp('Runtime.callFunctionOn', {
  objectId,
  functionDeclaration: `function () { this.scrollIntoView({ block: 'center' }); this.click() }`,
})
```

点击后必须回读页面状态确认弹窗真的关闭、状态真的改变；按钮存在不等于点到了。

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

## 视频号登录 iframe 是跨域的，快捷登录点不到（2026-08-21 EP.02）

视频号创建页的登录组件在 `open.weixin.qq.com` 的**跨域 iframe** 里（`snapshotText` 能显示
「微信快捷登录」按钮文本，但 DOM / accessibility 都读不到，`elementFromPoint` 也命中不了）。
agent 无法自动点「微信快捷登录」：

- `DOM.getDocument({pierce:true})` 不穿透跨域 iframe；`Accessibility.getFullAXTree` 也不含它。
- 语义 `click('微信快捷登录')` 报 `Element not found`。
- 只有 `snapshotText` 能显示 iframe 内文本（ego-browser 的 CDP 穿透），但无法定位点击。

**结论**：本机微信已登录时若快捷登录按钮在跨域 iframe 里点不到，不要反复试——直接
`handOffTaskSpace(task.id)` 交给用户，让用户点「微信快捷登录」完成授权，再用
`waitForAgentControl(task.id)` 等归还。这比「先试自动点再交接」省一轮。
