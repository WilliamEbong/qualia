# Plan

1. `qualia/server/app.py`: drop `current_codings` from the per-table copy and add `current_coding_ids` (ordered). `api_models.Workspace`: new field, `current_codings` defaulted to `[]`.
2. `web/src/lib/entities.ts` `hydrateWorkspace()`; `lib/workspace.ts` applies it on reload. Regenerate OpenAPI and types.
3. Measure on a scratch copy of the demo project; verify Workspace, Matrix and Analysis with Playwright.

Ponytail: no pagination, lazy loading or compression (gzip was rejected earlier for loopback CPU cost); remove only the duplicate copy, the largest single cost.
