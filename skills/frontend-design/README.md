# 界面设计师 · Interface Designer

![Version](https://img.shields.io/badge/version-0.3.0-CC785C)

手工川工作室维护的前端设计 Skill：把需求、真实内容和现有代码变成有辨识度、
交互一致、支持图片音视频的可用界面。

## 适用场景

- 页面、组件、工具栏、设置与导航设计。
- 修复图标、按钮、状态和响应式之间的交互不一致。
- 制作 GSAP 交互地图、教学展示与多媒体案例集。
- 只读审查现有界面的内容、操作与真实访问路径。

完整品牌定位与营销落地页优先使用 `lov-oh-my-landingpage`；性能架构、API 请求封装、
纯 CSS 清理和独立剪辑不由本 Skill 接管。

## 工作室版本增加了什么

| 关注点 | 具体约定 |
| --- | --- |
| 产品语义 | 链接、动作、状态、切换各用合适控件，同级操作保持一致 |
| 内容适配 | 根据受众、任务与素材决定风格，保留既有设计系统 |
| 图片与音视频 | 来源、加载、错误、实际播放和替代内容分别验收 |
| GSAP | 关系重排与演示，包含减少动效、清理和失败时可读路径 |
| 站点集成 | 桌面、手机、语言和身份分支一起核查，实际点击目标路由 |
| 可信证据 | 历史案例、新版本演练、静态检查与线上结果分别记录 |

工作室是维护者，不是所有作品的默认品牌。用户可以明确要求专题自由选风格。
这是对本地 `frontend-design` 0.2.0 方法的独立整理，来源说明见
[Provenance](references/provenance.md)。旧版安装保留，新版使用独立 ID。

## 安装

官网安装命令：

```sh
npx lovstudio skills add frontend-design
```

需要手动管理源码时，将源码保存在自己的 Skill 源目录，设置 `SKILL_SOURCE`
为该目录、`SKILL_INSTALL_DIR` 为共享 Skill 安装目录后执行：

```sh
mkdir -p "$SKILL_INSTALL_DIR"
ln -s "$SKILL_SOURCE" "$SKILL_INSTALL_DIR/lov-frontend-design"
```

安装目标必须空闲，不能覆盖旧文件。宿主适配入口使用相对链接指向共享安装位。
也可以通过统一目录指定 Skill ID 安装：

```sh
npx skills add lovstudio/skills --skill lov-frontend-design -g -y
```

## 使用

“用 lov-frontend-design 把这些真实案例做成适合课堂展示的交互页面，支持图片、音频和
视频，并用 GSAP 解释能力分布。风格服从内容。”

“用 lov-frontend-design 只读检查官网资源入口，验证电脑和手机上的标签、键盘与跳转。”

“Design this settings toolbar with consistent control semantics and accessible states.”

## Profile 与依赖

每次读取 [skill.yaml](skill.yaml) 的 `user-profile/v1`。品牌、语言、项目路径与偏好从
当前请求、项目和共享 Profile 解析；不写死维护者环境。只有明确长期偏好才持久保存。

```sh
python3 scripts/profile_store.py read --skill-id lov-frontend-design --pretty
```

可见文案依赖 `lov-branding-consistency`。主体为 instruction-first，不绑定前端框架。
使用项目已有工具链；运行验收需浏览器工具，Profile/Skill 校验需 Python 3.8+ 与 PyYAML。
GSAP 只在任务需要时使用；安装依赖不是此 Skill 固定副作用。

## 验证与案例

```sh
python3 scripts/validate_skill.py .
```

完整验收见 [Acceptance](references/acceptance.md)。
[真实案例](cases/cases.json) 收录能力地图与官网入口，并区分旧任务证据和新版本复核。
[Skill Card](skill-card.md) 提供能力维度与限制；[定价卡](pricing-card.yaml) 记录免费依据。

本 Skill 免费提供源码与方法，媒体生成和运行工具的成本另计。
版本与安装入口以 [官网目录](https://lovstudio.ai/skills/frontend-design) 和
[源码 Release](https://github.com/lovstudio/frontend-design-skill/releases) 为准。
渠道发布记录与发行定价卡由 Publisher 在源码之外管理。
