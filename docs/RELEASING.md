# Release verification

1. Start from a clean checkout. Inspect pending changes.
2. Update the app version, package lockfile, and changelog consistently.
3. Run `npm ci`, `npm test`, and `npm run test:overlay` in `electron-app`.
4. Build the installer with `npm run dist`.
5. Smoke-test installation, Start-menu launch, cloud and local dictation, repeated
   hotkeys, title controls, tray quit, update checking, and sign-in startup on Windows.
   Record Windows/DPI/model versions and what was actually tested. Use the matrix below.
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

## Windows smoke-test matrix

Record pass/fail and app, Windows, display scale, microphone, and local model versions for each row:

| Area | Check |
| --- | --- |
| Install and update | Clean install, Start-menu launch, install over the previous version, then uninstall; confirm user data is preserved during update. |
| Cloud dictation | Enter a key in `%LOCALAPPDATA%\ALTWISP\.env`, restart, speak into Notepad, stop, and confirm the transcript is pasted. |
| Local dictation | Select `tiny` or `base`, allow the first download, then repeat offline with the cached model. |
| Microphone and recovery | Check the live meter and one-second test; deny microphone permission; force a transcription error and try both Retry and Delete. |
| Window behavior | Repeat hotkey start/stop, tray quit, sign-in startup, and overlay placement on primary and mixed-DPI displays. |
| Updates | Check for a newer release and open the release page from Settings. Private repositories require an authorized browser session. |

## Signing and license review

Set `WINDOWS_SIGNING_CERTIFICATE` to a base64-encoded PFX and `WINDOWS_SIGNING_PASSWORD` in GitHub Actions secrets to sign release installers. The workflow verifies the installer signature when signing is configured. Without those secrets, the installer is unsigned; do not claim otherwise. The certificate and password must never be committed.

Before external distribution, review the bundled Electron, Python worker, and model/library licenses, retain required notices, and document any exceptions. Verify the generated installer contents and `SHA256SUMS.txt` against the published release.
