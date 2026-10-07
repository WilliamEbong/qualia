# Plan

1. `qualia/eval/metrics.py` `run_agreement` (pure, sklearn kappa). `qualia/evaluation.py` `repeatability()` using `classify_segments` with `use_cache=False, cache_results=False, persist=False`.
2. `qualia/improve/experiment.py`: `_model_operator` (validates backend in the model catalog and the model ID, rewrites `backend`/`model` in routing.yaml), wired as agent `model` with `candidate_backend`/`candidate_model`; refuses evaluation overrides.
3. CLI commands, API models/routes, OpenAPI; web: Evaluation "Check repeatability" panel and Experiments "Try another classification model" form reusing the model picker.
4. Docs (user guide sections 14–15, README, CONTRACTS).

Ponytail: no storage table for repeatability, no automatic model search, no per-code model choice.
