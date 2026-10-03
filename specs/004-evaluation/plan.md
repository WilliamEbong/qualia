# 004-evaluation implementation plan

## Entry gate and technical context

Phase 4 runs only after its preceding required gates; this plan does not bypass the runbook order. Main activates this supplied directory in .specify/feature.json, then runs analyze. Reuse the approved Python 3.14/uv, FastAPI/Typer/pydantic, SQLite and React 19/Vite/TypeScript stack. Use only the dependencies listed in docs01/02; pinned-version absence uses the documented nearest-release adaptation with evidence. Verify current version-accurate APIs with Context7 before implementation. These documents specify behavior and boundaries; they do not assert unverified library signatures.

Main owns migrations, openapi.json and backend protocol. Reconcile against the live Phase 1 contract before implementation; never silently edit an established contract in a worker lane. Tests are offline by default; live tests use the live marker and never run in CI. Every UI change needs Playwright MCP verification. Record progress/repairs through main in BUILD-STATE, without touching sacred documents.

## Architecture and file responsibilities

Main analysis on2026-10-03: required preceding offline contracts are verified. Native Codex setup/live
gates remain owner-pending; doc02's blocked-work ladder explicitly authorizes these independent
evaluation/demo tasks. No live gate is waived. The demo's visible database contains dev/validation
transcripts only; protected texts and gold stay in the sibling vault. Full source remains ignored.
Transcript split rounding/quality strata and known video overlap are fixed in docs/research/demo-data.md.

1. qualia/eval/{metrics,alpha,calibration}.py are sealed deterministic functions; qualia/io/benchmarks.py validates JSONL and orchestration outside eval obtains predictions through the Phase 3 router.
2. qualia/cli.py exposes benchmark import/evaluate/demo; Store records evaluation runs atomically. Filesystem orchestration handles split creation and manifests outside sealed modules.
3. scripts/fetch_demo.py pins remote source/checksum and writes only ignored data; qualia/io/demo.py translates dataset records into existing import/codebook/human-event operations. Main session owns contract changes.
4. tests/test_metrics.py, test_alpha.py, test_benchmarks.py and test_demo.py use small synthetic fixtures. A real fetch is a separate verified integration step, never an online dependency for CI.
5. web/src/lib/evaluation.ts obtains validation summaries; components render tables and existing suggestion ECE captions. Protected evaluation has no default web route.

## Constitution check

- I: Append-only evidence and required provenance stay enforced by Store/SQLite; never update historic coding, feedback, usage, egress, experiment or evaluation records.
- II: Codebook/methodology changes require explicit human action; automated paths use frozen versions.
- III: Evaluation remains sealed deterministic code; protected test contents never enter the optimizer.
- IV: Vendor launch/auth/HTTP isolation and schema validation remain mandatory; classification has no tools.
- V: Offline reading/manual work persists; external calls require project policy, availability and budget, with one egress record per attempt; localhost Host/token/headers remain effective.
- VI: No secrets, research DBs, protected vaults or raw demo data in Git; authorized public snapshots require a separate license check.
- VII: Verify stated behavior with fixtures, commands and browser evidence. No new dependency or speculative feature is authorized by this plan.

## Validation and handoff

Implement tasks in listed dependency order; a main-owned contract update must finish before consumers change. Re-run exact failed checks during repair. Use the spec success criteria and verbatim excerpts as the gate checklist, then run converge (at most three rounds per runbook), record unresolved issues honestly and preserve the resumable state. Phase-specific test files and evidence locations appear in tasks.md; filenames may follow an equivalent existing owner without adding duplicate abstractions.
