# ALTWISP

ALTWISP is a privacy-friendly Windows voice-to-text desktop agent. Select a text box, press and release `Ctrl+Windows`, speak, then press and release `Ctrl+Windows` again. The floating recorder never takes focus, and the formatted result is pasted into the text box you originally selected.

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

## Install and run

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

The automated tests do not use the microphone, clipboard, network, or paid APIs.
