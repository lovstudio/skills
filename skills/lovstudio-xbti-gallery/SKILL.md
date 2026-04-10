---
name: lovstudio:xbti-gallery
description: >
  Browse the XBTI Gallery — all community-created BTI personality tests at xbti.lovstudio.ai.
  Trigger when user says "XBTI Gallery", "xbti-gallery", "BTI列表", "浏览人格测试",
  "show BTI cases", or wants to see available BTI variants.
allowed-tools: [Bash, Read]
license: MIT
compatibility: Requires `gh` CLI for listing cases.
metadata:
  author: lovstudio
  version: "1.0.0"
  tags: bti personality-test gallery xbti
---

# xbti-gallery — Browse Community BTI Tests

Open the XBTI Gallery and list all community-created BTI personality tests.

## When to Use

- User wants to browse existing BTI personality tests
- User says "打开 XBTI Gallery" or "show me BTI cases"
- User wants to see what others have created before making their own

## Workflow

### Step 1: Open Gallery

```bash
open https://xbti.lovstudio.ai
```

### Step 2: List Available Cases

Fetch and display all BTI variants from the repository:

```bash
gh api repos/lovstudio/XBTI/contents/cases 2>/dev/null | python3 -c "
import json, sys
try:
    items = json.load(sys.stdin)
    if isinstance(items, list):
        for item in items:
            if item.get('type') == 'dir':
                print(f'  - {item[\"name\"]}')
    else:
        print('  (no cases yet)')
except:
    print('  (unable to fetch)')
"
```

If no cases exist, tell the user: "Gallery 还没有案例，用 `/lovstudio-xbti-creator` 创建一个并提交吧！"
