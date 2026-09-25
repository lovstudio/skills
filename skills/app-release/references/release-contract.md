# Release Contract

Every run is one release transaction spanning only the channels already
declared by the target project or explicitly requested by the user.

## Completion model

| Channel | Intermediate evidence | Completion evidence |
|---|---|---|
| Source | local commit | release commit on remote main |
| GitHub | tag pushed | annotated tag plus published Release and assets |
| Android direct | signed local APK | anonymous download with matching SHA-256 |
| Android store | artifact uploaded | intended track/version code read back |
| iOS | archive uploaded | build valid/eligible, bound, and review submitted |
| Website | provider accepted upload | production deployment ready on custom domain |
| Documentation | files edited | shipped version, URLs, and states agree |

A release may be complete while a store review is pending. “Complete” then
means all release actions were performed and the pending review state was read
back. It does not mean the store listing is public.

## Authority boundary

- Explicit “release”, “发布”, “ship”, or named production channels authorizes
  ordinary release mutations inside that project.
- “Prepare”, “audit”, “plan”, “dry run”, and “先不要发布” stop before push,
  upload, submission, production deployment, or external messages.
- Do not broaden the request to unrelated products, accounts, repositories,
  pricing changes, or new providers.
- Existing paid-app pricing is preserved unless the user requests a change.
  Always read it back when an App Store release is submitted.

## Version consistency

Track a single canonical marketing version and platform-specific monotonically
increasing build identifiers.

Typical sources include:

- `package.json`, `pyproject.toml`, `Cargo.toml`, `VERSION`;
- Tauri, Electron, Flutter, Xcode, Gradle, or platform configuration;
- Android `versionName` and `versionCode`;
- iOS `CFBundleShortVersionString` and `CFBundleVersion`;
- website download filenames and visible version labels;
- changelog headings, README, detailed release notes, and tests.

After native generators run, re-read the produced app/APK/IPA instead of
assuming the source manifest won.

## Release ordering

1. Inventory source and live external state.
2. Select and synchronize version/build identifiers.
3. Update changelog, docs, website paths, and tests.
4. Run the full quality gate.
5. Build, sign, and inspect native artifacts.
6. Upload artifacts and wait for platform processing.
7. Commit the immutable release, merge main, tag, and push.
8. Publish GitHub Release and production website.
9. Bind/submit store builds when processing is valid.
10. Read back every channel and report the state matrix.

The exact upload/tag order may follow repository automation, but every public
artifact must be traceable to the same release commit and version.

## Git and concurrent work

- Check the actual worktree and branch before editing.
- Preserve unrelated dirty files and other agents' work.
- Commit only intended release files and artifacts.
- If the release started on a feature branch, merge or fast-forward it into the
  repository's main branch using the project's established policy.
- Once a tag or store build is published, later edits belong to another version.

## Evidence and errors

- Prefer machine-readable API/CLI output over UI text.
- Keep artifact SHA-256, byte size, signing identity summary, version/build,
  processing state, deployment ID, release URL, and commit ID.
- Error reports should include the failing stage, command category, platform
  code, artifact/version, and a copyable concise diagnostic. Redact secrets.
- HTTP 200 alone proves reachability, not that the correct release is present.
  Verify expected text or bytes as well.

## User-visible release notes

Describe observable value: features, fixes, supported systems, and material
behavior changes. Keep internal prompts, credential layout, account operations,
workarounds, and production intent out of public copy.
