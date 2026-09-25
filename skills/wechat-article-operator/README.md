# 公众号草稿操作（旧入口） · WeChat Draft Operator (Legacy)

![Version](https://img.shields.io/badge/version-0.2.1-CC785C)

> 已归并：新任务请使用 `lov-publish-wechat-article` 的 `existing-draft` 管线。本目录只保留历史实现与兼容路由，不应继续安装或被语义发现。

自动读取、编辑、保存并重载验证微信公众号文章，为内容智能和品牌化能力提供可靠操作底座。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILLS_INSTALL_DIR/lov-wechat-article-operator"
```

## 使用

```text
$lov-wechat-article-operator 读取当前公众号文章，返回标题、摘要、章节和封面。
```

```text
$lov-wechat-article-operator 把这段代码块插到品牌介绍前，其他内容保持不变，并在保存后重载验证。
```

输出包括文章状态、计划内修改、持久化验证，以及关键不变量检查。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/verify_article_state.py --self-test
```

## 依赖

- 能复用用户登录状态的浏览器自动化适配器
- Python 3.8+
- PyYAML（仅源码结构校验）

## License

MIT
