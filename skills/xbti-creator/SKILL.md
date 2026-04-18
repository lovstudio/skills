---
name: lovstudio:xbti-creator
category: xBTI
tagline: "Create custom BTI personality tests (LBTI, FBTI, etc.) with AI-generated content + avatars."
description: >
  Create a complete custom BTI personality test (like LBTI, FBTI, etc.) based on the XBTI architecture.
  User provides a theme name and preferences, AI generates all content: dimensions, questions,
  personality types, descriptions, and avatar images via lovstudio:image-creator.
  Trigger when user says "创建BTI", "自定义人格测试", "make a BTI", "custom personality test",
  "XBTI变体", "xbti-creator", or mentions creating something like LBTI/FBTI/etc.
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion]
license: MIT
compatibility: >
  Requires Node.js 18+ and a package manager (pnpm/npm/bun).
  Avatar generation requires lovstudio:image-creator skill and ZENMUX_API_KEY.
metadata:
  author: lovstudio
  version: "1.0.0"
  tags: bti personality-test generator xbti
---

# xbti-creator — Create Your Own BTI Personality Test

Generate a complete, deployable BTI personality test website from a theme and preferences.
Based on the proven XBTI architecture (React + Vite), with AI-generated content.

## When to Use

- User wants to create a themed personality test (e.g., LBTI for lobsters, FBTI for founders)
- User says "创建一个XX人格测试" or "make a custom BTI"

## Workflow (MANDATORY)

### Step 1: Collect Theme Info

**Use `AskUserQuestion` to gather:**

| Field | Example | Required |
|-------|---------|----------|
| BTI名称 | LBTI | Yes |
| 主题 | 龙虾的人格分析 | Yes |
| 风格偏好 | 幽默毒舌 / 温暖治愈 / 学术严肃 | Yes |
| 人格数量 | 16-25（默认20） | No |
| 特殊彩蛋人格 | 有/无（默认有） | No |
| 项目目录 | 默认 ~/projects/{NAME} | No |
| 提交到 Gallery | 是/否（默认否）— 提交到 xbti.lovstudio.ai 供他人体验 | No |

### Step 2: Environment Setup

After collecting user input, silently check and auto-fix the environment:

```bash
# 1. Node.js (required)
node --version  # Need 18+

# 2. Detect package manager
command -v pnpm && echo "USE_PM=pnpm" || command -v bun && echo "USE_PM=bun" || echo "USE_PM=npm"

# 3. git
git --version

# 4. image-creator skill
ls ~/.claude/skills/lovstudio-image-creator/gen_image.py 2>/dev/null && echo "OK" || echo "MISSING"

# 5. Zenmux API key
[ -n "$ZENMUX_API_KEY" ] && echo "OK" || echo "MISSING"

# 6. Python deps
python3 -c "import google.genai; from PIL import Image" 2>/dev/null && echo "OK" || echo "MISSING"
```

**Auto-fix (no user interaction needed for these):**

- `lovstudio:image-creator` missing →
  ```bash
  npx skills add lovstudio/skills --skill lovstudio:image-creator
  ```
- Python deps missing →
  ```bash
  pip install google-genai Pillow --break-system-packages 2>/dev/null || pip3 install google-genai Pillow
  ```

**Require user input only if truly blocked:**

- Node.js missing → tell user to install and stop
- `ZENMUX_API_KEY` missing → ask user to provide it:
  1. 注册 Zenmux: https://zenmux.ai/invite/K6KT2X (邀请码，有免费额度)
  2. 获取 API Key: https://zenmux.ai/settings/keys
  3. 设置: `export ZENMUX_API_KEY="your-key"` (建议加到 ~/.zshrc)

**Do NOT proceed to Step 3 until environment is fully ready.**

### Step 3: Design Dimension System

Based on the theme, design **5 维度模型**, each with **3 子维度** = 15 dimensions total.

