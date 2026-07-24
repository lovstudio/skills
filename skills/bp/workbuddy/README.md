# WorkBuddy Connector 发行说明

本目录用于生成 `LovStudio BP Skill Kit` 的 WorkBuddy `skill-only`
Connector 提交包。

## 接入判断

- Connector 类型：`skill-only`
- 不需要 `mcp.json`
- 不需要 `cli.json`
- 不需要 OAuth、Token 或其他用户凭证
- 不调用 LovStudio 私有服务
- Skill 本体按 MIT License 免费开源

## 提交包内容

```text
lovstudio-bp-workbuddy-v0.2.0/
├── connector-meta.json
├── icon.svg
├── README.md
├── SUBMISSION.md
└── skills/
    ├── lovstudio-bp/
    ├── lovstudio-bp-outline/
    ├── lovstudio-bp-deck/
    └── lovstudio-bp-polish/
```

四个 Skill 可以独立使用，也可以由 `lovstudio-bp` 总控按需组合。

## 构建

输出目录必须是一个尚不存在的新目录：

```bash
python3 scripts/build_workbuddy_connector.py \
  --output-dir /path/to/lovstudio-bp-workbuddy-v0.2.0
```

脚本会同时生成同名 ZIP，并执行结构、元信息、Frontmatter、私有路径和
PPT 运行时适配检查。它还会生成
`lovstudio-bp-workbuddy-v0.2.0-individual/`，其中包含四个可在
WorkBuddy“上传技能”界面逐个导入的 ZIP。

## 维护

更新 BP Skill Kit 后：

1. 更新 `workbuddy/connector-meta.json` 的版本和文案；
2. 使用新的版本化目录重新构建；
3. 将 ZIP 提交给 WorkBuddy 运营团队审核。
