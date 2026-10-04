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

## Approved Codex proposal implementation (2026-10-04)

Decision04 replaces only the blocked direct-editing Codex mechanism. Main owns strict OperatorProposal/OperatorResult adapters in qualia/ai/schemas.py, trusted inventory/validation/application in qualia/improve/proposal.py and experiment.py accounting/recovery integration. AI lane owns only codex_cli.py and its operator/no-tools tests. Extract the existing bounded structured-JSON transport without changing classifier behavior; run_operator returns validated proposal plus input_tokens/output_tokens/cli_version and never touches project files. The main coordinator builds the exact dispatch prompt before ledger admission, applies validated replacements inside its snapshot/recovery region, and generates reports itself. Reuse current JSON configuration parser, strict routing adapter and unchanged privacy/budget bound tuple. No new dependency, schema migration, API or UI contract.

Freeze protocol: run_operator(project, prompt, *, model=None, max_output_tokens=8192, report_path='experiments/0001.md') returns {hypothesis, edits:[{path, original_sha256, content}], input_tokens, output_tokens, cli_version}. project/report_path are compatibility inputs only; Codex must not read/write them. Proposal adapter rejects extras; operator transport preserves telemetry on malformed output. Limits:64 inventory files,64KiB/file,128KiB serialized dispatch;16 edits,64KiB/edit,128KiB aggregate UTF-8 replacements; hypothesis1–2000 chars. Inventory defaults to existing .txt/.md prompt files plus routing/segmentation JSON. Fail closed on unsafe or oversized permitted files. Exact identity includes device/inode/mode/link-count/mtime/size and content hash; recheck every input before writes. All edits validate first; I/O failures use existing snapshot restoration.

Verification order: strict adapters and red adversarial tests; production no-tools transport; trusted proposal application/ledger/rollback tests; independent review; one4-invocation-ceiling public synthetic live Codex experiment; full offline regression, docs, convergence and private CI. No unchanged frontend requires new browser work. Every constitutional principle remains satisfied by the original orchestration and narrower operator capability; no protected documents change except doc01 section10.

Decision04 implementation verified at0fcc799: native no-tools captures plus actual ChatGPT status check, strict bounded proposal/application, complete dispatch hash, rejection telemetry and partial-write recovery. Operator47 tests, coordinator/proposal72 passed with1platform skip, full offline534 passed/5skipped/6live deselected. Public synthetic Astra/Luna experiment passed1test in41.92s: three invocations, macro-F1/exact-match1.0 to1.0, ECE0 to0, agreement undefined, correct REVERT and unchanged methodology/provenance/clean Git. User guide now covers both operators. Private CI/final convergence follows; earlier native-direct isolation failures remain historical facts and that route is disabled.

Final private Checks37184680691 passed at e95972e on2026-10-04. T018 evidence is complete. Feature005 satisfies its approved scope; owner-run pre-public security review is a separate release action.
