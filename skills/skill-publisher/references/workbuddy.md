# WorkBuddy（CodeBuddy 开放平台）发布标准

This adapter builds a self-contained Connector ZIP from portable local source.
Platform metadata, icon, staging directory, and archives stay outside source.

## Inputs

```text
<local-source>/
├── SKILL.md
├── README.md
├── kit.yaml                 # Skill Kit only
└── skills/                  # Skill Kit only

<publisher-profile>/workbuddy/<skill-name>/
├── connector-meta.json
└── icon.svg
```

`connector-meta.json` includes:

- `name`, `name_zh`, `name_en`
- `description`, `description_zh`, `description_en`
- globally unique kebab-case `source`
- `type: "skill-only"`
- SemVer `version`
- `source_type` plus one supported source locator
- two to five Chinese and English examples
- `minWorkbuddyVersion` when a version-gated field is used

Display names should contain 2–20 characters. Chinese and English descriptions
should each contain 20–100 characters and describe the user outcome.

## Package transformation

The builder copies portable source to staging and converts package frontmatter
to WorkBuddy fields without mutating canonical source. For Skill Kits, every
declared module is included and every named pipeline must reference known module
IDs.

## Build

Choose a new output path for each build:

```bash
python3 "$SKILL_DIR/scripts/build_workbuddy.py" SOURCE \
  --meta PUBLISHER_PROFILE/connector-meta.json \
  --icon PUBLISHER_PROFILE/icon.svg \
  --output-dir OUTPUT_DIR
```

The builder emits a combined Connector ZIP and individual Skill ZIPs, validates
the staged package, and rejects broken references, private paths, placeholders,
caches, compiled Python artifacts, missing metadata, or missing modules.

## Evidence

## CodeBuddy 上架

1. 打开 `https://www.codebuddy.cn/open/console/dashboard`，选择“上架新 Skill”。
2. 上传 builder 输出的 `*-individual/<skill-name>.zip`；聚合 Connector ZIP 不用于单项上架。
3. 等待“解析成功”，填写中英文展示名与用户价值描述，提交审核。
4. 记录审核中、已上架或已驳回状态；微信群审核沟通不等同于公开上架证据。

Record source version and commit when available, source and package validation,
ZIP paths and SHA-256 checksums, archive listing, module count, metadata, and icon
presence.

`prepared` means the package exists and passes local gates. If personal-library
import is requested, continue until the installed list shows the Skill. Public
marketplace publication requires separate evidence from the public marketplace.
