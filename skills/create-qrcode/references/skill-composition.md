# Skill Group Composition

## Nearby Skills Inspected

- `lov-image-creator`：生成插画、海报或代码渲染图片，属于相邻图像能力，但不保证
  二维码矩阵、quiet zone 或扫码一致性，因此不承担本结果。
- `lov-image-decorator`：给已有图片增加 caption 与 Logo，可消费本 Skill 生成的 PNG；
  它不会编码二维码内容。
- `lov-business-card`：名片可以包含二维码，但最终验收是完整名片，不是通用二维码。
- LovStudio 内置 `qr-code-generator`：浏览器端工具，支持 Warm Academic 配色、圆角、
  M 级纠错和海报下载。它是产品实现证据，不是可移植 Agent Skill。
- `qr` 与 `qrencode` CLI：能生成标准二维码，是底层替代工具；它们不提供统一的 Profile、
  海报、隐私输出契约和扫码回读。

## Atomic Handoffs

- 上游输入由用户、文本文件或其他能力提供 UTF-8 载荷；本 Skill 从载荷字节开始负责。
- 核心原子是 `lov-create-qrcode`：输入载荷与样式偏好，输出已校验 PNG 和机器可读结果；
  扫码内容一致性是本 Skill 的最终验收边界。
- 下游 `lov-image-decorator` 可接收 PNG 做传播图包装；它只负责装饰，不能替代扫码验收。
- 下游名片、文档、幻灯片和发布能力可嵌入已验证 PNG；它们必须保持 quiet zone 和比例。
- 二维码识别能力可反解现有图片，但不参与生成流程。

## Overlap Decisions

没有发现拥有同一可移植结果契约的已安装 Skill。浏览器二维码工具保留其交互式产品
职责；`lov-create-qrcode` 复用它已验证的视觉语言，但提供本地 CLI、Profile 与自动
验收，不复制网站组件或依赖网站运行时。

## Composition Decision

本源是 Single Skill。编码、样式解析、海报包装和扫码回读共同服务同一个用户可见结果，
拆成多个模块只会增加交接成本。相邻 Skills 均通过图片文件可选交接，不是硬依赖。
