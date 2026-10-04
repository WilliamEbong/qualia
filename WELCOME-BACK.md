# Qualia — build in progress

The offline workspace, AI review, evaluation and guarded improvement loop are implemented and verified. The real AnnoMI demo passed the five-code/review/KEEP/export browser workflow with a scripted fake backend. Native Claude and Codex readiness remains disabled pending the recorded request-accounting, isolation and output-bound decisions. Research projects remain outside this repository. Last pushed checkpoint: 8029a36, private CI success. Presentation and portfolio verification are in progress. Read `docs/BUILD-STATE.md` for exact evidence.

Run `uv run qualia open` to use the populated demo, or `uv run qualia init my-study` for a new study. Jev account exists; billing/key remain owner-managed and optional. Follow [the detailed Jev setup guide](docs/JEV-SETUP.md); never paste a key in chat. Native setup/accounting decisions are recorded in ignored OWNER-NEEDED.md. Automatic review rejected a private live Claude diagnostic after quota reset; no live call started. No live parity or build-complete claim is made.

Resume from this folder with `codex` and the recovery prompt in `scripts/prompts/recovery.md`, or use the existing runner after its preflight gates pass:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run-build.ps1
```

Do not mark BUILD COMPLETE until all load-bearing acceptance checks have evidence.
