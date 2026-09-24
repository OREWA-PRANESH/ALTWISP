# Privacy and data handling

**Groq mode** sends recorded audio to Groq. With AI polish enabled it also sends
recognized text for formatting. Provider retention, terms, limits, and availability
are separate from ALTWISP. **Local mode** downloads a model on first use and then
processes recordings on your machine; cloud polish is disabled.

Settings, plaintext API-key configuration, history, dictionary, and snippets live
under `%LOCALAPPDATA%\ALTWISP`. ALTWISP does not encrypt them. Model libraries
manage separate download caches, potentially outside this directory.

History is enabled by default. Disable Save history for future dictations; use
Clear history for existing records. Dictionary and snippets are separate data.
Deleting database rows is not a secure-erasure guarantee for storage or backups.

Recordings use temporary files. Successful processing normally removes them.
Failed recordings may remain pending in the worker; Home offers Retry and Delete
while that worker is running. Abnormal termination may leave files. Do not assume
recordings never touch disk or are securely erased.

Pasting uses the clipboard and attempts to restore its prior text. Clipboard
managers/history can retain copies. Target checks operate at window level, not
individual field level.

The separate website loads fonts and animation scripts from external services.
Website dependencies are not part of local-mode transcription.

Redact keys and private text in reports. Never upload your `.env`, database,
or recordings unless you intentionally created a non-sensitive reproduction.
