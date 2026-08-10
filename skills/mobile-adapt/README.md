# lov-mobile-adapt

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

Scan and fix mobile adaptation issues in web projects: viewport, overflow, safe area, responsive layouts, 100vh pitfalls, touch targets, and multi-level page navigation.

Independent source repository, also distributed through [lovstudio skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/mobile-adapt-skill --all -g
```

The aggregate bundle remains available:

```bash
npx skills add lovstudio/skills --all -g
```

Or through Claude Code plugin marketplace:

```text
/plugin marketplace add lovstudio/skills
/plugin install dev-tools@lov-dev
```

Requires: Python 3.8+ (no external dependencies)

## What It Does

1. **Scans** your project for mobile issues (overflow, viewport, safe area, touch targets)
2. **Asks** which categories to fix
3. **Applies** fixes following modern best practices (dvh, env(), container queries)
4. **Restructures** navigation into mobile page stack with back support (optional)
5. **Verifies** fixes by re-scanning

## Scanner

```bash
python3 ~/.claude/skills/lov-mobile-adapt/scripts/scan_mobile_issues.py /path/to/project
```

| Option | Default | Description |
|--------|---------|-------------|
| `project` | (required) | Path to project root |
| `--format` | `text` | Output: `text` or `json` |

Checks: viewport meta, overflow risks, 100vh usage, safe-area-inset, touch target sizes, responsive breakpoints, Tailwind-specific issues, text overflow.

## Covered Issues

| Category | What gets fixed |
|----------|----------------|
| Viewport | Missing/incorrect meta viewport, viewport-fit=cover |
| Overflow | Fixed widths, horizontal scroll, image overflow, text overflow |
| Viewport units | 100vh → 100dvh with fallback |
| Safe area | env(safe-area-inset-*) on fixed/sticky elements |
| Touch targets | Interactive elements below 44px minimum |
| Responsive | Missing breakpoints, mobile-first media queries |
| Navigation | Sidebar → mobile page stack with back button |
| Browser chrome | theme-color, status bar, input zoom, pull-to-refresh |

## License

MIT
