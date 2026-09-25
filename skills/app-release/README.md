# 应用发版助手 · App Release Pilot

![Version](https://img.shields.io/badge/version-1.0.1-CC785C)

把一个应用版本完整发布到项目已有的 GitHub、Android、iOS、官网和文档渠道，
并以签名、哈希、远端状态和公开回读作为完成证据。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILLS_INSTALL_DIR/lov-app-release"
```

## 使用

完整发版：

```text
发布新版，同步更新 GitHub、iOS、Android、官网和文档。
```

Skill 会自动识别版本入口与既有分发渠道，构建签名制品、提交商店、部署官网，
最后回读每个渠道的真实状态。

指定版本与渠道：

```text
发布 2.3.0：GitHub Release、App Store、官网和 Android 公共下载。
```

English trigger：

```text
Release the app everywhere and verify every production channel.
```

以下请求不属于本 Skill：

```text
只帮我设计一套 GitHub Actions 发布流水线，先不要发布。
```

该请求应由 CI/CD 配置能力处理，且不改变生产状态。

## 执行原则

- 用户明确说“发布”时直接推进声明渠道，不重复询问同一生产确认。
- 版本、构建号、下载地址、变更记录与商店元数据保持一致。
- iOS 上传后等待 `VALID` 再绑定构建并送审。
- Android 公共下载必须验证正式签名与公网 SHA-256。
- GitHub Release、官网、商店与文档分别回读，不用局部成功代替整体完成。
- 商店处于审核中时如实报告，不写成已经公开上架。

## 文件结构

```text
app-release-skill/
├── SKILL.md
├── references/
│   ├── release-contract.md
│   ├── android.md
│   ├── ios-app-store.md
│   └── web-github-docs.md
├── README.md
├── CHANGELOG.md
└── scripts/validate_skill.py
```

## 质量门

```bash
python3 scripts/validate_skill.py .
```

验证还应确认安装链接指向当前源码，并分别测试一个触发短语和一个非触发短语。

## 依赖

- Python 3.8+ 与 PyYAML，仅用于 Skill 源码验证。
- 实际发版依赖目标项目已有的 Git、构建 SDK、签名、商店、GitHub 与部署工具。

## License

MIT
