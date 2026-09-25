# YOLO 模式 · YOLO Mode

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

启用 YOLO 模式时先检查当前 session，通过宿主允许的接口准备任务必要权限，然后按预设和偏好继续。受阻步骤保存进度，
继续其他能做的工作；做完后直接交付。

## 使用

在支持 Skill 的宿主输入：

```text
/lov-yolo-mode 我去吃饭，继续把当前任务做完。
```

支持 Skill 引用的宿主也可使用 `$lov-yolo-mode`；是否注册为 slash 菜单由宿主决定。

也可以说“开启无人值守，我去睡觉，按我的偏好做，不要问我问题”。单独调用会接续当前
未完成目标。没有明确目标时结束为空闲，不自行找任务。说“关闭无人值守”即可退出。

启动时必须核实当前 session 的真实权限。权限足够则直接复用；宿主提供正式接口且允许
当前授权范围的设置时直接配置并回读。无切换能力时准确报告，不假称已开启全权限。
执行范围默认是当前任务，可由用户明确扩展为当前 session。遇到审批限制会完成准备、记录受阻原因，
继续独立工作。没有剩余可执行工作时保存恢复点并结束，不挂着等用户。

它不能解除宿主审批，也不保证系统休眠或客户端退出后继续运行。定时恢复需用户明确
要求并由宿主调度成功；YOLO 模式只准备当前任务必要权限，不自动授权无关应用、创建定时任务或设置防休眠。
权限准备流程见 [当前 session 权限准备](references/session-permissions.md)。

## 本地安装

在本 Skill 源目录执行，安装位已占用时先检查，不覆盖：

```bash
mkdir -p "$HOME/.agents/skills" "$HOME/.codex/skills"
ln -s "$PWD" "$HOME/.agents/skills/lov-yolo-mode"
ln -s ../../.agents/skills/lov-yolo-mode "$HOME/.codex/skills/lov-yolo-mode"
```

当前交付为本地源码与安装，未发布到目录。目录发布后使用统一命令：

```bash
npx skills add lov-yolo-mode -g -y
```

## 跨会话偏好

读取共享 `user-profile/v1`，遵循当前请求、项目、环境配置、Skill records、个人偏好和
安全默认值。只将用户直接说出的持久偏好写入 `skills.lov-yolo-mode.records`，不保存
推断或全量授权，也不跨会话自动开启模式。详见 [Profile 合同](references/user-profile.md)。

## 依赖与验证

核心为指令型单 Skill，无守护进程或业务 CLI。Profile 脚本需要 Python 3.8+，校验需要
PyYAML；`lov-branding-consistency` 仅约束可见说明。业务 Skill 可选交接，不是隐藏依赖。

```bash
python3 scripts/validate_skill.py .
```

[真实创建案例](cases/cases.json)、[行为演练](cases/behavior-review.md) 与
[校验输出](cases/validation.txt) 分别记录实物交付、人工语义检查和本地验证。
演练不代表跨宿主运行实测，不能证明任何宿主绝不会弹出审批。

许可 MIT；免费本地使用，付费与远程渠道均未发布。

## 名称迁移

0.2.0 从 `lov-unattended` 更名为 `lov-yolo-mode`，源目录为 `yolo-mode-skill`。
安装入口已迁移，原 Profile 记录保留，并将已声明偏好复制到新命名空间。
