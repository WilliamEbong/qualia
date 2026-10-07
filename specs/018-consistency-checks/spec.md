# Consistency checks

Owner request (2026-10-07): "implement all of your suggestions" after the consistency discussion. Items 4 and 5 of that list: measure how much a model varies when asked the same thing twice, and treat a model change as a measured experiment instead of a settings edit. Qualia cannot fix sampling (no temperature control through the subscription CLIs, and project rules forbid it), so variation has to be measured.

## Requirements

- FR001: A repeatability check classifies the same stable sample of project segments (1–200, default 50, hash-ordered so the same project samples the same segments) twice with the cache off, and reports the share of segments with identical code sets and, per code, the yes/no agreement and Cohen's kappa between the runs, plus calls used. It writes no coding events or cache entries; calls pass the usual gates and ledger.
- FR002: A model experiment (`--agent model`) switches the project's classification backend/model to a candidate and runs the standard measured loop: baseline and candidate on validation, confirmation run, unchanged policy deciding KEEP/REVERT, Git commit/tag, full report. The candidate is validated before any baseline evaluation; per-run backend/model overrides are refused because both sides must follow project settings.
- FR003: CLI `qualia repeatability` and `qualia improve --agent model --candidate-backend B --candidate-model M`; API `POST /repeatability` and `POST /experiments/model`; Evaluation and Experiments pages offer both with the model picker.
- FR004: Docs explain when to use each and their cost (two runs of the sample; three validation evaluations for a model experiment).

Assumptions: repeatability results are shown and returned, not stored (usage is in the ledger); the existing policy's call-ratio limit applies to model switches, so a switch that needs many more calls is reverted unless the policy is changed by the owner.

## Success criteria

- SC001: Unit test for run agreement; repeatability with steady and varying backends (no events, no cache); model experiment validation-before-calls, measured decision and API routes.
- SC002: Playwright on both pages with the fake backend. SC003: full suites, docs.
