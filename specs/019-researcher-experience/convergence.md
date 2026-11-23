# Convergence

- FR001-FR002: `benchmark_status`, `import_with_frozen_version` (shared with the CLI), GET/POST `/benchmarks` (dev/validation only); tests/test_benchmark_api.py.
- FR003, FR005: `benchmarkReason`, `experimentPrerequisites` (evaluation.test.ts); Evaluation Benchmarks card and Run gating; Experiments checklist; checked live.
- FR004: `studyStatus` (workspace.test.ts); Home status block; checked live.
- FR006-FR007: `matrixTotals`, `groupByCode` (workspace.test.ts); Matrix totals, Retrieval groups; checked live.
- FR008: migration 006, `MemoInput.author`, `memoMeta` (test_memos.py, workspace.test.ts); checked live with a v5 upgrade.
- FR009: Analysis `section` state and views; checked live (overview fits one screen; chart selection opens evidence).
- FR010: read-only layout and single notice; demo e2e passes.
- SC004: Python 706 passed, web 71 passed, typecheck, build, demo e2e; OpenAPI and types regenerated.
Not built (owner decision, OWNER-NEEDED.md): per-card trust caption collapse; code-colour highlight change.
