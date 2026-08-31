# lov-repost-wechat-article

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

把合作方微信公众号原文完整保留下来，在清楚署名、不声明原创和隔离内部语境的前提下，加入发布方开场、判断与品牌收尾，并把结果交给现有公众号发布链远端核验。

## 适用场景

- “转发一下合作方这篇推文，尽量保持原汁原味。”
- “从微信记录里找到对方的文章，整理成公众号转载草稿。”
- “Repost this WeChat article with our short introduction and attribution.”

普通原创文章同步、既有草稿修改、微信群聊转发都不属于这个 Skill。

## 输入与输出

输入可以是公开微信文章 URL，也可以是合作方、标题、日期等可由 `lov-wdb-cli` 缩窄的线索。输出包括来源快照、原文冻结区、发布方增量、转载 manifest、Lovpen 微信 HTML、封面收据和经过远端回读的草稿收据。

默认动作只到 `draft_created`。正式公开发布必须由用户再次明确授权。

## 本地安装

当前真源可安装到共享 Agent Skills 目录：

```bash
ln -s /path/to/repost-wechat-article-skill ~/.agents/skills/lov-repost-wechat-article
```

进入远端分发后，统一安装命令为：

```bash
npx skills add lov-repost-wechat-article -g -y
```

## Profile

`skill.yaml` 声明 `user-profile/v1`。Skill 每次读取当前发布主体、品牌名称、官网、语气和工作目录；只有用户明确表达的长期转载偏好才写入 `skills.lov-repost-wechat-article.records`。

## 保真审计

```bash
python3 scripts/audit_repost.py \
  --source-text source-text.txt \
  --edition-html article.lovpen.wechat.html \
  --source-account "来源账号" \
  --source-url "https://mp.weixin.qq.com/s/example" \
  --required-block '[data-repost-block="publisher-intro"]' \
  --expected-source-images 12
```

脚本核对来源块唯一、可见原文逐字一致、来源 URL、原图数量和新增区块数量。加入 `--remote-html` 后复核微信远端正文。

## 组合关系

- 可选上游：`lov-wdb-cli` 定位分享消息和公开 URL。
- 核心：本 Skill 冻结原文、隔离私密语境并编辑转载增量。
- 下游：`lov-publish-wechat-article` 负责 Lovpen、封面、网关、草稿和正式发布状态。

完整边界见 [`references/skill-composition.md`](references/skill-composition.md)。

## 真实案例

首个案例为转发合作方 `S创Slush` 的《S创上海2026全嘉宾Loading…100%》。原文可见文字、14 张原图和来源 URL 保持不变，发布方增加独立首图、开场、来源说明、收尾与品牌尾注；远端草稿回读 15 张图，状态为 `draft_created`，未声明原创、未公开发布。

证据见 [`cases/schuang-2026-evidence.json`](cases/schuang-2026-evidence.json)。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/audit_repost.py --help
```

## 依赖

- Python 3.9+
- beautifulsoup4
- `lov-branding-consistency`
- `lov-publish-wechat-article`
- 可选：`lov-wdb-cli`

## License

MIT。来源文章、图片、Logo 和其他外部素材的权利仍由调用者与原权利人管理。

