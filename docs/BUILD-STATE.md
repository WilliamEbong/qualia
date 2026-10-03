BUILD IN PROGRESS

# Qualia build state

Started 2026-10-03. Baseline: f1d8719. Owner authorized autonomous implementation of docs 01–05, with Jev account already created. No application code existed at baseline. Source documents and ratified constitution remain protected.

## Adjusted plan and checkpoints

- [x] P0.1 Tooling, login, model and toolbelt audit.
- [~] P0.2 Environment schema, service/classification pings.
- [x] P0.3 Repo comparison and workstream classification.
- [x] P0.4 Project safety kit, entrypoints, rule probes.
- [x] P0.5 Constitution verification, private remote, subagent probe.
- [x] P1.1 Spec Kit foundations specification → plan → tasks → analyze.
- [x] P1.2 Python/web scaffolds, CI, environment template.
- [x] P1.3 SQLite schema, migrations, append-only provenance and workspace initialization.
- [x] P1.4 Secure local API skeleton, generated contract; I1/I7 gate; converge.
- [x] P2.1 Spec Kit workspace artifacts and analysis.
- [x] P2.2 Import, segmentation, cases, codebook versions, memos and export.
- [x] P2.3 Workspace UI, keyboard/span coding, retrieval and matrix; converge.
- [x] P3.1 Spec Kit AI coding artifacts and analysis.
- [~] P3.2 Backends, schemas, routing, budget, cache and egress ledger.
- [~] P3.3 Review UI and feedback, I4/I5/budget gate; converge.
- [ ] P4.1 Spec Kit evaluation artifacts and analysis.
- [ ] P4.2 Metrics, benchmarks, pinned demo data and split manifests.
- [ ] P4.3 Evaluation UI, metric/oracle/idempotency gate; converge.
- [ ] P5.1 Spec Kit improvement artifacts and analysis.
- [ ] P5.2 Protected experiment protocol, policy and operator lanes.
- [ ] P5.3 History UI, I2/I3 and MVP browser gate; converge.
- [ ] P6.1 Security/hygiene audits, CI and secret/data checks.
- [ ] P6.2 Live Claude/Codex experiment parity.
- [ ] P7.D0 Design guard and baseline screenshots.
- [ ] P7.D1 Tokens, fonts, theme, DESIGN.md.
- [ ] P7.D2 Workspace and review presentation.
- [ ] P7.D3 Experiments presentation.
- [ ] P7.D4 Codebook and matrix presentation.
- [ ] P7.D5 Landing/demo presentation.
- [ ] P7.D6 Motion, accessibility and mobile checks.
- [ ] P7.D7 Design acceptance, final screenshots and bounded critique loop.
- [ ] P8 Portfolio Spec Kit artifacts, snapshot, demo, README, Pages and performance gate (sacrificial).
- [ ] P9 Jev Spec Kit artifacts, adapter, fixture tests and owner setup guide (sacrificial).
- [ ] P10 Full acceptance sweep, subscription policy recheck, final evidence/report.

## Workstream audit

3.1 repo/kit: partial (Git, Spec Kit, docs, runner). 3.2–3.14: not started. Constitution v1.0.0 already ratified and consistent with docs 01 §6 and §4: preserve, do not recreate. No OWNER-ANSWERS.md. No .env, database, migrations or app yet; database connectivity does not apply until P1.

## Preflight evidence

| Tool | Observed |
|---|---|
| Git | 2.48.1.windows.1 |
| GitHub CLI | 2.93.0; authenticated as WilliamEbong outside sandbox |
| uv | 0.11.29 |
| Python | CPython 3.14.3, C:/Python314/python.exe |
| Node / npm | 24.14.1 / 11.11.0 |
| Codex | 0.160.0 after authorized update; gpt-6-astra and gpt-6-luna listed |
| Claude Code | 2.1.284; claude.ai subscription authenticated |
| Windows PowerShell | 5.1.19041.7725; current tool shell also has PowerShell 7.6.5 |
| Toolbelt | Playwright, Context7, Firecrawl callable in desktop; CLI configuration checks pending |

