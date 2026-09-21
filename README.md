<p align="center">
  <img src="docs/assets/altwisp-orb.png" alt="ALTWISP orb logo" width="180">
</p>

<h1 align="center">ALTWISP</h1>
<p align="center"><strong>Voice, uninterrupted.</strong><br>Windows voice dictation with cloud or local processing.</p>

<p align="center">
  <a href="https://github.com/OREWA-PRANESH/ALTWISP/releases/latest"><img src="https://img.shields.io/badge/Windows-10%20%2F%2011%20%C2%B7%20x64-536DFE?style=flat-square" alt="Windows 10 and 11, x64"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-16B8AC?style=flat-square" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/Desktop-Electron-7483B5?style=flat-square" alt="Electron desktop">
  <img src="https://img.shields.io/badge/Worker-Python-7483B5?style=flat-square" alt="Python native worker">
  <a href="https://github.com/OREWA-PRANESH/ALTWISP/actions/workflows/ci.yml"><img src="https://img.shields.io/badge/CI-Automated%20checks-536DFE?style=flat-square" alt="Automated CI checks; open workflow for results"></a>
</p>

<p align="center">
  <img src="brag-output/ALTWISP-video.gif" alt="ALTWISP in action" width="960">
</p>

<p align="center">Speak naturally. Put your words where you work.<br>Windows voice dictation with Groq cloud transcription or local Whisper.</p>

<p align="center">
  <a href="https://github.com/OREWA-PRANESH/ALTWISP/releases/latest"><strong>Download for Windows</strong></a> ·
  <a href="https://altwisp.vercel.app"><strong>Visit the website</strong></a> ·
  <a href="#step-by-step-windows-installation">Installation guide</a> ·
  <a href="#how-to-use">How to use</a> ·
  <a href="CONTRIBUTING.md">Contribute</a>
</p>

## ALTWISP

Windows voice dictation that inserts your words into the application you are already using.

