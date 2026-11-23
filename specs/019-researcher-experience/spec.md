# Researcher experience

Owner delegation (2026-11-23, relayed by the orchestrating session): build the items fresh design reviewers named as blocking a 9/10, in order of what a researcher feels most. Out of scope here, and recorded for the owner instead: any change to trust captions (per-card model-reported, ECE and trigger captions), KEEP/REVERT, the code-colour highlight, or docs 01–05. Those are fixed by doc 04 and the project rules.

## Requirements

- FR001 Benchmark state: `GET /api/projects/{slug}/benchmarks` returns, for the dev and validation splits only, whether each is imported and, if so, its record count, frozen codebook version and import time. The protected split is never reported or importable over the API.
- FR002 In-app benchmark import: `POST /api/projects/{slug}/benchmarks` takes `{split: dev|validation, version: int|null, content: str}` (JSONL text, at most 20 MB) and calls the existing `import_benchmark` with the frozen version (latest when null) and its active code IDs, exactly as `qualia benchmark import` does: same validation, identical re-import is a no-op, a changed split is refused, nothing is written on error. Evaluation offers it as a form (file, split, version).
- FR003 Run gating: Run validation evaluation is disabled with the plain reason "Import a validation benchmark first" while the validation split is absent. The tuning experiment is disabled with its reason while dev or validation is absent.
- FR004 Home study status: for the open project, Home shows sources, passages, coded passages, pending suggestions and the latest frozen version, and one next step chosen in order: import a source; create codes; freeze the codebook; code a passage; review pending suggestions; otherwise analyse. The step is a button that opens the right view.
- FR005 Experiments prerequisites: a checklist above the start cards states, each as met or not met in plain words, a frozen codebook, a dev benchmark, a validation benchmark and an available classifier. The clean-folder requirement is stated as an instruction (it is checked when the experiment starts).
- FR006 Matrix totals: a total per code (distinct coded segments across the shown cases) and per case, plus the grand total of distinct coded segments, clearly labelled as totals.
- FR007 Retrieval grouping: excerpts are grouped under code headings; within a code, one entry per excerpt with source, segment and version on one line.
- FR008 Memo metadata: migration 006 adds nullable `memos.author`; saving from the app records the current coder's name; each memo card shows kind, created date and author where recorded (older memos show no author).
- FR009 Analysis views: Analysis opens on an overview (counts, criteria, section list) and shows one section at a time: frequencies, groups, co-occurrence, words, numeric, evidence. Selecting evidence from any chart switches to the evidence view.
- FR010 Read-only demo: in the public snapshot, write controls (forms, import, create, edit, run, accept/reject buttons) and empty model menus are hidden; a single notice under the header says it is a read-only demo and how to get the app.

Assumptions: benchmark import content is sent as text (benchmarks are UTF-8 JSONL); the 20 MB bound matches existing upload bounds; totals are counts of distinct coded segments, matching the matrix cells' definition; author is display metadata, not provenance (provenance stays in coding events).

## Success criteria

- SC001 Python tests: benchmark status and import routes (dev/validation only, protected refused, identical re-import no-op, changed split refused, invalid file writes nothing), migration 006 from v5 with memo author round-trip.
- SC002 Vitest for the pure next-step choice, matrix totals and retrieval grouping.
- SC003 Playwright on Home, Evaluation (import then run enabled), Experiments, Matrix, Retrieval, Memos, Analysis views and the static demo.
- SC004 Full Python and web suites, typecheck, build, demo e2e; OpenAPI and generated types updated.
