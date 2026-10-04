# Double-click app convergence

Five requirements, four success criteria and six tasks reviewed. Scoped feature converged.

- FR001: `qualia-app.exe` (standard gui-script entry, no console) and `qualia app` start the local server and open an Edge/Chrome `--app` window, or the default browser. Design change found by real testing: a dedicated browser profile made Edge open its onboarding and "Sync your profile" windows and keep running after Qualia's window closed. The launcher now uses the person's normal browser profile, open pages call `/api/health` every 30 s, authenticated API requests increment `app.state.activity`, and the launcher stops the server after 18 consecutive 10-second checks without activity (about 3 awake minutes; laptop sleep does not count).
- FR002: a second launch only opens another window; a foreign program on the port and launch failures produce plain-language messages (Windows message box when windowless, `QUALIA_HOME/qualia-app.log` for details).
- FR003: `Install Qualia.cmd` → `scripts/install-qualia.ps1` (PowerShell 5.1, ASCII, parse-checked) installs uv/Git when missing, `uv sync --locked --no-dev --inexact`, builds screens only when absent, adds the demo when online, creates Desktop and Start-menu shortcuts with `web/public/qualia.ico`, and opens Qualia. Re-running is safe and keeps a developer environment intact.
- FR004: `.github/workflows/release.yml` built `Qualia-main.zip` on a manual run (43 MB, 580 files, prebuilt `web/dist`, CRLF batch file preserved, no `.env` or demo data).
- FR005: README "Get started" and USER-GUIDE §2 lead with download → Install Qualia → icon, with update/remove steps; stop and troubleshooting text updated; developer path kept.
- SC001: `tests/test_launcher.py` 5 passed (real server stays up while checked in and stops when quiet; second launch; foreign port; default-browser fallback; Edge discovery).
- SC002: on this Windows 10 machine the installer ran from a git-archive package, from the CI-built zip extracted with `Expand-Archive`, and from the real folder. Each opened an app window without dialogs (UI Automation check); after closing the window the server stopped in 158–168 s with no Qualia processes left. Final shortcuts point to the real folder.
- SC004: full offline suite 566 passed, 5 skipped, 6 live deselected; Ruff, data guard, gitleaks and web typecheck/37 tests/build pass.

Not covered: managed computers that block scripts or winget, macOS/Linux double-click packaging, signed installers and automatic updates (the native desktop-app phase).
