# Feature planning coverage

Prepared on 2026-10-03 for the six explicitly named doc02 feature directories. These are specification, plan and task artifacts only: no feature is implemented, analyzed, converged or acceptance-certified by this report.

## Sources and workflow

Read the installed lean `speckit-specify`, `speckit-plan` and `speckit-tasks` skills, constitution v1.0.0 and docs01–05. Followed the user-supplied directories without asking again. The main agent owns `.specify/feature.json`; this lane deliberately stages future features without changing that pointer. Main must activate each feature in phase order, inspect current contracts, run analyze, implement and converge. Existing 001 artifacts, source documents, BUILD-STATE and application code were not changed by this planning lane.

Each spec includes authoritative workstream and relevant final-acceptance lines copied directly from doc02, testable numbered functional requirements/success criteria, user scenarios and informed defaults. The 3.5 workstream is quoted in full where relevant and explicitly apportioned among workspace, AI review and experiment history. Shared final gates retain their original wording and are not falsely represented as wholly owned by an earlier phase.

## Coverage

| Feature / phase | Workstreams | Requirements | Criteria | Tasks | Principal evidence |
|---|---|---:|---:|---:|---|
| 002-workspace / 2 | 3.3, non-AI 3.5, 3.9 | 11 | 5 | 15 | TXT/MD/CSV idempotency; Unicode/overlapping spans; immutable freeze; memo/retrieval/matrix; no-text/export; Playwright keyboard/reload |
| 003-ai-coding / 3 | 3.6, review 3.5 | 11 | 5 | 13 | I4/I5/budget; actual no-tools probe; per-attempt ledger/egress; cache invalidation; duplicate review; trust markers |
| 004-evaluation / 4 | 3.7, 3.10 | 10 | 5 | 13 | hand metrics; three alpha oracle fixtures; split isolation; pinned license/checksum; demo idempotency; ECE/n/a |
| 005-improvement-loop / 5 | 3.8, history 3.5 | 12 | 5 | 13 | I2/I3; policy boundaries/confirmation; scope and rollback attacks; KEEP/tag; full fake MVP/export |
| 006-portfolio / 8 | 3.12 | 8 | 5 | 11 | licensed snapshot; zero API requests; read-only demo; truthful README; private-until-owner Pages gate; Lighthouse |
| 007-jev-backend / 9 | 3.11 | 10 | 5 | 11 | strict primitive HTTP contract; key/vendor isolation; double opt-in; USD/attempt bounds; redaction; honest live/recorded status |

Total: 62 functional requirements, 30 success criteria and 76 open implementation/verification tasks. Task IDs are local to each feature. Groups execute setup → foundations → prioritized stories → verification, with earlier groups and consumed main-owned contracts required before consumers proceed.

## Requirement-to-task map

| Feature | Implementation and validation coverage |
|---|---|
| 002 | FR001–003 → T003–005/T010/T013; FR004 → T006/T010/T012; FR005–006 → T007/T011/T014; FR007 → T007–008/T010/T012; FR008 → T011–014; FR009–010 → T009/T013; FR011 → T001/T010/T013 |
| 003 | FR001–003 → T001–004/T011; FR004–005 → T005/T007/T011; FR006 → T005/T011; FR007 → T006; FR008–009 → T008–010; FR010 → T010/T012; FR011 → T011 |
| 004 | FR001 → T005/T007; FR002/004 → T002–003/T006; FR003 → T004; FR005/008 → T005–007; FR006 → T001/T008; FR007 → T009/T012; FR009 → T010–011/T013; FR010 → T001/T008/T012 |
| 005 | FR001–002 → T001/T005–006; FR003 → T004; FR004 → T005/T007; FR005–006 → T002–003/T006; FR007–008 → T007–008; FR009 → T005/T007/T012; FR010 → T010/T012; FR011 → T004/T009; FR012 → T011–012 |
| 006 | FR001 → T006; FR002 → T001–003/T009; FR003 → T004–005/T010; FR004 → T005/T010; FR005 → T007; FR006 → T008; FR007 → T005/T007/T009–010; FR008 → T010 |
| 007 | FR001/004–006 → T001–004/T006/T009; FR002 → T003/T008–009; FR003/007 → T005/T009; FR008 → T004–005/T009; FR009 → T002/T007; FR010 → T008 |

## Decisions and activation checks

- 002 follows the main agent's proposed mutations and `qualia/io/imports.py` owner. Stored span offsets are Unicode code points; browser UTF-16 conversions need explicit regression fixtures. Preserve existing contract names where equivalent rather than creating duplicate modules.
- Matrix counts are distinct current coded segments per case/code. Export text exclusion covers all transcript excerpts; protected vault is never included by default.
- 003 requires proving the actual no-tools surface for CLI classification; doc02's shell/search flags are necessary but do not by themselves prove inherited MCP/app integrations are absent. Exact additional isolation switches must come from verified installed CLI behavior.
- ECE before evaluation is explicitly unavailable. Scores retain model-reported wording and cannot be marketed as empirical accuracy.
- 004 fixes metric denominator, set-match, zero-division and n/a behavior before experiments. Dataset pin, redistribution rights and fallback reachability need real evidence; synthetic fixtures never stand in for real-data claims.
- 005 requires clean baselines and scope checks covering tracked/untracked files, confirmation runs and safe rollback of unauthorized project changes. Vault tampering rejects and flags without reading protected data to repair it. Crash/commit/tag recovery needs tests; no false KEEP after failed persistence.
- 006 stays private until the owner changes visibility/enables Pages. Any missing demo data-source logic belongs to implementation after design mode is off, not to the presentation-only restyle. No invented live URLs or performance numbers.
- 007 uses the existing dated `docs/research/jev.md` research. Model/pricing/OpenAPI must be rechecked before a live call. Synthetic fixtures and sanitized recorded provider responses are labeled separately; an absent key defers only optional live coverage.
- Phase 6 hygiene/parity and Phase 7 D0–D7 design remain governed by their separate runbooks; they are not silently removed because they have no new numbered feature directory here.
- The Phase 7 design guard protects logic paths and trust rendering; styling cannot remove provenance, model-reported/ECE captions, review reasons, egress notices or KEEP/REVERT grammar.

## Verification

The planning check compares every quoted workstream and acceptance line against the unchanged doc02 source, checks that each feature has all three files with expected FR/SC/task counts and ordered unique IDs, and checks required spec sections. Passing that check validates artifact structure and source quotation only; it is not the later Spec Kit analyze/converge or product gate.
