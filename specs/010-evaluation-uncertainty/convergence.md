# Evaluation uncertainty convergence

Six requirements, four success criteria and six tasks reviewed. Scoped feature converged.

- FR001–003: `per_code` rows carry 95% Wilson `precision_ci95`/`recall_ci95` from scipy (null on zero denominators); `review_share`/`review_cutoff` use sklearn's precision–recall curve with a fixed 90% target; three definitions captions. Hand-derived tests: 1 of 1 → [0.2065493, 1.0], 1 of 2 → [0.0945312, 0.9054688]; lowest qualifying cutoff, unreachable and empty cases. Sealed-import rule passes.
- FR004: Markdown report lists both review scalars and interval columns (test_evaluation asserts them).
- FR005–006: Evaluation page shows `0.750 (0.30–0.95)` style ranges with a Wilson caption, plain-language help for every summary metric, cited kappa/alpha words, a review sentence with the project's current review threshold, and a calibration-by-score-band table. Old runs fall back to bare values (unit tested).
- SC002: 36 web tests, typecheck and build pass.
- SC003: Playwright (project installation; the MCP browser profile was locked by a stale session) captured design-review/P15/evaluation-{1280,375}-{light,dark}.png from a real `qualia evaluate --project demo --backend rules` run (#4): no horizontal overflow, no console errors. Measured WCAG contrast of new text: minimum 4.94:1 light, 6.9:1 dark. Lighthouse was not run because it is not installed locally and was not downloaded unattended; the contrast and overflow probes cover the changed elements.
- SC004: Full offline suite at the 010 commit: 540 passed, 5 skipped, 6 live deselected. Ruff, data guard, pip-audit (no known vulnerabilities) and gitleaks (5 new commits, no leaks) pass. Protected docs and constitution unchanged.

No metric changes any decision; the kappa/alpha words are reading aids. scipy is declared under decision05 and was already locked through scikit-learn.
