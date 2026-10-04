# Plan

1. `qualia/launcher.py` (SERVER lane, stdlib only): `find_browser()` checks the usual Edge/Chrome install paths and PATH; `main()` reads the port like `qualia open`, probes the port with `urllib` (Qualia's page carries a `qualia-token` meta tag), then either opens a window only, reports a foreign port, or runs `uvicorn.Server` in the main thread while a helper thread waits for `server.started`, starts the browser with `--app`, `--user-data-dir=QUALIA_HOME/.app-browser`, `--no-first-run`, `--no-default-browser-check`, waits for the browser process, and sets `server.should_exit`. Messages go to a Windows message box via `ctypes` when there is no console, else stderr.
2. `pyproject.toml`: `[project.gui-scripts] qualia-app = "qualia.launcher:main"`; `qualia/cli.py`: `qualia app` command calling the same function.
3. `web/public/qualia.ico`: rendered once from `favicon.svg` (Playwright) and wrapped as a PNG-in-ICO with stdlib; committed.
4. `Install Qualia.cmd` (repo root) → `scripts/install-qualia.ps1` (PowerShell 5.1): steps as FR003, `$LASTEXITCODE` checked after each native command, shortcuts via `WScript.Shell`.
5. `.github/workflows/release.yml`: build web on Ubuntu, `git archive` + `web/dist` → zip; upload artifact; `gh release create` on tags.
6. Tests `tests/test_launcher.py`; docs README Get started, USER-GUIDE §2, CONTRACTS note.

Ponytail: no tray icon, idle timer, auto-updater, uninstaller script or installer framework; Edge/Chrome only for app windows (the terminal `qualia open` remains for everything else).
