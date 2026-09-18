# Verification and remaining release work

Repository review: 2026-09-18.

## Verified

- GitHub API confirms this repository is private; visibility remains unchanged.
- Release workflow for `v2.0.2` succeeded and published
  `ALTWISP-Setup-2.0.2.exe` (184,262,844 bytes).
- `site/` is excluded from the desktop package; keeping it in the same repo is safe.
- The current 17 automated tests pass.
- A real Electron test of the packaged app previously passed 100 show/hide cycles
  at the laptop's fractional DPI. This checks geometry, not microphone accuracy.
- Tracked file inventory excludes `.env`, recordings, databases, ZIPs, and EXEs.

## Remaining work before a broad public release

- `npm audit` currently reports two high-severity dependency groups: Electron
  and `extract-zip`. The installed Electron line is 38; remediation suggested by
  npm requires a major upgrade. Upgrade in a dedicated change and repeat actual
  recorder, tray, title-control, packaging, and Windows tests. Do not use a forced
  dependency upgrade without that verification.
- Run a clean Windows install/update/uninstall, microphone/cloud/local-model,
  sign-in startup, and mixed-monitor smoke-test matrix. These are not proven by
  unit tests or the window geometry test.
- Consider signing Windows installers and fully locking native dependencies.
- Confirm license ownership/third-party compliance before external distribution.
- The owner must explicitly approve public visibility. Private release links do
  not provide public one-click downloads.

Do not describe ALTWISP as bug-free or universally compatible. Keep README claims
consistent with implemented behavior and retain a clear changelog.
