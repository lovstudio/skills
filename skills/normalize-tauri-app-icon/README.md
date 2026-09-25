# Tauri 图标校准 · Tauri Icon Alignment

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

将 Tauri macOS Dock 图标的可见外框与参考图标对齐，并验证新 `.icns` 已实际嵌入开发运行时。

## 本地安装

本 Skill 已按标准目录结构设计；在任意兼容 Agent 中可建立本地链接：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILL_SKILLS_INSTALL_DIR/lov-normalize-tauri-app-icon"
```

## 使用

### 用参考图标校准视觉外框

```bash
python3 scripts/tauri_app_icon.py measure --input reference.png
python3 scripts/tauri_app_icon.py normalize \
  --input target.png \
  --reference reference.png \
  --output target-normalized.png
python3 scripts/tauri_app_icon.py measure --input target-normalized.png
```

输出 JSON 会给出 alpha 可见边界、可见比例和输出文件，适合写入验收记录。

### 验证 Tauri 开发模式实际使用的新图标

```bash
python3 scripts/tauri_app_icon.py verify-build-watch \
  --build-rs src-tauri/build.rs \
  --watch icons/app/icon.icns \
  --watch icons/app/icon.png

python3 scripts/tauri_app_icon.py verify-embed \
  --source-icns src-tauri/icons/app/icon.icns \
  --build-out src-tauri/target/debug/build
```

若最后一条命令没有返回匹配项，说明资源可能已更新，但当前调试二进制尚未嵌入它。

## 原子组合

本 Skill 不把 Logo 设计、SVG 矢量化、Tauri 初次安装或发版变成隐式依赖。与现有
Skills 的上游、下游与重叠边界见 [`references/skill-composition.md`](references/skill-composition.md)；它明确了每个交接的文件合同与最终验收归属。

## Profile 合同

`skill.yaml` 声明了 `user-profile/v1`。仅当用户明确要求长期保留某个参考图标或可见比例时，使用 `scripts/profile_store.py` 将它保存到本 Skill 的 `records.*`；源代码不保存用户路径或图形资产。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

质量门检查结构、引用、Profile 合同、Skill Card、真实案例、定价依据和分发状态。运行时验收还需完成 `verify-embed` 及同一 Dock 状态下的视觉比较。

## 依赖

- Python 3.8+
- `Pillow>=9.0`
- PyYAML
- 目标项目提供的 Tauri CLI

## License

MIT
