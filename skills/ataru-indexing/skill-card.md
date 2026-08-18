# Skill Card — lov-ataru-indexing

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note.

## Description

在无界面环境下把本机 Ataru 会话记忆索引带到可检索状态：解析并版本门控本地 Ataru
可执行文件，读取索引状态，只在需要时发起增量构建，等待其他进程正在进行的构建，
最后交回一份带 actions 与规模数据的 JSON 报告。

## Owner

Lovstudio（手工川工作室），https://lovstudio.ai

## License / Terms

MIT。自由使用、修改与再分发，保留版权与许可声明。本许可不覆盖 Ataru 本体。

## Use Case

面向在本机运行、需要检索历史 AI 会话的 Agent 与脚本。输入是用户机器上已存在的
会话历史目录与一个 Ataru 0.41.3+ 可执行文件；任务是在任何检索发生之前确认索引
可用，并在必要时把它构建出来。

## Deployment Geography

全球，纯本机执行。适用于已安装 Ataru 的 macOS 机器，或同一仓库内的本地 dev build。

## Requirements / Dependencies

无凭据。需要 Python 3.8+（仅标准库）、Ataru 0.41.3 或更新版本，以及索引目录的
本机读写权限。

## Known Risks and Mitigations

| 风险 | 缓解 |
| --- | --- |
| 旧版 Ataru 把 index 子命令当成桌面启动参数，打开窗口抢走前台且永不返回 | 每个候选先跑 `--version`，低于 0.41.3 直接拒绝并列出被拒候选与版本 |
| 构建锁只在进程内生效，可能与桌面端并发构建 | 构建前读状态，`building` 时轮询等待；底层写临时目录再原子替换 |
| `--force` 丢弃现有索引重扫全部会话，分钟级开销 | 仅在用户明确要求时使用，默认增量，report 区分 full-rebuild 与 catch-up-build |
| 子命令挂住会阻塞调用方 | 所有调用带超时，超时返回 `ATARU_CLI_TIMEOUT` 与完整命令行 |

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Skill group composition](references/skill-composition.md)

## Skill Output

stdout 上的单个 UTF-8 JSON 对象，含 `state`、`searchAvailable`、`needsBuild`、
`isBuilding`、`progressPercent`、规模统计，以及本次执行的 `actions`。索引不可用时
退出码 1，无可用二进制退出码 3，超时退出码 4。

## Skill Version

0.1.0

## Ethical Considerations

索引内容是用户本机的完整 AI 会话历史，属于高敏感数据。全程本地执行，不上传任何
消息内容；报告只含统计量与状态，错误信息只出现可执行文件路径与版本。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)：在 2704 会话、847072 消息的真实本机语料
上完成状态确认与幂等 ensure，并拒绝了一个会打开窗口的旧版二进制。

### Dimension Map

机器可读卡记录了 correctness、safety、idempotence、efficiency 四个维度及其证据。

### Pricing Basis

见 [`pricing-card.yaml`](pricing-card.yaml)。作为 Ataru 本体的附属工具免费分发。

### Distribution

免费渠道：github、lovstudio。无付费渠道。
