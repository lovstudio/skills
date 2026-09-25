# User Profile contract

每次调用先读 `skill.yaml` 声明的 `user-profile/v1` 上下文。字段包括语言、时区、输出目录、
共享无人值守偏好与 `skills.lov-yolo-mode.records.policy` 及 `skills.lov-yolo-mode.records.session_setup`。不输出整份 Profile。

解析顺序：当前请求和参数、项目规则、显式环境配置、本 Skill records、共享 preferences、
共享 user/workspace Profile、安全默认值。环境的 Profile 路径用于选择配置文件，不授予权限。

```bash
python3 scripts/profile_store.py read --skill-id lov-yolo-mode
```

脚本使用 `SKILL_PROFILE_PATH` 或 `SKILLS_PROFILE_PATH`，否则使用已存在的共享 Profile；
无文件时读取为空。文件不可读则记录诊断并按现有上下文推进，不提问或覆盖损坏文件。
`read` 可返回较宽的共享结构，调用方只采用声明字段并避免向用户或日志回显私人数据。

直接声明且适用于以后启用本模式的偏好，可按真实内容保存：

```bash
python3 scripts/profile_store.py record --skill-id lov-yolo-mode \
  --path records.policy --value '"无人值守模式下不主动提问；使用预设与偏好，授权受阻时不等待互动。"' \
  --confirm
```

`--confirm` 代表用户已直接声明该值，无需再次发问。写入原子进行，保留其他配置，报告实际
文件路径。调用者先读取现有 records，避免用单条陈述覆盖其他已有偏好。推断值、运行中
标记、秘密及含糊的“所有动作都批准”不保存。操作授权仍查当前请求及有效站立授权。

`ask_missing: false`、`max_questions: 0` 明确禁止本模式主动提问。字段的 `question` 文本
是兼容 Manifest 的缺失处理说明，不可显示成问题。无有效目标则 idle_no_task；缺少关键
事实则 deferred_input，不把缺失字段变成配置向导。更高优先级强制交互要求仍有效。

原 `skills.lov-unattended.records` 保留作为迁移来源；新运行读取新命名空间。
复制用户原始陈述并记录新的 session 设置偏好，不把偏好当成工具权限生效证据。
