# Phase 2 ENGINE/API contract review

Reviewed commit e17bbf3 on 2026-10-03 against specs/002-workspace. Read-only review of ENGINE, CLI and API; root owns implementation fixes and browser acceptance. Previously green suites were not rerun. Only two concrete concerns received focused synthetic reproductions.

## Findings

1. **High — FR-009 / SC-004: no-text export can leak transcript through mapped attributes.** Importing CSV with `attribute_columns=['text']` stores the source transcript in `attributes.value`. The exporter removes fields named text but does not remove that value. Focused reproduction returned `no_text_contains_transcript=True` for both JSON and CSV. Narrow fix agreed with root: redact freeform attribute values in no-text exports and mark metadata redaction explicitly. Preserve provenance identifiers; no-text is not a deidentification promise.

2. **Medium — FR-001/002/011: CLI newline decoding changes source identity.** The CLI calls Path.read_text, which normalizes CRLF to LF. Importing a synthetic CRLF file through the bytes adapter created source 1; importing the same file through the current CLI read operation created source 2. Both reported one new source. Root will pass read_bytes directly to the UTF-8 adapter, preserving content and matching API identity.

3. **Medium — FR-011: CLI lacks explicit lineage selection.** API ImportInput and the adapter accept version_of; the CLI import command has no corresponding option. Root will add and forward it alongside the byte-preservation fix.

No ENGINE/API contract convergence claim is made until these focused fixes receive their regressions. Root acknowledged and owns all three changes; this review changed no implementation files.

## Reviewed behavior

- CSV parsing uses strict column-count checks and pydantic source validation with filename/row errors; all records validate before the Store transaction. Source hashes deduplicate exact text, while explicit lineage and case associations remain separate.
- Store import failures roll back source, segments, cases and attributes together. Case edits and attribute upserts are atomic; source associations are additive and rename-only edits preserve them.
- Paragraph, utterance and deterministic sentence segmentation retain offsets into immutable strings. Stored spans count Unicode code points, and retrieval uses matching SQLite character offsets. Existing non-BMP/overlap regression evidence is relevant; browser selector/reload verification remains root's separate gate.
- Draft code edits validate parent cycles and lists of examples. Archived codes remain historical records. Frozen snapshots and hashes do not change when the draft changes.
- Manual assignments/removals append complete provenance. Retrieval follows current events; matrix cells count distinct segments, avoiding inflated counts from overlapping spans and multi-case joins.
- CSV export neutralizes spreadsheet formula prefixes. Evaluation predictions remain excluded, config content is represented only by hashes, and exporter code never traverses the protected vault. No-text frozen snapshots are explicitly marked redacted while retaining their original version hashes; text-inclusive export preserves full definitions.
- CLI/API cover codebook creation/save/archive/freeze/list, coding/removal, memos, cases/attributes, retrieval, matrix and exports. The lineage option is the concrete parity exception above. SQL writes remain in Store and the existing server security middleware protects the new routes.

## CI and acceptance status

Main-branch Checks for e17bbf3d753b60be5607b361a627acc26b7bab58 completed successfully: [run 37159091407](https://github.com/WilliamEbong/qualia/actions/runs/37159091407). Dependabot runs were excluded from this conclusion. The root's reported full suite was 58 passed; this review did not repeat it. New fixes require their own exact regression evidence and new-head CI.

Workspace, keyboard, Unicode saved-span reload and matrix browser acceptance are intentionally left to the root's ongoing Playwright verification.
