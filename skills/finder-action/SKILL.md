---
name: lov-finder-action
license: MIT
compatibility: 'macOS 14+. Mode A requires Automator. Mode B requires Xcode and xcodegen
  (`brew install xcodegen`). Ad-hoc signed — works locally, not distributable.

  '
description: 创建 macOS Finder 文件快捷操作或目录背景菜单扩展。支持明确输入与结果回读。Use to create a Finder context
  menu action.
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 0.4.3
  tags:
  - macos
  - finder
  - context-menu
  - quick-action
  - finder-sync-extension
  - swift
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
---

# Finder 快捷动作 · Finder Actions

创建 macOS Finder 文件快捷操作或目录背景菜单扩展。

## Triggers

### Activate when

- “创建 macOS Finder 文件快捷操作或目录背景菜单扩展。”
- “Create a Finder context menu action.”

### Do not activate when

- 只是查询本 Skill 的说明，或请求与上述结果无关的任务；不执行实际业务操作。
- 用户仅要预览或审查时，不进入修改、提交或发布分支。

## Execution boundary

自然语言请求即可触发；无需旧 slash 路径、参数插值或指定助手。明确解析当前请求中的
项目、目标文件、选项与输出位置；用当前宿主实际提供的文件、搜索、CLI 和浏览器能力。
项目依赖版本与外部 API 在执行时核实，不能假设示例是现行配置。随包脚本从 Skill 根解析，
业务文件从目标项目根解析。先读当前状态，保护已有未提交内容与其他任务的暂存区。
分析、预览请求保持只读；修改、提交、推送、部署和发布各依当前请求的明确范围执行。
不绕过保护、自动发送消息、强制结束用户进程或抢前台。失败保留可诊断原始错误。

## Workflow

1. 根据是否需要选中文件选择 Automator Quick Action 或 Finder Sync Extension；解析动作名称、文件类型、实际处理逻辑与目标目录。

2. Quick Action 使用按参数接收的脚本（`inputMethod=1`，`"$@"`）与 workflow plist，工具路径从实际安装解析，处理中文、空格、多选和同名输出；按下文「Quick Action 安装」从 [document.wflow 模板](references/automator-template.xml) 与 [Info.plist 模板](references/automator-info-template.xml) 生成，并核验当前系统字段。

3. Finder Extension 使用实际 Xcode 工具链、独立 bundle ID、必要沙盒权限和精确监控目录，菜单 action 明确 target；按当前 Apple 文档核实能力，不要求整个磁盘临时例外权限。

4. 需要跨进程 helper 时使用可验证的结构化消息和固定操作集合，不从剪贴板读取任意 shell 命令，不用 helper 绕过系统权限。

5. 生成构建配置和代码后检查 plist、编译及扩展注册；本地 ad-hoc 签名与可分发签名分别报告，不将前者称作正式发行。

6. 不强制 killall Finder、打开 Automator 或切换应用前台；需用户启用扩展的步骤准确说明。实际菜单触发只有完成观察后才标验证。

7. 保留现有 workflow 与应用，明确安装位置和回退路径；不覆盖同名菜单动作。

## Quick Action 安装

`document.wflow` 模板只含一个 Run Shell Script action：`inputMethod=1`、`shell=/bin/bash`，
输入 `com.apple.Automator.fileSystemObject`，`workflowTypeIdentifier=com.apple.Automator.servicesMenu`，
`presentationMode=15`，输出 `com.apple.Automator.nothing`。脚本占位 `SHELL_SCRIPT`、菜单名占位
`ACTION_NAME` 一律用 `plutil` 写入（自动处理 XML 转义），不手工拼接 XML。`SKILL_DIR` 指本 Skill 根目录。

```bash
NAME="动作名称"                                    # 菜单显示名，同时是 workflow 包名
DEST="$HOME/Library/Services/$NAME.workflow"
[ -e "$DEST" ] && { echo "同名 workflow 已存在：$DEST" >&2; exit 1; }
bash -n action.sh                                  # 已写好的处理脚本
STAGE="$(mktemp -d)/$NAME.workflow"; mkdir -p "$STAGE/Contents"
cp "$SKILL_DIR/references/automator-template.xml" "$STAGE/Contents/document.wflow"
cp "$SKILL_DIR/references/automator-info-template.xml" "$STAGE/Contents/Info.plist"
plutil -replace actions.0.action.ActionParameters.COMMAND_STRING -string "$(cat action.sh)" "$STAGE/Contents/document.wflow"
plutil -replace NSServices.0.NSMenuItem.default -string "$NAME" "$STAGE/Contents/Info.plist"
plutil -replace NSServices.0.NSSendFileTypes -json '["com.adobe.pdf"]' "$STAGE/Contents/Info.plist"  # 按目标 UTI；文件与文件夹通用保留 public.item
plutil -lint "$STAGE/Contents/document.wflow" "$STAGE/Contents/Info.plist"
diff <(plutil -extract actions.0.action.ActionParameters.COMMAND_STRING raw -o - "$STAGE/Contents/document.wflow") action.sh
mv -n "$STAGE" "$DEST"
/System/Library/CoreServices/pbs -update
```

- 同名 workflow 已存在时停止，换名或询问用户；不覆盖、不合并。lint 或 diff 失败时只丢弃 staging 目录。
- 不执行 `killall Finder`，不自动打开 Automator。菜单未出现时，按当前系统版本核实后请用户在系统设置中检查该服务的启用状态，或由用户自行在 Automator 打开并保存一次。
- 回退路径：把 `$DEST` 移到废纸篓（`mv "$DEST" ~/.Trash/`）后再次运行 `pbs -update`。
- 报告安装路径与回退命令；实际右键触发经观察后才标记已验证。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
