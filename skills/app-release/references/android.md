# Android Release

Read this reference when Android is part of the release surface.

## Detect the configured channel

- Existing Play Console or store automation → publish the expected AAB/APK to
  the configured track and read the release back.
- Existing website/public-download flow → publish a signed APK and verify it
  anonymously.
- Both already exist → update both from the same version and signing lineage.
- Do not introduce a new store or hosting service during a routine release.

## Version and build

- `versionName` equals the canonical marketing version.
- `versionCode` is an integer greater than every uploaded build. Follow the
  project's encoding policy; never reuse an accepted code.
- Confirm package/application ID, minimum SDK, target SDK, and supported ABIs.

## Build and signing

Use the project's existing build command and release keystore. Examples:

```bash
pnpm android:apk:build
./gradlew bundleRelease
```

Do not create a new signing identity when the application already has one.
Resolve secrets through the project's credential store or environment and keep
them out of logs and repository files.

For a direct APK, align and sign with the installed Android build tools when the
project build does not already emit a signed artifact:

```bash
zipalign -p -f 4 "$UNSIGNED_APK" "$ALIGNED_APK"
apksigner sign --ks "$KEYSTORE" --ks-key-alias "$KEY_ALIAS" \
  --ks-pass env:KS_PASS --key-pass env:KEY_PASS \
  --out "$SIGNED_APK" "$ALIGNED_APK"
```

## Artifact audit

```bash
apksigner verify --verbose --print-certs "$SIGNED_APK"
zipalign -c -v 4 "$SIGNED_APK"
aapt dump badging "$SIGNED_APK"
zipinfo -1 "$SIGNED_APK" | sort
shasum -a 256 "$SIGNED_APK"
```

Verify:

- v2/v3 or the project's required signature schemes pass;
- signer certificate matches the previous release lineage;
- package ID, `versionName`, and `versionCode` are correct;
- required ABIs are present and no unexpected debug payload ships;
- minimum/target SDK match product documentation;
- the final checksum is computed after signing.

## Direct public download

- Use a versioned immutable filename.
- Update the website button, tests, README, and release notes.
- A private GitHub Release asset may return 404 to anonymous users. Use the
  project's public domain or public object storage when public download is part
  of the product.
- After production deploy, download the full remote artifact to a temporary
  location and compare SHA-256 with the signed local artifact.
- Confirm response status, `Content-Type`, content length, and the page's actual
  JavaScript/HTML reference to the new filename.

## Store track

Use the repository's existing Play publishing tool. Read back at least:

- package ID;
- track name;
- version code;
- release status and rollout fraction;
- artifact processing result.

If review or staged rollout remains pending, report that state rather than
calling the version fully public.
