# 002-workspace — Import, manual coding, and research workspace

## Overview and scope

Deliver the offline non-AI workflow: import TXT/MD/CSV, maintain cases and a versioned hierarchical codebook, assign overlapping codes to spans, write memos, retrieve excerpts, inspect a code-by-case matrix, and export auditable research artifacts.

The full 3.5 quotation below spans later phases. This feature implements its non-AI workspace, codebook, memos, retrieval and matrix. Suggestions/review belong to 003; evaluation to 004; experiment history to 005. The quoted idempotency gate's demo portion is completed in 004. Reproducibility export supports available records now and includes AI/evaluation/experiment records as those phases land.

Governing sources: docs/01–05 and constitution v1.0.0. This is a prepared feature; main activates it in phase order and runs analyze before implementation. No implementation or acceptance pass is claimed here.

## Authoritative workstreams (verbatim from doc02)

- **3.3 Import & domain [LB]** TXT/MD/CSV importers (content-hash idempotent); segmentation per `segmentation.yaml` (paragraph | utterance | sentence); cases + attributes from CSV columns; codebook CRUD + `qualia codebook freeze`.
- **3.5 Workspace UI [LB]** data, state and keyboard logic in `web/src/lib/`, markup in components (M4); doc 04 layout; span viewer; keyboard coding (↑/↓ segment, number = code, `a`/`r` accept/reject); codebook tree; right panel (codes, suggestions, model-reported score, provenance popover); memos; retrieval; matrix with heat shading + drill-down; review queue; experiment history.
- **3.9 Export [LB]** `qualia export --format csv|json [--no-text]`; `--bundle reproducibility` (events, versions, experiments, evaluation runs, config hashes, CLI versions).

## Functional requirements

- FR-001: Import UTF-8 TXT, MD and mapped CSV through pydantic adapters; reject invalid records with filename/row context and no partial source writes. Deduplicate by content hash and retain immutable source versions.
- FR-002: Segment imported sources by configured paragraph, utterance or sentence rules; store ordered source offsets and optional speakers, and reconstruct the exact segment text from immutable source text.
- FR-003: Create and update cases, source-case associations and attributes from explicit UI/CSV inputs; display source/case filtering without changing source content.
- FR-004: Provide human-only hierarchical codebook CRUD with cycle rejection, positive/negative examples and archive status. Freeze deterministic immutable snapshots with hashes; changing a draft cannot change a frozen version.
- FR-005: Assign and remove one or more codes on full segments or arbitrary overlapping spans by mouse and keyboard. Append events with segment, frozen codebook version, human actor and pipeline hash; never mutate history.
- FR-006: Persist and reload span anchors without offset drift, including non-BMP Unicode and overlapping multi-code selections. Use Recogito; use CSS Custom Highlight API only if its saved-span reload probe fails.
- FR-007: Provide memo creation/editing and links to code or segment, retrieval by current code/case, and the documented code-by-case matrix with count labels and excerpt drill-down.
- FR-008: Render source/case/codebook/memo navigation, transcript, active focus, code sidebar and provenance popover. Human events use solid stripes; trust fields remain visible. Data/state/keyboard logic stays in web/src/lib; components contain presentation.
- FR-009: Export CSV and JSON with complete event provenance and frozen versions. --no-text excludes transcript content throughout the export, including excerpts; evaluation predictions and vault content are excluded by default.
- FR-010: Export a reproducibility bundle of events, versions, available experiments/evaluations, config hashes and CLI versions; any requested source text is an explicit option, and protected vault data never enters a default bundle.
- FR-011: Expose matching CLI and validated local API operations using the frozen foundation contracts. All SQL writes remain in qualia/store/db.py and existing Host/token/header protections remain effective.

## User scenarios

- US1: A researcher imports one transcript twice and a mapped CSV, filters by case, creates a hierarchical codebook and freezes it. The second identical import reports zero new sources.
- US2: A researcher selects an overlapping Unicode span, applies two codes, navigates five segments using the keyboard, removes one assignment and reloads the page. Current spans and immutable history agree.
- US3: A reviewer opens a memo, retrieves a code, follows a matrix cell and exports without text. Counts match the excerpts; exported provenance can identify every decision without exposing transcript content.

## Success criteria

- SC-001: Import fixtures cover all three formats and segmentation modes; repeated imports add zero sources; invalid CSV rows identify their source and leave no partial transaction.
- SC-002: Domain/store tests prove hierarchy cycle rejection, immutable frozen snapshots, append-only assignment/removal and Unicode span round-trips.
- SC-003: Playwright MCP verifies working workspace, codebook, memos, retrieval and matrix screens; keyboard coding of five segments and span reload pass with screenshots.
- SC-004: CSV/JSON/no-text/reproducibility fixtures validate required provenance, correct current-coding counts, text exclusion and protected-vault exclusion.
- SC-005: Offline Python and web checks pass; generated API types match exported OpenAPI; no sealed-module, sole-writer or server-security invariant regresses.

## Authoritative acceptance excerpts (verbatim from doc02)

- [ ] Idempotency: same import twice → "0 new sources"; migrate twice → no-op; `qualia demo` twice → no duplicates.

Quoted shared gates retain their original scope. This feature proves its relevant part; later-phase responsibilities are stated above. Common I1/I6/I7 protections remain mandatory regressions, never exemptions.

## Informed assumptions

- Imported text is immutable. Exact content hashes deduplicate regardless of filename; importing changed content creates a new source and records version_of when an existing source lineage is explicitly selected. Do not infer lineage from unrelated matching names.
- Span offsets stored on coding events are zero-based, half-open offsets relative to the segment, consistent with 001_initial.sql. Source segment offsets use the same convention relative to source text. Browser UTF-16 offsets must round-trip Unicode safely to Python string offsets.
- CSV mapping is explicit: require a text column, permit a case identifier, speaker and named attribute columns; report filename and row for invalid input. Default segmentation is paragraph; utterance follows nonempty lines with optional speaker labels; sentence segmentation is a deterministic documented heuristic, not a new NLP dependency.
- Human codebook edits require explicit user actions. Existing frozen snapshots remain unchanged; coding must use a selected frozen version containing the chosen code. Code deletion becomes archival where historical references exist.
- Matrix cells count distinct currently coded segments per code/case, with multi-case sources appearing under each linked case. The label explains this unit; drill-down returns the same segments.
- Number keys select displayed code shortcuts; arrow keys move active segment. Shortcuts do not fire while editing text fields. A full-segment selection is the default when no text span is selected.
- JSON/YAML config conventions and the existing SQLite contract from 001 are retained. Plain doc04 tokens guide the working UI; the presentation-only polish remains Phase 7.
