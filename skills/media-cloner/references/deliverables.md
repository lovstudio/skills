# 工作区与交付物

## 工作区

`cloner.py init` 生成：

```text
SLUG-style-clone/
├── README.md
├── research/                 仅本地：原片、报告、测量、OCR、转写、截图
│   ├── candidates.json
│   ├── sources.json          样本、哈希、冻结拆分
│   ├── rules-draft.json      规则草稿（宿主撰写）
│   ├── per-video-analysis.json
│   ├── sources/ download-reports/ measurements/ layout/ tones/
│   ├── transcripts/raw/ transcripts/normalized/
│   └── evidence-images/
├── style-pack/SLUG-v0.1/     风格包
├── deliverables/             说明书、预览、演示
├── cases/                    演示的 brief、计划与质检
└── work/                     模板工程与构建文件
```

`cloner.py status --project DIR` 给出当前阶段和下一步，中断后从这里续做。

## 风格说明书

### 文件名

用 `作者-博主名风格复刻-YYYY-MM-DD-v0.1.md`，放在 `deliverables/`：

- 作者取 Profile 的 `user.name` 或 `brand.name`；
- 日期用交付当天；
- 版本与风格包一致。

### 结构

1. **一句话本质。** 这是什么形态的内容，和同类相比独特在哪。每个词都要能在规则里找到依据。
2. **样本与方法。**
   - 样本：格式期、样本数与拆分、子类型分布；
   - 方法：取样方式、ASR 与测量方法；
   - 局限：已知的局限。
3. **八维规则。** 按维度列规则，每条附支持数/分母、强度、证据 ID 与例外。数字写单位与方法。
4. **叙事模板。** 阶段、建议占比、来源样本。
5. **版式与声音参数。**
   - 版式：标题、字幕、资料卡、画中画的坐标与颜色；
   - 声音：分隔方式、响度与真峰值。

   原作值与平台安全区调整后的值分开写。
6. **留出结果。** 覆盖率、命中/部分/未中/不适用、受污染项、独立命中，以及下一版修订候选。
7. **禁用清单。** 不可迁移的身份、品牌、素材与观点。
8. **未知项。** 字体、剪辑软件、未测的听感等。
9. **文件索引。** 风格包、模板、预览、演示的相对路径。

### 写作要求

- **措辞来源。** 用户在对话里给过的说法，照原词用。
- **标注推断。** 所有推断标明是推断。
- **不编造。** 不写相似度分数、盲评结论或“已验证有效”。

## 状态

| 状态 | 含义 |
| --- | --- |
| `split_frozen` | 样本与拆分已冻结 |
| `measured` | 训练集测量与转写齐全 |
| `verified` | 风格包通过 `verify` |
| `frozen` | 已记录 SHA-256，可以打开留出 |
| `holdout_checked` | 留出报告覆盖全部“规则 × 样本”并写入汇总 |
| `guide_written` | 说明书已写好 |
| `template_previewed` | 模板预览帧已核对 |
| `demo_rendered` | 演示已渲染并质检，不等于可以发布 |
| `packaged` | 已交给 Skill 工坊生成专属 Skill 并本地安装 |
| `published` | 已在用户要求的渠道上线并回读 |
