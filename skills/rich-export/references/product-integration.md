# 产品集成

## 推荐服务边界

将导出做成异步 Job，而不是在前端点击后直接把大文件塞进浏览器内存。

```text
产品内容模型 → Export manifest → 导出 Worker
                                  ├─ HTML single / directory
                                  ├─ DOCX
                                  ├─ PDF
                                  └─ ZIP + manifest
                                      ↓
                              对象存储 / 下载中心
```

最小 API：

```text
POST /exports              # body: manifest + formats
GET  /exports/{id}         # queued | rendering | complete | failed
GET  /exports/{id}/files   # 仅 complete 时返回带过期时间的下载项
```

## Worker 约束

1. 每个任务使用独立临时目录；完成后只上传成品和 manifest。
2. 给 Pandoc、浏览器打印和 ZIP 分别设置超时与结构化日志。
3. 只允许读取任务目录和经过允许列表校验的远端媒体；拒绝绝对路径、`..` 穿越、内网 URL 和未声明的 iframe。
4. 把输入 hash、渲染器版本、字体版本和失败日志摘要写入导出 manifest，便于重跑和排障。
5. 给 HTML 加 CSP；PDF/DOCX 渲染前将所有视频、音频、iframe 变成静态投影。

## 前端产品体验

- 首先选择格式，再选择“单文件 / 文件夹 ZIP”包装；不要把包装方式和格式混成一个难懂的下拉框。
- 提前显示格式能力：HTML 标记“保留交互”，DOCX 标记“可编辑”，PDF 标记“适合打印”。
- 对媒体很大的单文件 HTML 显示体积预估与 ZIP 建议，不默默生成难以发送的文件。
- 完成态展示每个文件、大小、生成时间和一次“全部下载”；失败态呈现具体格式与可重试按钮，不用一条笼统错误覆盖全部结果。
