# Changelog

## 0.1.1

- 增加宿主无关的只读读取脚本 `scripts/read_codex_session.py`：Claude Code 等没有 Codex 线程工具的宿主可以直接解析本地 rollout，输出状态、最近回合、工具活动与待处理调用。
- SKILL.md 明确“宿主线程工具优先、本地脚本兜底”的工作流，并把兼容性改为宿主无关表述。
- 增加 `scripts/test_read_codex_session.py` 回归测试。

## 0.1.0

- Initial local Skill source.
