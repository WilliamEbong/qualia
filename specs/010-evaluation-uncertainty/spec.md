# Evaluation uncertainty

Owner decision05 (docs/answers/05-calibrated-decisions.md) asks for evaluation that is honest about uncertainty and readable by a non-statistician, borrowing proven ideas from open-source Jev projects (Wilson intervals from gbesse/jev-codebook; the review-budget idea from pozapas/jev-calibrated-narrative-coding). It declares `scipy>=1.18,<1.19`; no other dependency, migration or API-shape change.

## Requirements

- FR001: Each `per_code` metric row gains `precision_ci95` and `recall_ci95`: a 95% Wilson interval `[low, high]` computed by `scipy.stats.binomtest(...).proportion_ci(method='wilson')`, or `null` when its denominator (predicted or reference count) is zero. Existing point values are unchanged.
- FR002: Metrics gain top-level `review_share` and `review_cutoff`. Over scored predicted code assignments (the ECE population), `review_cutoff` is the lowest model-reported score at which the assignments scoring at or above it reach 90% precision (`sklearn.metrics.precision_recall_curve`), and `review_share` is the share of scored assignments below it. No scored assignments gives both `null`; an unreachable target gives `review_share` 1.0 and `review_cutoff` null.
- FR003: `definitions` explains the three additions in one sentence each, including that the review figures describe this validation set, not future accuracy.
- FR004: The Markdown evaluation report lists both review scalars and shows interval columns for precision and recall.
- FR005: The Evaluation page shows precision and recall as `0.82 (0.61–0.94)` with one caption explaining Wilson ranges; shows a plain-language review sentence that includes the project's current `human_review_below`; gives each summary metric a one-sentence plain-language explanation; labels kappa (Landis–Koch: slight/fair/moderate/substantial/almost perfect) and alpha (Krippendorff: reliable ≥0.800, tentative ≥0.667, insufficient below) with a word and cited source; and lists the already computed `calibration_bins` as a "calibration by score band" table inside the existing details element.
- FR006: Runs stored before this feature (missing keys) render the previous values without errors; nothing is recomputed or rewritten.

Constraints: `qualia/eval` stays sealed and deterministic; metric math uses maintained libraries only. Trust grammar (`model-reported`, ECE caption text, KEEP/REVERT) is unchanged. Components hold markup only; formatting, wording and banding live in `web/src/lib/`. Layout keeps no horizontal scroll at 375px, visible focus and Lighthouse accessibility ≥95.

Assumptions: the 90% target is a fixed module constant stated in the caption (no new config); kappa/alpha bands are presentation only and never change any decision; the static demo snapshot contains no evaluation and is unaffected.

## User scenarios

A researcher evaluates the AI coder on the validation split. For each code they see precision and recall with a range, so "1.00 (0.21–1.00)" visibly signals one example rather than certainty. A sentence tells them how much of the AI's work to check to reach 90% precision and where their current review threshold sits. Kappa and alpha carry a word ("tentative") with its source, and a small table shows how often the model was right in each score band.

## Success criteria

- SC001: Hand-computed metric tests pass for intervals (1 of 1 → [0.2065, 1.0]; 1 of 2 → [0.0945, 0.9055]), null denominators, review share/cutoff on a sorted example, unreachable and empty inputs; the sealed-import rule test passes.
- SC002: Web unit tests cover interval formatting, band words, the review sentence and old-run fallback; typecheck, lint, tests and build pass.
- SC003: Playwright screenshots of the Evaluation page at 1280 and 375 (light and dark) show the additions without horizontal overflow; Lighthouse accessibility ≥95.
- SC004: Full offline suite, Ruff, data guard, dependency audit and gitleaks pass; protected docs and constitution unchanged.
