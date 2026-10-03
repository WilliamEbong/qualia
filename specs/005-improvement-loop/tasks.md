# 005-improvement-loop tasks

All items are open. Dependencies: each task requires earlier tasks in its group and all previous groups unless the task explicitly says it is an independent verification. No parallel lane starts before main freezes its consumed contracts. Main owns pointer updates, analysis/convergence, commits and BUILD-STATE; workers report evidence.

## Setup

- [ ] [T001] Read frozen policy templates, manifest and evaluator contracts; write explicit snapshot/output-scope and interruption-recovery decisions in specs/005-improvement-loop/plan.md.

## Foundational work

- [ ] [T002] Add synthetic candidate/baseline/challenge fixtures and fake operator attack cases under tests/fixtures/improve/; test policy boundaries before implementation in tests/test_improve_policy.py.
- [ ] [T003] Implement pure threshold/confirmation decisions in qualia/improve/policy.py; cover gain, priority tolerance, challenge, tests, call ratio and zero-baseline behavior.
- [ ] [T004] Implement bounded run_operator in qualia/ai/backends/{claude_cli,codex_cli}.py and fake operator support; verify executable isolation, cwd, tools, prompts and egress accounting in tests/test_operator_backends.py.
- [ ] [T005] Implement clean-baseline snapshot, canonical path containment, scope diff and protected-hash validation in qualia/improve/experiment.py; test tracked/untracked/path-escape attacks.

## User stories in priority order

- [ ] [T006] Integrate baseline/candidate/confirmation evaluation in qualia/improve/experiment.py without protected-data reads or coding-event changes; prove misleading operator text cannot alter policy.
- [ ] [T007] Implement safe snapshot rollback of unauthorized and mutable changes, preserving pre-existing files; test methodology/codebook attacks and clean Git status in tests/test_improvement.py.
- [ ] [T008] Implement KEEP commit/tag, REVERT reporting and Store experiment records with recovery behavior; test duplicate tags, failed commit and interrupted attempt handling.
- [ ] [T009] Add improve CLI and read-only history API in qualia/cli.py and qualia/server/{api_models,app}.py; regenerate openapi.json/types through main and include experiment data in existing exporters.
- [ ] [T010] Implement web/src/lib/experiments.ts plus timeline/detail markup under web/src/components/ and pages/; preserve fixed KEEP/REVERT grammar and measured metric displays.

## Validation and completion

- [ ] [T011] Create tests/e2e/mvp.spec.ts for demo → five keyboard codes → fake AI → accept/reject → measured gain/KEEP/tag → bundle provenance; run all exact I2/I3 gates.
- [ ] [T012] Use Playwright MCP to verify affected history/MVP screens; save evidence in design-review/phase-5/ and record live parity prerequisites in specs/005-improvement-loop/plan.md.
- [ ] [T013] Main runs phase analysis/convergence, full offline checks and gate reporting; Phase 6 owns scripts/smoke-agents.ps1 live parity and security/public-data sweep.
