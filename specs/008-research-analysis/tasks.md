# 008 tasks

## Setup
- [ ] [T001] Main records researched semantics, freezes analysis input/output contracts in docs/CONTRACTS.md, activates feature and runs analysis against spec/plan/constitution.
## Foundation
- [ ] [T002] ENGINE writes hand-computed failing fixtures in tests/test_analysis.py for FR001–008, then implements sealed qualia/eval/analysis.py.
- [ ] [T003] Main adds read-only Store coordinator and safe reproducible exports in qualia/io/analysis.py, typed API models/routes and CLI; generates openapi.json and web/src/api/schema.d.ts. Cover FR001/002/010/012 with tests/test_analysis_api.py.
## User stories
- [ ] [T004] WEB implements lib state/query/drill-through/download helpers and Analysis component, covering FR002–009; add navigation and focused Vitest tests after frozen API lands.
- [ ] [T005] Extend scripts/build_snapshot.py and static adapter with a default report computed from public rows only; test FR011 and zero API behavior.
- [ ] [T006] Verify CSV/JSON/chart/Python/R export content and run the Python starter against a fixture per FR010/SC002; document scripts require explicit user execution outside Qualia.
## Verification
- [ ] [T007] Main uses Playwright MCP to verify live and static analysis, mobile layout, linked excerpts and downloads; save design-review/analysis/ evidence for SC001–004.
- [ ] [T008] Independent audit checks denominators, suggestions exclusion, protected/nonmutation and no-default-text export; repair exact failures, full offline regressions, spec convergence and README/BUILD-STATE update for SC005.
