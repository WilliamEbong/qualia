# Tasks

- [ ] [T001] Failing tests: migration 003 and triggers, store record/decide (accept new, accept revision with edits, reject, decide twice, frozen versions unchanged) in tests/test_code_proposals.py; append-only coverage in tests/test_foundations.py (FR001–002, FR007, SC001).
- [ ] [T002] Migration 003, `APPEND_ONLY_V1`/`APPEND_ONLY`/`TABLES`, Store `record_code_proposals`, `decide_code_proposal`, `code_proposal_evidence` (FR001–002, FR007).
- [ ] [T003] Pure miner qualia/core/proposals.py with unit tests for the three signals, thresholds and de-duplication (FR003).
- [ ] [T004] AI schema/validation (fabricated quote, unknown evidence id, wrong kind, name collision, unsent target) and `proposal_prompt` (FR005).
- [ ] [T005] Backends: generalised Claude/Codex transport with unchanged classification tests, `propose` on claude/codex/fake, protocol note (FR006).
- [ ] [T006] qualia/ai/proposals.py orchestration with router-gate tests (external off blocks with no usage, egress + usage rows on success, zero coding events, rules/jev refused, validation failure stores nothing) (FR004–006).
- [ ] [T007] API routes, workspace payload, OpenAPI + web types regenerated; CLI `codebook propose|proposals|decide`; export tables; API/CLI/export tests (FR008).
- [ ] [T008] Web: entities, lib/proposals.ts (+ Vitest), Codebook Proposals section, accept-through-editor, origin caption, demo tolerance (FR007–008, SC002).
- [ ] [T009] Playwright MCP verification with the fake backend at 1280/375, light/dark; demo build zero `/api/` (SC002–003).
- [ ] [T010] Docs (USER-GUIDE, README, CONTRACTS), live check or recorded skip, full verification, convergence, BUILD-STATE (FR009, SC003–004).
