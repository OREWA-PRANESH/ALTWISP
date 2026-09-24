# Changelog

## Unreleased

- No changes yet.

## 2.0.5

- Show the active Windows microphone and let users test another input before selecting it for dictation.
- Report silent or nearly silent capture instead of submitting it for transcription.
- Keep the sign-in startup preference unchanged when saving only the microphone selection.
- Add audio-capture regression tests.

## 2.0.4

- Added a live microphone meter, one-second microphone test, and retry/delete controls for failed recordings.
- Fixed recorder orb activation after sign-in startup and replayed recording state when its window loads.
- Added a release check and link to install newer versions manually.
- Upgraded Electron to 44.4.5 and added dependency audits and optional installer signing checks to CI.
- Organized packaging helpers, expanded installation and privacy guidance, and added contributor documentation.
- Added the MIT license, community policies, issue/PR templates, and automatic CI.
- Disabled Electron Builder's automatic tag publishing so the release workflow can attach the installer and checksum itself.

The `v2.0.3` tag did not publish an installer; its changes are included in 2.0.4.

## 2.0.2

- Fixed cumulative orb growth and drift at fractional Windows display scaling.
- Added fixed geometry checks and a 100-cycle Electron regression test.
- Removed duplicate title controls and added custom maximize behavior.
- Added Auto/English language selection and corrected the dashboard orb graphic.
- Hid dashboard scrollbars while retaining scrolling.
- Removed unused Chromium locales and enabled normal installer compression.

## 2.0.1

- Established the canonical user API-key configuration location.
- Prepared tagged Windows installers and the native worker build setup.

Notes describe source changes. Check actual release assets for publication status.
