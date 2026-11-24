# Review batches and evidence search

William asked for this on 2026-11-23, relayed by the orchestrating session ("so proceed"). Build the two workflow changes the design root-cause pass named as the ones a researcher would feel: deciding many suggestions for one code at once, and searching the evidence.

## Requirements

- FR001 Group by code: the review queue offers "Group by: reason | code". Reason is today's grouping and stays the default. Code groups list each code once, with its pending count. Within a group, each suggestion is one compact row: the excerpt, its `suggested · model-reported` score, and its own Accept and Reject. The calibration, reason, rationale and provenance disclosure stays on every row.
- FR002 Batch decision: each code group offers "Accept all n" and "Reject all n". The confirmation names the count and the code ("Accept all 12 suggestions of Waiting and uncertainty?") and who will be recorded.
- FR003 Audit: `POST /api/projects/{slug}/review/batch` takes `{suggestion_ids: [int, 1..500, unique], decision, actor, note}`. It records each suggestion exactly as a single review does: its own `coding_events` row (human actor, its own time, `suggestion_id` and copied provenance including the model-reported score) and its own `feedback_events` row. It is one transaction: if any id is absent or already reviewed, nothing is written and the error names the id.
- FR004 Undo: an accepted batch can be undone from the notice that follows it. `POST /api/projects/{slug}/review/batch/undo` takes `{event_ids, actor}` (the accept events the batch returned). For each one that is still the current coding of its span, it appends a human `remove` event, exactly like Remove assignment. The accept records stay. It is one transaction, and it refuses any id that is not an accept event. A rejected batch cannot be undone: reopening a suggestion would mean writing a model event the model never made, and the audit trail is append-only. Its confirmation says so.
- FR005 Retrieval search: a text box filters the excerpts already loaded, matching any part of the excerpt or its passage and ignoring case and accents. A speaker filter lists the speakers found in the results: the segment's speaker, or a leading "Name:" in its text. The count shows "n of m excerpts". When nothing matches, a no-match state names the search and offers to clear it. The empty state for a study with no coding stays as it is.

Assumptions: 500 is the batch bound (larger queues are decided in several batches); the search is client-side over the current code and case filter, since retrieval already returns every current excerpt for that filter.

## Success criteria

- SC001 Python: a batch accept writes one coding event and one feedback event per id with the same provenance as single reviews; a batch with an already-reviewed or unknown id writes nothing; undo appends one remove per still-current accept, leaves the accept records, and refuses non-accept ids; the API validates bounds and duplicates.
- SC002 Vitest: grouping by code, search and speaker filtering (accents, no match), and speaker derivation.
- SC003 Browser checks: group by code, accept all with confirmation, undo, and Retrieval search with no match. The same two reviewers score Review and Retrieval before and after.
