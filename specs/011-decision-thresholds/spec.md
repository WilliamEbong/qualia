# Decision thresholds

Owner decision05 (docs/answers/05-calibrated-decisions.md) asks for per-code suggestion thresholds tuned on data, after gbesse/jev-codebook, delivered as a deterministic no-AI improvement agent that Qualia's existing KEEP/REVERT policy judges. It also asks for review-queue UX that explains why an item is waiting. No dependency, migration or API-shape change.

## Requirements

- FR001: Project routing accepts optional `code_thresholds`, a map from positive integer code ID strings to a number in (0, 1]: the minimum model-reported score for that code to become a suggestion. It is absent from new-project defaults, outside the privacy/budget `BOUNDS`, so measured operators may change it. Invalid keys or values are rejected as invalid configuration.
- FR002: The router applies one rule to every backend: a code is suggested when its score is at least its configured threshold, otherwise the backend's `default_threshold` (Jev: 0.5; others: none, so every emitted code is kept). With no `code_thresholds`, behavior matches today exactly.
- FR003: Jev returns every active code's noul probability; thresholding moves from the adapter to the router. The cache stores raw backend output, and thresholds are re-applied on cache hits. Escalation, disagreement, evaluation predictions and persisted suggestions all use the thresholded codes.
- FR004: `classify_segments` and `evaluate_project` accept `with_candidates=False`. When requested, the result also carries raw `candidates` (and evaluation returns its references); otherwise the result shape is unchanged, so API responses and stored rows do not grow.
- FR005: `qualia improve --agent thresholds` runs no AI. Before the experiment snapshot it evaluates the dev split, picks for each code the threshold on the grid 0.05…0.95 that maximises that code's F1 against dev references (ties nearest 0.5; codes without dev positives or with best F1 0 keep their current value), writes `code_thresholds` to routing.yaml and states the old→new values as its hypothesis. The existing validation evaluation, policy and confirmation decide KEEP or REVERT. A missing dev split fails before any snapshot or journal.
- FR006: Review shows why each item waits: the reasons caption includes the project's current review threshold (for example `Below review threshold (0.70)`), and each reason group is ordered least-certain first. The Codebook view notes explicit thresholds ("AI suggests at ≥ 0.60"). The Experiments empty state names `qualia improve --agent thresholds`. Trust grammar, group labels and `aria-label`s are unchanged.

Constraints: sealed `qualia/eval` holds the tuning math (sklearn `f1_score`); no score is rewritten, so every displayed score stays model-reported; methodology and codebook definitions are untouched; the protected split is never read by the agent; components hold markup only.

Assumptions: thresholds apply to whichever backend answers, including an escalated strong tier, because they are part of one measured pipeline; the dev pass may use the cache (validation runs stay fresh, as today); the agent's ledger row is a zero-cost local `fake` provider entry named `thresholds-operator-v1`.

## User scenarios

A researcher with dev and validation benchmarks runs `qualia improve --agent thresholds`. Qualia finds that "Change talk" needs a lower bar (0.35) and "Neutral" a higher one (0.80) on dev, applies them, and keeps the change only if validation macro-F1 improves by the policy margin; the experiment card shows the hypothesis with the new values. In Review, an item reads "Below review threshold (0.70) · segment 12", and the least certain items appear first.

## Success criteria

- SC001: Schema, router, Jev, evaluation and metric tests cover validation, default-equivalence, threshold application on fresh and cached paths, escalation/disagreement interaction, opt-in candidates, raw Jev probabilities and tuning ties/skips.
- SC002: An improvement test proves the thresholds agent reaches KEEP with committed and tagged `code_thresholds`, records a dev evaluation, writes no coding events, and fails cleanly without a dev split.
- SC003: Web tests cover the threshold caption and ordering; Playwright screenshots of Review, Codebook and Experiments at 1280/375 show no horizontal overflow.
- SC004: Full offline suite, Ruff, data guard, dependency audit, gitleaks and web checks pass; protected docs and constitution unchanged.
