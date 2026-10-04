# Requirements analysis

Five requirements and four success criteria map to six tasks; coverage 100%.

- Principle V: the launcher reuses `create_app()` and the 127.0.0.1 binding; the browser profile lives in `QUALIA_HOME`, outside the repository; no new network listener or exposure. The installer downloads only uv (astral.sh official installer), Git (winget, user-confirmed by Windows), locked Python packages and the pinned AnnoMI demo, all of which the existing developer path already requires.
- Principle VI: no secrets are read or written; the Jev key stays in `.env`, untouched by the installer.
- Principle VII / technology constraints: no new dependency (stdlib `ctypes`, `urllib`, `subprocess`; uvicorn already present). Windows PowerShell 5.1 compatible. The gui-script entry point is standard packaging, not a framework.
- Protected files: `scripts/run-build.ps1` and `scripts/prompts/*` untouched; docs 02–05 unchanged.

Risks: SmartScreen or execution policy on managed PCs (documented, out of scope); Edge first-run prompts in a new profile (suppressed with `--no-first-run`); a second Chromium profile process handing off (handled by the already-running path). No CRITICAL issue.
