# ALTWISP

ALTWISP is a privacy-friendly Windows voice-to-text desktop agent. Select a text box, press and release `Ctrl+Windows`, speak, then press and release `Ctrl+Windows` again. The floating recorder never takes focus, and the formatted result is pasted into the text box you originally selected.

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

The original Python desktop client remains in `src` while the Electron rewrite is validated and packaged.

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

## Legacy Python client

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\src\main.py
```

For free on-device transcription:

```powershell
pip install -r requirements-local.txt
```

Open Settings, select `local`, and choose a Whisper model. The model is downloaded on first use. `small` is the default balance between speed and accuracy on CPU.

Groq mode requires a `.env` file containing `GROQ_API_KEY=...`. Do not commit or distribute that file.

## Background startup on Windows

Enable **Launch ALTWISP when I sign in to Windows** in Settings. This registers the app under the current user's Windows Run key and starts it with `--background` after sign-in.

ALTWISP intentionally runs as a per-user background desktop agent instead of a Windows Service. Windows Services execute in Session 0 and cannot safely interact with the signed-in user's microphone, clipboard, global input hooks, or dashboard. A service would therefore break the core dictation workflow. Launch-at-login provides service-like persistence in the correct interactive session.

## Build an executable

```powershell
.\build.ps1
```

Copy `.env` beside the executable only if you use Groq mode. Local mode does not need an API key.

## Test

```powershell
python -m unittest -v test_edge_cases.py
python -m compileall -q src
```

Run all regression tests with `python -m unittest discover -v`.
The automated tests do not use the microphone, clipboard, network, or paid APIs.

### Responsiveness check

`python src/main.py --self-test latency.json` exercises 20 simulated hotkey
start/stop cycles against the real floating window, including slow microphone
initialization. It reports event-to-window-call latency, not end-to-end speech
recognition latency. The executable supports the same option.

The orb disappears immediately when capture stops; transcription continues in
the background. If you switch windows before completion, copy the result from
Home instead of having it pasted into the wrong window. Connection failures
offer retry/discard in the dashboard and retain only the latest failed recording
for the current session. Quitting or discarding removes that temporary audio.
Local mode also disables cloud polishing. Hidden orbs do not animate.