**Rules:**
- Dimension names must be thematic (e.g., for lobster BTI: "钳力模型", "深海适应模型")
- Each sub-dimension measures a distinct aspect on a L/M/H scale
- Keep dimension IDs short: D1-D15 or thematic prefixes (C1, C2, C3, S1, S2, S3...)
- Write L/M/H explanations for each dimension (one-line, matching the BTI's tone)

Output: `src/data/dimensions.js` — see `references/xbti-data-format.md` for exact format.

### Step 4: Generate Questions

Generate **30 questions** (2 per dimension), each with **3 options** (value 1, 2, 3).

**Rules:**
- Questions must match the theme and tone
- Option values: 1 = low on that dimension, 2 = medium, 3 = high
- Mix question styles: direct statements, scenarios, hypotheticals
- Include 1-2 memorable/funny questions per model for engagement
- Optionally: add 1-2 special trigger questions for a hidden personality type

Output: `src/data/questions.js`

### Step 5: Design Personality Types

Generate **16-25 personality types**, each with:

| Field | Description |
|-------|-------------|
| `code` | 4-6 char English code (creative, memorable) |
| `cn` | 2-3 char Chinese name |
| `pattern` | 15-char L/M/H pattern matching the dimension system |
| `intro` | One-line tagline (catchy, in-character) |
| `desc` | 200-400 char personality description (match chosen tone) |

**Rules:**
- Codes should be thematic and creative (not generic like TYPE-A)
- Patterns must cover the L/M/H space well — avoid clustering
- Include 1 fallback type (for < 60% match) and optionally 1 hidden type
- Descriptions should be entertaining and shareable — this is what goes viral

Output: `src/data/types.js`

### Step 6: Scaffold the Project

Clone the XBTI template from GitHub and clean up:

```bash
git clone https://github.com/lovstudio/XBTI.git {TARGET_DIR}
cd {TARGET_DIR}

# Remove origin-specific files, keep the engine
rm -rf .git .vercel image/* CHANGELOG.md docs/
mkdir -p image
git init

# Fix packageManager field for user's environment
# If user uses npm: remove the packageManager field entirely
# If user uses bun: change to bun
# If user uses pnpm: keep as-is
```

**packageManager handling** (important for portability):
- The cloned `package.json` has `"packageManager": "pnpm@x.y.z"`
- If user doesn't use pnpm, **remove this field** to avoid errors
- Then run `{PM} install` with whatever package manager the user has

Then overwrite the data files with generated content:
- `src/data/dimensions.js`
- `src/data/questions.js`
- `src/data/types.js`

Update branding in:
- `index.html` — title, meta tags
- `src/components/IntroScreen.jsx` — hero title, subtitle, attribution
- `src/index.css` — theme colors (optional, ask user)
- `package.json` — name, description, remove packageManager if needed

**Keep `src/logic/scoring.js` as-is** — the algorithm is universal. Only update import paths if dimension IDs changed.

### Step 7: Generate Avatar Images

For each personality type, programmatically generate an avatar image using the `lovstudio:image-creator` skill.

**Prompt Crafting (nano-banana-pro style):**

For each personality type, craft a prompt optimized for stylized character generation:

```
[Subject: character visual based on personality], [Action/Pose],
[Environment: thematic background], chibi style character,
cute cartoon illustration, simple flat design, vibrant colors,
white background, centered composition,
best quality, masterpiece, ultra high res, 8k
```

Examples:
- CTRL (控制者): "A confident chibi character with arms crossed, wearing a golden crown, standing on a glowing control panel with buttons and levers, chibi style, cute cartoon illustration, simple flat design, vibrant colors, white background, centered composition, best quality, masterpiece, 8k"
- DEAD (死者): "A peaceful chibi ghost character floating with closed eyes, translucent body, surrounded by ZZZ symbols and stars, chibi style, cute cartoon illustration, simple flat design, soft muted colors, white background, centered composition, best quality, masterpiece, 8k"

**Generation Process:**

1. Craft all prompts (one per personality type), present to user
2. Ask user: "先生成一个预览确认风格，还是直接批量生成全部？"
3. **Preview mode**: Generate one image, show result, iterate on prompt style if needed:
   ```bash
   python3 ~/.claude/skills/lovstudio-image-creator/gen_image.py \
     "PROMPT_HERE" \
     -o {TARGET_DIR}/image/{CODE}.png \
     -q medium --no-open
   ```
4. **Batch mode**: Once style confirmed, loop through all types:
   ```bash
   # For each personality type:
   python3 ~/.claude/skills/lovstudio-image-creator/gen_image.py \
     "PROMPT_FOR_TYPE" \
     -o {TARGET_DIR}/image/{CODE}.png \
     -q medium --no-open
   ```
   Use `Read` tool to display each generated image to user for quick review.

5. Verify all images exist:
   ```bash
   ls -la {TARGET_DIR}/image/
   ```

**IMPORTANT:** All image generation is fully automated via CLI — do NOT ask user to manually download or operate any web UI.

### Step 8: Install & Launch

```bash
cd {TARGET_DIR}

# Install dependencies with user's package manager
{PM} install

# Start dev server
{PM} run dev
# or: npx vite (universal fallback)
```

Tell the user the dev server URL (usually http://localhost:5173) and invite them to test the full flow.

### Step 9: Submit to XBTI Gallery (Optional)

**Skip this step if user chose NOT to submit in Step 1.**

If user chose to submit, create a PR to `lovstudio/XBTI` repo:

```bash
# 1. Fork & clone the XBTI repo
cd /tmp
gh repo fork lovstudio/XBTI --clone
cd XBTI

# 2. Create case directory (follow existing structure: cases/sbti/, cases/cbti/)
CASE_NAME=$(echo "{BTI_NAME}" | tr '[:upper:]' '[:lower:]')
mkdir -p cases/${CASE_NAME}/images

# 3. Copy data files + images
cp {TARGET_DIR}/src/data/dimensions.js cases/${CASE_NAME}/
cp {TARGET_DIR}/src/data/questions.js cases/${CASE_NAME}/
cp {TARGET_DIR}/src/data/types.js cases/${CASE_NAME}/
cp {TARGET_DIR}/image/*.png cases/${CASE_NAME}/images/

# 4. Create index.js (re-export entry point, required by registry)
cat > cases/${CASE_NAME}/index.js << EOF
export const meta = { id: '${CASE_NAME}', name: '${BTI_NAME}', desc: '${THEME}', author: '$(git config user.name)', authorUrl: '' };
export { dimensionMeta, dimensionOrder, DIM_EXPLANATIONS } from './dimensions.js';
export { questions } from './questions.js';
export { TYPE_LIBRARY, TYPE_IMAGES, NORMAL_TYPES } from './types.js';
EOF

# 5. Create case.json (combined metadata + data for static access)
#    Use Node.js to merge all data into a single JSON file:
node -e "
const dim = require('./cases/${CASE_NAME}/dimensions.js');
const q = require('./cases/${CASE_NAME}/questions.js');
const t = require('./cases/${CASE_NAME}/types.js');
const data = {
  meta: { id: '${CASE_NAME}', name: '${BTI_NAME}', desc: '${THEME}', author: '$(git config user.name)', authorUrl: '' },
  ...dim, ...q, ...t
};
require('fs').writeFileSync('./cases/${CASE_NAME}/case.json', JSON.stringify(data, null, 2));
"

# 6. Update cases/registry.js — add import and entry
#    Read current registry, add new import and array entry
# 7. Update cases/index.json — add new case metadata entry

# 8. Create PR
git checkout -b add-case/${CASE_NAME}
git add cases/${CASE_NAME} cases/registry.js cases/index.json
git commit -m "feat: add ${BTI_NAME} case (${THEME})"
git push origin add-case/${CASE_NAME}
gh pr create \
  --repo lovstudio/XBTI \
  --title "feat: add ${BTI_NAME} (${THEME})" \
  --body "$(cat <<'PREOF'
## New BTI Case

- **Name**: {BTI_NAME}
- **Theme**: {THEME}
- **Style**: {STYLE}
- **Types**: {TYPE_COUNT} personality types

Generated with [xbti-creator](https://github.com/lovstudio/skills)
PREOF
)"
```

**Update `cases/registry.js`:** Add `import * as {CASE_NAME} from './{CASE_NAME}';` and append to the CASES array.

**Update `cases/index.json`:** Append `{"id":"{CASE_NAME}","name":"{BTI_NAME}","desc":"{THEME}","author":"...","authorUrl":"..."}` to the array.

Tell user the PR URL and that it will appear on xbti.lovstudio.ai after merge.

```bash
# Clean up
rm -rf /tmp/XBTI
```

## Reference Files

- `references/xbti-data-format.md` — exact data structure format for all files

## Design Principles

1. **Theme consistency** — every element (dimensions, questions, types, avatars) must feel thematic
2. **Shareability** — personality descriptions should be entertaining enough to screenshot and share
3. **Balance** — personality types should cover the spectrum, no type should feel "objectively better"
4. **Humor** — even serious themes benefit from wit in the descriptions
5. **Completeness** — the output should be a fully working, deployable website
