# ALTWISP optimization audit — 2026-09-30

## Changes

- Preserve unsaved Settings, Dictionary and Snippets drafts when dictation finishes. Preserve edited latest text during navigation and History searches during refresh.
- Reset the microphone meter when recording stops. Ignore microphone-list replies belonging to a previous page and preserve unavailable saved-device selections.
- Add search across the 80 recent dictations. Wrap long transcripts, reserve room for the Home orb, restore subtle scrollbars, improve toggle descriptions and associate labels with controls. Keep the existing palette, orb and recorder animation.
- Fix writing-style saves: `form.style` is a DOM property; read the actual control through `form.elements.style`.
- Disable irrelevant engine controls and settings/microphone actions during recording or testing. Catch command and clipboard failures, prevent duplicate submissions and show readable errors.
- Coalesce snapshot requests and defer them while the dashboard is hidden. Remove the dashboard MutationObserver by rendering the language choices and orb markup directly. Send only state and volume events to the recorder window.
- Cache bounded history, statistics and vocabulary reads with mutation invalidation and a lock. Count words consistently across whitespace. Reuse transcription/polish clients and compiled replacement expressions.
- Prevent settings changes, retry and microphone tests from racing with active dictation. Preserve completed transcripts when automatic paste fails, avoiding duplicate history on retry. Keep worker stdout exclusively for JSON messages.
- Bound crash-restart attempts until the worker has stayed alive for 30 seconds. Show unavailable state on worker failure, discard late replies, and give the worker a three-second shutdown deadline.
- Restore AI polish after the old `llama-3.3-70b-versatile` request returned HTTP 404. The configured account exposes `openai/gpt-oss-120b`; requests use low reasoning effort and exclude reasoning from the transcript. [Groq model documentation](https://console.groq.com/docs/model/openai/gpt-oss-120b). Explicit correction guidance prevents “tomorrow, no, Friday” becoming “not Friday”.

## Measurements

Using a disposable database with 5,000 synthetic records and the pre-change storage implementation from `bd0112a`, 40 repeated dashboard reads measured median **11.6935 ms before** and **0.0112 ms after warming the cache**. This is a database-read benchmark, not a claim about whole-app CPU, memory, transcription speed, or cold/mutating reads. Cache mutation, copy isolation and concurrent reads/writes have regression coverage.

Live synthetic English speech was recognized by Groq Whisper in **1.599 seconds**. Local Whisper **tiny** recognized the same speech in **0.435 seconds** on a warm model; the first run, including model acquisition/loading, took **83.128 seconds**. These are single smoke samples, not accuracy or speed comparisons. The default local model remains small.

Live polish checks covered punctuation, a spoken correction, a quoted question, and an instruction inside dictation. They produced formatted speech without answering the question or following the instruction. These examples cannot establish accuracy for all languages or prompts.

## Checks performed

```powershell
npm --prefix electron-app test
& electron-app/.venv-worker/Scripts/python.exe -m unittest discover -s electron-app/tests -p 'test_*.py'
npm --prefix electron-app run test:dashboard
npm --prefix electron-app run test:overlay
npm --prefix electron-app run test:app
npm --prefix electron-app run build:worker
& electron-app/.venv-worker/Scripts/python.exe electron-app/tests/worker-runtime.py --packaged --microphone
& electron-app/.venv-worker/Scripts/python.exe electron-app/tests/storage-benchmark.py
node --check electron-app/electron/main.js
node --check electron-app/renderer/app.js
git diff --check
```

- 18 Node tests and 22 Python tests passed, including shutdown during transcription without a delayed paste.
- Dashboard runtime checks use the real Electron renderer and isolated preload with fixture IPC: all pages, dictionary/snippet creation and deletion, history search/clear, engine controls, writing-style persistence, drafts, busy/error recovery, delayed microphone replies, hidden refresh deferral, snapshot bursts, and 980×680 / 1180×800 layouts. Captured screenshots were inspected. The intentional failed-save case logs a fixture error and passes recovery assertions.
- Recorder runtime passed 100 repeated activations with stable geometry on the current fractional-DPI display.
- Real main-process/worker smoke used a disposable profile: startup, IPC, SQLite entries, saved settings, forced crash and automatic recovery, and changed-target paste protection passed.
- Source worker CRUD, malformed-message recovery and clean shutdown passed. Rebuilt packaged worker startup, CRUD, settings validation/persistence, malformed JSON/list recovery, microphone enumeration and clean shutdown passed.
- The packaged worker enumerated 22 input endpoints. A two-second test opened the real default microphone; a live reading was RMS 33, below the dictation threshold. No microphone audio was sent to the cloud. Only generated synthetic speech/text was sent to Groq.

## Remaining validation and execution limits

Testing ran on the available Windows host. No separate cloud Windows desktop was provisioned; desktop hotkeys, microphone devices, clipboard and foreground-window behavior depend on an interactive OS session.

Windows refused foreground activation of the synthetic paste target. The app correctly rejected the paste and left the target unchanged. Successful native paste and clipboard restoration have isolated regression coverage, but a real successful paste still needs an interactive check. Real physical hotkey use, other microphones, sleep/resume, reboot/sign-in startup, a newly installed NSIS release, and local models other than tiny were not verified here.

No installer was published and these changes are not committed or pushed. Production website content was not redeployed by this desktop audit. Temporary test profiles contain synthetic data only; user history/settings and the installed app were not changed.
