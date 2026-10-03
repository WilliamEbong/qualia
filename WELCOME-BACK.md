# Qualia — build in progress

Foundations and the offline workspace are implemented and verified: import TXT/Markdown/CSV, cases, frozen codebooks, overlapping span/keyboard coding, memos, retrieval, matrix and auditable exports. Research projects remain outside this repository. Latest completed checkpoint: bed61f6, private repository, passing CI; 60 Python tests and 7 web tests pass with Playwright evidence. AI coding/review is in progress; evaluation and improvement follow. Read `docs/BUILD-STATE.md` for exact progress.

Run `uv run qualia init my-study`, then `uv run qualia open` for the current manual workspace. Jev account exists; billing/key remain owner-managed and optional. Follow docs/JEV-SETUP.md; never paste a key in chat. Native Codex setup/bounds decisions are recorded in ignored OWNER-NEEDED.md while unaffected build work continues. Claude live preflight is quota-deferred until 18:10 Denver on October 3. No live parity or build-complete claim is made.

Resume from this folder with `codex` and the recovery prompt in `scripts/prompts/recovery.md`, or use the existing runner after its preflight gates pass:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run-build.ps1
```

Do not mark BUILD COMPLETE until all load-bearing acceptance checks have evidence.
