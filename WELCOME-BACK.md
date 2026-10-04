# Qualia - ready to publish (one step left for you)

Everything is done, committed and pushed to private main. CI status for the final push is in the last BUILD-STATE entry.

## What changed in this round

- **README** is now a guided tour. It covers what Qualia does and why to trust it, has cropped screenshots of each feature, a five-minute start, an "AI options" table and the measured demo results. The architecture, verified walkthrough and Decisions log are kept.
- **User guide**:
  - §13 contains the full Jev setup: account, key, `.env`, readiness check, synthetic first test, using Jev, privacy and error meanings.
  - Every new feature has a cropped screenshot, and the command reference lists tuning, AI improvement and Jev commands.
  - Machine-specific paths such as `C:\Users\Owner\...` are replaced with general ones.
- **Screenshots** in `design-review/final/features/` are Playwright captures of just the relevant part of the app, never your screen.

## Release checks passed

- **Secrets:** gitleaks found no leaks across all 57 commits and all tracked files.
- **Private files:** no `.env`, databases, protected data or owner notes were ever committed.
- **App security:** confirmed 127.0.0.1 binding, Host checks, per-launch token and CSP.
- **Screenshots:** all 101 tracked screenshots and every frame of the tour GIF show only demo or synthetic content.

## Why I didn't flip it public

Your project rules say only you change visibility, and a safety hook blocks the command. You also planned a `/security-review` first. The repo is ready; publishing takes about two minutes:

1. Optional: run `/security-review` in Claude Code on this repository.
2. Make it public:
   ```powershell
   gh repo edit WilliamEbong/qualia --visibility public --accept-visibility-change-consequences
   ```
3. On GitHub: Settings → Pages → Source: **GitHub Actions**. Then go to Actions → **Public demo** → **Run workflow** to publish the static demo. The first automatic run fails until Pages is enabled.
4. Optional: Settings → Emails → "Keep my email addresses private". Past commits keep your Gmail address; history must not be rewritten.

These steps are also recorded in docs/answers/06-public-release.md.

## Still open from before

- Two stale `qualia open --no-browser` servers from 2026-10-03 still hold `qualia.exe`. Close them, then run `uv sync` and `uv run qualia open`.
- The optional follow-up task "Shrink Qualia's 12 MB workspace payload" is waiting in the app.
