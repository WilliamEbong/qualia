# Plan

Order follows what a researcher feels most: the Evaluation dead end first, then Home's orientation, then the reading views.

1. Benchmarks (FR001-003): `qualia/io/benchmarks.py` gains `benchmark_status(project)` (dev/validation only, from the existing index; never reads the vault). `evaluation_routes.py` adds `GET`/`POST /benchmarks` with `BenchmarkImportInput` (split Literal dev|validation, version optional, content max 20 MB); POST reuses the CLI's frozen-version and active-code lookup (moved into one helper used by both). OpenAPI + generated web types. Web: `lib/evaluation-state.ts` loads status; Evaluation shows an import form and disables Run with "Import a validation benchmark first"; Experiments reads the same status for its checklist and tuning gate.
2. Home status (FR004): pure `nextStep()` in `lib/entities.ts` from workspace counts; Landing shows the status block for the open project with one button.
3. Retrieval grouping and Matrix totals (FR006-007): pure helpers in lib (`groupByCode`, `matrixTotals`), rendered in Retrieval.tsx.
4. Memo author (FR008): migration `006_memo_author.sql` (`ALTER TABLE memos ADD COLUMN author TEXT`), `MemoInput.author` optional, `db.save_memo` stores it, web sends `w.actor`, cards show kind · date · author.
5. Analysis views (FR009): `view` state in `lib/analysis-state.ts`; Analysis.tsx renders overview + the selected section; chart selection switches to evidence.
6. Demo (FR010): `w.readOnly` hides write controls and empty selects in components; one notice under the header.
7. Tests per item; docs (user guide sections for Home, Evaluation import, Analysis views); CONTRACTS additive note.

Ponytail: no new tables beyond one column, no benchmark editing or deletion from the web, no protected split over HTTP, no per-view routing in the URL.
