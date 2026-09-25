# 微信体验校准 · WeChat Experience Alignment

![Version](https://img.shields.io/badge/version-0.2.1-CC785C)

从官方证据和原始微信数据出发，系统修复消息语义、组件选择、交互语法与视觉表现的偏差，而不是只做表层样式模仿。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILL_SKILLS_INSTALL_DIR/lov-align-wechat-uiux"
```

## 使用

典型触发方式：

- “这个拍一拍被显示成应用卡片了，对齐微信官方并修好。”
- “系统检查聊天页里还有哪些 UIUX 和微信官方不一致。”
- “This message renderer does not match official WeChat behavior; fix the parity issue.”

输入可以是截图、XML/JSON、数据库记录、消息类型、页面入口、错误日志或代码位置。输出包括根因、规范化语义、实现改动、回归证据和真实运行时缺口。

Skill Kit 提供四个模块：

- `wechat-evidence`：官方、产品、原始数据与代码证据；
- `wechat-semantics`：规范化消息和状态模型；
- `wechat-ui-parity`：官方交互语法与产品设计系统内的实现；
- `wechat-parity-validation`：解析、下游、视觉和运行时验收。

## 对齐案例契约

复制 `assets/parity-case.example.json` 后填写真实证据：

```bash
python3 scripts/validate_parity_case.py path/to/case.json
```

只有证据、语义、体验与验证四层均完整，案例才具备进入实现或验收的条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/validate_parity_case.py assets/parity-case.example.json
```

另需验证安装路径确实解析到本仓库，并分别演练一个触发短语、一个非触发任务和至少一条 Kit 流水线。

## 依赖

- Python 3.8+
- PyYAML（仅用于 Skill 源码校验）
- 目标项目自身的测试、构建和运行时工具

## License

MIT
