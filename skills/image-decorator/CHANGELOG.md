# Changelog

## [0.2.3] - 2026-09-07

### Added

- 统一展示名为「图片装帧」，保持调用 ID 与能力契约。

## 0.2.2 — 2026-08-31

- 将 `compatibility` 移至标准顶层字段，使 canonical Skill 校验器能够正确识别运行依赖。

## 0.2.1 — 2026-08-29

- 修复 `screenshot-caption` 仍保留 Modern Screenshot 透明阴影画布的问题。
- 截图模式现会裁除透明/半透明阴影边，并以边缘主色展平透明圆角，不裁不透明 UI 内容。
- 增加透明截图画布裁边与展平回归测试。

## 0.2.0 — 2026-08-29

- 新增 `screenshot-caption` 无外框截图版式，避免与截图自身窗口边界、圆角和阴影叠加。
- 保留 `editorial-caption` 作为艺术作品与摄影图片的默认画框版式。
- 增加截图像素完整性与无外框尺寸回归测试。

## 0.1.0 — 2026-08-29

- 创建 `lov-image-decorator` Single Skill。
- 新增确定性 Pillow CLI，支持 PNG、JPEG、WebP、CJK caption 与品牌 Logo。
- 内置 Warm Academic `editorial-caption` 样式、LovStudio 官方方形 Logo 和 Noto Sans SC。
- 增加真实文章封面案例、测试、Profile、Skill Card、定价与分发状态。
