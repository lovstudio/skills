---
name: lovstudio:finder-action
category: Dev Tools
tagline: "Generate Mac Finder right-click menu actions. Quick Action or Finder Sync Extension."
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
  version: "0.3.0"
  tags: macos finder context-menu quick-action finder-sync-extension swift
examples:
  - name: OpenCC
    url: https://github.com/MarkShawn2020/mac_open-claude-code
    description: Right-click to open Claude Code in iTerm2 (with helper app)
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
- **沙盒必须开启**（`app-sandbox: true`），否则扩展不会被系统加载
- 文件写入需用 `temporary-exception.files.absolute-path.read-write: [/]`，`files.user-selected.read-write` 无效

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
- **打开终端**：AppleScript 控制 iTerm2/Terminal（见 `references/applescript-iterm.swift`）
- **执行脚本**：`Process()` 启动 shell 命令

**AppleScript 自动化**需要在 entitlements 中添加：
```yaml
com.apple.security.automation.apple-events: true
```

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

## 沙盒限制与 Helper App 方案

Finder Sync Extension 的沙盒限制非常严格：

| 操作 | 是否允许 | 说明 |
|------|----------|------|
| 写入 /tmp | ❌ | 即使添加 temporary-exception 也被阻止 |
| Process() 子进程 | ❌ | 无法启动外部命令 |
| NSAppleScript | ❌ | 无法控制其他应用 |
| NSWorkspace.open(file) | ❌ | 无法打开文件/目录 |
| NSWorkspace.open(app) | ✅ | 可以打开应用 |
| NSPasteboard | ✅ | 可以读写剪贴板 |

**推荐方案**：创建一个非沙盒的 Helper App，Extension 把命令放入剪贴板后打开 Helper App，由 Helper App 执行实际操作。

### Helper App 示例

```bash
mkdir -p "/Applications/OpenCCHelper.app/Contents/MacOS"
cat > "/Applications/OpenCCHelper.app/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key><string>run.sh</string>
    <key>CFBundleIdentifier</key><string>com.lovstudio.OpenCCHelper</string>
    <key>LSUIElement</key><true/>
</dict>
</plist>
EOF

cat > "/Applications/OpenCCHelper.app/Contents/MacOS/run.sh" << 'EOF'
#!/bin/bash
CMD=$(pbpaste)
osascript << APPLESCRIPT
tell application "iTerm"
    activate
    tell current window
        create tab with default profile
        tell current session
            write text "$CMD"
        end tell
    end tell
end tell
APPLESCRIPT
EOF
chmod +x "/Applications/OpenCCHelper.app/Contents/MacOS/run.sh"
```

Extension 中调用：
```swift
let command = "cd '\(targetPath)' && claude"
NSPasteboard.general.clearContents()
NSPasteboard.general.setString(command, forType: .string)
NSWorkspace.shared.open(URL(fileURLWithPath: "/Applications/OpenCCHelper.app"))
```

## 其他已知限制

- **Bundle ID 不能含下划线**：使用连字符或驼峰命名（`OpenCC` 而非 `open_cc`）
- **NSHomeDirectory() 返回容器路径**：沙盒中返回 `~/Library/Containers/<bundle-id>/Data/`，监控目录需硬编码真实路径
- **NSMenuItem 必须设置 target**：`item.target = self`，否则 action 不会触发
- Finder Extension 菜单项位置由系统决定，无法排在「新建文件夹」之前
- Quick Action 环境没有 `$PATH`，工具路径必须用绝对路径
- Automator workflow 需在 Automator 中打开保存才能注册
- Extension 使用 ad-hoc 签名，仅限本机使用
