# 005-improvement-loop tasks

Offline tasks below are verified; T004 retains its native readiness gate. Dependencies: each task requires earlier tasks in its group and all previous groups unless the task explicitly says it is an independent verification. No parallel lane starts before main freezes its consumed contracts. Main owns pointer updates, analysis/convergence, commits and BUILD-STATE; workers report evidence.

## Setup

- [x] [T001] Read frozen policy templates, manifest and evaluator contracts; write explicit snapshot/output-scope and interruption-recovery decisions in specs/005-improvement-loop/plan.md.

## Foundational work

- [x] [T002] Add synthetic candidate/baseline/challenge fixtures and fake operator attack cases under tests/fixtures/improve/; test policy boundaries before implementation in tests/test_improve_policy.py.
- [x] [T003] Implement pure threshold/confirmation decisions in qualia/improve/policy.py; cover gain, priority tolerance, challenge, tests, call ratio and zero-baseline behavior.
- [x] [T004] Implement bounded run_operator in qualia/ai/backends/{claude_cli,codex_cli}.py and fake operator support; verify executable isolation, cwd, tools, prompts and egress accounting in tests/test_operator_backends.py.
- [x] [T005] Implement clean-baseline snapshot, canonical path containment, scope diff and protected-hash validation in qualia/improve/experiment.py; test tracked/untracked/path-escape attacks.

## User stories in priority order

- [x] [T006] Integrate baseline/candidate/confirmation evaluation in qualia/improve/experiment.py without protected-data reads or coding-event changes; prove misleading operator text cannot alter policy.
- [x] [T007] Implement safe snapshot rollback of unauthorized and mutable changes, preserving pre-existing files; test methodology/codebook attacks and clean Git status in tests/test_improvement.py.
- [x] [T008] Implement KEEP commit/tag, REVERT reporting and Store experiment records with recovery behavior; test duplicate tags, failed commit and interrupted attempt handling.
- [x] [T009] Add improve CLI and read-only history API in qualia/cli.py and qualia/server/{api_models,app}.py; regenerate openapi.json/types through main and include experiment data in existing exporters.
- [x] [T010] Implement web/src/lib/experiments.ts plus timeline/detail markup under web/src/components/ and pages/; preserve fixed KEEP/REVERT grammar and measured metric displays.

## Validation and completion

- [x] [T011] Create tests/e2e/mvp.spec.ts for demo → five keyboard codes → fake AI → accept/reject → measured gain/KEEP/tag → bundle provenance; run all exact I2/I3 gates.
- [x] [T012] Use Playwright MCP to verify affected history/MVP screens; save evidence in design-review/phase-5/ and record live parity prerequisites in specs/005-improvement-loop/plan.md.
- [x] [T013] Main runs phase analysis/convergence, full offline checks and gate reporting; Phase 6 owns scripts/smoke-agents.ps1 live parity and security/public-data sweep.

## Phase 1: Convergence

- [x] [T014] Complete Codex operator activation using the owner-approved no-action-tools proposal mechanism in decision04; verify native empty tool registry, trusted application scope, public admission, failure telemetry and one synthetic live experiment per FR-003/T004. The failing native file-tool path remains disabled, with no broadened permissions.

## Approved mechanism implementation

Resume dependency override: T015 schema freeze precedes T016 transport; T015 trusted application and T016 precede T017 integration, then T018 verification. These tasks complete the historical T004/T014 gates; mark those gates complete only after T018. Historical group ordering does not make activation a prerequisite for its own implementation.

- [x] [T015] Main adds strict proposal schemas in qualia/ai/schemas.py; tests inventory, bounds, forbidden/stale/linked paths and all-before-write validation in tests/test_improve_proposal.py, then implements qualia/improve/proposal.py (FR003/004/009).
- [x] [T016] AI lane reuses bounded no-tools transport in qualia/ai/backends/codex_cli.py; updates tests/test_codex_operator.py and adds actual native production proposal captures, preserving prior direct-tool failure evidence and all classification behavior (FR003).
- [x] [T017] Main integrates complete dispatch hashing and trusted proposal application with unchanged snapshot/evaluation/recovery in qualia/improve/experiment.py; tests KEEP, REVERT, errors, partial writes and retained usage in tests/test_improvement.py (FR002–009/011).
- [ ] [T018] Independently review scope, accounting and no-tools evidence; run the bounded public Codex case in tests/live/test_native_improvement.py, full regression and Spec Kit convergence; update README/docs/USER-GUIDE.md/BUILD-STATE/WELCOME-BACK with measured evidence (all requirements and success criteria).
