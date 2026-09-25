# 图片上云 · Image Uploader

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

复用现有 PicGo 图床配置，把本地图片变成网址，或安全地批量改写 Markdown
中的本地图片引用。

## 本地安装

推荐使用 LovStudio 三层链接，让 Codex 与 Claude 共用同一份真源：

```bash
SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "$HOME/.agents/skills" "$HOME/.codex/skills" "$HOME/.claude/skills"
ln -s "$SKILL_SOURCE_DIR" "$HOME/.agents/skills/lov-upload-image"
ln -s ../../.agents/skills/lov-upload-image "$HOME/.codex/skills/lov-upload-image"
ln -s ../../.agents/skills/lov-upload-image "$HOME/.claude/skills/lov-upload-image"
```

已有目标不会被初始化器覆盖；请先检查 `readlink` 和 `realpath`，不要删除未知来源。

## PicGo 前置条件

优先使用 PicGo GUI 或 PicGo-Core 的 Server API，默认地址为
`http://127.0.0.1:36677`。它会直接复用 PicGo 当前选中的图床、插件和命名规则。

```bash
python3 scripts/upload_image.py doctor --json
```

若 Server 开启了认证，只通过环境变量提供秘密：

```bash
export PICGO_SERVER_SECRET="从安全存储取得的值"
```

不要把图床密钥或 Server secret 写入 Skill、Markdown、Profile 或命令参数。

## 使用

上传单张图片并验证网址：

```bash
python3 scripts/upload_image.py upload ./images/cover.png --verify
```

stdout 直接返回网址。需要稳定的机器输出时加 `--json`；也可以一次传入多张图片。

批量处理 Markdown：

```bash
python3 scripts/upload_image.py markdown ./article.md --dry-run --json
python3 scripts/upload_image.py markdown ./article.md --verify --json
```

默认生成 `article.uploaded.md`，不改原文。显式传 `--in-place` 时会先保留
`article.md.bak`。同一文件在文档中出现多次，只上传一次。

支持普通 Markdown 图片、图片引用定义、HTML `<img src>`、Obsidian 图片嵌入、
URL 编码路径和带空格的尖括号路径。远程地址、代码块与行内代码保持不变；详见
[`references/markdown-coverage.md`](references/markdown-coverage.md)。

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`。可持久化 PicGo Server 地址、后端选择和
Markdown 写入模式，但只在用户明确要求长期默认时写入；凭据永不持久化。详见
[`references/user-profile.md`](references/user-profile.md)。

## 原子组合

[`references/skill-composition.md`](references/skill-composition.md) 记录了图片生成、
博客发布、微信发布等相邻 Skill 的输入输出边界。它们可在制品层交接，但不是
本 Skill 的隐藏依赖。

## 可信度与案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)
- [`cases/cases.json`](cases/cases.json)
- [`pricing-card.yaml`](pricing-card.yaml)

## 质量门

```bash
python3 tests/test_upload_image.py
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+
- 已配置的 PicGo GUI Server 或 PicGo-Core CLI
- PyYAML（仅 Skill 源校验）

## License

MIT
