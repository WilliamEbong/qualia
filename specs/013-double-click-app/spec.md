# Double-click app

The owner asked for an install and start-up experience suitable for non-technical researchers, without the terminal (2026-10-04, delegated: "Go with your recommendation, build autonomously"). The chosen option is a downloadable package with a one-time installer and a desktop icon that opens Qualia in its own app window and stops it when the window closes. A full native desktop app (Tauri) stays a later phase (doc 01). No change to data location, privacy, AI behaviour or the API.

## Requirements

- FR001: A windowless `qualia-app` program (a standard Python GUI entry point, so no console window appears on Windows) starts the local server, opens Qualia in a Microsoft Edge or Google Chrome app window (no tabs or address bar, dedicated profile under `QUALIA_HOME`), and stops the server when that window closes. `qualia app` runs the same flow from a terminal.
- FR002: If Qualia is already running on the configured port, a second launch only opens another app window. If the port belongs to something else, or no Edge/Chrome is found, the user sees a plain-language message (a Windows message box when there is no console) instead of a silent failure.
- FR003: Double-clicking `Install Qualia.cmd` once installs uv if missing, installs Git through winget if missing (or explains how), installs Qualia's dependencies without developer tools (`uv sync --no-dev --locked`, which also fetches Python), builds the interface only when no prebuilt one is present, adds the AnnoMI demo when online, creates Desktop and Start-menu "Qualia" shortcuts with the Qualia icon, and starts Qualia. Every step reports progress in plain words; a failure stops with an actionable message. Re-running is safe.
- FR004: A release workflow packages the tracked source plus the prebuilt interface into `Qualia-<version>.zip` (artifact on manual runs; GitHub release asset on `v*` tags), so downloaders need neither Node nor Git to get started.
- FR005: README and user guide lead with the download → install → icon path and explain how to stop, update and uninstall; the developer command path remains documented.

Constraints: server still binds 127.0.0.1 with Host checks and a per-launch token; research data stays in `QUALIA_HOME`; no new runtime dependency; Windows PowerShell 5.1 compatible; `scripts/run-build.ps1` and `scripts/prompts/*` untouched.

Assumptions: Edge is present on supported Windows 10/11 machines; managed computers that block scripts or winget remain out of scope (the desktop-app phase addresses them); unsigned scripts can trigger a one-time Windows prompt, documented with the "Unblock" step.

## User scenarios

A researcher downloads the zip from GitHub Releases, unblocks and extracts it, and double-clicks **Install Qualia**. A window narrates each step; at the end Qualia opens with the demo project and a Qualia icon sits on the desktop. Later they double-click the icon, work, and close the window; nothing keeps running.

## Success criteria

- SC001: Offline tests cover browser discovery, the already-running and foreign-port paths, and a real end-to-end launch on a free port where closing the (fake) browser stops the server.
- SC002: On this Windows machine, the installer run on a clean extraction of the release package succeeds, creates both shortcuts, and the icon opens the app window; closing it stops the server process.
- SC003: The release workflow produces the zip in CI.
- SC004: Full offline suite, Ruff, data guard, dependency audit, gitleaks and web checks pass; docs updated.
