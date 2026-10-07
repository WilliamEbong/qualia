# Model choices convergence

Five requirements, three success criteria, five tasks: converged.

- FR001-FR002: `qualia/ai/models.py` catalog and task defaults; routing tests cover defaults, tiers, project overrides and pinned IDs. Found and fixed a routing bug: the default tier named `claude` shadowed the Claude backend, so explicit Claude requests always ran on Haiku.
- FR003: one shared `useModelChoice` hook and `ModelPicker` component (first built by Codex gpt-6-astra in its web lane) on Review, Codebook proposals, Evaluation and Experiments; Playwright: list "Task default · Claude Haiku 4.5", four Claude models, descriptions, custom ID field; proposal default "Claude Opus 5.5"; no horizontal overflow at 375 px.
- FR004: migration 005; Claude `modelUsage` parsed into `model_version`; stored on suggestions and proposals, kept through cache reuse (tests). Live: a default Claude proposal ran on Opus and recorded `claude-opus-5-5`; a Haiku classification recorded `claude-haiku-4-5-20251001`.
- FR005: user guide "Choose a model" (defaults table, model descriptions, project defaults, pinning) and README paragraph and Decisions.

Found during live checks: Haiku sometimes returned spans past the segment end, so strict validation rejected whole batches. The request now states each segment's length; live Haiku batches went from 2 of 7 invalid to 6 of 6 valid.
