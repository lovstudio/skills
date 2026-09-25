# Cover Prompt Publication

Treat the cover production prompt and the article-visible prompt as separate artifacts.

## Skill-owned production template

封面生产 Prompt 的源文件属于 branding skill 本身，见
[Hero editorial painterly Prompt](../prompts/cover-hero-editorial-painterly.md)。执行封面管线时，
先读取该模板，再结合文章命题、用户配置和最终素材策略生成本次完整 Prompt；输出目录中的
`cover-production-prompt.md` 只是本次执行的实例，不是唯一来源。

## Options

```json
{
  "opening_hero": {
    "enabled": true,
    "ratio": "3:4",
    "placement": "before_intro",
    "marker": "opening-hero"
  },
  "cover_prompt": {
    "enabled": true,
    "placement": "before_endcap",
    "title": "封面 Prompt",
    "marker": "cover-prompt"
  }
}
```

For the `full` branding pipeline, both options are enabled by default. A current request or resolved user configuration can explicitly disable either one; enabling one does not enable the other.

## Production and reader prompts

Preserve the production prompt as an internal artifact with the full composition, crop, source, editing, and output requirements. Derive the reader prompt from the final method actually used. The production prompt must inherit the skill-owned template's resolved direction (`hero`, `editorial`, `painterly`, `text: none`, and a center-safe zone) unless the user explicitly selects another direction.

Remove from the reader prompt:

- local and temporary file paths;
- internal conversation context and working notes;
- tool names, retry history, and intermediate failures;
- claims that a supplied artwork or deterministic Logo composition came from text generation alone;
- private brand facts or unpublished source material.

Retain in the reader prompt:

- intended asset type and aspect ratio;
- subject, composition, visual hierarchy, palette, and rendering language;
- Logo placement and the requirement to use the official `publication.logo` asset without redrawing it or substituting a studio/product mark;
- meaningful negative constraints;
- required public-domain or licensed input artwork when reproduction depends on it.

## Article block

Render only a heading and one directly copyable prompt block. Use `data-lov-block="cover-prompt"` as the unique marker. Place the block after the article conclusion and before the stable brand endcap by default; the `full` pipeline publishes it unless explicitly disabled. Do not add a process diary, model commentary, or reuse instructions around it.

## Opening hero

By default, create a vertical reading-oriented image rather than reusing the sharing cover without review. Use `3:4`, place the official publisher Logo from `publication.logo` near the lower center, preserve a single visual focal point, and insert the block before the introduction with `data-lov-block="opening-hero"`. It must be the first body block; when the platform title is already visible, do not emit a duplicate body `h1` before or after it. Keep it outside introduction cards, blockquotes, borders, and colored content containers. An explicit `opening_hero.enabled: false` skips this block.

## Validation

- Confirm each enabled block appears exactly once.
- Confirm the opening hero is the first article body block and uses the expected CDN asset after reload.
- Confirm the reader prompt matches the final cover method and contains no private path.
- Confirm title, digest, sharing cover, TOC, article body, and endcap remain unchanged unless separately authorized.
