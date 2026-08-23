# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.6.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## [0.5.3] - 2026-08-23

### Fixed

- preserve user-edited platform descriptions
- freeze description provenance before unrelated form mutations and strengthen generated-copy quality gates

## [0.5.2] - 2026-08-21

### Fixed

- 补充视频号跨域iframe登录与B站立即投稿遮挡经验
- add guarded handoff for cross-origin wechat login iframe; note bilibili submit button occlusion (2026-08-21 EP.02)

## [0.5.1] - 2026-08-21

### Fixed

- 原创默认勾选 + 合集默认询问 + 文案以用户手改为准
- SKILL.md 原创段改为创作者账号默认勾选（用户连续多期要求后仍未自动勾）；合集默认询问归属；描述/标题以用户手改最终版为准，不在终稿确认时展示旧版

## [0.5.0] - 2026-08-18

### Added

- 把两平台的控件定位判据前置成硬规则，补齐视频号描述写法与 B 站表单真实选择器
- SKILL.md 平台差异从三条扩到四条，新增「控件类名一律从 page-anatomy 抄，不许猜」：两边都是自研组件库，antd 猜测全不命中且查不到不报错，表现为点了没反应
- SKILL.md 发布完整性门禁新增封面素材来源：从 output/covers/<ep>/ 与 output/deliverables 取，B 站 16:9 是已知缺口，禁止 ffmpeg 抽首帧顶替
- references/bilibili/page-anatomy.md 补分区/合集/封面的真实选择器表（.video-human-type / .video-season / .cover-main），以及封面 image input 在弹窗打开前不挂载、编辑页分区 disabled 不可改
- references/bilibili/page-anatomy.md 记下定位反模式：querySelectorAll('*') + innerText.includes 必然先命中最外层容器，读回值不许用 innerText 取相邻行
- references/wechat-channels/page-anatomy.md 同步定位反模式，给出 shadow root 内叶子节点 + 文本全等的写法
- references/description-template.md 新增视频号描述五条硬要求（系列全称开场、博主介绍式语气、不泄露制作术语、平铺直叙、客套收尾），与项目 AGENTS.md 的重复记录合并到此处
- SKILL.md frontmatter 把 compatibility 提到顶层，description 补齐中文触发措辞并避免折行切断 Use when

## [0.4.0] - 2026-08-18

### Added

- 从 lov-publish-wechat-channels 升级为双平台发布器 lov-media-publisher，新增 Bilibili 适配
- 新增 references/bilibili/page-anatomy.md：Vue 应用不吃合成事件（必须用原生 value setter 且 inputType 不能省）、计数器要下一轮 js() 才读得到真值、简介是 Quill 实例、svg.close 与 .hot-tag-item 只吃 CDP 真鼠标、主上传区按 upload-wrp 祖先链锚定
- 新增 references/bilibili/platform-constraints.md：16 GB / 10 小时硬限制、标题 80 与简介 2000、合集创建 20 字但编辑表单 50 字、话题专用标签的实测拒绝名单、稿件发布后可编辑
- 记录 B 站封面是两个独立槽（4:3 与 16:9），列表/空间/信息流用的是 16:9，唯一可信验证是公开接口的 pic 字段
- 记录合集撞字数上限时的判据：先分别读创建表单与编辑表单的 maxLength，默认用系列全称，降级用短名必须有实证
- scripts/check_video.py 与 scripts/check_copy.py 新增 --platform，硬限制与文案规则按平台取；check_copy.py 另增 --title 与 --collection-stage
- 新增 skill.yaml 与 references/skill-composition.md，通过 lov-skill-creator 的源校验

### Changed

- references/browser-workflow.md 与 references/publish-gates.md 去平台化，只保留两平台都成立的部分；平台专有内容下沉到 references/wechat-channels/ 与 references/bilibili/
- 视频号专有的页面结构与约束移到 references/wechat-channels/ 子目录
- 发布门禁按可逆性分口径：视频号不可逆，B 站可编辑但改完要重新点「立即投稿」

## [0.3.0] - 2026-08-17

### Added

- 发布前必须由用户确认终稿，并把实测的平台约束与页面结构沉淀成门禁
- 新增 awaiting_confirmation 状态：publish 在字段表全项通过后停下，发系统通知与语音播报，把终稿（含被平台改写的字段）交给用户确认后才提交
- 新增 scripts/check_copy.py：离线预检短标题 16 字上限与禁用逗号、合集 10 字上限且不可修改、描述里的纯文本 # 不算话题
- 新增 scripts/notify_user.py：系统通知 + 语音播报，用于扫码与终稿确认两个卡点；通知失败不阻塞发布
- 新增 references/page-anatomy.md：wujie shadow root 结构、控件定位表、穿透定位文件输入、预渲染弹窗按可见性过滤、一次读完字段表的探针
- 封面槽位数改为按 .cover-tips 实测，不再假设固定两个；实测当期只有一个 3:4 槽，4:3 无上传入口
- 记录 ego-browser helper 签名坑：handOffTaskSpace/waitForAgentControl 需传 id，captureScreenshot 收路径字符串

## [0.2.0] - 2026-08-15

### Added

- 记录平台转码拒绝后的重压方案与浏览器交互修复
- 新增 references/encoding-recipes.md：CRF 抽样定码率预算、2-pass 重压参数与重压后验证
- 禁止交出控制权后自行 takeOverTaskSpace 抢回，交出时通知并后台轮询
- 补充 contenteditable 描述区的清空重建写法，避免过期 caret 产生脏文案
- 话题必须由「#话题」按钮生成标签节点，纯文本 # 不算通过
- 视口边缘按钮改用元素自身 scrollIntoView + click，坐标点击会静默失效
- 封面按每个比例独立居中裁切，新增近黑边带检测，禁止填充留黑条
- 重发场景禁用文件名/时长/首帧做指纹，改用提交时间、标题、话题或新封面

## [0.1.0] - 2026-08-14

### Added

- add complete publish metadata and cover safety gates
- verify original terms and final checkbox state before submission
- preserve the review page when requested and prevent duplicate submit attempts

## [0.0.3] - 2026-08-11

### Fixed

- Switch 发布流程到 ego-browser task space
- 更新浏览器工作流为 ego-browser 的 snapshot/upload/回读步骤

## [0.0.2] - 2026-08-11

### Fixed

- 补齐发布器触发契约并通过 canonical source validation
- 将 metadata.tags 标准化为 YAML 列表
- 保留标准 compatibility 元数据并加入 Triggers/non-trigger 条件

## [0.0.1] - 2026-08-11

### Fixed

- 确保重发时沿用已确认的标题、描述、话题和原创设置并逐项回读
- 补充子 frame/shadow DOM 上传控件的动态定位回退
- 将原创审核中等列表状态明确归类为 platform_pending
