# lov-do-they-love-me

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

把两个人的微信私聊做成有证据的恋爱指数分析：量化互动节奏，用本地模型把消息分成
工作／情感／生活三类，最后产出一张手机竖版信息图。结论必须带口径与误差，
**工作内容不计入情感热度**。

## 安装

```bash
npx skills add lov-do-they-love-me -g -y
```

## 从源码安装（维护者）

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p ~/.agents/skills
ln -sfn "$SKILL_SOURCE_DIR" ~/.agents/skills/lov-do-they-love-me
for host in ~/.claude/skills ~/.codex/skills; do
  mkdir -p "$host"
  ln -sfn ../../.agents/skills/lov-do-they-love-me "$host/lov-do-they-love-me"
done
readlink -f ~/.claude/skills/lov-do-they-love-me   # 应解析到本目录
```

## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享
Profile 读取用户、品牌、工作区和本 Skill 的长期记录。用户直接说出的持久
偏好或品牌事实由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

```bash
export SKILL_DIR="$SKILL_SOURCE_DIR"

# 1) 取数（交给 lov-wdb-cli，隔离副本只读）
python3 "$WDB_SKILL/skills/wdb-query/scripts/wdb_cli.py" chats \
  --contact "<昵称>" --from 2026-07-18 --to 2026-09-11 --limit 5000 --format jsonl > messages.jsonl

# 2) 量化 + 日历矩阵
python3 "$SKILL_DIR/scripts/chat_metrics.py"    --messages messages.jsonl --me <我> --other <对方> --out metrics.json
python3 "$SKILL_DIR/scripts/matrix_dataset.py"  --messages messages.jsonl --me <我> --other <对方> --out matrix.json

# 3) 语义分层（规则层 + 本地模型）+ 校准
python3 "$SKILL_DIR/scripts/export_text.py"     --messages messages.jsonl --me <我> --other <对方> --out label_input.jsonl
# 先校准：示例必须在校准集之外，否则算出来的是假准确率
python3 "$SKILL_DIR/scripts/semantic_label.py"  --input label_input.jsonl --out gold_pred.jsonl \
  --eval-gold gold.json --report accuracy.json
# 再全量标注（--context 40 会带上一条上文，短句才判得准）
python3 "$SKILL_DIR/scripts/semantic_label.py"  --input label_input.jsonl --out labels.jsonl \
  --model qwen3:8b --batch 20 --context 40
python3 "$SKILL_DIR/scripts/topic_composition.py" --labels labels.jsonl --out composition.json --accuracy accuracy.json

# 4) 出图，再交给 lov-mobile-infographic 成卡
python3 "$SKILL_DIR/scripts/card_figures.py"    --matrix matrix.json --composition composition.json \
  --metrics metrics.json --outdir figures --partner-label "<昵称>"
python3 "$SKILL_DIR/scripts/verify_figures.py"  --card card.html --out verify.json
```

输入：本机微信私聊导出（`messages.jsonl`，字段见 `references/chat-metrics.md`）。
输出：`metrics.json`、`matrix.json`、`labels.jsonl`、`accuracy.json`、`composition.json`、
`figures/*.svg`，以及由下游 Skill 渲染的 `card.html` / `card.png` / `card.audit.json`。

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

- Python 3.9+（量化与出图脚本只用标准库）
- Playwright for Python（几何复核、卡片渲染）
- 本地 Ollama 模型（默认语义标注后端，不联网）
- 可选上游 `lov-wdb-cli`、可选下游 `lov-mobile-infographic`

## License

MIT
