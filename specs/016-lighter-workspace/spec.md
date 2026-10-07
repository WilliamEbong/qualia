# Lighter workspace payload

Follow-up recorded in BUILD-STATE P15.3 and the handoff: the workspace response for the AnnoMI demo was 12–13 MB, which drove the simulated Lighthouse performance score down (59 mobile) and made a headless browser run out of memory. Measured on a copy of the demo project (2026-10-06): `coding_events` 5.58 MB and `current_codings` 5.65 MB of 13.46 MB. Every current-coding row is also a coding event, so the response carried most rows twice.

## Requirements

- FR001: The workspace response sends `current_coding_ids` (event IDs from the `current_codings` view) instead of the current-coding rows; `current_codings` stays in the schema as an empty default for compatibility.
- FR002: The web app rebuilds current coding from `coding_events` by ID on every load; static demo snapshots that embed rows keep working unchanged.
- FR003: No change to stored data, provenance, analysis inputs (analysis reads the database directly) or exports.

## Success criteria

- SC001: On a copy of the demo project, the response shrinks from 13.46 MB to about 7.4 MB with identical current assignments, matrix and analysis in the browser.
- SC002: API tests assert the IDs; a web unit test covers rebuilding and the demo fallback; full suites pass.
