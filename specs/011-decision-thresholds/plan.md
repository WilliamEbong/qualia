# Plan

Python AI lane (`qualia/ai/schemas.py`, `qualia/ai/router.py`, `qualia/ai/backends/jev.py`), ENGINE lane (`qualia/eval/metrics.py`, `qualia/evaluation.py`, `qualia/improve/experiment.py`) and WEB lane (`web/src/lib/review-state.ts`, `review.ts`, Codebook/Experiments components). No dependency, migration, OpenAPI or stored-shape change: `code_thresholds` lives in the existing routing JSON, and candidates are in-memory only.

## Design

1. `schemas.Routing.code_thresholds: dict[str(^[1-9][0-9]*$), float(0 < t ≤ 1)]`, default empty. Not added to `workspace.ROUTING` or `proposal.BOUNDS`.
2. `jev.py`: drop the `>= .5` emission filter; class attribute `default_threshold = .5`.
3. `router.classify_batch_inputs`: where `provider` is known, `assign(prediction)` keeps codes with `score >= code_thresholds.get(str(code_id), getattr(provider, 'default_threshold', None) or 0)`. Cache-hit and fresh paths both cache/collect the raw prediction and store `(assigned, backend, model, cli_version, raw)`. Escalation, disagreement, `predictions` and persisted suggestions read `[0]`; `with_candidates=True` adds `candidates` from `[4]`.
4. `metrics.tune_thresholds(records, candidates, code_ids, current)`: per code, maximum score per segment (missing = 0), grid `i/20`, sklearn `f1_score(zero_division=0)`, tie → nearest 0.5, skip codes without positives or best F1 0; returns `{**current, **tuned}` with string keys. `ponytail:` comment on dev overfitting, guarded by validation.
5. `evaluation.evaluate_project(..., with_candidates=False)`: pass through; return `candidates`, `references` and `code_ids` only when requested.
6. `experiment.py`: `_operator('thresholds')` returns a placeholder invoke, a zero-cost `FakeBackend` provider and `thresholds-operator-v1`; injected operators rejected. Inside the loop, next to `prepare_proposal` and before backup/fingerprint, run the dev evaluation (`use_cache=True, with_candidates=True`), tune, and bind an invoke that writes routing.yaml via `canonical()` with a hypothesis listing old→new values by code name. Missing dev split raises before snapshot (load_benchmark already raises).
7. Web: `review-state.ts` reasons caption appends the current `human_review_below` to the below-threshold label in the card caption only; groups sort by ascending score. Codebook adds a caption for codes with explicit thresholds (routing passed from workspace data through lib). Experiments empty state copy names the agent.
8. Docs: CONTRACTS (raw cache, router thresholds, batch sizing), USER-GUIDE §12/§15 and glossary, `docs/research/jev.md` third-party findings, README Decisions, docs/01 §10, BUILD-STATE, WELCOME-BACK.

Main session owns all lanes for this small slice. Verification as in SC001–SC004; Playwright via the project's own installation (the MCP browser profile is locked by a stale session).
