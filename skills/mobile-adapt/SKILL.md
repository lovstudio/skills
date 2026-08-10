---
name: lov-mobile-adapt
description: >
  Adapt an existing web project for mobile devices: fix overflow, add responsive
  layouts, convert to multi-level page navigation with back support, handle
  notch/Dynamic Island safe areas, fix 100vh browser chrome issues, and optimize
  touch targets. Trigger when user says "mobile adapt", "移动端适配",
  "responsive optimization", "手机适配", "fix mobile overflow", "add safe area",
  "多级页面", "移动端布局", or mentions adapting a site for phones/tablets.
license: MIT
compatibility: >
  Requires Python 3.8+ (no external dependencies).
  Works with any web project: React, Vue, Next.js, Nuxt, Svelte, plain HTML/CSS.
metadata:
  author: lovstudio
  version: "0.1.0"
  tags: mobile, responsive, safe-area, overflow, navigation
---

# mobile-adapt — Mobile-First Adaptation for Web Projects

Scan and fix mobile adaptation issues in an existing web project: viewport
configuration, overflow prevention, safe area handling, responsive breakpoints,
100vh pitfalls, touch targets, and multi-level page navigation.

## When to Use

- Converting a desktop-first site to work well on mobile
- User reports overflow, cut-off content, or notch overlap on phones
- Adding mobile navigation (back button, page stack) to a sidebar-based layout
- Fixing 100vh issues on iOS/Android browsers
- General "make it mobile friendly" requests

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

Resolve `SKILL_DIR` from the installed skill context before running the helper.
For manual execution, set it to the directory containing this `SKILL.md`.

### Step 1: Scan the Project

Run the scanner to identify issues:

```bash
python3 "$SKILL_DIR/scripts/scan_mobile_issues.py" <project-path>
```

For JSON output (easier to process programmatically):

```bash
python3 "$SKILL_DIR/scripts/scan_mobile_issues.py" <project-path> --format json
```

Review the output. The scanner checks:
- viewport meta tag presence and `viewport-fit=cover`
- CSS overflow risks (fixed widths, min-width)
- 100vh usage (should be 100dvh)
- safe-area-inset usage on fixed/sticky elements
- Touch target sizes (< 44px)
- Responsive breakpoint coverage
- Tailwind-specific issues (h-screen → h-dvh)
- Text overflow without ellipsis handling

### Step 2: Ask the User

**IMPORTANT: Use `AskUserQuestion` to collect scope BEFORE making changes.**

Present the scan results summary, then ask:

```
Question: "扫描发现 X 个问题。要修哪些类别?"
Options:
  1. 全部修复 (Recommended) — fix all categories found
  2. 只修布局和溢出 — overflow + responsive only
  3. 只修导航 — convert to mobile stack navigation
  4. 让我选具体类别 — pick specific categories
```

If the project has sidebar/tab navigation on desktop, also ask:

```
Question: "桌面端的侧边栏/tab 导航要改成移动端多级页面吗?"
Options:
  1. 是,改成 push/pop 页面栈 (Recommended)
  2. 改成底部 tab bar
  3. 不改导航结构
```

### Step 3: Fix Issues

Apply fixes in this priority order:

1. **Viewport meta** — add or fix `<meta name="viewport">` with `viewport-fit=cover`
2. **Global overflow guard** — add `overflow-x: hidden` to html/body
3. **100vh → 100dvh** — replace all 100vh usages, add fallback
4. **Safe area padding** — add `env(safe-area-inset-*)` to fixed/sticky elements
5. **Image/media overflow** — add `max-width: 100%; height: auto`
6. **Text overflow** — add ellipsis/line-clamp where `white-space: nowrap` exists
7. **Touch targets** — increase size of interactive elements below 44px
8. **Responsive breakpoints** — add mobile-first media queries or Tailwind responsive
9. **Navigation restructure** — convert to mobile page stack if requested

For each fix, refer to `references/mobile-patterns.md` for the correct pattern.

### Step 4: Navigation Restructure (if applicable)

When converting sidebar/panel navigation to mobile stack:

1. Identify the navigation structure (sidebar, tabs, nested panels)
2. Create a responsive layout wrapper that switches between desktop and mobile
3. On mobile: render as a full-screen page stack with back button
4. Use CSS slide transitions for page push/pop
5. Preserve desktop layout unchanged at `md:` breakpoint and above

See `references/mobile-patterns.md` → "Multi-Level Page Navigation" for
implementation patterns per framework.

### Step 5: Verify

After all fixes:

1. Re-run the scanner — confirm issues resolved
2. Check the site in a mobile viewport (375px width)
3. Verify:
   - No horizontal scroll
   - Content not cut off by notch or home indicator
   - All interactive elements are tappable (44px+)
   - Navigation back button works
   - Full-height layouts don't overflow behind browser chrome

## CLI Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `project` | (required) | Path to web project root |
| `--format` | `text` | Output format: `text` or `json` |

## Key Patterns (quick reference)

| Problem | Fix |
|---------|-----|
| Missing viewport meta | `<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">` |
| 100vh overflow | `height: 100dvh` (with `100vh` fallback) |
| Notch overlap | `padding: env(safe-area-inset-top)` on fixed elements |
| Horizontal overflow | `overflow-x: hidden` on body + `max-width: 100%` on media |
| iOS input zoom | `font-size: 16px` on inputs |
| Small touch targets | `min-height: 44px; min-width: 44px` |
| Pull-to-refresh conflict | `overscroll-behavior-y: contain` |

For detailed patterns see `references/mobile-patterns.md`.
