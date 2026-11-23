# Why screens score below 9: causes, not symptoms (2026-11-23)

Sources: the fresh scorer reports of rounds 5–7. The final batch was scored by two scorers, Q and R. "Scorers" counts the reports that named the reason; the counts are taken from my round notes, not re-tallied from the raw reports.

| # | Screen | Reason under 9 | Scorers | Root cause | Status |
|---|---|---|---|---|---|
| 1 | Review (both) | Queue too long, cards too long, repeated text | 6+ (every round) | Every card repeated the full ECE caption, the group's own trigger reason, rationale and provenance, because the contract required all trust text on every card | Fixed `2e98c70` after owner approval (doc 04 change `70a89eb`) |
| 2 | Workspace, Retrieval | Coded text looks like a browser text selection | 4+ | The 22% code-colour fill is visually the same thing as a selection | Fixed `3c5f00f` (owner-approved underline) |
| 3 | All screens (phone) | Header takes a quarter of the first screen | 4 | The desktop header is stacked rather than re-planned for phones: brand, theme, project, status caption and the View row each get their own row | Fixed `2d52241`: one phone header row (brand, project, ⋯ menu), status notice kept; content starts at 139 px, was 207. Tactic: impeccable adapt.md mobile nav, Linear/GitHub mobile headers |
| 4 | Review (phone) | Reviewer field is in the wrong place (scorers disagree: first vs after the queue) | 4 | The reviewer's name is a once-per-session setting, but it is shown as a full form field on every visit, so wherever it goes it costs space or gets missed | Fixed `fc398fd`: field until a name is saved, then "Recording decisions as X · Change". Tactic: GitHub/Linear ambient identity, NVivo initials once |
| 5 | Workspace | "AI agrees" line duplicates a code already applied | 3 | A suggestion for a code the researcher already applied is drawn as a second, separate mark. The stripe contract (dashed suggestion, solid human) keeps it separate | Fixed `4973f76`: agreeing suggestion joins the applied code's line with its own dashed stripe and caption. Tactic: GitHub PR inline suggestions, ATLAS.ti AI coding notes |
| 6 | Experiments | Disabled Start buttons don't say why | 3 | The reason lives in the checklist above, not on or next to the disabled control | Fixed `762d3c4`: reason under each disabled button, aria-describedby, names an unfrozen codebook. Tactic: GitHub merge box; impeccable craft floor |
| 7 | Matrix | No sticky code column, no legend for the heat | 2 | Wide table with no frozen first column; heat colour is not explained | Fixed `1f7497d`: keyline on the frozen column, heat key 0 to max. Tactic: Excel freeze panes, NVivo/ATLAS.ti matrix legends |
| 8 | Analysis | Fold-out sections look unstyled and inconsistent | 2 | Native `details` summaries styled per screen instead of one disclosure pattern | Open |
| 9 | Retrieval | No text search | 2 | Missing feature: retrieval filters by code and case only | Open |
| 10 | Memos | Compose form always open | 2 | Writing a memo is the rarer action but gets the first screen | Open |
| 11 | Home | Progress view could be fuller | 1 | Status block is counts only, with no sense of how far through coding the study is | Open |
| 12 | Demo (all) | No recorded evaluation or experiment to look at | 3 | The demo snapshot contains neither; `demo/data` is protected and fixed | Not fixable without the owner |

## How this pass worked

- Research: a read-only Opus agent read the William Web Design kit (CRAFT.md, COPY.md and its rules), impeccable, taste-skill, frontend-design and design-critique, and compared the tactics with NVivo, ATLAS.ti, Dovetail, Linear and GitHub. The tactic for each fixed cause is in its row.
- William approved the two contract changes in this session himself (2026-11-23). Docs 04 and 05 record them (`70a89eb`).
- Usage was near its limit, so each cause was checked by measurement in the browser while it was being fixed. The fresh-reviewer cause checks were folded into the one final scoring round, not run separately.
- Not done this pass: causes 8 (one disclosure style), 9 (Retrieval text search), 10 (Memos compose button) and 11 (fuller Home progress). Cause 12 needs new demo data, which is protected.

## Final scoring (two fresh Opus scorers, A and B, screenshots before and after)

**Cause checks:**

| Cause | A | B |
|---|---|---|
| 1 Review length | reduced (page 8089 → 4988 px) | reduced (desktop 8089 → 4988, phone 11972 → 7091 px) |
| 2 Highlight looks like a selection | reduced (faint fill still reads as a selection) | gone |
| 3 Phone header | reduced (about 140 px) | gone (about 300 → 140 px) |
| 4 Name field | not fixed | reduced |
| 5 Duplicate suggestion line | gone | gone |
| 6 Disabled-button reasons | gone | gone |
| 7 Matrix column and key | gone | gone |

For cause 4, both captures used a fresh browser with no saved name, so they show the first-visit field by design. After a name is saved, every screen shows the one-line "Recording decisions as X · Change", which was verified in the browser. The scorers saw only the first visit.

**Scores (desktop / phone):** A 7.6 / 6.8, B 7.3 / 6.6. The previous round's scorers gave 8.3 / 7.6 and 7.7 / 6.7. These are different people, and the screens they rate lowest have changed: the fixed causes no longer appear among their reasons.

**The next causes, from this round's reasons:**

| Screen | Reason | Scorers | Root cause |
|---|---|---|---|
| Review | 15 near-identical cards (same code, same score), with no grouping or batch action | 2 | The queue is grouped by trigger reason only. When one code is suggested many times, the researcher must decide each card one by one. Needs group-by-code with "accept all n" (a feature with server-side batch review). |
| Evaluation | The Run button is apart from the backend and model settings it uses | 2 | Round 7 moved Run into the result panel's empty state. The settings and the action should sit in one form. |
| Workspace (phone) | The coding sheet covers part of the passage being coded | 2 | The sticky sheet's height (30vh) overlaps the active passage. The transcript needs bottom padding equal to the sheet, or the sheet should start collapsed. |
| Experiments (phone) | Checklist statuses wrap onto their own lines | 2 | The round 7 phone rule puts each status under its label. A status column that fits or a mono suffix would read better. |
| Analysis (phone) | The tab strip is clipped with no scroll cue | 2 | The tabs need the same edge chevron as the code row. |
| Matrix | The Total header is about 3 px off the baseline | 2 | `.matrix-total` header alignment |
| Workspace / Review | The same identity field is labelled "Human actor" on Workspace and "Reviewer" on Review | 1 | Two labels for one setting. The e2e test uses "Human actor". |
| Retrieval | No text search, no speaker filter | 2 | A missing feature (cause 9) |
| Memos | The compose form always takes half the page | 1 | Cause 10, still open |
