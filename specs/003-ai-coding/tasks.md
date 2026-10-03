# 003-ai-coding tasks

All items are open. Dependencies: each task requires earlier tasks in its group and all previous groups unless the task explicitly says it is an independent verification. No parallel lane starts before main freezes its consumed contracts. Main owns pointer updates, analysis/convergence, commits and BUILD-STATE; workers report evidence.

## Setup

- [ ] [T001] Re-read qualia/ai/protocol.py, project routing defaults and docs/research/preflight-ai.md; verify installed CLI help/model IDs and record no-tools probe in docs/research/preflight-ai.md.

## Foundational work

- [ ] [T002] Define valid/malformed/injection/unknown-ID result fixtures in tests/fixtures/ai/ and pydantic adapters in qualia/ai/schemas.py; cover every rejection with segment identity.
- [ ] [T003] Implement deterministic rules and fake backends in qualia/ai/backends/{rules,fake}.py with contract tests in tests/test_ai_backends.py.
- [ ] [T004] Implement Claude/Codex classification launchers in qualia/ai/backends/{claude_cli,codex_cli}.py; assert exact argv, fresh cwd, stdin, timeout/output bounds, no sampling and no-tools isolation in tests/test_cli_backends.py.
- [ ] [T005] Implement ledger/budget reservation and egress orchestration in qualia/ai/ledger.py plus Store methods in qualia/store/db.py; test concurrent limits and each retry attempt.
- [ ] [T006] Implement cache keys and validated cache reads in qualia/ai/cache.py; test every key component and invalid cached data in tests/test_ai_cache.py.

## User stories in priority order

- [ ] [T007] Implement availability/egress/budget/threshold routing and bounded retries in qualia/ai/router.py; test offline use, unavailable tiers, 0-call budget and 10,000-character rejection.
- [ ] [T008] Append suggestions and atomic review/feedback via qualia/store/db.py; implement below-threshold, real disagreement and reproducible QC triggers; test duplicate concurrent reviews.
- [ ] [T009] Add classify/availability/review CLI and API operations in qualia/cli.py and qualia/server/{api_models,app}.py; regenerate openapi.json and web/src/api/schema.d.ts through main.
- [ ] [T010] Implement web/src/lib/review.ts data/keyboard logic and review/provenance rendering in web/src/components/ and pages/; test trigger grouping and honest ECE state.

## Validation and completion

- [ ] [T011] Run vendor-launch/sealed-module scans, exact I4/I5/budget tests and Python/web checks; add opt-in synthetic live tests in tests/live/test_classification.py.
- [ ] [T012] Use Playwright MCP for review flow and every trust marker; save evidence in design-review/phase-3/ and report the gate to main.
- [ ] [T013] Main activates specs/003-ai-coding, analyzes before implementation and converges afterward; unresolved load-bearing isolation failures enter the repair/gate batch rather than being declared passed.
