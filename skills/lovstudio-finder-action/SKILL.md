---
name: lovstudio:finder-action
description: >
  Generate Mac Finder right-click menu actions. Two modes: (A) Automator Quick Action
  for file/folder context menus, (B) Finder Sync Extension (Swift + xcodegen) for
  blank-space context menus. Automatically selects mode based on user intent. Trigger
  when user mentions "Finder右键", "右键菜单", "Quick Action", "Finder extension",
  "空白处右键", "新建文件", "context menu", or wants to add custom actions to Finder.
license: MIT
compatibility: >
  macOS 14+. Mode A requires Automator. Mode B requires Xcode and xcodegen
  (`brew install xcodegen`). Ad-hoc signed — works locally, not distributable.
metadata:
  author: lovstudio
  version: "0.2.0"
  tags: macos finder context-menu quick-action finder-sync-extension swift
---

# finder-action — Mac Finder 右键菜单动作生成器

根据用户描述生成 Finder 右键菜单动作，自动判断模式：

| 场景 | 模式 | 技术方案 |
|------|------|----------|
| 右键**文件/文件夹** | Quick Action | Automator workflow |
| 右键**空白处** | Finder Extension | Swift + xcodegen |

## 参数格式

`<动作名称> [触发描述]`

示例：
- `pdf2png .pdf 将PDF所有页面纵向拼接成一张PNG` → Quick Action
- `新建md文件 在空白处右键创建markdown文件` → Finder Extension

## 模式判断

关键词命中 → Finder Extension 模式：
- 提到「空白处」「背景」「目录背景」「新建文件」「blank space」「background」
- 动作不需要选中文件即可触发

其他情况 → Quick Action 模式

---

## Mode A: Quick Action（Automator workflow）

### Step 1: 分析需求

收集（缺失时 AskUserQuestion）：
- **动作名称**：右键菜单显示名
- **触发文件类型**：`.pdf`、`.md`、`.jpg` 等
- **核心命令**：用什么工具做什么

### Step 2: 检查依赖

```bash
which <所需工具>
```

不存在则提示 `brew install <tool>`。

### Step 3: 生成 shell 脚本

```bash
#!/bin/bash
for f in "$@"; do
  [[ "$f" == *.<ext> ]] || continue
  output="${f%.<ext>}.<out_ext>"
  <具体命令> "$f" -o "$output"
done
```

- 工具路径用绝对路径（Quick Action 环境没有 `$PATH`）
- `"$@"` 接收文件参数（inputMethod=1）

### Step 4: 创建 Automator workflow

创建 `~/Library/Services/<动作名称>.workflow/Contents/document.wflow`。

模板见 `references/automator-template.xml`。

关键配置：
- `inputMethod`: `1`
- `serviceInputTypeIdentifier`: `com.apple.Automator.fileSystemObject`
- `workflowTypeIdentifier`: `com.apple.Automator.servicesMenu`

### Step 5: 验证注册

```bash
plutil -lint ~/Library/Services/<动作名称>.workflow/Contents/document.wflow
/System/Library/CoreServices/pbs -update
killall Finder
```

### Step 6: Automator 保存（关键）

```bash
open -a Automator ~/Library/Services/<动作名称>.workflow
```

必须在 Automator 中 Cmd+S 保存一次才会正式注册。

---

## Mode B: Finder Sync Extension（Swift app）

### Step 1: 检查工具链

```bash
which xcodegen && which xcodebuild
```

缺 xcodegen 则 `brew install xcodegen`。

### Step 2: 创建项目结构

```
<ProjectName>/
├── project.yml
├── <ProjectName>/
│   └── AppDelegate.swift
└── FinderExtension/
    └── FinderSync.swift
```

### Step 3: 生成 project.yml

模板见 `references/xcodegen-template.yml`。替换 `APP_NAME` 和 `BUNDLE_ID`。

关键点：
- 宿主 App: `LSUIElement: true`（无 Dock 图标）
- Extension: `NSExtensionPointIdentifier: com.apple.FinderSync`
- 签名: `CODE_SIGN_IDENTITY: "-"`（ad-hoc）

### Step 4: 生成 AppDelegate.swift

```swift
import Cocoa

@main
class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {}
}
```

### Step 5: 生成 FinderSync.swift

模板见 `references/finder-sync-template.swift`。

核心 API：
- `FIFinderSyncController.default().directoryURLs = [URL(fileURLWithPath: "/")]` — 监控所有目录
- `menu(for: .contextualMenuForContainer)` — 空白处右键菜单
- `FIFinderSyncController.default().targetedURL()` — 获取当前目录

常见 action 模式：
- **创建文件**：`FileManager.default.createFile` + 自动递增文件名
- **打开终端**：`NSWorkspace.shared.open` Terminal at target
- **执行脚本**：`Process()` 启动 shell 命令

### Step 6: 构建安装

```bash
xcodegen generate
xcodebuild -project APP_NAME.xcodeproj -scheme APP_NAME -configuration Debug build
cp -R ~/Library/Developer/Xcode/DerivedData/APP_NAME-*/Build/Products/Debug/APP_NAME.app /Applications/
open /Applications/APP_NAME.app
pluginkit -e use -i BUNDLE_ID.FinderExtension
```

### Step 7: 验证

```bash
pluginkit -m -i BUNDLE_ID.FinderExtension
```

不出现时指引：**系统设置 → 通用 → 登录项与扩展 → 已添加的扩展** → 勾选。

## 已知限制

- Finder Extension 菜单项位置由系统决定，无法排在「新建文件夹」之前
- Quick Action 环境没有 `$PATH`，工具路径必须用绝对路径
- Automator workflow 需在 Automator 中打开保存才能注册
- Extension 使用 ad-hoc 签名，仅限本机使用
