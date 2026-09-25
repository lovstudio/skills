---
name: lov-normalize-tauri-app-icon
description: >
  校准 Tauri macOS Dock 图标的可见外框、圆角安全区与运行时嵌入链路；适用于“Dock 图标太大”“统一 Tauri app icon”或“normalize Tauri app icon”等请求，并输出可复核的资源与运行时证据。
license: MIT
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Edit
metadata:
  author: local skill maintainers
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - tauri
    - app-icon
    - macos
    - dock
    - visual-regression
  compatibility: "Python 3.8+ with Pillow; Tauri CLI for icon generation; macOS for live Dock verification."
  dependencies:
    - "Pillow>=9.0"
    - "PyYAML"
---

# Tauri 图标校准 · Tauri Icon Alignment

把 Tauri macOS 应用图标校准到与参考图标相同的视觉外框，并验证当前运行的原生进程确实嵌入了新图标。完成标准是 Dock 中的实际显示尺寸与资源、构建产物和运行时证据一致。

## Triggers

### Activate when

- 用户说“Dock 里的 Tauri 图标太大/太小”“图标没有圆角”或“把 app icon 对齐到参考应用”。
- 用户说“统一 Tauri app icon 的视觉大小”“检查 macOS Dock 图标为什么没更新”。
- User says “normalize Tauri app icon”, “match the Dock icon size”, or “verify the Tauri icon embedded in dev”.

### Do not activate when

- 用户只需要设计一个新 Logo、品牌图形或插画；交给视觉设计或 Logo 生成能力。
- 用户只要打包、签名、上传或发布桌面应用；交给应用发布能力。
- 用户处理 iOS、Android 或 Windows 的专有图标规范，且不涉及 Tauri/macOS Dock；使用相应平台的图标工作流。

## User Profile (cross-session)

Every invocation reads the shared `user-profile/v1` contract declared in
`skill.yaml`. Resolve current request, project context, Skill records, shared
preferences, and shared user/brand data in that order. Keep the source
portable: do not copy local paths, logos, or private project details into it.

When a user explicitly asks to retain a future calibration choice (for example,
a reference icon or preferred visible-envelope ratio), save it under
`records.*` with `scripts/profile_store.py record --confirm` and report the
saved Profile path. Do not persist inferred values, image contents, credentials,
or private paths. See [`references/user-profile.md`](references/user-profile.md).

## Skill Group Composition

Read [`references/skill-composition.md`](references/skill-composition.md)
before selecting adjacent Logo, SVG, Tauri-install, or release Skills. They are
optional artifact-level handoffs, never hidden runtime dependencies of this
Skill. This Skill owns the final visual-envelope and runtime-embedding
acceptance criterion.

## Workflow (MANDATORY)

**Follow these steps in order. Do not call a resource change complete from a
source-image inspection alone.**

### Step 0: Resolve the project and required evidence

1. Locate the active Tauri project, its `src-tauri/tauri.conf.json`, icon source,
   generated icon directory, `src-tauri/build.rs`, and the currently running
   native executable if one exists.
2. Preserve unrelated dirty worktree changes. Identify the branch and actual
   process working directory before editing.
3. Ask at most one focused question only when neither a reference icon nor a
   target visual ratio can be inferred from screenshots or project assets.
4. Load `references/tauri-icon-runtime.md` before making a runtime conclusion.
5. Load `references/skill-composition.md` and follow its single-owner handoff
   rule before invoking a related Skill.

When running the bundled CLI manually, set the Skill root first:

```bash
export SKILL_DIR="/path/to/lov-normalize-tauri-app-icon"
python3 "$SKILL_DIR/scripts/tauri_app_icon.py" --help
```

### Step 1: Measure visual envelopes, not canvas dimensions

Use alpha bounds to compare the non-transparent silhouette. A 512px canvas
does not establish that two icons look the same size in Dock.

```bash
python3 "$SKILL_DIR/scripts/tauri_app_icon.py" measure --input TARGET.png
python3 "$SKILL_DIR/scripts/tauri_app_icon.py" measure --input REFERENCE.png
```

Record the `visible_side`, `visible_ratio`, corner alpha, and the screenshot
pixel bounds when available. If the target has opaque square corners but the
requested result needs a rounded macOS silhouette, correct the artwork first;
the normalizer preserves the supplied alpha shape and does not invent a logo.

