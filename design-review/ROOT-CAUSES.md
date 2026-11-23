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
