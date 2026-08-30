# lov-branding-consistency

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

让公众号、网站、App、策划案、海报等场景中的每一句文案，都从真实受众与品牌角色
出发；同时隔离读者文案、无障碍文本、归属信息和内部制作说明。

## 本地安装

    npx skills add lovstudio/branding-consistency-skill -g -y

本地真源安装：

    export SKILL_SOURCE_DIR="$(pwd)"
    mkdir -p "$HOME/.agents/skills"
    ln -s "$SKILL_SOURCE_DIR" "$HOME/.agents/skills/lov-branding-consistency"

## 使用

### Caption

输入：

    公众号正文首图 Caption：
    Piet Mondrian《Composition (No. 1) Gray-Red》与手工川官方 Logo 构成的正文首图

输出决策：正文已有完整作品说明时，首图不显示 Caption。需要归属时使用：

    Piet Mondrian，《Composition (No. 1) Gray-Red》，1935。

### App 微文案

输入：`同步失败，请检查相关配置并重试。`

输出会结合失败原因与下一步，例如：`网络连接中断，Profile 尚未同步。重试`。
不把统一的营销语气强塞进错误状态。

## 用户 Profile

`skill.yaml` 声明 `user-profile/v1`。Skill 每次读取用户、品牌、工作区、共享偏好和
`skills.lov-branding-consistency.records`；用户明确要求长期沿用的文案边界通过
`scripts/profile_store.py` 原子写回 Profile，源代码保持可移植。

## 原子组合

`references/skill-composition.md` 记录与 writing-style、humanizer、copywriting、
article creator 和发布能力的边界。所有会生成、编辑、排版或发布读者可见文本的
LovStudio Skill 都显式依赖本 Skill；纯搜索、数据、构建与部署能力不依赖。

## 辅助审计

    python3 scripts/copy_audit.py --text '待检查文案' \
      --surface wechat --component caption

脚本只检查元话语、制作术语与组件错配；最终语境与品牌判断仍由主流程完成。

## 质量门

    python3 scripts/copy_audit.py --self-test
    python3 scripts/validate_skill.py .

## 生态依赖校验

`references/dependent-skills.yaml` 维护所有会产出受众可见文本的 LovStudio Skill。
校验 canonical source 是否都已显式依赖本 Skill：

    python3 scripts/sync_dependents.py \
      --manifest references/dependent-skills.yaml \
      --search-root /path/to/lovstudio-skills \
      --search-root /path/to/oneshot-skills \
      --json

## 依赖

- Python 3.8+
- PyYAML（仅完整源校验）

## License

MIT
