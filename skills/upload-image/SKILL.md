---
name: lov-upload-image
description: >
  复用用户现有 PicGo 配置上传一张或多张本地图片并返回网址，也可批量把 Markdown 内的本地图片引用改成在线地址；适用于“上传这张图”“替换 md 图片链接”或 "upload images with PicGo"。
license: MIT
metadata:
  author: skill-publisher
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - picgo
    - image-upload
    - markdown
    - local-assets
    - url-rewrite
  compatibility: "Portable Agent Skills format; Python 3.8+ and PicGo GUI Server or PicGo-Core CLI."
  dependencies:
    - python3
    - picgo
---

# 图片上云 · Image Uploader

Turn local image files into public URLs through the user's existing PicGo
configuration. It can return URLs directly or create a Markdown copy whose local
image references have been replaced safely and consistently.

## Triggers

### Activate when

- 用户说“把这张本地图片上传并给我网址”“用 PicGo 上传这些图片”。
- 用户说“把这个 md 里的本地图片全部换成线上地址”“批量上传 Markdown 图片”。
- The user asks to “upload this image with PicGo” or “replace local Markdown image paths with online URLs”.

### Do not activate when

- 用户要生成、编辑、压缩或翻译图片，但不要求上传；交给对应图片处理能力。
- 用户指定发布到微信公众号、博客 CMS 或其他会返回平台素材 ID 的渠道；由目标平台 Skill 管理其上传协议。
- 用户只想下载远程图片到本地，或只想修复普通 Markdown 超链接。

## Product Contract

- Reuse PicGo's selected uploader, plugins, naming rules, and existing credentials.
- Prefer the PicGo Server API because it shares the running GUI configuration.
  Fall back to PicGo-Core CLI only when the Server is unavailable and a CLI exists.
- Never read, print, copy, or persist image-host credentials. A protected PicGo
  Server secret may only come from the environment variable named by
  `--secret-env`, defaulting to `PICGO_SERVER_SECRET`.
- Validate every local Markdown reference before uploading any file. Missing files
  stop the run before remote state changes.
- Deduplicate identical local files during one Markdown run and preserve reference
  order when mapping returned URLs.
- Write Markdown only after all uploads and optional URL checks pass. The default
  output is a new `.uploaded.md` file; in-place mode is explicit and makes a backup.
- Report a URL only when PicGo returns a valid absolute HTTP or HTTPS address.

## User Profile (cross-session)

Read `skill.yaml` and the shared `user-profile/v1` context at the start of every
run. Resolve settings in this order: current request, environment, Skill records,
shared preferences, then safe defaults.

Supported durable records are `records.server_url`, `records.backend`, and
`records.markdown_write_mode`. Save them with `scripts/profile_store.py` only
when the user directly asks for a lasting default. Never persist a Server secret,
image-host key, token, cookie, or inferred value. See
`references/user-profile.md` for the full contract.

## Skill Group Composition

Read `references/skill-composition.md` before composing adjacent capabilities.
This Skill owns only the local-image-to-public-URL and Markdown-rewrite outcome.
Image creation may happen upstream and destination-specific publishing may happen
downstream, but neither is a hidden runtime dependency.

## Workflow (MANDATORY)

### Step 0: Resolve runtime and PicGo

1. Resolve `SKILL_DIR` from the active Skill context or installed path.
2. Read `skill.yaml` and resolve `server_url`, `backend`, and write mode using the
   precedence above. Default to `http://127.0.0.1:36677`, `auto`, and new-file mode.
3. Run the non-mutating preflight:

   ```bash
   python3 "$SKILL_DIR/scripts/upload_image.py" doctor --json
   ```

4. When PicGo.app is installed but not running, add `--start-app` to the requested
   upload command. If Server mode is disabled, ask the user to enable PicGo Server
   or provide a configured PicGo-Core CLI; do not install or reconfigure an image
   host silently.

Read `references/picgo-integration.md` for backend selection and error semantics.

### Step 1: Preflight inputs

- Resolve paths without moving or editing source images.
- For Markdown, run `--dry-run --json` first and inspect `references`,
  `unique_files`, and the resolved file list.
- Treat HTTP(S), protocol-relative, `data:`, `blob:`, anchors, fenced code, and
  inline code as non-local and leave them unchanged.
- Stop before upload if any discovered local image does not exist.

Read `references/markdown-coverage.md` for supported reference forms.

### Step 2A: Upload one or more images

Run:

```bash
python3 "$SKILL_DIR/scripts/upload_image.py" upload \
  "/path/to/image.png" \
  --verify \
  --json
```

For one image without `--json`, stdout is exactly the returned URL. For multiple
images, use JSON when another tool will consume the result. Preserve the input to
URL mapping from the `uploaded` array.

### Step 2B: Upload and rewrite Markdown images

Preflight, then execute:

```bash
python3 "$SKILL_DIR/scripts/upload_image.py" markdown \
  "/path/to/article.md" \
  --dry-run \
  --json

python3 "$SKILL_DIR/scripts/upload_image.py" markdown \
  "/path/to/article.md" \
  --verify \
  --json
```

The second command writes `article.uploaded.md`. Use `--output PATH` for another
new file. Use `--in-place` only when the user explicitly wants the source edited;
it creates `article.md.bak` unless `--no-backup` is also explicit. Never use
`--force` without first resolving the exact output target.

### Step 3: Validate and report

- With `--verify`, require a successful HEAD or ranged GET response for every URL.
- For Markdown, read back the output and confirm that the reported number of local
  references changed, already-remote references stayed unchanged, and no local
  source path remains outside examples or code blocks.
- Report the returned URL or output document path, upload count, rewritten
  reference count, backup path when applicable, and any verification gap.
- A PicGo success does not grant permission to upload private, licensed, or secret
  images. Confirm the user controls the material when that is not evident.

## Error Contract

Failures use this copyable form on stderr:

```text
ERROR context_id=lov-upload-image-xxxxxxxx code=category: concise diagnosis
```

The script exits before Markdown writes when upload or verification fails. An
upload can still have created remote objects before a later verification failure;
report that possibility instead of claiming rollback.

## Dependencies

- Python 3.8+ standard library; PyYAML is only needed for the Skill validator.
- One configured PicGo backend: a running GUI/Core Server API, or PicGo-Core CLI.
- Network access to the selected image host and, when requested, returned URLs.
