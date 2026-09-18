# Contributing

Bug reports, documentation, tests, and focused fixes are welcome. The repository
currently requires collaborator access; public access is pending.

Search existing issues first. For substantial changes, open an issue explaining
the user problem and proposed behavior before implementing it.

## Development workflow

1. Follow [source setup](README.md#build-from-source) on Windows x64.
2. Create a branch for one focused change.
3. Preserve user-data compatibility, clipboard safety, and hotkey behavior.
4. Run `npm --prefix electron-app test`.
5. For window/recorder changes, run `npm --prefix electron-app run test:overlay`.
6. For packaging changes, build and inspect the complete Windows package.
7. Open a pull request describing the problem, resulting behavior, and tests.

State what was actually tested. Unit tests are not a full microphone, API,
installation, or reboot smoke test. Keep website changes under `site/`, which
is independent of desktop packaging.

Never commit `.env`, credentials, transcripts, recordings, databases, models,
dependencies, virtual environments, or generated output. Use sanitized examples.
Retain third-party notices. Contributions use the project's MIT license.

Use issue templates for normal bugs and suggestions. Follow the
[Code of Conduct](CODE_OF_CONDUCT.md). Report security issues through
[SECURITY.md](SECURITY.md). No response-time guarantee is offered.
