# Qualia — build in progress

Foundations and the offline workspace are implemented and verified. AI coding/review, bounded vendor adapters, exact cache/provenance and evaluation metrics are implemented with targeted passing tests. Native Codex remains disabled pending the recorded isolation/bounds decisions. Phase4 demo/benchmark and evaluation browser verification are in progress; independent improvement policy follows. Research projects remain outside this repository. Last fully verified phase checkpoint: bed61f6 (private CI success); later checkpoints are resumable work, not a build-complete claim. Read `docs/BUILD-STATE.md` for exact progress.

Run `uv run qualia init my-study`, then `uv run qualia open` for the current manual workspace. Jev account exists; billing/key remain owner-managed and optional. Follow docs/JEV-SETUP.md; never paste a key in chat. Native Codex setup/bounds decisions are recorded in ignored OWNER-NEEDED.md while unaffected build work continues. Claude live preflight is quota-deferred until 18:10 Denver on October 3. No live parity or build-complete claim is made.

Resume from this folder with `codex` and the recovery prompt in `scripts/prompts/recovery.md`, or use the existing runner after its preflight gates pass:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run-build.ps1
```

Do not mark BUILD COMPLETE until all load-bearing acceptance checks have evidence.
