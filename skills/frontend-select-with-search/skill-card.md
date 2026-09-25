# 搜索下拉框 · Searchable Select · Skill Card

## Description

将超过阈值的前端 Select 升级为可搜索、可滚动且键盘可访问的兼容组件，并用真实滚轮事件验证 Dialog 与 Portal 场景。

## Owner

LovStudio contributors；由源仓库维护者负责版本与案例证据。

## License / Terms

MIT。允许使用、复制、修改和分发；须保留版权与许可声明，软件按现状提供。

## Use Case

面向维护 HTML、React、Vue、Svelte 或既有组件系统的工程师和代码 Agent。输入是前端仓库、Select 搜索或滚动需求和可复现界面；输出是共享组件修复、调用面清单和真实交互证据。

## Deployment Geography

全球可用，预期在用户本地 Agent 运行时和其授权的项目工作区内执行。

## Requirements / Dependencies

无需凭据。使用目标项目现有前端工具链和浏览器交互工具；Profile 与本地 Skill 校验需要 Python 3.8+ 和 PyYAML。

## Known Risks and Mitigations

- 自定义组合框可能破坏原生 Select 的表单或受控值语义：先声明兼容契约，并覆盖受控、非受控、required、name、reset 和动态选项。
- Dialog 可能拦截 Portal 内的滚轮：修复允许滚动的弹层归属，并用真实滚轮测量 `scrollTop` 后再验收。
- 搜索可用但键盘或辅助技术关系不完整：采用一致的 Combobox/Listbox 模式，验证方向键、Enter、Escape、焦点恢复和禁用项。
- 超大远程数据集不适合本地全量过滤：将检索、取消和错误状态交给项目数据层，不默认上传候选标签。

## References

- [Primary Skill instructions](SKILL.md)
- [Searchable Select playbook](references/select-search-playbook.md)
- [Real user case](cases/cases.json)

## Skill Output

输出项目原生 HTML、JavaScript、TypeScript 或组件文件补丁，以及 Markdown 格式的 Select 清单和验证报告。验收覆盖 5/6 项边界、真实滚轮后的 `scrollTop` 变化、滚动后选择、键盘行为和项目质量门。

## Skill Version

0.1.0

## Ethical Considerations

默认在本地处理候选标签，不向远程服务发送项目数据。保留现有许可与归属，不把未执行的浏览器、触控、辅助技术或构建检查写成已验证。

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) 记录了 GTDV 创建弹窗中从“超过 5 项支持搜索”到修复 Dialog/Portal 滚动锁的真实案例。

### Dimension Map

- 阈值覆盖：真实验证 5 项原生以及 6、16、17 项可搜索。
- 滚动正确性：真实滚轮使 240px 可视区、588px 内容的列表 `scrollTop` 从 0 变为 348，随后选中成功。
- 交互兼容性：中文过滤、Enter 选择、父弹窗恢复和生产构建通过。
- 可移植性：不绑定专有路径或单一框架，按组件契约和弹层所有权处理差异。

### Pricing Basis

本地使用免费，因为当前交付是可移植指令和验收方法，没有托管或专有服务成本。范围包含 Select 搜索、滚动、兼容性和验证；若未来加入自动迁移器、持续适配服务或托管检索则复评。

### Distribution

- Local：已安装。
- GitHub：未发布。
- LovStudio：未发布。
- WorkBuddy：无付费发布计划。
- SkillPay：无付费发布计划。
