# Plan

Python 3.14 metrics in sealed `qualia/eval/metrics.py`, Markdown report in `qualia/evaluation.py`, React 19 Evaluation view with logic in `web/src/lib/`. One dependency declaration (`scipy>=1.18,<1.19`, already locked transitively by scikit-learn 1.9); no migration, no OpenAPI change (`EvaluationResult.metrics` is an untyped dict), no new UI dependency. Context7 confirmed `scipy.stats.binomtest(k, n).proportion_ci(confidence_level, method='wilson')` and `sklearn.metrics.precision_recall_curve` (precision has one more entry than thresholds; thresholds ascend; all-negative input warns).

## Design

1. `metrics.py`
   - `_wilson(k, n)` → `[low, high]` floats from scipy, `None` when `n == 0`.
   - Per code: `tp`, `predicted` and `support` counts from the existing truth/guess vectors; add `precision_ci95 = _wilson(tp, predicted)`, `recall_ci95 = _wilson(tp, support)`; empty corpus keeps `None`.
   - `_review(scores, correct)` over the existing ECE population: no scores → `(None, None)`; no correct assignment → `(1.0, None)` (skips sklearn's all-negative warning); otherwise the lowest `precision_recall_curve` threshold whose precision ≥ `REVIEW_PRECISION = 0.9` is the cutoff, and the share is the fraction of scores below it; none qualifying → `(1.0, None)`.
   - Three new `definitions` captions (`ci95`, `review_share`, `review_cutoff`).
2. `evaluation.py::report_markdown`: add `review_share`, `review_cutoff` to the scalar list and two interval columns rendered `[low, high]`.
3. Web
   - `evaluation-state.ts`: optional types for the new keys and `calibration_bins`; pure helpers `formatInterval`, `reliabilityWord` (Landis–Koch for kappa, Krippendorff for alpha), `reviewSentence(metrics, threshold)`, `calibrationRows`; `metricRows` gains a one-sentence `help` per row and appends the band word to kappa/alpha values. Missing keys fall back to the previous rendering.
   - `evaluation.ts`: per-code text uses `formatInterval`; exposes `reviewSentence` (threshold from `w.data.routing.human_review_below` when numeric) and `calibrationRows`.
   - `Evaluation.tsx` (markup only): help line under each metric name, review sentence paragraph, Wilson caption under the per-code table, calibration table inside the existing details. Existing labels, ECE caption and `aria-label`s unchanged.
4. Docs: CONTRACTS additive keys, README Decisions (scipy), USER-GUIDE §14 metric meanings, BUILD-STATE, convergence.

Main session owns the change (single small slice across ENGINE and WEB lanes, no parallel lane needed). Verification: targeted then full pytest, Ruff, data guard, pip-audit, web typecheck/lint/test/build, Playwright screenshots at 1280/375 light/dark, Lighthouse.
