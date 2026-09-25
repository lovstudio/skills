# 资源回收设计 · Resource Reclamation · Skill Card

## Description

把具体客户端 App 的 listener、任务、worker、缓存、native handle 与外部资源治理成服从宿主生命周期、fail-closed、可恢复并能阻止 ABA 的所有权协议。重点不是“删得更多”，而是只在 scope、owner、activity、lease、identity 和恢复路径全部可证明时行动。

## Owner

维护方：LovStudio / 手工川工作室。联系入口随源码分发渠道提供。

## License

[MIT License](../../LICENSE)。允许使用、修改和再分发；终止、驱逐或删除动作仍需目标 App 所有者的明确授权。

## Use Case

面向负责 desktop、mobile、hybrid 或 Web/PWA 客户端生命周期与资源所有权的工程师。覆盖 App/window/scene/page、route/view、worker/service、native handle、WebView/isolate、cache/socket，以及按需加载的 PTY/tmux/worktree 等 external adapter。

按 `scope_release → hibernate → cache_evict → external_reclaim` 的风险顺序治理；`persistent_delete` 默认交给产品专用流程。

## Deployment Geography

全球；在具体 Electron、Tauri、native desktop、iOS、Android、React Native、Flutter 或 Web/PWA 项目的受控开发与测试环境运行。

## Requirements

- `invocation: kit_only`；通过 `$KIT_DIR` 加载共享 evidence、policy、playbook 与 helper。
- 具体 App/build、host、runtime/framework 和生命周期事件。
- durable owner、registration、authoritative activity、lease、identity 与 recovery state。
- 项目原生 lifecycle adapters、teardown APIs 和测试框架。
- 远端或生产动作需要最小权限与精确目标授权；设计和 dry-run 默认不需要。

## Known Risks

- host suspension、timeout 或空产物可能被误判为 idle。缓解：按 adapter 解释生命周期，unsupported/unknown 一律不进入高风险动作。
- 同名资源可能在检查间重建。缓解：两次 inventory 加最终 O(1) fingerprint 条件检查。
- filesystem 或 persistent data 清理可能丢失用户内容。缓解：dirty、unknown、in-use、unregistered 保持 protect；persistent delete 独立授权。
- sweep 可能触发立即 hydration/restart。缓解：先修复 creation seam，再验证 background、resume 与 process-death。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Conservative reclamation policy](../../references/reclamation-policy.md)
- [App runtime evidence contract](../../references/evidence-contract.md)
- [Platform adapter matrix](../../references/platform-adapters.md)
- [Yoda reclamation case](cases/cases.json)
- [Yoda implementation commit](https://github.com/lovstudio/yoda/commit/290fbc48c713163f20bd6f956e80e15d00dfa357)

## Skill Output

输出 App lifecycle specification、protect/candidate 决策矩阵、dry-run inventory，以及用户要求实现时的项目原生源码与测试。检查 host lifecycle、universal blockers、changed fingerprint、single-flight、持久数据保护与真实 resume；helper 不执行 destructive action。

## Skill Version

0.2.0

## Ethical Considerations

优先保护用户工作与可恢复身份。未经精确授权不终止、不驱逐持久状态、不删除数据；不从名称猜所有权；一次性授权不得写入 Profile 或跨会话复用。

## User Cases

[Yoda 案例](cases/cases.json)是首案校准：`platform_family: desktop`、`runtime: electron`。commit `290fbc48…` 包含 fail-closed、ABA、single-flight、dirty/unregistered/live-cwd worktree 保护及相关测试。案例没有执行生产盲删，也没有完成 live teardown 后的 on-demand resume，因此保持 `implemented_not_runtime_verified`。

## Dimension Map

| 维度 | Evidence | Score status |
| --- | --- | --- |
| 宿主生命周期安全 | 0.2.0 要求 host/runtime adapter，unsupported 不当作 idle | design_backed |
| Fail-closed 覆盖 | Yoda owner/provider revalidation 实现及失败测试 | implementation_and_test_backed |
| ABA 安全 | 同名 replacement fingerprint 与 concurrent cleanup 测试 | test_backed |
| 持久数据保护 | dirty/unregistered/live-cwd/changed-branch worktree 实现与测试 | implementation_and_test_backed |
| 可恢复性 | teardown 顺序与可重试失败已实现；live resume 仍缺 | implementation_backed_live_gap |

分数保持 `null`；这些状态区分设计、实现、测试与真实运行验收，Yoda 证据不外推为其他平台 benchmark。

## Pricing Basis

[Pricing card](pricing-card.yaml)定义当前 SKU 为免费、价格 0。包含 kit-only 方法、共享 helper 使用方式和 Yoda 实现证据；不存在付费 SKU 或渠道产物，也不包含生产执行、托管清理或数据恢复保证。

## Distribution

| Channel | Channel class | Current offer | State |
| --- | --- | --- | --- |
| workbuddy | paid-capable marketplace | no paid SKU/artifact | not_prepared |
| skillpay | paid-capable marketplace | no paid SKU/artifact | not_prepared |
| github | free source channel | free source | source_ready_not_published |
| lovstudio | local source channel | free source | local_ready |

渠道类别与当前定价分开表达；没有渠道被描述为 live 或已有付费商品。
