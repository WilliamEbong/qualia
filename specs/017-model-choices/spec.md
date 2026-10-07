# Model choices

The owner asked how Qualia keeps AI behaviour consistent and for "reasonable default models based on intelligence needs for the task and cost effectiveness ... easy to change with brief descriptors" (2026-10-07). Today each backend has one default model (Claude `haiku`, Codex `gpt-6-luna`) for every task, the UI offers only a free-text model override (and none for proposals), and provenance stores the requested alias, so a provider moving an alias to a newer model leaves no trace.

Research (2026-10-07): the Codex CLI catalog describes GPT-6-Astra as "frontier intelligence for the most demanding work", GPT-6.1-Sol as the "latest workhorse model" and GPT-6-Luna as "fast and affordable". Anthropic's model reference lists Claude Fable 5.1 (most capable, $10/$50 per million input/output tokens on the API), Opus 5.5 ($4/$20), Sonnet 5.5 ($2/$10) and Haiku 4.5 ($1/$5); subscription usage scales similarly. A probe showed the Claude CLI's JSON reports the exact model (`modelUsage` keyed by e.g. `claude-haiku-4-5-20251001`); Codex events report no model.

## Requirements

- FR001: A built-in catalog lists each backend's models with a label and a one-line descriptor of strength, relative cost and suggested use.
- FR002: Task defaults follow intelligence need and volume: classification (high volume, applying definitions) uses Claude Haiku / Codex GPT-6-Luna; escalation of uncertain passages uses Claude Opus / Codex GPT-6-Astra; codebook proposals (rare, interpretive) use Claude Opus / Codex GPT-6.1-Sol. A project's `routing.yaml` `tasks` entry still overrides a default.
- FR003: The Review classification form and the Codebook proposal form offer a model list with descriptors, marked with the task default, plus "Other exact model ID" for any model or a pinned version (e.g. `claude-opus-5-5`).
- FR004: When a CLI reports the model that answered, Qualia records it (`model_version`) on suggestions and proposals alongside the requested model and shows it in provenance; cached results keep it.
- FR005: User guide and README explain the defaults, how to change them per run or per project, and pinning versus following the latest model.

Constraints: no change to isolation, schemas' strictness, budgets or the improvement operator's models (Opus 5.5 / GPT-6-Astra); migration 005 is additive; descriptors make no price claims for Codex beyond the catalog's wording.

Assumptions: Claude `modelUsage` may list more than one model; all keys are recorded, sorted and comma-separated. Codex records the requested model only.

## Success criteria

- SC001: Tests: task defaults and project overrides in routing; availability returns models and defaults; Claude `model_version` parsed and stored on suggestions, proposals and cache reuse; migration 005.
- SC002: Playwright: model lists with descriptors in Review and Codebook, the custom ID field, and a fake-backend run.
- SC003: Full suites pass; docs updated.
