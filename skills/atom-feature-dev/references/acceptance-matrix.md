# Acceptance Matrix

## Required evidence

每个适用 surface 至少记录：入口命令或 URL、实际输入、观察输出、退出状态或 HTTP 状态、
副作用回读、测试时间和制品版本。截图可辅助 UI 验收，但不能替代结构化结果或持久化回读。

## Cross-surface vector

至少一个测试向量必须从两个 surface 进入同一 Core SDK。比较前先规范化：移除 request ID、
时间戳、显示文案和传输包装，仅比较业务输出、错误类别与副作用。允许差异必须在 contract 中
显式声明。

## Minimum matrix

| Case | SDK | CLI | API | UI | Agent | Profile |
| --- | --- | --- | --- | --- | --- | --- |
| Golden path | required | if applicable | if applicable | if applicable | if applicable | active preset |
| Parameter boundary | required | one adapter | one adapter | validation | schema validation | invalid value |
| Expected failure | required | exit code | HTTP error | recovery copy | tool error | fallback |
| Side effect | readback | readback | readback | refreshed state | tool result | persisted scope |

## Dashboard gate

Dashboard 必须从 manifest、测试报告或运行 API 读取状态。以下均为失败：用组件常量写死绿色状态；
把 build 通过显示成 released；只显示最后一次成功而隐藏当前失败；修改参数后不标记旧证据失效。

Workbench 的 Run 只能执行 manifest 明确声明的 argv `command`，默认关闭且需要启动参数显式授权。
Profile 写入同样默认关闭。每次运行保留 surface、resolved input、退出码、耗时与脱敏后的输出，
便于 Compare 和 Review 回读。

## Operations applicability

Docs 与测试默认适用。SEO/GEO 只适用于可公开发现的页面或文档；Auth 只适用于需要身份、权限或
跨设备数据；支付只适用于真实售卖或计量；分析只收集完成用户任务所需的最小事件。`not-applicable`
必须记录理由，并在需求变化时复评。
