# sgc-skill-creator

![Version](https://img.shields.io/badge/version-4.0.0-CC785C)

创建、验证并安装本地 LovStudio Skill 或自包含 Skill Kit。它会根据产品需求自动判断实现形态、Single/Kit 结构以及是否需要用户初始化层，不再让用户选择技术方案。

远程仓库、目录市场、平台发行包与上传验收由独立的 `sgc-skill-publisher` 负责。

## 安装

```bash
git clone https://github.com/lovstudio/skill-creator-skill \
  "${LOVSTUDIO_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}/sgc-skill-creator"
```

## 创建本地 Skill

```bash
python3 "$SKILL_DIR/scripts/init_skill.py" wcx \
  --install-dir "$LOVSTUDIO_SKILLS_INSTALL_DIR"
```

需要持久化品牌、工作区或输出目录时，由代理自动增加：

```bash
python3 "$SKILL_DIR/scripts/init_skill.py" landing-page \
  --user-config \
  --install-dir "$LOVSTUDIO_SKILLS_INSTALL_DIR"
```

包含可独立调用阶段时，由代理自动创建 Skill Kit：

```bash
python3 "$SKILL_DIR/scripts/init_skill.py" bp \
  --kit \
  --module bp-outline \
  --module bp-deck \
  --module bp-polish \
  --user-config \
  --install-dir "$LOVSTUDIO_SKILLS_INSTALL_DIR"
```

## 本地交付边界

Creator 的完成标准是：

1. 本地源码生成完成。
2. `python3 scripts/validate_skill.py .` 通过。
3. Skill 已链接到本地 Agent Skills 目录。
4. 触发、非触发以及 Kit 流水线完成基本验收。

发布到 LovStudio、WorkBuddy 或其他平台时，使用 `sgc-skill-publisher`。

## 依赖

- Python 3.8+
- PyYAML
- Git（仅在需要本地版本历史时使用）

## License

MIT