## Decisions and assumptions

- Preserve pre-existing docs, runner and constitution. Perform phases in runbook order; only independent research overlaps.
- No secret was present in a repository .env. Prepare placeholders and leave Jev off until the owner fills the local file. Jev never blocks core work.
- Default sandbox cannot access user credential stores or uv cache. Confirm identity using narrowly scoped escalated checks; do not ask owner to reauthenticate working logins.
- Main session owns contracts and commits. Subagents are explicitly authorized by docs 01–02.

## Repair log

1. Preflight: `gh auth status` reported invalid token, `codex login status` reported Not logged in, `uv python list --only-installed` failed opening user cache. Diagnosed as sandbox access, not missing tools/logins. Exact checks passed with scoped escalation. No credential or guard changes.

## Evidence and remaining gates

Implementation, live calls, private remote and acceptance gates are pending. No claim of completion.

Spec Kit analysis (001): 7 FR, 3 SC, 8 tasks; 100% coverage; no critical findings. Prerequisite script passed; no extensions configured. Independent P0 pings/kit finishing. Two harmless preflight command issues: DOCX console encoding requires UTF-8; invalid inline here-string replaced by apply_patch before any write.



## Phase 0/1 evidence, 2026-10-03
- Private repository verified: https://github.com/WilliamEbong/qualia (`visibility: PRIVATE`). Codex updated using owner runbook from 0.144.6 to 0.160.0; catalog includes gpt-6-astra. Existing runner unmodified; explicitly pass `-Model gpt-6-astra` when launching it.
- Constitution verification complete, unchanged. Safety kit JSON/TOML and Node syntax validated; 10 build + 6 design guard probes passed. Five mandated Codex rules return forbidden. Fresh Claude hook activation remains pending its quota reset; scripted guard proof is not a claim of hook activation.
- Claude toolbelt: Context7/Firecrawl present; standalone Claude Playwright process failed to connect. Desktop Playwright MCP works and is used. No duplicate servers installed; no user config changes.
- AI preflight details: docs/research/preflight-ai.md. Codex Luna synthetic classification and Astra subagent probe passed. Claude authenticated but quota-limited until 18:10 Denver; this defers only Claude live checks. Additive Codex isolation skips user config and disables agents for classification.
- Foundation test command `.venv/Scripts/python.exe -m pytest -q`: **11 passed**. I1 append-only tables and required provenance, I7 Host/token/origin/headers, migration idempotency, review atomicity and manifest tampering verified. Ruff clean.
- Web: generated API types, tsc, Vitest (1), Vite production build passed; npm install audit 0 vulnerabilities. Playwright navigated http://127.0.0.1:8765, confirmed title and foundation content. Screenshot: design-review/foundations.png. Final product UI is not yet built.
- No tracked research/local secret files. Source docs 02–05 diff empty. Runtime dependencies match requested release families (FastAPI 0.142.2, Typer 0.27.2, pydantic 2.13.5, uvicorn 0.54.0, sklearn 1.9.1).
- Contracts documented in docs/CONTRACTS.md; database/API/backend lane ownership stays with main.

Repair cycles: pytest failed before fixtures due sandbox temp-directory access; exact command passed with scoped escalation (no changed tests). Independent verifier reproduced CTE-prefixed write in read helper and incomplete model provenance; fixed with SQLite authorizer and conditional constraints; regression test passes. Also repaired project/vault resolved-path containment, migration backup version advancement and partial-init retry preservation before schema freeze. Two benign warnings remain: installed Starlette deprecates httpx TestClient (works); pytest cache access warning from mixed sandbox ownership (tests still execute).


