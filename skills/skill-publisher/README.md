# lov-skill-publisher

![Version](https://img.shields.io/badge/version-0.5.0-CC785C)

把已经验证并安装在本地的 Skill 发布到一个或多个独立渠道。发布前默认调用 `lov-skill-pricing` 自动生成或刷新可解释定价，再把同一价格契约适配到各渠道，同时保持平台元数据和发行产物不污染源代码。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILL_SKILLS_INSTALL_DIR/lov-skill-publisher"
```

也可以通过 Skills CLI 安装：

```bash
npx skills add lovstudio/skill-publisher-skill -g -y
```

## 当前适配器

| 渠道 | 交付结果 | 完成证据 |
|------|----------|----------|
| Skill Publisher | GitHub 源仓库、Release、目录和线上详情页 | 线上版本与内容可见 |
| 腾讯 WorkBuddy | Connector ZIP，可继续导入个人技能库 | 包校验、校验和及安装列表 |
| 支付宝 SkillPay | 商品 ZIP、人民币定价和审核提交 | 解析成功、提交回执与商品状态 |

其他平台通过 `references/channels.md` 的适配器契约扩展，并在实现时核对最新官方要求。

## 使用示例

- 直接调用 `lov-skill-publisher`：默认发布到全部支持渠道。
- 只说“发布”也会先自动定价；用户明确给出的价格、币种和免费/付费状态会作为定价约束保留。
- “把这个本地 Skill 发布到 Skill Publisher。”
- “给这个 Skill 生成 WorkBuddy 包。”
- “把这个 Skill 按 ¥19.9 提交到 SkillPay。”
- “把这个 Skill 分发到全部渠道，并分别验证。”

## 质量门

```bash
python3 scripts/validate_skill.py . --target source
```

WorkBuddy 包：

```bash
python3 scripts/build_workbuddy.py SOURCE \
  --meta CONNECTOR_META \
  --icon ICON \
  --output-dir OUTPUT_DIR
```

## 依赖

- Python 3.8+
- PyYAML
- `lov-skill-pricing`（默认发布前自动定价）
- Git 与 GitHub CLI（Skill Publisher 渠道）
- 各目标渠道所需凭据

## License

MIT
