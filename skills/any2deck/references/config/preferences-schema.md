# EXTEND.md Schema

Structure for user preferences in `.lovstudio-skills/lovstudio-any2deck/EXTEND.md`.

## Full Schema

```yaml
# Slide Deck Preferences

## Defaults
style: blueprint              # Preset name OR "custom"
audience: general             # beginners | intermediate | experts | executives | general
language: auto                # auto | en | zh | ja | etc.
review: true                  # true = review outline before generation

## Custom Dimensions (only when style: custom)
dimensions:
  texture: clean              # clean | grid | organic | pixel | paper
  mood: professional          # professional | warm | cool | vibrant | dark | neutral
  typography: geometric       # geometric | humanist | handwritten | editorial | technical
  density: balanced           # minimal | balanced | dense

## Custom Styles (optional)
custom_styles:
  my-style:
    texture: organic
    mood: warm
    typography: humanist
    density: minimal
    description: "My custom warm and friendly style"

## Branding (optional, opt-in)
branding:
  logo: /path/to/logo.png       # Required to enable logo compositing (PNG or JPG)
  logo2: /path/to/logo2.png     # Optional secondary logo (placed left of primary)
  logo2_gap: 32                 # Gap between two logos in px (default: 32)
  logo_height: 46               # Logo height in px (default: 46)
  pad_top: 20                   # Top padding (default: 20)
  pad_right: 26                 # Right padding (default: 26)
  skip_slides: [1]              # Slides to skip (cover etc.); defaults to [1] + last slide
  qr_code: /path/to/qr.png      # Optional QR to composite into final slide
  qr_slide: 0                   # Slide number for QR placement
  qr_box: [990, 229, 1250, 507] # X1,Y1,X2,Y2 of placement area in px
```

## Field Descriptions

### Defaults

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `style` | string | `blueprint` | Preset name, `custom`, or custom style name |
| `audience` | string | `general` | Default target audience |
| `language` | string | `auto` | Output language (auto = detect from input) |
| `review` | boolean | `true` | Show outline review before generation |

### Custom Dimensions

Only used when `style: custom`. Defines dimension values directly.

| Field | Options | Default |
|-------|---------|---------|
| `texture` | clean, grid, organic, pixel, paper | clean |
| `mood` | professional, warm, cool, vibrant, dark, neutral | professional |
| `typography` | geometric, humanist, handwritten, editorial, technical | geometric |
| `density` | minimal, balanced, dense | balanced |

### Custom Styles

Define reusable custom dimension combinations.

```yaml
custom_styles:
  style-name:
    texture: <texture>
    mood: <mood>
    typography: <typography>
    density: <density>
    description: "Optional description"
```

Then use with: `/lovstudio-any2deck content.md --style style-name`

## Minimal Examples

### Just change default style

```yaml
style: sketch-notes
```

### Prefer no reviews

```yaml
review: false
```

### Custom default dimensions

```yaml
style: custom
dimensions:
  texture: organic
  mood: professional
  typography: humanist
  density: minimal
```

### Define reusable custom style

```yaml
custom_styles:
  brand-style:
    texture: clean
    mood: vibrant
    typography: editorial
    density: balanced
    description: "Company brand style"
```

## File Locations

Priority order (first found wins):

1. `.lovstudio-skills/lovstudio-any2deck/EXTEND.md` (project)
2. `$HOME/.lovstudio-skills/lovstudio-any2deck/EXTEND.md` (user)

## First-Time Setup

When no EXTEND.md exists, the skill prompts for initial preferences:

1. Preferred style (preset or custom)
2. Default audience
3. Language preference
4. Review preference
5. Save location (project or user)

Creates EXTEND.md at chosen location.
