# Why screens score below 9: causes, not symptoms (2026-11-23)

Sources: the fresh scorer reports of rounds 5–7. The final batch was scored by two scorers, Q and R. "Scorers" counts the reports that named the reason; the counts are taken from my round notes, not re-tallied from the raw reports.

| # | Screen | Reason under 9 | Scorers | Root cause | Status |
|---|---|---|---|---|---|
| 1 | Review (both) | Queue too long, cards too long, repeated text | 6+ (every round) | Every card repeated the full ECE caption, the group's own trigger reason, rationale and provenance, because the contract required all trust text on every card | Fixed `2e98c70` after owner approval (doc 04 change `70a89eb`) |
| 2 | Workspace, Retrieval | Coded text looks like a browser text selection | 4+ | The 22% code-colour fill is visually the same thing as a selection | Fixed `3c5f00f` (owner-approved underline) |
| 3 | All screens (phone) | Header takes a quarter of the first screen | 4 | The desktop header is stacked rather than re-planned for phones: brand, theme, project, status caption and the View row each get their own row | Open |
| 4 | Review (phone) | Reviewer field is in the wrong place (scorers disagree: first vs after the queue) | 4 | The reviewer's name is a once-per-session setting, but it is shown as a full form field on every visit, so wherever it goes it costs space or gets missed | Open |
| 5 | Workspace | "AI agrees" line duplicates a code already applied | 3 | A suggestion for a code the researcher already applied is drawn as a second, separate mark. The stripe contract (dashed suggestion, solid human) keeps it separate | Open (contract-bound) |
| 6 | Experiments | Disabled Start buttons don't say why | 3 | The reason lives in the checklist above, not on or next to the disabled control | Open |
| 7 | Matrix | No sticky code column, no legend for the heat | 2 | Wide table with no frozen first column; heat colour is not explained | Open |
| 8 | Analysis | Fold-out sections look unstyled and inconsistent | 2 | Native `details` summaries styled per screen instead of one disclosure pattern | Open |
| 9 | Retrieval | No text search | 2 | Missing feature: retrieval filters by code and case only | Open |
| 10 | Memos | Compose form always open | 2 | Writing a memo is the rarer action but gets the first screen | Open |
| 11 | Home | Progress view could be fuller | 1 | Status block is counts only, with no sense of how far through coding the study is | Open |
| 12 | Demo (all) | No recorded evaluation or experiment to look at | 3 | The demo snapshot contains neither; `demo/data` is protected and fixed | Not fixable without the owner |
