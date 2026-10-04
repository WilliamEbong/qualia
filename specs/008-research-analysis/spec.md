# 008 — Mixed-methods analysis and data-science workbench

## Authorization and scope

On 2026-10-03 the owner requested data science, visualization and applicable NVivo features, then selected **both** mixed methods and data science. This extends the original build. Use reversible, local, read-only analysis first; preserve all original safety and live-provider gates. Main selects this feature directory under the owner's autonomous-build instruction. No new dependency, methodology change or protected-document rewrite is required.

## Requirements

- FR001: Add an Analysis view and matching CLI/API using existing visible workspace data only. No writes, egress, protected-vault reads or AI calls. Pending/rejected suggestions never count as coding.
- FR002: Filter by source, case, any/all selected current code IDs and literal case-insensitive text. Report the complete selection criteria, denominator counts and current coding-event IDs so results are reproducible. Validate unknown IDs, query length and bounded options before computation.
- FR003: Show code frequency as distinct selected segments and distinct linked cases, with explicit denominators and percentages. Repeated/overlapping spans of one code do not inflate presence. Display frozen version IDs and explain that display names are current code names; excerpt provenance retains historical names.
- FR004: Compare code presence across a researcher-selected case attribute. Count each case once in its group; missing and conflicting attribute values form explicitly labeled groups. Multi-case sources can contribute to multiple cases/groups and this caveat remains visible.
- FR005: Show pairwise code co-occurrence with an explicit same-segment or overlapping-span mode. Same-segment counts each segment once per unordered pair. Overlap is a positive-length intersection; touching boundaries do not overlap. A separate segment-presence Jaccard always uses the intersection divided by union of selected segments carrying either code, regardless of overlap mode. Never describe association as causation.
- FR006: Provide literal text queries, any/all coding queries, and Unicode word frequency with counts and distinct-segment frequency. Tokenization, case folding, minimum word length, stopword handling and result limits are explicit. Return matching segment IDs for excerpt drill-through, and show total versus displayed matches.
- FR007: For explicitly selected case attribute fields, calculate finite-number count, missing count, invalid/conflicting count, mean, median, sample standard deviation, minimum and maximum. Do not silently infer that categorical numbers are continuous measurements. Empty/insufficient data displays n/a.
- FR008: Calculate pairwise-complete Pearson correlation with sample size for selected numeric fields; constant or fewer-than-three paired observations return n/a. Show an accessible scatter plot for a selected pair with case identity. No p-values, statistical-significance or causal claims.
- FR009: Render accessible frequency bars, co-occurrence heat table and numeric scatter plot, accompanied by exact data tables and linked source excerpts. SVG export preserves titles, labels, counts and criteria; charts never rely solely on color. At375px there is no page overflow; table overflow stays in its own container.
- FR010: Export reproducible analysis JSON, case-by-code/attribute CSV, and downloadable Python/R starter scripts that read that CSV using standard-library Python/base R. Include no source text by default, neutralize spreadsheet formula-leading strings, use stable column IDs and provide a column dictionary. Scripts never execute inside Qualia.
- FR011: The read-only static demo includes a report recomputed solely from the approved snapshot and no API calls. Static filters requiring recomputation are disabled with an explanation; chart/excerpt exploration remains available.
- FR012: Preserve existing coding, review, evaluation and improvement behavior; generated API types match the server. Add hand-computed fixtures for duplicate spans, links/groups, Unicode, empty data, numeric missingness, overlap and correlations; verify UI with Playwright MCP and run existing regression suites.

## Scenarios and success criteria

- US1/SC001: A researcher compares themes by participant group, clicks a nonzero result and sees exactly its contributing excerpts with event provenance. Fixture counts and percentages match hand calculations.
- US2/SC002: A researcher chooses numeric case measurements, inspects missingness and Pearson N, exports CSV and runs the supplied Python/R code externally. The Python starter is executed against the fixture export and reproduces the expected means; R syntax/source is reviewed unless R is installed.
- US3/SC003: A researcher runs a text/code query and contrasts same-segment with overlap co-occurrence. A boundary-touch fixture counts only in same-segment mode, and repeated spans do not duplicate presence.
- SC004: Live local and static UI navigation, chart/table labels, filters, excerpt drill-through and downloads work in Playwright MCP at1280px and375px. Static browser records zero API requests.
- SC005: Analysis leaves coding tables, manifests, project files and protected data unchanged; default exports omit transcripts. Existing offline tests pass and dependency list is unchanged.

## Deliberate limits

This increment covers useful NVivo-style mixed-methods exploration and reproducible descriptive data science. Advanced model fitting/inference, topic models, audio/video coding, proprietary NVivo project import, conceptual-map editing and real-time collaboration remain future features, not implied parity claims. Data science exports enable deeper work in Python/R without embedding an unrestricted code runner or choosing the researcher's methodology.
