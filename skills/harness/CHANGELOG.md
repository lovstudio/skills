# Changelog

## 0.1.0 — 2026-11-10

- 首个本地版本。一次扫描覆盖三块内容：根 Prompt 与宿主绑定、各宿主已安装的 Skill、
  工作室 Skill 源码（版本号、Git 状态、目录与镜像对照）。
- 本地驾驶舱 `serve`：总览、System Prompt、Skills、工作室、整理五个页签；默认只读，
  `--allow-write` 才能在界面里执行整理。
- 终端摘要 `report`、完整快照 `scan`、单文件只读导出 `export`。
- 整理引擎 `tidy` / `undo` / `journal`：先预览后执行，只增删符号链接或移动条目，逐批记录，可撤销。
- `selftest` 在临时目录上验证扫描、整理、撤销与驾驶舱接口。
