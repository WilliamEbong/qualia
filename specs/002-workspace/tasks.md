# 002-workspace tasks

All items are open. Dependencies: each task requires earlier tasks in its group and all previous groups unless the task explicitly says it is an independent verification. No parallel lane starts before main freezes its consumed contracts. Main owns pointer updates, analysis/convergence, commits and BUILD-STATE; workers report evidence.

## Setup

- [ ] [T001] Read frozen contracts in qualia/store/migrations/001_initial.sql, qualia/ai/protocol.py and openapi.json; document any required main-owned contract changes in specs/002-workspace/plan.md.
- [ ] [T002] Verify approved Recogito, TanStack Table, shadcn, FastAPI, Typer and openapi-typescript APIs with Context7; record saved-span reload probe and selected adapter in docs/research/web-apis.md.

## Foundational work

- [ ] [T003] Add synthetic TXT/MD/CSV, malformed-row and Unicode span fixtures in tests/fixtures/workspace/; define expected import/export results before implementing FR-001/002/006/009.
- [ ] [T004] Implement validated adapters in qualia/io/imports.py and pure segmentation in qualia/core/segmentation.py; test all modes and exact offsets in tests/test_import.py.
- [ ] [T005] Extend qualia/store/db.py with atomic idempotent import, cases, attributes and source lineage; verify rollback and duplicate hashes in tests/test_workspace_data.py.

## User stories in priority order

- [ ] [T006] Implement human codebook hierarchy/archive/freeze in qualia/core/codebook.py and qualia/store/db.py; prove cycle rejection and version immutability in tests/test_codebook.py.
- [ ] [T007] Implement span assignment/removal and memo operations in qualia/store/db.py; test overlapping codes, actor/version validation and history in tests/test_coding.py.
- [ ] [T008] Implement retrieval and distinct-segment matrix queries in qualia/store/db.py; assert drill-down/count equivalence in tests/test_retrieval.py.
- [ ] [T009] Implement CSV/JSON/no-text/reproducibility exports in qualia/io/exporters.py; cover text leakage and vault exclusion in tests/test_export.py.
- [ ] [T010] Add CLI operations in qualia/cli.py and validated routes in qualia/server/{api_models,app}.py; main regenerates openapi.json and web/src/api/schema.d.ts after server tests pass.
- [ ] [T011] Implement workspace data/state/Unicode selection and keyboard controls in web/src/lib/workspace.ts with Vitest coverage under web/src/lib/; consume the regenerated contract.
- [ ] [T012] Build source/case navigation, transcript span viewer, codebook, memos, retrieval and matrix markup in web/src/components/ and web/src/pages/ using doc04 trust semantics.

## Validation and completion

- [ ] [T013] Run offline import/coding/export/server checks and web typecheck/test/build; fix causes through the repair loop without changing protected contracts.
- [ ] [T014] Verify all affected screens with Playwright MCP; save keyboard/span reload/matrix evidence under design-review/phase-2/ and hand criterion results to the main session for BUILD-STATE.
- [ ] [T015] Main session activates specs/002-workspace in .specify/feature.json, runs analyze before implementation and converge after it, and records its gate/commit in docs/BUILD-STATE.md.
