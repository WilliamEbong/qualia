# Inductive and reflexive workflow

Delegated by the owner on 2026-10-06 (see `docs/answers/07-improvement-round.md`). The review of Qualia against core qualitative concepts found: inductive coding needs three separate steps for each emerging code (draft, freeze, code); memos link only to a segment or code and are silently overwritten when edited; themes and reflexivity have no support beyond free-text memos. This feature closes those gaps with the smallest changes that keep the provenance model intact.

## Requirements

- FR001: In the coding panel, a person can name a new code (optional definition, optionally keeping the selected text as a positive example) and in one action create the draft code, freeze a new codebook version and assign the code to the current selection or segment. The caption states that the freeze includes all current draft edits.
- FR002: Memos have a kind: `analytic` (default), `reflexive`, `theme` or `method`, and may link to a case and a source as well as a segment and a code.
- FR003: Editing a memo keeps the replaced version in an append-only `memo_revisions` table written by a database trigger (saving unchanged values adds nothing). The Memos page shows earlier versions; exports include them.
- FR004: The Memos page filters by kind and labels linked segments with their source name.
- FR005: The CLI `memo` command accepts `--kind`, `--case` and `--source`; editing with `--memo-id` changes only the options given and reports invalid input without a traceback.
- FR006: The user guide explains themes as a documented pattern (a parent code plus a theme memo linked to it), reflexive memos, and disclosure of AI assistance.

Constraints: migration 004 is additive; `memos` stays mutable but its history is immutable; no new dependency; demo snapshots without the new keys still load.

Assumptions: no theme entity or child-to-parent count roll-up yet (documented pattern first; add when real use shows the need); memo revisions are not restorable from the UI (they are evidence, readable and exported).

## User scenarios

A researcher reading a transcript notices "being invisible", selects the words, types the code name and presses **Create, freeze and assign**. Later they write a reflexive memo about their own experience of waiting rooms, link it to the source, and revise it twice; both earlier versions remain visible and exported.

## Success criteria

- SC001: Store tests for kinds, links, history and unchanged saves; CLI test for partial edits; migration and append-only coverage.
- SC002: Playwright verification of in-vivo coding and memo history on a synthetic project.
- SC003: Full offline suite and web checks pass.
