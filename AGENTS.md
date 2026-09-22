# Repository Guidelines

## Project Structure & Module Organization

ALTWISP is a Windows Electron app with a Python worker. Desktop orchestration and IPC live in `electron-app/electron/`; the dashboard and recorder overlay are in `electron-app/renderer/`; hotkeys, audio capture, transcription, storage, and paste behavior are in `electron-app/native/`. JavaScript and Python tests are in `electron-app/tests/`. Installer scripts and assets are under `electron-app/scripts/` and `electron-app/assets/`. The independent website is in `site/`; documentation and privacy/release notes are in `docs/`.

## Build, Test, and Development Commands

Run commands from the repository root unless noted:

```powershell
npm --prefix electron-app install
npm --prefix electron-app start
npm --prefix electron-app test
npm --prefix electron-app run test:overlay
npm --prefix electron-app run build:worker
npm --prefix electron-app run dist
```

`start` launches the Electron app, `test` runs the Node test suite, `test:overlay` exercises repeated recorder-window activation, `build:worker` prepares the native worker, and `dist` builds the Windows installer. Run Python tests explicitly with `python -m pytest electron-app/tests` when the environment provides pytest.

## Coding Style & Naming Conventions

Match the existing compact JavaScript style and use two-space indentation in JavaScript, HTML, and CSS. Use `camelCase` for JavaScript functions and variables, `snake_case` for Python functions and fields, and kebab-case for CSS classes. Keep IPC payload names stable and preserve the isolated preload bridge. Avoid unrelated formatting changes.

## Testing Guidelines

Add focused regression tests for behavior changes. Use descriptive test names such as `orb stays physically compact...`. Run both `npm --prefix electron-app test` and `npm --prefix electron-app run test:overlay` for hotkey, overlay, audio, or recorder changes. Tests do not replace real microphone, API, packaging, or reboot smoke tests; state exactly what was verified.

## Commit & Pull Request Guidelines

Use short Conventional Commit-style messages, for example `fix: smooth recorder orb response`, `test: cover overlay geometry`, or `docs: update setup guidance`. Keep each commit focused. Pull requests should explain the user problem, summarize the resulting behavior, list exact tests run, and include screenshots or a short recording for visible UI changes. Link the relevant issue for substantial work.

## Security & Configuration

Never commit `.env`, API keys, recordings, transcripts, databases, models, virtual environments, dependencies, or generated installer output. Use `.env.example` for placeholders. Treat clipboard, microphone permissions, user-data compatibility, and packaged-install paths as sensitive behavior; review `SECURITY.md` before handling credentials or reporting vulnerabilities.
