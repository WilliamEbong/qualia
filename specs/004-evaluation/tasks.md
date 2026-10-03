# 004-evaluation tasks

All items are open. Dependencies: each task requires earlier tasks in its group and all previous groups unless the task explicitly says it is an independent verification. No parallel lane starts before main freezes its consumed contracts. Main owns pointer updates, analysis/convergence, commits and BUILD-STATE; workers report evidence.

## Setup

- [ ] [T001] Verify scikit-learn metric APIs through Context7 and inspect dataset primary sources; record pin/checksum/license and label definitions in DATA-LICENSES.md and specs/004-evaluation/plan.md.

## Foundational work

- [ ] [T002] Create hand-computed multi-label, empty/degenerate, calibration and three independent alpha fixtures under tests/fixtures/evaluation/; document formulas and denominators in tests/test_metrics.py.
- [ ] [T003] Implement sealed metrics/calibration in qualia/eval/{metrics,calibration}.py with scikit-learn; prove exact/partial match, n/a and zero-division behavior.
- [ ] [T004] Implement qualia/eval/alpha.py and dev-only oracle comparisons in tests/test_alpha.py; confirm krippendorff is absent from runtime dependencies in pyproject.toml.
- [ ] [T005] Implement JSONL adapters and deterministic transcript splits in qualia/io/benchmarks.py; test invalid records, split disjointness and manifest containment in tests/test_benchmarks.py.

## User stories in priority order

- [ ] [T006] Implement evaluation orchestration outside qualia/eval, routing predictions through existing AI policy, storing results via Store and emitting MD/JSON; prove coding_events unchanged.
- [ ] [T007] Add benchmark/evaluate commands in qualia/cli.py with explicit --protected access; test ordinary validation cannot read vault and tampering fails before evaluation.
- [ ] [T008] Implement pinned SHA-256 data fetch in scripts/fetch_demo.py, using the pre-authorized fallback only with logged reachability evidence; keep demo/data ignored.
- [ ] [T009] Implement qualia/io/demo.py case/attribute/codebook/human-label mapping using existing stores/importers; test two-run idempotency in tests/test_demo.py.
- [ ] [T010] Add validation-only metric API models/routes and regenerate openapi.json and web/src/api/schema.d.ts via main; do not expose protected records.
- [ ] [T011] Implement evaluation state and ECE lookup in web/src/lib/evaluation.ts, render metric tables and truthful n/a captions in web/src/components/; add Vitest states.

## Validation and completion

- [ ] [T012] Run exact metric/alpha/idempotency gates, sealed-import and data scans plus Python/web checks; record actual real-data counts separately from synthetic fixture results.
- [ ] [T013] Verify evaluation and ECE UI with Playwright MCP, save design-review/phase-4/ evidence, and deliver acceptance results to main for convergence and BUILD-STATE.
