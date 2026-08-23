# lov-skill-pricing

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

为一个或多个 Agent Skill 生成有依据、可解释、可复评的 Skill Pricing Card，包含建议价、价格带、价值说明、渠道策略和证据缺口。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)/skill-pricing-skill"
mkdir -p "${SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILLS_INSTALL_DIR/lov-skill-pricing"
```

安装链接由当前 Agent 的 `SKILLS_INSTALL_DIR` 决定，源目录保持可移植。

## 使用

```text
$lov-skill-pricing 给这个把访谈整理成公众号文章的 Skill 做 Pricing Card：输入源码和 README，输出一次性价格、首发测试价、价值依据和推广策略。
```

```text
$lov-skill-pricing 批量评估写书、品牌海报和 PDF 翻译三个 Skill；统一评分口径，分别给出单项价、套餐价、渠道适配和证据缺口。
```

输入可以是 Skill 源目录、README、能力 brief、现有价格或一组 Skill；输出默认是 Markdown，用户指定时附 JSON 摘要。当前平台价格上下限、结算机制和协议会单独核验，文章中的历史观察与现行规则分层记录。

## 设计依据

本 Skill 参考文章[《Skill 定价与 Skill Pricing Card》](https://mp.weixin.qq.com/s/Q9HkH6mGloXDyBFLQnhMTw)的核心思路：把创作者时间与维护成本纳入模型，再结合稀缺性、购买信心、实际结果价值、生态飞轮、维护负担与复制风险，形成可解释的价格卡。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+
- PyYAML（仅用于源码结构校验）
- 当前平台事实核验能力（按需）

## License

MIT
