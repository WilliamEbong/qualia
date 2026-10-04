# 005-improvement-loop implementation plan

## Entry gate and technical context

Phase 5 runs only after its preceding required gates; this plan does not bypass the runbook order. Main activates this supplied directory in .specify/feature.json, then runs analyze. Reuse the approved Python 3.14/uv, FastAPI/Typer/pydantic, SQLite and React 19/Vite/TypeScript stack. Use only the dependencies listed in docs01/02; pinned-version absence uses the documented nearest-release adaptation with evidence. Verify current version-accurate APIs with Context7 before implementation. These documents specify behavior and boundaries; they do not assert unverified library signatures.

Main owns migrations, openapi.json and backend protocol. Reconcile against the live Phase 1 contract before implementation; never silently edit an established contract in a worker lane. Tests are offline by default; live tests use the live marker and never run in CI. Every UI change needs Playwright MCP verification. Record progress/repairs through main in BUILD-STATE, without touching sacred documents.

## Architecture and file responsibilities

1. qualia/improve/{experiment,policy}.py coordinate snapshot, operator, scope/hash checks, evaluator and decisions. Pure policy code accepts metrics; filesystem/process orchestration remains outside sealed core/eval.
2. Vendor run_operator lives only in qualia/ai/backends/{claude_cli,codex_cli}.py; fake operator fixture is local. Store is the only DB writer, ledger the only usage orchestration path.
3. Filesystem rollback uses validated absolute project-root containment and known snapshot paths. Never issue git clean on arbitrary or global directories; application-scoped cleanup is distinct from agent shell prohibitions.
4. Persist experiment DB records through Store and human-readable project experiments/NNNN.md; coordinate commit/tag and append-only records so failures never falsely claim KEEP. Refuse duplicate tags and recover interrupted attempts explicitly.
5. web/src/lib/experiments.ts owns data/state; components/pages render the timeline and detail view. Main owns API/DB/protocol amendments and type regeneration.

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

## Implemented protocol and gates (2026-10-03)

The orchestrator requires clean Git and an exclusive operation lock, snapshots the full project tree (including ignored files and file modes), and takes a consistent SQLite backup. Only routing, segmentation, prompt changes and designated new report/proposal outputs are accepted. Pinned manifests are compared without rebaselining existing artifacts. Unauthorized changes restore from the trusted snapshot; vault tampering preserves evidence and flags owner recovery without reading gold content. A pending recovery journal blocks ordinary writers when interrupted Git/DB accounting cannot be resolved safely.

Baseline, candidate and confirmation use the same validation benchmark with caches bypassed. Protected evaluation is never called. Store remains sole writer; ledger accounting precedes dispatch. KEEP commits/tags before the append-only experiment row; failed coordination preserves recovery evidence. Fake workflows and exact I2/I3 checks pass. Native operators remain unavailable pending actual Windows isolation and per-process-versus-request accounting decisions, so live parity is not claimed. MCP executed the full default-demo acceptance sequence; the opt-in test file records the same sequence for a fresh explicitly selected fixture.

## Resume plan (2026-10-04)

Complete T004 under the recorded owner decisions. Separate AI lanes own vendor adapters and native synthetic path probes; main owns experiment coordination, immutable usage and live experiment fixtures. Test admission before dispatch, failed-attempt telemetry, unchanged provenance/rollback and strict per-vendor readiness. Use small synthetic workspaces for live operator verification to avoid consuming hundreds of default-demo classifier invocations. Do not represent offline fake evaluation as native classifier quality. Finish with exact I2/I3 tests, full regression, private CI and truthful convergence.

Resume outcome: Claude FR003 implementation and synthetic live verification passed (Opus operator, Haiku validation,1.0→1.0 macro-F1, correct REVERT). Full offline445 passed/5 skipped/6 live deselected. Codex FR003 remains blocked by demonstrated outside-read and network failures in native0.160.0, with no safe activation claim. T014 records the remaining convergence work; all other previously verified functionality remains.
