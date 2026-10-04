# Tasks

- [ ] [T001] Failing tests: schema validation (tests/test_ai_schemas.py), router thresholds on fresh/cached paths, escalation/disagreement and opt-in candidates (tests/test_ai_router.py), raw Jev probabilities with default 0.5 filtering (tests/test_jev_backend.py) (FR001–004, SC001).
- [ ] [T002] Implement code_thresholds in qualia/ai/schemas.py, raw-score Jev in qualia/ai/backends/jev.py and router thresholding/candidates in qualia/ai/router.py (FR001–004).
- [ ] [T003] Failing then passing tune_thresholds tests in tests/test_metrics.py; implement in qualia/eval/metrics.py; with_candidates in qualia/evaluation.py with tests/test_evaluation.py (FR004–005, SC001).
- [ ] [T004] Failing then passing thresholds-agent tests in tests/test_improvement.py; implement in qualia/improve/experiment.py (FR005, SC002).
- [ ] [T005] Review/Codebook/Experiments UX in web/src/lib and components with web tests; Playwright screenshots (FR006, SC003).
- [ ] [T006] Docs (CONTRACTS, USER-GUIDE, research/jev.md, README, doc01 §10), full verification, convergence, BUILD-STATE and WELCOME-BACK (SC004).
