# Verification and remaining release work

Repository review: 2026-09-24.

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

- Electron has been upgraded to 44.4.5 and `npm audit --audit-level=high` reports
  no vulnerabilities in the current lockfile. The 100-cycle overlay test passes
  on the upgraded runtime. Repeat installed-app smoke tests before release.
- Run a clean Windows install/update/uninstall, microphone/cloud/local-model,
  sign-in startup, and mixed-monitor smoke-test matrix. These are not proven by
  unit tests or the window geometry test.
- Consider signing Windows installers and fully locking native dependencies.
- Confirm license ownership/third-party compliance before external distribution.
- The owner must explicitly approve public visibility. Private release links do
  not provide public one-click downloads.

Do not describe ALTWISP as bug-free or universally compatible. Keep README claims
consistent with implemented behavior and retain a clear changelog.
