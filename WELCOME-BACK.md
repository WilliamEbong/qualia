# Qualia — build in progress

Baseline contains the approved docs and runner, no application. Phase 0 audit is underway. Read `docs/BUILD-STATE.md` for completed checks and remaining phases. Jev account exists; key remains owner-managed and optional.

Resume from this folder with `codex` and the recovery prompt in `scripts/prompts/recovery.md`, or use the existing runner after its preflight gates pass:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run-build.ps1
```

Do not mark BUILD COMPLETE until all load-bearing acceptance checks have evidence.
