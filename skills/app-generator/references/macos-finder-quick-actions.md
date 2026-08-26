# macOS Finder Quick Actions

Read this reference whenever the brief asks for a Finder right-click action,
Finder Quick Action, or a packaged macOS app extension.

## Surface contract

For an operation on selected Finder files or folders, `Finder right-click menu`
means the **Quick Actions** submenu by default. Completion requires the action to
appear there and in Finder's Preview pane. An implementation visible only under
**Services** does not satisfy the request.

Use a traditional Service only when the user explicitly needs system-wide processing
of selected content in arbitrary apps, replacement of the current selection, or a
Services keyboard shortcut.

Do not classify the surface from names alone:

- A headless Action Extension can use `com.apple.services`.
- Automator Quick Actions can be stored in `Library/Services`.
- `NSExtensionServiceAllowsFinderPreviewItem = YES`, Finder extension enablement,
  and runtime menu placement distinguish a Finder Quick Action.

## Host decision

Prefer a native Swift/SwiftUI containing app when the Quick Action is the product's
primary capability. It provides the most direct Xcode target, embedding, entitlement,
signing, and App Store/notarization path.

Use a Tauri host only when the browser-rendered interface is material to the product.
In that case, add a native Swift Action Extension and a macOS packaging layer that
places the signed `.appex` in the final app's `Contents/PlugIns` directory. A standalone
workflow installed into the user's Services directory is not a replacement for the
packaged extension.

## Required implementation

Create a macOS Action Extension target and configure its `Info.plist`:

```xml
<key>NSExtension</key>
<dict>
  <key>NSExtensionAttributes</key>
  <dict>
    <key>NSExtensionActivationRule</key>
    <!-- Use precise UTType and selection-count conditions. -->
    <dict>...</dict>
    <key>NSExtensionServiceAllowsFinderPreviewItem</key>
    <true/>
    <key>NSExtensionServiceFinderPreviewLabel</key>
    <string>Localized action label</string>
    <key>NSExtensionServiceFinderPreviewIconName</key>
    <string>QuickActionIcon</string>
  </dict>
  <key>NSExtensionPointIdentifier</key>
  <string>com.apple.services</string>
  <key>NSExtensionPrincipalClass</key>
  <string>$(PRODUCT_MODULE_NAME).ActionRequestHandler</string>
</dict>
```

Use `com.apple.services` plus `NSExtensionRequestHandling` when the action is headless.
Use `com.apple.ui-services` plus an `NSViewController` when a small, focused interface
is required.

Keep activation rules narrow:

- declare only the UTTypes the action truly supports;
- set maximum selection counts deliberately;
- test mixed selections and folders separately;
- do not use a universally true predicate merely to make the item appear everywhere.

Place reusable domain logic in a shared Swift package or framework. Keep adapters for
the containing app, Action Extension, and optional App Intent thin. Use App Intents for
Shortcuts, Spotlight, Siri, and automation reach; they do not replace the packaged
Action Extension required for a direct Finder Quick Action.

Keep work in the extension short and cancellable. Open or hand off to the containing
app for lengthy processing, progress history, complex configuration, or recovery.

## Disallowed substitutions

Unless the user explicitly requests them, do not satisfy the Quick Action contract with:

- an `NSServices` entry in the containing app;
- an Automator Service or workflow visible only under Services;
- a Finder Sync extension used merely to inject generic menu commands;
- documentation telling the user to construct their own Shortcut;
- a Tauri/Rust command that works only after opening the main app.

Finder Sync is appropriate for synchronization/status behavior in registered folders,
including badges and related folder controls. It is not the default general-purpose
Finder context-menu mechanism.

## Static and build verification

Run the project audit with the requested surface made explicit:

```bash
python3 "$SKILL_APP_GENERATOR_SKILL_DIR/scripts/audit_app_project.py" \
  --root . \
  --app-type macos \
  --native-integration finder-quick-action
```

For a hybrid Tauri app, use `--app-type tauri` with the same native-integration flag.

Before completion, verify:

1. The project contains an app-extension target.
2. Its configuration contains `NSExtensionActivationRule` and
   `NSExtensionServiceAllowsFinderPreviewItem = YES`.
3. The containing app embeds the `.appex` in `Contents/PlugIns`.
4. The extension and outer app pass strict code-signature verification.
5. The installed extension is visible and enabled under System Settings > Privacy &
   Security > Extensions > Finder.

## Runtime acceptance

Test the packaged app, not only an Xcode or Tauri development process:

1. Install or copy the packaged app to the intended location.
2. Enable its Finder extension.
3. Relaunch Finder if registration needs refreshing.
4. Select one supported file and confirm the command appears under **Quick Actions**.
5. Show Finder's Preview pane and confirm the same command is available there.
6. Run it and verify the real file result, collision behavior, and error reporting.
7. Select unsupported and mixed inputs; confirm the command is absent when invalid.
8. Confirm the feature is not available only under **Services**.

Record what was verified from the packaged runtime. Do not report a Finder Quick
Action as complete from source inspection, compilation, or a Service-menu sighting.
