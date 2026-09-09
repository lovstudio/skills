# Skill Group Composition

这个记录用于避免相邻 Skill 变成意外重复或隐藏依赖。

## Nearby Skills Inspected

| Skill | Classification | Decision |
| --- | --- | --- |
| `lov-wxmp-cracker` | overlap | 路由目标是“公众号文章导出为可复用结构化内容”，与本 Skill 基本相同；但本地只有付费加密包，无 `uvx` 和兑换权益，运行时不可直接调用。本 Skill 作为免费、自包含的本地替代，不依赖它。 |
| `lov-wxmp-cli` | overlap | 目标是公众号缓存读取与 Markdown/HTML/JSON/CSV 导出；同样需要付费解密和登录态，当前机器不可用。本 Skill 处理公开文章 URL 的抓取、图片保留和 OCR，覆盖其中的本地导出部分。 |
| `lov-publish-wechat-article` | optional downstream atom | 消费本地 Markdown 后写入公众号草稿或发布。本 Skill 不远程写入；用户把整理稿交给它时，交接物是本地 `.md` 和 `images/`，由发布 Skill 拥有平台写入验收。 |
| `lov-media-crawler` | adjacent atom | 处理视频号、抖音、小红书等媒体下载。本 Skill 只处理公众号文章 URL，不处理视频号；二者通过 URL 路由区分，不互相调用。 |
| `lov-branding-consistency` | optional downstream atom | 整理稿面向读者并保留来源、事实边界和品牌表述。本 Skill 在顶栏声明该依赖，但它不是抓取或 OCR 的运行时前置条件。 |
| `lov-article-creator` / `lov-writing-style` | not composed | 处理原创文章创作与文风改写；本 Skill 不创作或重写，只做来源保真整理。 |

## Atomic Handoffs

```text
public mp.weixin.qq.com URL
        |
        v
lov-read-wechat-article (core atom)
  manifest.json + images/ + article.md
        |
        +--> optional lov-publish-wechat-article
        |      本地 Markdown 写入远端草稿/发布
        |
        +--> optional lov-branding-consistency
               品牌与读者可见文本复核
```

本 Skill 的核心输入是公开公众号文章 URL，核心输出是本地 Markdown、原图和
manifest。它不把任何远端发布动作当作自己的验收，也不依赖付费解密包。

## Overlap Decisions

`lov-wxmp-cracker` 和 `lov-wxmp-cli` 在“公众号文章本地化”上有重叠。由于当前环境
没有其解密运行时，本 Skill 保留独立实现：公开 URL、标准库抓取、本地图片保留、
macOS Vision OCR、Markdown 生成。后续如果用户启用付费能力，可以让付费 CLI
成为可选的更完整上游，但本 Skill 的公开文章路径不以此为前置条件。

## Composition Decision

本 Skill 是 **Single Skill**。抓取、OCR、Markdown 草稿生成都是同一个用户可见
结果“公众号 URL → 本地 Markdown”的实现步骤，不需要独立业务触发，也不构成
需要分别交付的 Kit 模块。相关外部 Skill 只作为可选下游交接，不嵌入源码。
