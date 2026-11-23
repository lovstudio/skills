# 项目交接 · Project Handover

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

把做到一半的项目交给别人继续：生成一个对方解开就能接着干的交接包，并在全新目录从零重建验证过。

## 安装

```bash
npx lovstudio skills add project-handover -g -y
```

本地开发时，在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${LOVSTUDIO_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$LOVSTUDIO_SKILLS_INSTALL_DIR/lov-project-handover"
```

## 使用

对你的 Agent 说：

- “把这个项目交接给小王，他也用 Agent 继续对接甲方，别带合同和我的账号。”
- "Hand over this project to the team taking it over; prepare a handover package."

你会得到：

```text
<项目>/output/handover/<交接包>/
  HANDOVER.md     现状、待办、关键决定、工程地图、环境与账号、操作手册、未出包清单、缺口、验收记录
  AGENTS.md       接手方 Agent 的工作约定
  CLAUDE.md       指向 AGENTS.md
  MANIFEST.tsv    文件清单与 SHA-256
  …               工程与素材
<交接包>.zip      干净的归档（无 __MACOSX）
```

交接包只在本地生成，发给谁由你决定。

## 流程

1. 盘点：体积、可重新生成的目录、密钥、个人信息、本机路径、所需凭据、依赖工具版本。
2. 补读最新进展：从群聊、会议、文档里确认对方最后看到哪版、最新提了什么。
3. 定范围：默认不带合同、付款、分成、联系方式、私聊、私人笔记和账号。
4. 整理与遮盖本机路径。
5. 写交接文档和接手约定。
6. 生成清单、打包。
7. 在全新目录解包、从零安装、完整重建，与原成品比对；把发现写回文档。

## 脚本

| 脚本 | 作用 |
| --- | --- |
| `scripts/handover_scan.py` | 只读盘点：体积、缓存候选、密钥、个人信息、本机路径、环境变量、锁文件 |
| `scripts/handover_stage.py` | 按计划 JSON 整理文件（示例见 `assets/plan.example.json`）|
| `scripts/handover_sanitize.py` | 遮盖生成物里的本机路径，默认只预演 |
| `scripts/handover_manifest.py` | 生成、校验文件清单；核对文档里的路径 |
| `scripts/handover_pack.py` | 打不含平台垃圾文件的 zip，并自检 |
| `scripts/media_compare.py` | 比对重建成品与原成品（声音逐位、画面逐帧 PSNR）|

## 用户 Profile（跨 session）

在 `skill.yaml` 中声明 `user-profile/v1`，读取共享 Profile；本 Skill 的长期记录有 `output_dir`、`sender_label`、`always_exclude`。你直接说出的长期偏好由 `scripts/profile_store.py` 写回。详见 [`references/user-profile.md`](references/user-profile.md)。

## 原子组合

见 [`references/skill-composition.md`](references/skill-composition.md)：补读进展可选用聊天、会议、文档类 Skill；新写文字交给 `lov-branding-consistency` 审校。

## 可信度卡与用户案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)
- [`cases/cases.json`](cases/cases.json)
- [`pricing-card.yaml`](pricing-card.yaml)

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.9+（标准库）
- `ffmpeg`、`ffprobe`（比对音视频时）
- 被交接项目自己的工具链（重建验收时）
- `lov-branding-consistency`

## License

MIT
