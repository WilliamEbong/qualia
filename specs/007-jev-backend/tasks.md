# 007-jev-backend tasks

All items are open. Dependencies: each task requires earlier tasks in its group and all previous groups unless the task explicitly says it is an independent verification. No parallel lane starts before main freezes its consumed contracts. Main owns pointer updates, analysis/convergence, commits and BUILD-STATE; workers report evidence.

## Setup

- [ ] [T001] Read docs/research/jev.md and docs/JEV-SETUP.md; reverify official OpenAPI/model/pricing with built-in web research and httpx APIs with Context7, recording dated changes in docs/research/jev.md.

## Foundational work

- [ ] [T002] Add labeled synthetic choice/score/noul and malformed/error fixtures to tests/fixtures/jev/ with provenance README; define strict expected normalized outputs.
- [ ] [T003] Implement key availability and provider request/response validation in qualia/ai/backends/jev.py, respecting the frozen protocol and no secret output.

## User stories in priority order

- [ ] [T004] Implement bounded httpx dispatch and redacted timeout/auth/validation/transient-error handling in qualia/ai/backends/jev.py; test through MockTransport in tests/test_jev_backend.py.
- [ ] [T005] Integrate explicit Jev enablement, external permission and daily-dollar reservation in qualia/ai/router.py and ledger.py; test zero calls under every denied condition and per-attempt retry accounting.
- [ ] [T006] Normalize noul/choice/score results and returned model identity into existing provenance; test probabilities, derived confidence labeling, token usage and cost calculations.
- [ ] [T007] Add tests/live/test_jev.py using tiny synthetic text with live marker and missing-key skip; capture sanitized actual-response fixtures only after a successful authorized request.
- [ ] [T008] Finalize docs/JEV-SETUP.md and .env.example parity with owner-only key/credit actions, exact verification commands and explicit off-by-default behavior.

## Validation and completion

- [ ] [T009] Run vendor/key-location scans, Jev contract tests, invalid-key redaction probe and all affected offline checks; label recorded/live coverage accurately.
- [ ] [T010] If existing backend UI changes, use Playwright MCP and save design-review/jev/ evidence; otherwise report API/CLI evidence without inventing a UI task.
- [ ] [T011] Main analyzes/converges specs/007-jev-backend and records verified or sacrificial deferred live status in BUILD-STATE; never stop the remaining final sweep waiting for billing/key input.
