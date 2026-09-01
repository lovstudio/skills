# lov-lovpen-add-wechat-channel-comp

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

把一个微信视频号原生 DOM 或 Lovpen DSL 规范化，并安全写入 Markdown 或 HTML。

## 本地安装

发布后的统一安装入口：

```bash
npx skills add lov-lovpen-add-wechat-channel-comp -g -y
```

当前本地真源安装：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
export SKILL_SHARED_DIR="${SKILL_SKILLS_INSTALL_DIR:?请设置共享 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILL_SHARED_DIR/lov-lovpen-add-wechat-channel-comp"
```

Claude Code、Codex 等宿主再用相对软链接指向共享入口。当前分发状态以
`skill-card.yaml` 为准；尚未发布到 GitHub、WorkBuddy 或 SkillPay。

## 使用

### DOM 写入现有 Markdown

先在目标文件放置唯一标记：

```html
<!-- lovpen-wechat-channel -->
```

再运行：

```bash
python3 scripts/render_wechat_channel.py \
  --input component.html \
  --format md \
  --output article.md \
  --json
```

结果是一条紧凑的 Lovpen `::wechat-channels` DSL，标记前后正文保持不变。

### DSL 写入现有 HTML

把 DSL 保存为 `component.dsl`，并在目标 HTML 放置同一标记：

```bash
python3 scripts/render_wechat_channel.py \
  --input component.dsl \
  --format html \
  --output article.html \
  --json
```

结果是一个带关键微信属性和声明式 Shadow DOM 模板的
`mp-common-videosnap` 原生组件。

未指定 `--output` 时输出片段到 stdout。也可使用 `--dom`、`--dsl`，或从 stdin
读取输入。现有文件缺少唯一标记时，脚本会停止，不追加或覆盖全文。

真实案例见 [`cases/cases.json`](cases/cases.json)，字段与写入规则见
[`references/component-contract.md`](references/component-contract.md)。

## 用户 Profile

`skill.yaml` 声明 `user-profile/v1`。只有用户明确要求跨 session 保留默认格式或标记时，
才通过 `scripts/profile_store.py` 写入本 Skill 的 records；组件内容和媒体标识不会持久化。

## 组合边界

本 Skill 只负责单组件规范化与落位。完整文章排版可把生成后的 Markdown 交给
`lovpen-cli`；微信公众号草稿写入与发布交给 `lov-publish-wechat-article`。这些都是可选
下游，不是运行依赖。详见
[`references/skill-composition.md`](references/skill-composition.md)。

## 质量门

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+
- PyYAML，仅用于完整 Skill 校验
- 无网络、浏览器或凭据依赖

## License

MIT
