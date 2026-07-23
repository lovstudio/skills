# lovstudio-bp · BP Skill Kit

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)
![License](https://img.shields.io/badge/license-MIT-173D2A)
![Free](https://img.shields.io/badge/Free-open--source-5DC98F)

一套可以拆开使用、也可以自由组合的投资人 BP 工具包。

```text
项目材料 → BP 大纲 → PPTX / PDF → 专业审稿与润色
             ↑            ↑              ↑
         bp-outline    bp-deck       bp-polish
              └──────── lovstudio-bp 总控 ────────┘
```

不再把“想清楚融资叙事”“制作 PPT”“审稿润色”塞进一次又长又重的执行。用户可以只拿需要的那一段，也可以让总控完成全流程。

由 [LovStudio](https://lovstudio.ai) 免费开源。

## 安装

安装整套 BP Skill Kit：

```bash
npx lovstudio skills add bp -g -y
```

只安装一个模块：

```bash
npx lovstudio skills add bp-outline -g -y
npx lovstudio skills add bp-deck -g -y
npx lovstudio skills add bp-polish -g -y
```

## 四个入口

| Skill | 最适合的任务 | 交付物 |
|---|---|---|
| [`lovstudio-bp`](SKILL.md) | 不确定用哪个，或要完成全流程 | 自动组合所需模块 |
| [`lovstudio-bp-outline`](skills/bp-outline/SKILL.md) | 从项目资料建立投资叙事 | Brief、证据账本、12–15 页大纲 |
| [`lovstudio-bp-deck`](skills/bp-deck/SKILL.md) | 把已确认大纲做成专业 PPT | PPTX、PDF、全稿预览、Deck Manifest |
| [`lovstudio-bp-polish`](skills/bp-polish/SKILL.md) | 审查或升级已有 BP/PPT | 100 分报告、逐页修改、定向重做 |

## 组合方式

### 只想先把内容想清楚

```text
$lovstudio-bp-outline 根据当前项目材料写一份种子轮 BP 大纲
```

### 已有大纲，直接做 PPT

```text
$lovstudio-bp-deck ./business-plan/outline.md --style minimal
```

### 已经有 BP，只想变得更专业

```text
$lovstudio-bp-polish ./project-bp.pdf --full
```

### 从材料到最终交付

```text
$lovstudio-bp 从当前项目生成完整 BP，不要问我问题，按推荐方案
```

总控默认组合：

```text
bp-outline → evidence gate → bp-deck → visual gate → bp-polish
```

每个阶段共享同一个工作区，不会重复提问，也不会覆盖已经确认的大纲。

组合与回退规则见 [references/composition.md](references/composition.md)。

## 工作区

```text
business-plan/
├── brief.md                 # 融资任务和产品定义
├── evidence-ledger.md       # 事实 / 推断 / 假设 / 缺口
├── outline.md               # 投资人叙事源文件
├── assets/                  # Logo、截图、照片、二维码、数据
├── deck-manifest.md         # 风格、页数、素材和导出状态
├── reports/bp-review.md     # 内容、证据和视觉审稿报告
├── project-bp.pptx
├── project-bp.pdf
└── project-bp-preview.png
```

## 体验原则

- 先读取项目与已有材料，再决定问什么。
- 只有真正影响结果的选择才询问用户。
- 用户说“按推荐方案”时直接使用种子轮 12–15 页默认值。
- 大纲确认后才进入视觉风格与 PPT 生产。
- 图表和视觉润色不能改变事实。
- 只重做有问题的页面，不因为一次修改推翻整份材料。
- 完整流程必须交付 PPTX、PDF、预览和审稿报告。

## 公开案例：Yoda 种子轮 BP

Yoda 案例经历了完整组合流程：从项目材料和用户反馈中重建产品定位，形成证据化 15 页大纲，再完成专业图表、品牌视觉、二维码与最终审稿。

![Yoda BP 封面](cases/yoda-bp-cover.png)

![Yoda BP 全稿预览](cases/yoda-bp-overview.png)

- [案例复盘](references/case-yoda.md)
- [案例质量报告](reports/yoda-bp-case-report.md)

## 兼容性

- Python 3.8+：工作区初始化和确定性审稿。
- [`lovstudio-any2deck`](https://github.com/lovstudio/any2deck-skill)：PPTX/PDF 生产。
- 当前市场、竞品、政策和融资事实需要访问权威来源。
- 不依赖作者私有路径；品牌和输出目录通过参数、环境变量或共享配置传入。

原有脚本入口继续可用：

```bash
python3 scripts/init_bp.py --name "Project" --output ./business-plan
python3 scripts/audit_bp.py --input ./business-plan/outline.md
```

## License

MIT
