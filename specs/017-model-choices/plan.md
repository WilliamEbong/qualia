# Plan

1. `qualia/ai/models.py` (pure data): `CATALOG` per backend (id, label, description) and `TASK_DEFAULTS` per task and backend; `default_model(task, backend)`. `router.DEFAULT_MODELS` and `_select` use it; project `tasks` overrides keep priority.
2. Availability response gains `models` per backend and `defaults` (task -> backend -> model, after project overrides).
3. Migration 005: `coding_events.model_version`, `code_proposals.model_version` (nullable). `Result`/`CodeProposalResult` accept optional `model_version`; Claude transport derives it from `modelUsage` keys; router and proposals persist it; cache entries carry it.
4. Web: `lib/models.ts` (options, default label); a `ModelPicker` in Review and Codebook proposal forms (select + optional exact ID); provenance shows the answering model.
5. Docs: user guide "Choose a model" subsection, README AI section line, CONTRACTS note.

Ponytail: no per-code model choice, no automatic model switching, no price table for Codex, no model change through the experiment loop yet (owner's item 5, later).
