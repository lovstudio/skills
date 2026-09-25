# Tauri macOS 图标运行时参考

## 先区分三层事实

Tauri 图标问题至少有三层，必须分别验证：

1. **资源层**：canonical artwork 和生成的 PNG/ICNS 是否具备正确的 alpha 外框、圆角和安全区。
2. **构建层**：`tauri.conf.json`、Tauri context 生成和 Cargo build script 是否重新读取这些资源。
3. **呈现层**：当前 macOS Dock 所属的原生进程是否使用新嵌入图标，并在与参考图标相同的 Dock 状态下显示。

资源层正确不等于构建层更新；构建层更新不等于正在运行的进程已经重新启动；进程已重启也不等于不同 Dock 缩放、缓存和显示器状态下的截图可以直接对比。

## 可见外框而非画布尺寸

对 RGBA 图标，视觉主体通常由 alpha 大于零的最小包围盒决定。令：

```text
visible_side = max(alpha_bbox_width, alpha_bbox_height)
visible_ratio = visible_side / canvas_side
```

同为 `512 × 512` 的两个文件，`visible_ratio` 分别为 `480/512` 和
`412/512` 时，后者在同一 Dock 缩放下理论上约为前者的 `412/480`。截图
测量应在相同的 Dock 放大状态、显示器缩放和活动状态下进行。

透明圆角是否存在也要独立检查。把一个 opaque 方形整体缩小，只会得到更小
的方形；它不会生成合格的圆角 artwork。

## Tauri 的开发模式图标

不同 Tauri 版本与 target 可能选择不同输入，但 macOS development context
通常会把 bundle icon 中的 `.icns` 原始数据嵌入 native executable；Unix 的
default window icon 通常走 PNG。不要凭印象固定某一个路径，应该检查：

- 项目的 `src-tauri/tauri.conf.json` 中 `bundle.icon`；
- 本机实际解析到的 Tauri build/codegen 输出；
- `src-tauri/target/debug/build/<crate>/out/` 中的图标副本；
- 实际 `target/debug/<app>` 的生成时间和运行 PID。

如果 `.icns` 资源在 native binary 之后才更新，而 Cargo 没有重新运行 build
script，Dock 仍会显示旧内嵌图标。显式的 `cargo:rerun-if-changed` 声明使
icon-only 改动成为可追踪的 build input。

## 最小验收链

```text
reference / target alpha measurement
  -> normalized canonical PNG
  -> Tauri icon-set regeneration
  -> tauri.conf.json path review
  -> build.rs icon watch verification
  -> native dev binary regeneration
  -> source ICNS SHA equals build-output copy
  -> same-state Dock visual comparison
```

在最后一步之前，结果应明确标为 `resource_ready` 或 `runtime_embedded`，不要
写作已完成 Dock 视觉验收。

## 失败分类

| 观察 | 最可能层 | 下一步 |
| --- | --- | --- |
| alpha 外框仍比参考大 | 资源层 | 重新按参考 ratio 归一化或修正 artwork。 |
| 资源已变但 binary 时间未变 | 构建层 | 检查 `build.rs` 的 rerun 输入和当前 dev runner。 |
| binary 已更新但 build output 无同 SHA 的 `.icns` | 构建层 | 检查 `bundle.icon` 和 Tauri codegen 的实际选择。 |
| 资源与嵌入都匹配，Dock 仍不同 | 呈现层 | 在同一 Dock 状态下复核，并调查缓存或系统 mask。 |

## 交互边界

处理已运行项目时，先确认实际 native process 的 cwd、binary timestamp 和
parent dev runner。不要为了展示 Dock 而用输入自动化强行抢占前台；优先使用
用户提供截图、非侵入式捕获或项目本身的原生重启路径。
