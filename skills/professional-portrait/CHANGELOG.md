# Changelog

## [0.2.3] - 2026-10-31

### Fixed

- 署名恢复为原值：a015a32 的去品牌化批量替换把 LICENSE 版权方 LovStudio 改成 Skill Publisher、metadata.author 由 lovstudio 改成 contributors，按替换前的原值改回

## [0.2.2] - 2026-10-31

### Fixed

- CI 自 a015a32 起每次失败且 0 个 job：validate.yml 调用的 skill-publisher/dev-skills 可复用工作流并不存在。改为在本仓库内运行 lov-skill-creator 的 validate_skill.py（固定到 976fb61），触发条件与其他 Skill 仓库一致（main 推送、v* tag、PR、手动）
- README 安装命令改为 npx skills add lov-professional-portrait -g -y，源码安装地址改回 github.com/lovstudio/professional-portrait-skill，补充插件市场安装 design@lovstudio，分发说明改为 lovstudio/skills，移除 example.com 占位链接
- cases/cases.json 的案例封面地址被同一次替换改成不存在的 skill-publisher 组织（404），改回 lovstudio/professional-portrait-skill

### Changed

- 补齐 validate_skill.py 要求的 Skill 结构：删去不受支持的 frontmatter 键 category、tagline（聚合目录使用 skills.yaml 自己的 category 与 tagline_en/tagline_zh）；description 精简到 200 字符内，其余触发语移入 Triggers；metadata.tags 改为列表；When to Use 改为 Triggers 并列出非触发条件（多人照片或换脸，Riso 头像交给 lov-riso-portrait，环境人像大片交给 lov-spectacular-ps，从零生成图像交给 lov-image-creator，加说明底栏或 Logo 交给 lov-image-decorator）；新增 references/skill-composition.md；skill.yaml 的 context.profile 补全 schema、source、read、persist

## [0.2.1] - 2026-09-25

### Added

- 合并本地未提交改动到上游 0.2.0 之上
- 本地改动：统一展示名为「职业形象照」，保持调用 ID 与能力契约。

## [0.2.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## 0.1.1

- Publish the authorized four-stage portrait-retouch comparison image.
- Attach the comparison image to the public case for marketplace display.

## 0.1.0

- Initial independent skill release.
