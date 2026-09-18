# ALTWISP

ALTWISP is a privacy-friendly Windows voice-to-text desktop agent. Select a text box, press and release `Ctrl+Windows`, speak, then press and release `Ctrl+Windows` again. The floating recorder never takes focus, and the formatted result is pasted into the text box you originally selected.

## Project layout

- `electron-app/electron/`: desktop windows, tray, and worker bridge.
- `electron-app/renderer/`: dashboard and recorder UI.
- `electron-app/native/`: hotkey, audio, transcription, and storage worker.
- `electron-app/assets/`: application icons.
- `electron-app/scripts/`: worker build and Windows packaging helpers.
- `electron-app/tests/`: automated and desktop runtime checks.
- `site/`: public website.
- `.github/workflows/`: CI and release publishing.

Generated folders (`dist/`, `native/build/`, `native/dist/`, `node_modules/`,
and `.venv-worker/`) stay out of Git. Keep complete packaged application folders
together; their executable depends on the accompanying resources.

## Electron desktop app (primary)

The modern rewrite lives in `electron-app`. It combines an Electron dashboard and transparent voice-reactive orb with a lightweight native Python worker for Windows hotkeys, recording, transcription, and pasting.

```powershell
cd electron-app
npm ci
npm start
```

The app stays in the Windows notification area when its dashboard is closed. Enable launch at sign-in from Settings for service-like background operation in the interactive user session.

To create the Windows installer:

```powershell
cd electron-app
npm ci
npm run dist
```

## Features

- Same-key start/stop dictation on key release (`Ctrl+Windows`)
- Paste last dictation (`Shift+Alt+Z`)
- Dashboard shortcut (`Ctrl+Alt+D`)
- Groq Whisper or fully local `faster-whisper` transcription
- Optional AI cleanup with safe raw-text fallback
- Local transcript history and usage statistics
- Custom dictionary replacements and reusable voice snippets
- Neutral, casual, formal, and concise writing styles
- Configurable local history retention
- Launch-at-login support for a persistent background desktop agent
- Windows system-tray icon with dashboard, dictation, paste-last, and quit actions
- Five-minute recording limit, reliable temp-file cleanup, and visible errors

Groq mode requires a user-local `.env` file containing `GROQ_API_KEY=...`. Copy `electron-app/.env.example` to `%LOCALAPPDATA%\ALTWISP\.env`, add your key, and restart ALTWISP. Never commit or distribute that file.

## Background startup on Windows

Enable **Launch ALTWISP when I sign in to Windows** in Settings. This registers the app under the current user's Windows Run key and starts it with `--background` after sign-in.

ALTWISP intentionally runs as a per-user background desktop agent instead of a Windows Service. Windows Services execute in Session 0 and cannot safely interact with the signed-in user's microphone, clipboard, global input hooks, or dashboard. A service would therefore break the core dictation workflow. Launch-at-login provides service-like persistence in the correct interactive session.

## Test

```powershell
npm --prefix electron-app test
```

The automated tests do not use the microphone, clipboard, network, or paid APIs.

The orb disappears immediately when capture stops; transcription continues in
the background. If you switch windows before completion, copy the result from
Home instead of having it pasted into the wrong window. Connection failures
offer retry/discard in the dashboard and retain only the latest failed recording
for the current session. Quitting or discarding removes that temporary audio.
Local mode also disables cloud polishing. Hidden orbs do not animate.
