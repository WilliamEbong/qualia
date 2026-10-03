# 004-evaluation — Protected benchmarks, evaluation, and demo data

## Overview and scope

Implement deterministic multi-label evaluation with an independently protected test split, and build an idempotent real-data demo whose labels and licenses can be traced to a pinned source.

This feature supplies metrics and demo data, plus evaluation/ECE UI. It does not authorize agents to inspect the protected split or change methodology. Real public source data remains in gitignored demo/data; shipping a static snapshot is a separate Phase 8 license gate.

Governing sources: docs/01–05 and constitution v1.0.0. This is a prepared feature; main activates it in phase order and runs analyze before implementation. No implementation or acceptance pass is claimed here.

## Authoritative workstreams (verbatim from doc02)

- **3.7 Evaluation [LB]** jsonl benchmarks + `qualia benchmark import`; bundle: per-code P/R/F1, macro/micro F1, exact/partial match, kappa (NaN → "n/a"), nominal alpha (`qualia/eval/alpha.py`), ECE, escalation rate, calls per 1k segments, latency; `qualia evaluate [--split validation | --protected]` → md + json.
- **3.10 Demo data [LB]** `qualia demo`: AnnoMI project (cases = transcripts, attribute = mi_quality, codebook from AnnoMI's README definitions, human codes as human events, §2 splits); idempotent.

## Functional requirements

- FR-001: Import validated JSONL benchmarks into project dev/validation directories and the protected vault outside the project; maintain manifest hashes and reject invalid/mismatched records before publication.
- FR-002: Calculate per-code precision/recall/F1, macro/micro F1, exact/partial match and kappa with scikit-learn where supported; render undefined kappa n/a. Sealed eval modules accept data and perform no DB, process, HTTP or environment access.
- FR-003: Implement nominal Krippendorff alpha in qualia/eval/alpha.py and validate against the dev-only krippendorff oracle on three independent fixtures within 1e-9; do not ship its GPL dependency at runtime.
- FR-004: Compute ECE, escalation rate, calls per 1,000 segments and latency with explicit denominator/empty-input semantics; retain enough evaluation metadata to reproduce each reported value.
- FR-005: Provide qualia evaluate --split validation and --protected with markdown/JSON output. Append evaluation runs and predictions to evaluation_runs, never coding_events.
- FR-006: Fetch AnnoMI via a pinned-commit/SHA-256 script into gitignored demo/data; validate checksum/license evidence and preserve the raw source unchanged.
- FR-007: Create qualia demo with transcripts as cases, mi_quality attributes, codebook definitions from the dataset README, expert labels as human events and deterministic transcript-level splits; a second run adds no duplicates.
- FR-008: Keep protected vault reads out of validation/evaluation UI and the future improvement path. Verify manifests before protected evaluation and reject tampering with a clear flag.
- FR-009: Expose validation metrics and ECE provenance in the local API/UI, including n/a states, model/codebook/pipeline identity and evaluation time; never expose raw protected records or imply model-reported confidence is accuracy.
- FR-010: Ensure benchmark/demo data and generated DBs never enter the app Git history; dataset licenses/attribution are recorded in DATA-LICENSES.md.

## User scenarios

- US1: A researcher imports a two-coder fixture, evaluates validation predictions and compares JSON/Markdown metrics with hand calculations; coding event counts do not change.
- US2: A reviewer explicitly evaluates the protected split after a manifest check; the regular validation UI and improvement code cannot load its records.
- US3: A contributor runs qualia demo twice and opens the workspace offline. Transcript cases, quality attributes and human coding provenance are present without duplicate data.

## Success criteria

- SC-001: Metrics equal hand-computed fixtures; nominal alpha matches the independent oracle within 1e-9 on three cases; undefined agreement and empty inputs are represented honestly.
- SC-002: All transcript IDs are disjoint across deterministic 60/20/20 splits; protected manifest tampering is detected, ordinary evaluation cannot select/read its records, and evaluation leaves coding_events unchanged.
- SC-003: Two demo runs yield identical source/case/segment/codebook/event counts and a reproducible pinned-data manifest.
- SC-004: Sealed-module and tracked-data scans pass; krippendorff is dev-only; DATA-LICENSES records verified evidence and any fallback decision.
- SC-005: Playwright MCP verifies validation metric/ECE display and n/a handling; Python/web gates pass with offline fixtures, and real fetch evidence is distinguished from fixture evidence.

## Authoritative acceptance excerpts (verbatim from doc02)

- [ ] Idempotency: same import twice → "0 new sources"; migrate twice → no-op; `qualia demo` twice → no duplicates.
- [ ] Metrics match hand-computed fixtures; own alpha = krippendorff oracle within 1e-9 on 3 fixtures.

Quoted shared gates retain their original scope. This feature proves its relevant part; later-phase responsibilities are stated above. Common I1/I6/I7 protections remain mandatory regressions, never exemptions.

## Informed assumptions

- JSONL benchmark records reference stable source/segment IDs, expected frozen-codebook labels and optional coder labels. Validation rejects unknown codes, missing text/identity and malformed arrays with filename/line context.
- Split deterministically by transcript, not utterance, using a recorded seed and sorted IDs into 60/20/20 dev/validation/protected. Record actual counts and resolve rounding deterministically; no transcript may occur in multiple splits.
- Evaluation labels use the full frozen codebook ordering, including absent labels. Document zero-division behavior. Exact match compares label sets; partial match is per-segment Jaccard, with two empty sets scoring 1. These definitions are fixed before experiments.
- Compute nominal alpha for nominal coder assignments only; do not treat multi-label sets as ordinal numbers. Fixtures include missing data and undefined/degenerate agreement; undefined kappa/alpha is rendered n/a, not zero.
- ECE is computed from finite model-reported confidence against correctness using ten equal-width bins, with the final bin including 1.0; document the prediction unit and empty-bin handling. Do not claim calibration when no scored predictions exist.
- Protected data is read only by explicit qualia evaluate --protected. Ingestion writes the vault once and manifests it; ordinary UI/routes, validation evaluation and improvement cannot read protected records.
- Use pinned AnnoMI and its README label definitions if retrievable/licensable; use the pre-authorized Zenodo 15698094 alternative only when the pin is unreachable, documenting source/license/mapping differences. Never replace missing real data with synthetic results represented as real.
