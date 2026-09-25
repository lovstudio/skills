# Production readiness checklist

Use this checklist after resolving the user's desired delivery scope. It is a
decision aid, not a replacement for the target repository's own instructions.

## 1. Declare the target

State one of the following before changing the project:

- **Local production install**: create and verify a platform-native artifact, then install it on the current machine only when the user asks.
- **Distributable artifact**: create and verify the package but do not install or publish it.
- **Release handoff**: prepare a verified candidate and hand version, notes, artifact, and evidence to an explicit release workflow.

Do not assume that a successful local build authorizes a Git tag, remote upload,
website deployment, store submission, or auto-update publication.

## 2. Inspect the real boundary

Collect the target project's existing rules, package manager, version sources,
development command, production command, native package configuration,
environment-variable paths, signing configuration, and updater configuration.

Classify each finding as one of:

- **pass**: it supports the declared production target;
- **warning**: it needs an explicit decision or manual verification;
- **blocker**: it prevents a truthful production result.

Never display environment-variable values, certificates, notarization tokens,
or other secrets in a report.

## 3. Build and test

Run the established package-manager quality gate and the target's real
production build command. Use a release/profile build where the target makes
that distinction. A Vite preview, dev server, unit test, or output directory
alone is not a production-artifact proof.

Report tests, warnings, and skipped checks separately. A build warning is not a
failure unless it invalidates the target's acceptance condition.

## 4. Verify the platform artifact

### macOS app bundles

Check the app's bundle identifier and version. Then use the native chain:

```bash
codesign --verify --deep --strict --verbose=2 "AppName.app"
codesign -dvv "AppName.app"
spctl -a -vv -t exec "AppName.app"
xcrun stapler validate "AppName.app"
```

Run stapler validation only when the build claims notarization. A Developer ID
signature and an accepted Gatekeeper result are distinct facts; record each.

### Other desktop targets

Use the project's configured installer or package and the platform's native
signature verifier. Confirm the application identifier, version, and installer
or executable signature. Do not substitute a source-tree binary for the
distributed artifact.

### Web targets

Verify the production command and emitted static or server artifact. Deploying
or serving it publicly is an external action and requires explicit authority.

## 5. Local installation

Local installation requires explicit user authority. Before replacing an app:

1. Resolve the exact existing application path and confirm it is not actively in use.
2. Preserve the previous bundle in a recoverable location instead of deleting it.
3. Copy the new bundle cleanly, avoiding stale files from an in-place merge.
4. Verify the installed bundle's identifier, version, signature, and executable digest against the staged artifact.
5. Do not claim that the app launched successfully unless it was actually launched and observed.

## 6. Release handoff

For an external release, pass only these facts to the release owner:

- project version sources and chosen version;
- production build command and verified artifact;
- signing/notarization result where relevant;
- quality-gate result and known warnings;
- release notes or outstanding blockers;
- exact statement of whether external publication is authorized.

The release owner, not this Skill, owns tags, uploads, public availability, and
live-channel readback.
