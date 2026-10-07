# Consistency checks convergence

Four requirements, three success criteria, three tasks: converged.

- FR001: `run_agreement` and `repeatability()`; tests with steady and varying backends confirm identical-set share, per-code agreement and kappa, two runs of calls, and no coding events or cache rows. Playwright: "Identical code sets on 100% of 4 passages · fake / fake-v1 · 2 calls" with the per-code table.
- FR002: `--agent model` runs the standard measured loop; candidate validated before any call; per-run overrides refused. Playwright: measuring fake against rules recorded REVERT (validation macro F1 1.000 -> 0.250) with the hypothesis "Classify with fake / fake-v1 instead of rules / rules-v1".
- FR003: CLI, API routes and both page forms. FR004: user guide "Check repeatability" and "Try another classification model", CLI table, README.
- Also fixed: in-app evaluation wrote `reports/` into the project and then blocked every experiment until committed by hand (reproduced, regression test).

Not covered: live repeatability or model experiments with subscription models (they cost multiple validation runs); the call-ratio policy limit may revert switches to slower-batching backends by design.
