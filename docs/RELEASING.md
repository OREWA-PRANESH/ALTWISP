# Release verification

1. Start from a clean checkout. Inspect pending changes.
2. Update the app version, package lockfile, and changelog consistently.
3. Run `npm ci`, `npm test`, and `npm run test:overlay` in `electron-app`.
4. Build the installer with `npm run dist`.
5. Smoke-test installation, Start-menu launch, cloud and local dictation, repeated
   hotkeys, title controls, tray quit, updates, and sign-in startup on Windows.
   Record Windows/DPI/model versions and what was actually tested.
6. Commit and push. Create an annotated `v<version>` tag at that commit and push it.
7. Watch **Build Windows release**. A pushed tag is not proof of successful release;
   confirm success and the attached Setup EXE.
   Future workflow builds also attach `SHA256SUMS.txt`; compare its checksum with
   `Get-FileHash .\ALTWISP-Setup-<version>.exe -Algorithm SHA256` before distributing.
8. Verify release links with the intended audience. Private repositories require
   authorized accounts; public download requires public access.

Publication must stop if tests or packaging fail. Do not rewrite published tags to
silently replace source. Keep generated outputs out of Git and preserve third-party
license notices in distributions. Only the owner decides when visibility changes.
