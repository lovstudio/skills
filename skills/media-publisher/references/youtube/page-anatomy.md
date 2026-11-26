# YouTube Studio 上传页结构（2026-11-26 实测，9 条切片批量上传）

入口 `https://studio.youtube.com`，右上「创建 → 上传视频」。页面是 Polymer / Web Components，普通 DOM 可查。

## 坑

- **上传只在 Studio 标签页处于前台时推进**：切到别的标签页或导航走，进度会停住；批量上传时一个标签页传完一条再开下一条，
  其间不要在同一标签页里跳到内容列表。
- **旧的上传弹窗不会从 DOM 移除**：每条上传都会新增一个 `ytcp-uploads-dialog`，`document.querySelector('ytcp-uploads-dialog …')`
  会命中隐藏的旧弹窗，标签、标题读回来是上一条的值。所有选择器都要先过滤可见（`getBoundingClientRect().width > 0`）再取。
- **点「发布」后先等 `Saving...` 消失**：按钮点下去后弹窗显示 `Saving...`，平台接受前关窗或导航会丢；等文案消失、出现「视频已发布」再关。
- **状态以内容列表 + oEmbed 回读为准**：内容列表的「公开范围」列读 `Public`，再请求
  `https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=<id>&format=json`，返回 200 才算公开可读。
