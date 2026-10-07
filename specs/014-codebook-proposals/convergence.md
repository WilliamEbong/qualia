# Codebook proposals convergence

Nine requirements, four success criteria and ten tasks reviewed: converged.

- FR001–FR002: migration 003 tables with append-only triggers; `decide_code_proposal` applies human-confirmed values to the draft only (new code, or only changed fields of a revision) in one immediate transaction with the decision; second decisions are refused (tests/test_code_proposals.py).
- FR003: `qualia/core/proposals.py` mines rejected suggestions (negative examples with de-duplicated review notes), unused codes and overlapping pairs, skipping pending signals (tests/test_proposal_miner.py; Playwright "Find evidence" on a synthetic project).
- FR004–FR006: draft/refine through `qualia/ai/proposals.py` with allow_external, availability, budget, usage and egress (`codebook_proposal:cli_invocation`); claude/codex/fake implement `propose`, rules/jev refused. FR005 amended after live use: examples are matched ignoring spacing/punctuation/case and stored in the passage's exact words; unmatched examples are removed and counted; structural errors reject the whole response.
- FR007: origin derived from decisions and shown on code cards ("created from model-proposed (fake) proposal #1 · accepted by researcher").
- FR008: API routes, workspace payload, CLI `codebook propose|proposals|decide`, export of both tables with text redaction; read-only demo shows "Proposals need the local app" (demo spec passed, zero `/api/` requests).
- FR009: user guide §6 "Draft and refine codes with proposals", README tour and Decisions.
- SC001: offline tests above plus API/CLI/export round trip. SC002: web unit tests (proposals.test.ts) and Playwright at 1280/375 (no horizontal overflow). SC003: full suites in BUILD-STATE P20. SC004: live synthetic runs — Claude Code 2.1.284 haiku six grounded draft codes in 29 s; Codex 0.160.0 gpt-6-luna two in 9 s; one egress row each, no codes or coding events written.

Not covered: refine mode was exercised offline (fake backend) only; no measurement of proposal quality on real studies.