### Step 2: Normalize from an explicit reference or ratio

Prefer an approved reference icon. The normalizer centers the visible alpha
envelope on a square transparent canvas and scales it to the reference ratio.
It refuses to overwrite an output unless `--force` is explicit.

```bash
python3 "$SKILL_DIR/scripts/tauri_app_icon.py" normalize \
  --input TARGET.png \
  --reference REFERENCE.png \
  --output normalized-icon.png
```

If no reference asset exists, use a measured target ratio and state where it
came from:

```bash
python3 "$SKILL_DIR/scripts/tauri_app_icon.py" normalize \
  --input TARGET.png \
  --target-visible-ratio 0.805 \
  --output normalized-icon.png
```

Re-run `measure` on the output and report both ratios. Do not silently round a
ratio or claim visual equivalence without a tolerance.

### Step 3: Regenerate the entire Tauri icon set

Generate the platform set from the normalized canonical source rather than
editing only one PNG. Use the project’s existing Tauri CLI and output layout:

```bash
pnpm tauri icon normalized-icon.png -o src-tauri/icons/<icon-set>
```

Update `bundle.icon` in `src-tauri/tauri.conf.json` so macOS points to the
generated `.icns` and Unix/default-window paths point to the generated PNGs.
Keep any other platform entries coherent with the project’s current bundle
contract. Review generated asset alpha bounds at the largest available size.

### Step 4: Verify the dev-runtime embedding path

Tauri macOS development builds can embed an application icon into the native
executable. A later on-disk `.icns` replacement is insufficient if Cargo did
not rerun the build script.

1. Inspect the generated Tauri context or build output to identify the actual
   development app-icon input.
2. Ensure `src-tauri/build.rs` declares each embedded icon input, for example:

   ```rust
   println!("cargo:rerun-if-changed=icons/<icon-set>/icon.icns");
   println!("cargo:rerun-if-changed=icons/<icon-set>/icon.png");
   tauri_build::build()
   ```

3. Verify the declarations without mutating source:

   ```bash
   python3 "$SKILL_DIR/scripts/tauri_app_icon.py" verify-build-watch \
     --build-rs src-tauri/build.rs \
     --watch icons/<icon-set>/icon.icns \
     --watch icons/<icon-set>/icon.png
   ```

4. Respect the project’s active development flow. Do not launch a competing
   GUI process or seize foreground control. Let the existing dev runner rebuild
   or use the project’s native restart path.
5. After the new binary exists, prove the compiled build output contains the
   same raw `.icns` bytes:

   ```bash
   python3 "$SKILL_DIR/scripts/tauri_app_icon.py" verify-embed \
     --source-icns src-tauri/icons/<icon-set>/icon.icns \
     --build-out src-tauri/target/debug/build
   ```

`verify-embed` returning no match means the result is resource-only, not a
verified Dock fix.

### Step 5: Perform a restrained live Dock check

Compare target and reference in the same Dock state, display scale, and zoom
level. Prefer a user-provided screenshot or a non-intrusive capture. Do not use
input automation to bring another app to front solely to reveal the Dock.

Accept visual alignment only when both the measured screenshot envelope and
the source ratio are within an agreed tolerance (normally one Dock pixel or
one point). If the source and embedded icon match but the Dock still differs,
separate system presentation/cache behavior from resource and build evidence
before changing the artwork again.

### Step 6: Report the result and evidence gap

Report:

- canonical source, generated icon set, and configuration paths;
- target/reference visible ratios and final screenshot envelope;
- the active executable timestamp or process identity;
- `verify-build-watch` and `verify-embed` outcomes;
- whether the result is `resource_ready`, `runtime_embedded`, or
  `dock_visually_verified`.

For CLI failures, include the script’s copyable `context_id`, field name, and
safe diagnostic details. Do not expose secrets or unrequested private paths.

## Dependencies

- Python 3.8+
- `Pillow>=9.0` for deterministic RGBA/alpha-bound measurement and PNG output
- PyYAML for `scripts/validate_skill.py`
- A Tauri CLI supplied by the target project for full icon-set generation
- macOS only when validating the live Dock presentation
