# lov-search-twitter

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

从人物、账号、关键词、X 链接、status ID 或截图出发，交付带来源分级的原帖索引、逐字正文、截图证据和未恢复清单。

## 安装

通过 Agent Skills 统一入口全局安装：

```bash
npx skills add lov-search-twitter -g -y
```

LovStudio 产品界面也可使用：

```bash
npx lovstudio skills add search-twitter
```

本仓库是 canonical source；本地开发链接应最终解析到这份源码。

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`。用户直接说明的长期输出语言、证据格式或工作区偏好可由 `scripts/profile_store.py` 写回共享 Profile；Cookie、Token 和浏览器会话永不持久化。

详见 [Profile 契约](references/user-profile.md)。

## 使用

从搜索结果、网页源码或笔记里提取候选原帖：

```bash
python3 scripts/search_twitter.py discover --input search-results.txt --pretty
```

恢复一组已知 status ID：

```bash
python3 scripts/search_twitter.py recover example_handle \
  1234567890123456789 1234567890123456790 --pretty
```

登记一张带来源页的转帖截图：

```bash
python3 scripts/search_twitter.py evidence screenshot.png \
  --kind screenshot_copy \
  --source-url https://example.org/source \
  --ocr-file screenshot.ocr.txt --truncated --pretty
```

CLI 只负责确定性的抽取、恢复和证据登记。广泛搜索必须同时覆盖普通网页与图片结果，特别是中文媒体、微博、微信公众号、Telegram、论坛和转载页。详见 [发现手册](references/discovery-playbook.md) 与 [证据模型](references/evidence-model.md)。

## 可信度边界

- 双渲染器正文一致只表示提取结果互相印证，不等于两份独立原始来源。
- Wayback 有 CDX 记录但页面是 X 空壳时，状态仍是 `unrecovered`。
- OCR 是截图的派生文本，不能自动升级为逐字原文。
- 公开搜索只能声明 best effort；“账号完整历史”需要获授权的时间线枚举与对账。

## 原子组合

[Skill 组合记录](references/skill-composition.md) 列出了与媒体下载、事实校验和本地历史检索的边界。外部 sibling Skill 不是隐藏依赖。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md`
- `cases/cases.json`
- `pricing-card.yaml`

## 质量门

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.9+
- 网络访问，用于公开渲染器与网页归档
- Web/image search 或浏览器，用于广泛发现与截图
- OCR 可选
- `twscrape` 仅在用户明确授权完整账号枚举后可选

## License

MIT
