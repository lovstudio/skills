# Atom Feature Contract

`.atom-feature/manifest.json` 是每个原子功能的控制面，不是业务数据库。它记录有哪些形态、
制品在哪里、验证到哪一层，业务规则仍由 Core SDK 拥有。

## Atomic boundary

一个 atom 必须能写成：给定规范化输入，经过一组明确副作用，得到规范化输出或可枚举错误。
如果输入、权限、生命周期或验收结果彼此独立，应拆成多个 atom。页面、接口和命令不是 atom；
它们是同一个 atom 的 surfaces。

## Canonical artifacts

- `manifest.json`：Feature 身份、状态、surface、operations 与证据索引；
- `contract.schema.json`：规范化输入、输出、错误与版本；
- `profiles.schema.json`：可持久化 Preset 字段、默认值、作用域和迁移版本；
- `presets.json`：用户创建的 Preset 与当前选择；只保存非秘密参数；
- `acceptance.json`：真实测试向量、预期规范化结果、副作用和允许差异；
- `status.json`：工具写入的观察状态，可由 Dashboard 读取；不能代替 manifest 的设计事实。

## Surface invariant

SDK 是业务真源。CLI、API、UI 与 Agent Skill 只能做四类工作：输入收集与校验、权限与传输、
调用 SDK、呈现结果。不得在 adapter 中复制计价、过滤、排序、状态迁移或错误映射规则。

每个 surface 记录 `status`、`artifact`、`contract`、`verification`；需要从 Workbench 执行的
surface 额外声明 argv 形式的 `command`，不得使用 shell 字符串。状态含义：

- `planned`：已确定适用但尚无可执行制品；
- `implemented`：制品存在并通过静态或局部测试；
- `verified`：真实入口运行且证据可回读；
- `released`：目标渠道可访问并已完成渠道回读；
- `not-applicable`：有明确理由，不是遗漏。

## Profile and Preset

Preset 的 key 必须来自 `contract.schema.json`，值必须通过同一校验器。解析顺序：当前调用显式
参数、当前项目上下文、选择的 Profile Preset、共享用户默认值、安全推断默认值，最后才询问。
秘密只记录 locator 或环境变量名，不进入 Profile、manifest、日志或 Dashboard。

## Compatibility

Manifest helper 只保证控制面 schema；目标实现语言和框架由项目决定。已有项目应增量接入，
新项目选择满足当前 atom 的最小技术栈，不为所有可能 surface 预建空目录。
