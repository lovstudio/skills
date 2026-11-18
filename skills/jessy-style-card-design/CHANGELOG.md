# Changelog

## 0.2.0 — 2026-11-18

- 改名：`lov-card-distill`（名片蒸馏）改为 `lov-jessy-style-card-design`（Jessy 名片设计），
  与 `lov-iris-style-card-design` 同族命名。旧调用 ID、安装链接与 Profile 命名空间不再保留（旧 ID 当天创建，没有存量记录）。
- 定位收窄：从“蒸馏任意参考名片”改为锁定 Jessy 版式，参考别的名片时另建同族 Skill。
- 新增 `references/jessy-style.md`（骨架、色彩角色、槽位、内容变化时怎么调），替代通用蒸馏方法。
- 新增 `assets/jessy-style.card.json` 与中性示例素材（示例 Logo、白色 Logo、example.com 二维码），可直接渲染；
  移除与 Jessy 版式无关的竖版示例。
- 线稿 prompt 固定为右下构图；生成模型环境变量改为 `JESSY_CARD_IMAGE_MODEL`。
- 公开副本：案例里的个人微信二维码换成扫不出内容的占位图，封面重新渲染；案例与版式说明只保留结构，不写来源经过。
- 定价：免费入口，上架 lovstudio.ai。

## 0.1.0 — 2026-11-18

- 首个版本：参考名片蒸馏方法、块级版式 spec 与渲染器（HTML + 正面 / 背面 / 正反 PNG）、
  浏览器内版式检查、多尺度二维码回读、线稿转墨线、装饰插画生成。
- 真实案例：照一张机构名片蒸馏手工川名片，回放与当日交付逐像素一致。
