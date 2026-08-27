# lov-search-file

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

从本机 AI 对话中追溯图片、文档和其他交付文件，返回仍然存在的路径、来源会话与
存储层级，优先推荐项目归档或下载目录中的耐久副本。

## 安装

```bash
npx lovstudio skills add search-file
```

本地开发安装：

真源目录为 `search-file-skill`。在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$SKILL_SKILLS_INSTALL_DIR/lov-search-file"
```

## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享
Profile 读取用户、品牌、工作区和本 Skill 的长期记录。用户直接说出的持久
偏好或品牌事实由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

```bash
# 从记得的对话主题追溯图片
python3 scripts/find_ai_file.py "P 头像" --kind image

# 已知 Codex session 时收窄范围，并返回结构化结果
python3 scripts/find_ai_file.py "职业形象照" \
  --session-id 019fabba-ca6f-79c1-8306-ff1a4cabf870 --json

# 加一个自定义文件根做文件名兜底
python3 scripts/find_ai_file.py "上次的路演 PPT" --root "$HOME/Documents" --json
```

输出包含候选绝对路径、是否存在、文件大小、修改时间、来源 session、对话证据和
`project-output` / `downloads` / `ai-cache` / `temporary` 存储层级。脚本只读文件，
本地增量索引以 `0600` 权限保存在用户缓存目录。

## 原子组合

每个新 Skill 都带有 `references/skill-composition.md`。它记录已检查的相邻
Skills、可选的上游/下游交接、重叠处理，以及为何选择 Single Skill 或自包含
Skill Kit；外部 sibling Skill 不作为隐藏依赖。

## 可信度卡与用户案例

每个新 Skill 都必须随源代码提供：

- `skill-card.yaml` / `skill-card.md`：用途、负责人、依赖、风险、输出与维度地图。
- `cases/cases.json`：至少一个真实的 Input → Prompt → Output 案例。
- `pricing-card.yaml`：免费或付费都要写清价值锚点、交付边界和复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.9+（仅标准库）
- ripgrep（推荐；缺失时可回退）

## License

MIT
