# 应用性能医生 · App Performance Doctor · Skill Card

## Description

把交互式应用的卡顿、掉帧、耗电、内存增长和后台泄漏拆成可测量的运行时问题。核心方法覆盖 Electron、Tauri、原生桌面、iOS、Android、React Native、Flutter 与 Web/PWA；Electron/Yoda 是首个完整案例，不是能力边界。

## Owner

LovStudio / 手工川工作室；由本地 Skill 维护者维护。

## License

MIT。Skill 可在保留许可与版权声明的前提下使用、修改和分发；目标项目的源码、日志、trace 和用户数据仍遵循其原有条款。

## Use Case

适合有具体应用、可重放症状和真实运行环境的客户端团队。Kit 先冻结设备/浏览器、构建、数据、网络、缓存、操作脚本与采样器，再从用户体验、运行时资源、内部工作量和规模四个轴建立证据，按“停止、批量、限界、生命周期、回收”顺序实施优化。

三个嵌入模块是 `runtime-audit`、`reclamation-engineering` 和 `runtime-verification`；它们通过 controller pipeline 协作，不作为独立安装商品。

## Deployment Geography

全球可用。需要 Python 3.9+ 和目标源码/运行时。最终移动端结论使用真实设备 release/profile build；Web/PWA 分开报告 lab 与 field/RUM；桌面使用实际 release/package。平台 profiler、Git、tmux、SSH 和数据库均为可选 adapter。

## Requirements

- 可确认目标 build/commit、运行边界和数据规模。
- 至少一个可重放工作负载及预先声明的指标/安全不变量。
- 修改代码需要实现授权；外部终止与持久删除需要更精确的目标授权。
- 没有对应平台 adapter 或真实运行证据时，必须降低 verdict。

## Known Risks

- 不同构建、设备、网络或采样器伪装成严格 A/B：前测冻结 comparison contract，不匹配就禁用精确百分比。
- 错套生命周期：移动 suspend/process death、Web BFCache/SW termination 与桌面 kill 分开建模。
- 旧快照误杀同名重建资源：动作前重读 live lease，并用实例 fingerprint 或原子条件操作阻止 ABA。
- 未知/dirty 数据被当缓存：未知只盘点，persistent delete 永不作为自动优化。
- profiler 自身制造负载：测量采样开销，限制频率、字节、并发和可见性。

## References

- [Primary workflow](SKILL.md)
- [Evidence contract](references/evidence-contract.md)
- [Runtime playbook](references/runtime-playbook.md)
- [Platform adapters](references/platform-adapters.md)
- [Reclamation policy](references/reclamation-policy.md)
- [Yoda Electron case](cases/cases.json)
- [Yoda generated report](cases/evidence/yoda-runtime-report.md)

## Skill Output

输出包括 Markdown 结论、`app-runtime-report/v1` JSON、冻结 comparison contract、所有权/工作量图、资源保护矩阵、正确性门和 evidence gaps。只有同负载真实运行证据达到预先声明阈值时才写 `verified`。

## Skill Version

0.2.0

## Ethical Considerations

只收集定位性能所需的最少信息，不复制凭据、私人内容或设备标识。未知状态解释为保护；外部终止、缓存清理和持久删除不得超出授权或平台政策。

## User Cases

案例 1 是 Yoda/Electron 长时运行治理：916 task 的规模扇出、61 个应用自有 tmux session、Agent 历史会话复活和混合 worktree inventory。案例明确区分约 916/1,832 的源码推导、15 个 Git 子进程的现场测量、3,115 项测试的正确性门，以及尚未完成的 input-latency/RSS 配对 A/B。

其他平台当前只有 adapter 设计与触发测试，不冒充真实案例。

## Dimension Map

- **诊断证据完整度（5，case-backed）**：推导、实测、源码事实和 acceptance 分开，并给 P0 假设 falsifier。
- **运行时降载能力（4，case-backed with runtime gap）**：Yoda 的批量、懒加载、轻量轮询已经落地，完整 UX/RSS A/B 尚缺。
- **生命周期安全性（4，implemented not runtime verified）**：竞态 guard 已实现并测试，未执行生产批量 cleanup/resume trial。
- **验收深度（4，partially verified）**：真实周期复测和完整正确性门存在，但并非所有性能阈值都有配对数据。
- **跨平台可迁移性（3，design-backed single-platform case）**：八类平台 adapter 已定义，完整实证仍只有 Electron。

## Pricing Basis

当前为免费 Kit。源码、方法、报告器、平台矩阵和 Yoda 案例可本地使用；托管 telemetry、商业实施、远程运维、生产数据保管和 SLA 不包含在免费边界内。

## Distribution

| Channel class | Current offer | Publication state |
| --- | --- | --- |
| Free · LovStudio | local source + Kit | `local_ready`，未对外发布 |
| Free · GitHub | source-ready repository content | `source_ready_not_published` |
| Paid · WorkBuddy | none | `not_prepared`；无 SKU/商品/产物 |
| Paid · SkillPay | none | `not_prepared`；无 SKU/商品/产物 |
