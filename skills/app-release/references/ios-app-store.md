# iOS and App Store Release

Read this reference when iOS or App Store Connect is part of the release.

## Baseline

Query the current product before building:

- bundle ID, team, latest marketing version, latest build number;
- active App Store version and review submission;
- release type, encryption declaration, availability, and price;
- distribution certificate and provisioning profile validity.

If the previous version is still under review, determine whether to keep that
version, replace its build, or cancel and update the unreleased version before
creating another submission. Do not leave two conflicting submissions.

## Build identifiers and signing

- `CFBundleShortVersionString` equals the canonical release version.
- `CFBundleVersion` is greater than every build already uploaded.
- Use the established bundle ID, Apple Distribution identity, development team,
  and App Store provisioning profile.
- Verify production entitlements: `get-task-allow=false`, required associated
  domains, URL schemes, privacy manifest, and encryption declaration.

Use the project's own command first, for example:

```bash
pnpm ios:app-store:build
```

Tauri or Xcode generation may rewrite the build number. Re-read the exported IPA.
When the repository already provides an XcodeGen/manual archive path, regenerate
from its tracked spec and reuse a verified prebuilt Rust library only as defined
by that project.

## IPA audit

Unpack the final IPA into a temporary directory and verify:

```bash
/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$APP/Info.plist"
/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$APP/Info.plist"
/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' "$APP/Info.plist"
codesign --verify --deep --strict --verbose=2 "$APP"
codesign -d --entitlements :- "$APP"
find "$APP" -maxdepth 1 -type f -name '*.a'
shasum -a 256 "$IPA"
```

Completion checks:

- bundle, marketing version, and build number are exact;
- privacy manifest exists when required;
- code signature and distribution entitlements are valid;
- no static library such as `libapp.a` exists at the application root;
- required frameworks and URL/query schemes remain present;
- `ITSAppUsesNonExemptEncryption` matches the application's behavior.

## Validate and upload

Use the project's configured App Store authentication. A common CLI path is:

```bash
xcrun altool --validate-app --file "$IPA" --type ios \
  --username "$APPLE_ID" --password "$APPLE_SPECIFIC_APP_PASSWORD" \
  --provider-public-id "$PROVIDER_ID"

xcrun altool --upload-app --file "$IPA" --type ios \
  --username "$APPLE_ID" --password "$APPLE_SPECIFIC_APP_PASSWORD" \
  --provider-public-id "$PROVIDER_ID"
```

Validation success is not upload success. Upload success is not processing
success. Poll App Store Connect until the intended build reports:

- `processingState=VALID`;
- `buildAudienceType=APP_STORE_ELIGIBLE`;
- the expected build number and encryption declaration.

## Bind and submit

Use the current App Store Connect API flow:

1. Cancel an obsolete pending review submission when replacing it.
2. Wait until its state allows edits.
3. Update or create the intended `appStoreVersion`.
4. Bind the valid build and query the version with `include=build` to confirm.
5. Update applicable localization/release metadata. For a never-released first
   version, a “What's New” field may not apply; preserve required description,
   screenshots, categories, privacy, and review details.
6. Create `reviewSubmissions` for the app.
7. Add a `reviewSubmissionItems` relationship to the App Store version.
8. Patch the submission with `submitted=true`.
9. Read back submission state, version/build, release type, and pricing.

For a paid application, preserve or deliberately update the configured base
territory and price point, then query the price schedule after submission.

## Completion evidence

Report:

- marketing version and build number;
- IPA SHA-256 and upload/delivery identifier;
- `VALID` and `APP_STORE_ELIGIBLE` processing states;
- review submission ID and state;
- release type, encryption declaration, and price/base territory;
- accepted platform warnings, such as a future minimum OS requirement.

`WAITING_FOR_REVIEW` is a successful submission state, not public availability.
