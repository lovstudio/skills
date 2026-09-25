# 网页截图导出 · Web Capture Export

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

给任意静态 HTML 网页加一个右下角「导出图片」按钮，点击即用 modern-screenshot
把主体内容导出为 PNG——截图与屏幕渲染一致（文字不换行）、2x 分辨率适合网络传播。

## 本地安装

按 Lovstudio 三层 symlink 链安装（真源 → `~/.agents/skills` → `~/.claude/skills`）：

```bash
SRC="$(pwd)"                                   # 真源 = integrate-modern-screenshot-skill
ln -sfn "$SRC" "$HOME/.agents/skills/lov-integrate-modern-screenshot"
ln -sfn "../../.agents/skills/lov-integrate-modern-screenshot" \
          "$HOME/.claude/skills/lov-integrate-modern-screenshot"
readlink -f "$HOME/.claude/skills/lov-integrate-modern-screenshot"  # 应解析到真源
```

## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享 Profile
读取用户、品牌、工作区和本 Skill 的长期记录（默认缩放、默认宽度等）。用户直接
说出的持久偏好由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

集成一个 HTML 报表并端到端验证：

```bash
python3 scripts/integrate_screenshot.py integrate 报表.html --scale 2
python3 scripts/integrate_screenshot.py verify 报表.html \
  --scale 2 --chrome "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# → OK out=1520x2998 node=760x1499 expect=1520x2998
```

指定主体内容选择器（tag / `#id` / `.class`）与下载文件名：

```bash
python3 scripts/integrate_screenshot.py integrate 看板.html \
  --selector ".dashboard" --width 900 --scale 2 --title "数据看板-2026-08-20.png"
```

内置冒烟自测：

```bash
python3 scripts/integrate_screenshot.py self-test --chrome "$(which chrome)"
```

## 原子组合

每个新 Skill 都带有 `references/skill-composition.md`。它记录已检查的相邻 Skills
（`lov-rich-export` 为可选上游、`lov-png2svg` 为可选下游）、交接边界，以及为何选择
Single Skill。外部 sibling Skill 不作为隐藏依赖。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md`：用途、负责人、依赖、风险、输出与维度地图。
- `cases/cases.json`：真实案例——给《手工川 DSH 剪辑成本审计》HTML 加一键导出 PNG。
- `pricing-card.yaml`：免费但写清价值锚点、交付边界与复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+（CLI 仅用标准库）
- 端到端验证需 headless Chrome/Chromium
- modern-screenshot v4.5.1 已内联于 `assets/`，无 CDN 依赖

## License

MIT