[Download the latest Windows release](https://github.com/OREWA-PRANESH/ALTWISP/releases/latest) · [Report a bug](https://github.com/OREWA-PRANESH/ALTWISP/issues/new/choose) · [Contribute](CONTRIBUTING.md)

**Access:** this repository is currently private. Source, issues, and releases are available only to authorized collaborators. Public distribution is planned; the download link is not yet accessible to signed-out visitors.

Authorized collaborators can [download the verified v2.0.2 installer directly](https://github.com/OREWA-PRANESH/ALTWISP/releases/download/v2.0.2/ALTWISP-Setup-2.0.2.exe). Use the latest-release link above to find future versions.

ALTWISP runs in the notification area. Press and release **Ctrl + Windows** to start recording, speak, and repeat to stop. A floating orb shows microphone activity without taking focus. Choose Groq cloud transcription or local Whisper processing.

## Contents

- [Advantages and uses](#advantages-and-uses)
- [Requirements](#requirements)
- [Windows installation](#step-by-step-windows-installation)
- [How to use](#how-to-use)
- [Privacy and storage](#privacy-and-storage)
- [Limitations](#limitations)
- [Troubleshooting](#troubleshooting)
- [Update and uninstall](#update-and-uninstall)
- [Build from source](#build-from-source)
- [Repository layout](#repository-layout)
- [Community and license](#community-and-license)

## Advantages and uses

- Dictate emails, messages, notes, drafts, and documentation into compatible text fields.
- Stay in your current app instead of switching to a separate transcription editor.
- Correct product names and terminology with a personal dictionary.
- Expand spoken snippet triggers into reusable text.
- Review and copy recent transcripts from the dashboard.
- Optionally polish cloud transcripts in neutral, casual, formal, or concise styles.
- Choose on-device recognition or cloud processing, and control whether history is saved.
- Start automatically after Windows sign-in.

ALTWISP is a dictation tool. It does not answer spoken questions or execute spoken commands.

## Requirements

- Windows 10 or 11, **x64**, and a working microphone.
- Windows permission for desktop applications to access the microphone.
- Groq mode: internet access and your own Groq API key. Provider limits and charges depend on your account.
- Local mode: internet for the first model download; cached models can subsequently run offline. Larger models require more memory, disk space, and CPU time.
- Allow at least 500 MB for the application, plus local model storage. The latest measured unpacked development build is approximately 376 MiB; release size can vary.

The Windows installer includes the app runtime and native worker. End users do **not** need Node.js or Python. macOS, Linux, and Windows ARM64 are not current release targets.

## Step-by-step Windows installation

1. Open [the latest release](https://github.com/OREWA-PRANESH/ALTWISP/releases/latest). Sign in with an authorized GitHub account while the repository is private.
2. Under **Assets**, download `ALTWISP-Setup-<version>.exe`. GitHub's `Source code` archives are for developers, not installers.
3. Run the Setup EXE and follow the installation prompts. Select your install location and shortcut options.
4. Launch **ALTWISP** from the Start menu or installed shortcut.
5. Enable microphone access in Windows **Settings → Privacy & security → Microphone** (Windows 11), or **Settings → Privacy → Microphone** (Windows 10), including access for desktop apps.
6. Configure cloud or local transcription below.
7. Open Notepad, click its text area, and follow the usage steps to test a short dictation.

Community builds may be unsigned. Check that the installer came from this repository's release page before proceeding through any publisher warning. Do not assume an unrelated download is an official build.

### Groq cloud setup

1. Create an API key in your [Groq account](https://console.groq.com/keys).
2. Launch ALTWISP once. Press **Win + R**, enter `%LOCALAPPDATA%\ALTWISP`, and open the folder.
3. Create a plain text file named `.env` there. Enable **File name extensions** in Explorer and ensure it is not `.env.txt`.
4. Add the following line with your own key:

   ```dotenv
   GROQ_API_KEY=your_groq_api_key_here
   ```

5. Save the file, fully quit ALTWISP from the tray menu, and launch it again.
6. Open **Settings**, select **Groq**, choose **Auto** or **English**, and save settings.

[The example configuration](electron-app/.env.example) contains only a placeholder. Never include your real key in commits, screenshots, bug reports, or release files.

### Local transcription setup

1. Open **Settings**, select **Local**, choose a model, and save settings.
2. Keep internet access available for the first dictation while the selected model downloads and initializes. First use can be substantially slower.
3. After download, that model runs on your CPU using INT8 computation. Start with `tiny` or `base` on slower computers; choose a larger model if you need better recognition.

Local mode needs no Groq key and disables cloud AI polish. Dictionary replacements and snippets still work. Choosing an uncached model requires another download.

### Runnable ZIP test builds

If a maintainer provides an application ZIP, extract the **entire** archive before opening `ALTWISP.exe`. Keep DLLs, locales, resources, and the native worker together. Do not run from inside the ZIP or copy only the EXE. ZIP builds do not register an installed Start-menu application automatically.

## How to use

1. Click the text field where you want your words.
2. Press and release **Ctrl + Windows** together. The orb appears and recording starts.
3. Speak, then press and release the same shortcut again to stop.
4. Keep the original target window and text field active while transcription completes.
5. ALTWISP attempts to paste using **Ctrl + V**. If pasting fails or you changed windows, open **Home** and copy the latest transcript.

This is a toggle shortcut, not push-to-talk. Recording stops at the default five-minute limit. A new dictation cannot start while processing is in progress.

Closing the dashboard leaves the app running in the tray. The tray menu opens the dashboard, starts/stops dictation, and quits the app. **Launch at sign in** starts it in the background in your interactive Windows session; it is not a Windows Service.

## Privacy and storage

| Item | Behavior |
| --- | --- |
| Groq transcription | Recorded audio is sent to Groq. |
| Cloud AI polish | Recognized text is sent to Groq when enabled. |
| Local mode | Recognition stays on your machine after model download; cloud polish is disabled. |
| History, dictionary, snippets | Stored in `%LOCALAPPDATA%\ALTWISP\altwisp.db`. |
| Settings | Stored in `%LOCALAPPDATA%\ALTWISP\settings.json`. |
| API key | Read from `%LOCALAPPDATA%\ALTWISP\.env`, a plaintext user file. |
| Clipboard | Used temporarily for pasting; the previous text clipboard is restored when possible. |
| Audio | Temporary files normally removed after processing; failed recordings may remain pending in the worker. |

History is enabled by default. Disable **Save history** for future dictations and use **History → Clear history** to remove stored transcripts. ALTWISP does not encrypt its local files. The current dashboard does not expose automatic retention or failed-recording retry/discard controls. See [Privacy details](docs/PRIVACY.md).

## Limitations

- Accuracy depends on noise, microphone quality, pronunciation, language, and model. Review important text.
- Cloud latency depends on the connection and provider; local latency depends on hardware and model size. No fixed latency is guaranteed.
- Pasting requires a compatible editable field. Elevated apps, protected fields, custom editors, remote desktops, and games may block it.
- Paste safety checks the target window, not the exact focused text field. Avoid changing fields while waiting.
- The language dropdown currently exposes Auto and English; not every model-supported language has been verified.
- The recorder anchors to the primary display. Not every mixed-DPI or multi-monitor configuration has been tested.
- Electron/Chromium and native transcription libraries make the installation larger than a small native utility. Local models add further storage.
- There is no automatic updater. Install newer releases manually.
- The current Electron app implements one global dictation shortcut. Paste-last and dashboard global shortcuts are not implemented.
- Python dependency ranges are bounded but not fully locked, so native rebuilds are not fully reproducible.
- This is actively maintained software, not a guarantee of zero bugs or universal compatibility.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Hotkey does nothing | Check the tray, quit duplicate app copies, restart, and try tray dictation. Other software may intercept shortcuts. |
| Microphone unavailable | Check desktop microphone permission, the default recording device, and other apps using it. |
| API key error | Check `.env` location/name and key, then fully quit and restart. |
| First local dictation is slow | Wait for download/initialization; try a smaller model. |
| Text is not inserted | Keep the original target active; copy from Home if the target blocks paste. |
| App remains after closing | Expected tray behavior. Use **Quit ALTWISP** to stop it. |
| Start-menu entry missing | Use the Setup EXE rather than an extracted ZIP. |
| GitHub download returns 404 | This repository is private; use an authorized account. |

Report reproducible problems using the [issue templates](https://github.com/OREWA-PRANESH/ALTWISP/issues/new/choose), with app version, Windows version, scaling, transcription mode, and sanitized steps.

## Update and uninstall

To update, quit the app, download the newest Setup EXE, and install it. Back up `%LOCALAPPDATA%\ALTWISP` first if your data is important. The user-data directory is separate from the installed app.

To uninstall, quit and use Windows **Settings → Apps**. User data and model caches may remain. Delete your user-data folder only after backing it up if you want to erase keys, settings, dictionary, snippets, and history. Model libraries manage caches separately.

## Build from source

Developer prerequisites: Windows x64, Git, Node.js 22, and Python 3.13 available as `python` (matching CI).

```powershell
git clone https://github.com/OREWA-PRANESH/ALTWISP.git
cd ALTWISP\electron-app
npm ci
npm run build:worker
npm start
```

`build:worker` prepares `.venv-worker` and the native executable. On a fresh clone, `npm start` alone is insufficient. Configure your user `.env` or select local transcription.

```powershell
# Unit and isolated hotkey checks: no microphone or paid API calls
npm test

# Real Electron window: 100 show/hide cycles, no microphone
npm run test:overlay

# Build Windows installer, including the worker
npm run dist
```

Installer output is in `electron-app/dist/`. A tag push triggers release CI; it does not prove publication. Confirm the workflow succeeded and a Setup EXE is attached. See [Release verification](docs/RELEASING.md).

## Repository layout

```text
.github/                 CI, release workflows, issue and PR templates
docs/                    Privacy and release process
electron-app/
  assets/                Application and tray icons
  electron/              Desktop windows, tray, worker bridge
  native/                Hotkeys, audio, recognition, storage, paste
  renderer/              Dashboard and recorder UI
  scripts/               Build and packaging helpers
  tests/                 Unit and Electron runtime checks
site/                    Static product website
```

Keeping the app and website together is intentional. `site/` is not bundled into the desktop app and is deployed independently at [altwisp.vercel.app](https://altwisp.vercel.app). Its CDN fonts and animations need network access. See [Website development](site/README.md).

Generated output, dependencies, recordings, databases, models, and keys stay out of Git.

## Community and license

Read [Contributing](CONTRIBUTING.md), [Code of Conduct](CODE_OF_CONDUCT.md), [Security policy](SECURITY.md), and [Changelog](CHANGELOG.md).

See [Verification and remaining release work](docs/VERIFICATION.md) for checks performed and known audit findings. Documentation completeness does not imply every platform or edge case has been tested.

ALTWISP source is licensed under the [MIT License](LICENSE). Third-party dependencies and downloaded models retain their own licenses. Public availability is pending while the repository remains private.