Phase1 convergence: 7 FR, 3 SC, 8 tasks and six implementation-plan decisions reviewed. Independent verifier confirms I1/I7, sole writer, exact generated schema, core boundary and protected source preservation. Sidecar/backup data guard gap corrected with 8 forbidden-path fixtures and matching ignores; suite now 21 tests. Foundation main-branch CI SUCCESS at ae770ec: https://github.com/WilliamEbong/qualia/actions/runs/37157791283. Contracts FROZEN (001_initial.sql, current OpenAPI and backend protocol); additive API mutations remain main-owned. Converged for Phase1. Phase0 Claude live/hook probes still quota-deferred; no blocker to offline workspace implementation.


Phase2 analysis: 11 FR, 5 SC and 15 tasks; all obligations covered, no critical or high conflicts. Phase2 consumers retain frozen schema and code-point offsets; main adds typed mutation endpoints. Engine lane started, frontend follows regenerated API. Sidecar guard now also covers sqlite3 variants.


Phase2 ENGINE/SERVER checkpoint: import TXT/MD/CSV, all three segmentation modes, atomic case/attribute/lineage writes, cycle-safe human codebook edits/freeze, exact overlapping Unicode spans, memos, retrieval, distinct-segment matrix, CSV/JSON and no-text/reproducibility exports implemented. Added matching CLI/API operations and regenerated OpenAPI/TypeScript types. Independent lane reports 57 passing engine/foundation/API tests; root complete suite includes launcher-setting regression. UI integration and browser gate remain in progress. No-text bundles explicitly mark redacted snapshots; full textual reproduction requires explicit include-text. CSV text fields neutralize formula prefixes.

Additional routine command correction: npm run api was invoked once from the repository root (no package.json); rerun from web succeeded. No code or detector change. Two non-secret .env launcher settings now load independently; blank lines cannot consume the next setting, proved by regression test. TYPESAFE_API_KEY remains unused pending its isolated backend.

Phase2 final: 60 Python tests passed; Ruff clean; frontend 7 Vitest tests, TypeScript and Vite build pass; dependency audit 0. Playwright MCP verified import, frozen codebook, 5 keyboard-coded segments, emoji/combining span 1:8 with overlapping codes after reload, removal provenance, draft rename retaining frozen event names, memo linked to segment, case matrix count 5 matching retrieval 5 distinct/6 coded excerpts, bundle download, and project-switch filter reset. Screenshots design-review/phase-2/. Review fixes: no-text attributes now redacted and marked; CLI reads exact bytes and supports version_of; UI historical labels use snapshots and project switches reset stale filters. Regression tests pass. Routine test fixture path corrected (home/projects/study); no detector changes. Recogito viewport culling explained full-page screenshot appearance; saved anchors pass with actual visible highlights. Spec Kit convergence: 11 FR, 5 SC, 15 tasks plus plan/constitution reviewed; zero remaining Phase2 gaps. Source docs02–05 unchanged. Phase2 gate PASS; Phase0 live quota/isolation remains separately pending.

Phase3 analysis: 11 FR, 5 SC, 13 tasks; 100% coverage. One necessary main-owned schema addition (002_attempt_accounting.sql) supplies CLI version and immutable reservation/completion linkage, preserving migration001/triggers. Atomic BEGIN IMMEDIATE admission precedes provider dispatch and egress; no in-memory budget-only lock. Implementers own disjoint AI backend/coordination and WEB lanes. Codex live classification remains unavailable pending honest generation-bound decision; operator confinement adaptation remains gated. Offline features proceed; no load-bearing external acceptance claimed.

Phase2 main CI SUCCESS at bed61f6: https://github.com/WilliamEbong/qualia/actions/runs/37160288072. Phase3 Store atomic reservation/concurrent admission tests: 2 passed; migration/provenance/workspace/CLI regressions: 15 passed. Open launcher now waits for Uvicorn's verified started signal (after socket bind) before opening browser; failed startup cancels the launcher. Context7 plus installed0.54 source verified API.
