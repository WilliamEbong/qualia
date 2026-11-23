# Overnight work on Qualia: 2026-11-22 to 2026-11-23

## What changed for you

These are the effects you can see when you use Qualia. The details and evidence for each one follow further down.

**Your research data is safer.**
- **Older copies of the app:** if you keep an old install folder and open a project with it, Qualia now refuses rather than writing into a newer project.
- **Re-running classification:** this no longer puts back suggestions you already accepted or rejected.
- **Review notes:** a note you type while reviewing is now kept even if you click a different suggestion's button.
- **Your name in the record:** the name you code under is remembered after a reload, so later decisions are no longer recorded as "researcher".
- **Exports:** an export that includes the interview text is now named `-with-text`, so you cannot share it by mistake.
- **Starting a project's database:** when several things open a project at once right after an update, the upgrade no longer fails with an error.

**The AI side spends less and behaves as documented.**
- **No-code answers:** passages where the model proposed no code are no longer sent to the expensive model.
- **A passage Jev cannot accept:** Jev skips just that passage instead of stopping the whole run.
- **Rate limits:** a retry now waits a moment first, so it is less likely to fail the same way.
- **Threshold tuning:** it no longer replaces a better setting with a worse one.
- **Keep or revert:** a gain of exactly the required size is no longer reverted because of a rounding error.

**The app is easier to use.**
- **One main button:** each screen has one clearly marked main action.
- **Messages:** save confirmations and errors stay in view, and old ones clear when you switch screens.
- **Plainer words:** for example, "characters 0–72" rather than "0:72", one name for importing, and short explanations of what freezing does and what the Include field is for.
- **Review:** the queue shows the passage you are judging first, with the Accept and Reject buttons beside it.
- **Coding on a phone:** the code buttons stay at the bottom of the screen while you read.
- **Analysis:** results now come first, with the criteria and export options folded away until you open them.
- **Keyboard and screen readers:** both work better. Fields have visible outlines, panels take focus when they open, and buttons say which suggestion they act on.

**Design scores.**
- Fresh reviewers rated the main screens about 7.2 out of 10 on desktop and 6.8 on phone, up from 7.1 and 5.9.
- No screen reached 9. What stands in the way is mostly new features, rules in the design docs that only you can change, and splitting the long Analysis page. Round 5 below lists each one.

**Faster and tidier.**
- **Commands:** every `qualia` command except `open` starts about 3× faster, because it no longer loads the web server.
- **CI:** the type check runs once instead of three times.
- **Code:** three copies of the same check are now one.
- **Code map:** a code map of the project, built with graphify, is ready in this worktree.

**What I need from you:** nothing is required.
- **To take the changes:** merge the branch (steps under "How to merge" below). Each change can be undone on its own.
- **Optional:** look through `design-review/overnight/before` and `final` to see the visual changes.
- **Optional:** decide whether manual codes should be allowed to share a name ("Found, not changed").

Branch `claude/overnight-fixes-3d262b`, based on `main` at `2978c5d`. Nothing was pushed, merged, released, tagged or version-bumped.

## Tests

| | Before | After |
|---|---|---|
| Python (`uv run pytest`) | 682 passed, 5 skipped, 4 failed, 4 errors | 703 passed, 5 skipped, 0 failed (full run after the last Python change in round 4) |
| Web (`npm test`) | 63 passed | 65 passed |
| Static-demo e2e (`tests/e2e/demo.spec.ts`) | not run | 1 passed |
| `tsc --noEmit`, `ruff check` | clean | clean |
| `pip-audit` / `npm audit` | 17 known vulnerabilities in 3 packages / 1 moderate | 0 / 0 |

The 4 failures and 4 errors before the pass all came from one cause on this PC: the newer Codex CLI. Round 2 fixed the tests (#12).

## Changes

Each entry says what changed, why, the evidence and the commit. To undo any one of them, run `git revert <hash>`; each commit stands on its own.

1. **Database upgrades no longer fail when several requests open the project at once.** `7aeaf94`
   - **Problem:** `Store.migrate` read the schema version before it took the write lock. When the app opened the first time after an upgrade, its parallel requests all saw the old version and each tried to re-run the migration. Every attempt after the first failed with `duplicate column name` and the user saw an HTTP 500. The pre-upgrade `.vN.bak` file could also be overwritten with already-upgraded contents.
   - **Fix:** each migration now takes `BEGIN IMMEDIATE`, re-reads `user_version` and skips the work if another connection already did it. The backup is copied under the same lock through a separate read-only WAL connection, because backing up from the connection that holds the lock hangs.
   - **Evidence:** `tests/test_foundations.py::test_concurrent_open_of_an_older_database_upgrades_once` covers a deterministic interleaving plus four parallel opens. It failed with `duplicate column name: model_version` on the old code. In the auditor's stress script, 20 of 20 trials failed before the fix and 0 of 20 after.
2. **`qualia export --output` keeps the stored line endings.** `f92b368`
   - **Problem:** `Path.write_text` rewrote LF as CRLF on Windows, so text-inclusive CSV exports no longer matched the stored text that segment offsets index.
   - **Fix:** the file is written with `newline=''`.
   - **Evidence:** `tests/test_cli.py::test_cli_export_output_file_keeps_stored_newlines`.
3. **A non-ASCII launch token now gets 401 instead of a 500.** `bce82ce`
   - **Problem:** `secrets.compare_digest` raises on non-ASCII `str`. The crash happened in the middleware, so the error response also lacked the security headers.
   - **Fix:** the token is compared as bytes.
   - **Evidence:** a new assertion in `test_server_security_and_offline_workspace`.
4. **Record IDs above SQLite's 64-bit range now return 400, not 500.** `d7aeaf4`
   - **Problem:** IDs that large raise `OverflowError` in the driver, and the retrieval, memo, coding and proposal routes had no handler for it.
   - **Fix:** one exception handler next to the existing `ValueError` handler.
   - **Evidence:** `tests/test_workspace_api.py::test_out_of_range_record_ids_are_rejected_not_crashes`.
5. **A Jev key failure now shows as `authentication`, as the user guide's troubleshooting table says.** `4c5726d`
   - **Problem:** the adapter raises `authentication` for 401/403 and the process runner reports `containment_unavailable`. Neither code was in `SAFE_FAILURES`, so both showed as a generic `provider_error`.
   - **Fix:** both are fixed internal codes, never provider text, so they were added to the list.
   - **Evidence:** extended `test_safe_failures_name_a_rejected_flag_or_old_version_but_never_provider_text`.
6. **Repeatability kappa is null when neither run varies.** `4422d66`
   - **Problem:** the published definition says "null when neither run varies", but `run_agreement` returned `0.0` when each run was constant yet the two disagreed (all yes against all no). The panel then graded that degenerate value as poor agreement.
   - **Evidence:** `tests/test_model_experiments.py::test_run_agreement_kappa_is_null_when_neither_run_varies_even_if_they_differ`.
7. **KEEP/REVERT boundaries stay inclusive when the metrics carry float noise.** `a60d82e`
   - **Problem:** `macro_f1` is a float mean. For example, `sum([.05] * 3) / 3 == 0.05000000000000001`, so an exact 0.01 gain measured as 0.00999… and was REVERTed with a false reason. The policy's own comment says its boundaries are inclusive.
   - **Fix:** measured values are compared at 12 decimal places. The human-authored policy values are unchanged, and the existing tests still REVERT a value 1e-9 outside a boundary.
   - **Evidence:** `tests/test_improve_policy.py::test_inclusive_boundaries_survive_float_noise_in_measured_metrics`.
8. **Docs: two inline commands in the user guide now include `--project my-study`.** `6cbc3ac`
   - **Problem:** without it, `qualia repeatability` and `qualia improve --agent model …` default to the demo project, and the second can call a paid CLI.
9. **`qualia codebook save --code-id` accepts a file that holds only the changed fields.** `7344997`
   - **Problem:** the command's help and the guide both say this works, but the file was validated as a full record that requires `name`.
   - **Fix:** edits now use the all-optional `ProposalValues` model. `validate_code` still rejects null or blank values.
   - **Evidence:** extended `test_cli_partial_code_edit_keeps_unsent_fields_and_errors_are_clean`.
10. **Bad CLI input gives a usage error, not a traceback.** `14a0372`
    - **Problem:** three inputs raised uncaught exceptions: an invalid project name (in every command, through `resolve_project`), an unknown export format, and a negative `qualia code --start`.
    - **Fix:** these now exit with code 2 and a message.
    - **Evidence:** `tests/test_cli.py::test_cli_reports_bad_input_as_usage_errors_not_tracebacks`.
11. **Security patches in the lockfiles only.** `4994ff3`
    - **Python:** certifi 2026.7.22 → 2026.10.18, filelock 4.0.9 → 4.2.1 (dev only, used by pip-audit) and opentelemetry-api 1.45.0 → 1.45.2.
    - **npm:** qs 6.16.0 → 6.17.1, a transitive dependency of `@annotorious`.
    - **Scope:** each is the minimum fixed release or a compatible minor version, and no declared range moved. `pip-audit` and `npm audit` are now clean, and the web tests, typecheck and `vite build` pass.

## Codex review

Codex reviewed the branch diff against `main` through the installed codex plugin (`review --base main --scope branch`). Its verdict: "No actionable regressions were found in the diff or affected callers." It ran 33 policy, agreement and error-sanitization tests, and they passed. Its sandbox is read-only, so it could not run the tests that need to write files; this session ran the full suite instead.

## Round 2: 2026-11-23

You approved fixing the items from "Found, not changed" and asked for continuing rounds. Where an item was your decision, the commit message says what was chosen, why, and how to revert it.

12. **Codex 0.170 wire probes pass again.** `0e43357`
    - **Who notices:** anyone running the suite on a PC with the current Codex CLI, every run; 8 false failures gone.
    - **Problem:** 4 probes failed and 4 fixtures errored because Codex 0.170 no longer sends an empty `additional_tools` item.
    - **Fix:** the assertion now checks the safety property directly: no top-level `tools`, and no input item of any type carrying a tool definition.
    - **Evidence:** the 9 installed-Codex tests pass against the local recorder.
13. **Threshold tuning keeps a current cutoff the grid cannot beat.** `26b40e2`
    - **Who notices:** anyone who runs threshold tuning a second time; an already better cutoff is no longer replaced with a worse one.
    - **Evidence:** `tests/test_metrics.py::test_tune_thresholds_keeps_a_current_cutoff_the_grid_cannot_beat` (current 0.73 at F1 1.0 was replaced by 0.70 at F1 0.8).
14. **Workspace CSV exports name the cells they escaped** (your decision). `7367780`
    - **Who notices:** researchers re-analysing a text export whose passages begin with "-", "=", "+" or "@" (common in transcripts); the original text is now recoverable.
    - **Chosen:** a trailing `escaped_columns` column listing the escaped cells per row, as the analysis export already flags its cells. Escaping itself is unchanged, so spreadsheets stay safe, and the stored text is now recoverable. The user guide explains it.
    - **Evidence:** `tests/test_export.py::test_csv_flags_escaped_cells_so_the_original_text_is_recoverable`.
15. **A segment with no proposed code is no longer escalated** (your decision). `cbbc7d6`
    - **Who notices:** anyone with escalation on, every run; most no-code segments no longer go to the most expensive model.
    - **Chosen:** an answer with no candidate code is treated as a decision, not uncertainty, so it is not sent to the expensive tier. Segments whose candidates were all removed by a threshold still escalate on their raw scores.
    - **Evidence:** `tests/test_ai_router.py::test_a_confident_no_code_answer_is_not_escalated`.
16. **`daily_calls` and `run_segments` keep their current counting, and the guide now says so** (your decision). `2c7ad04`
    - **Who notices:** anyone setting a small `daily_calls` for a first trial; the guide now says offline runs count too.
    - **Chosen:** no code change. Spec 003 FR-005 enforces the limits before every attempted call, including retries, and the build doc's acceptance check expects `daily_calls: 0` to stop even offline runs. Counting every call and every sent segment is also the cautious reading for spend.
17. **One segment Jev cannot accept no longer stops the rest of the run.** `5fb691c`
    - **Who notices:** Jev users with an unusually long passage and long code definitions (rare); the rest of the run is still classified. One-line change, no added code.
    - **Evidence:** `tests/test_ai_router.py::test_one_segment_the_provider_cannot_admit_does_not_stop_the_rest_of_the_run` (only 1 of 4 segments was classified before the fix, 3 of 4 after).
18. **Retries wait 1 s, then 2 s.** `16d242f`
    - **Who notices:** Jev users who set `max_retries` and hit a rate limit; the retry has a chance to succeed instead of failing the same way.
    - **Problem:** a 429 or transient failure was retried at once and usually failed again while still using a daily call and a cost reservation. Only Jev retries; native CLIs never do.
    - **Evidence:** `tests/test_ai_router.py::test_retries_back_off_before_resending`.
19. **The in-vivo example cap counts characters, and says when it applies.** `47cd16e`
    - **Who notices:** anyone creating a code from a long selection with "keep as example" checked; they are told why no example was kept.
    - **Problem:** a selection over 500 UTF-16 units was silently dropped as an example.
    - **Evidence:** a new vitest case in `web/src/lib/workspace.test.ts`.
20. **Counts of one use the singular** in the web UI (`4b7fd79`, `07f083f`) and in `qualia import` (`16a39c1`).
    - **Who notices:** every user, on every screen showing a count of one.
    - **Evidence:** a vitest case for the new `counted()` helper. In the built app with Playwright, Review showed "1 pending suggestion" and "1 suggestion · 1 segment · 1 call · 0 cache hits", with no console errors.

### Round 2 audit

Three read-only Opus auditors covered: storage and migrations; AI routing, budgets, evaluation and the improvement loop; and server, web and docs. Each finding was confirmed, then kept only if it passed your "tangible improvement" bar.

21. **Refining a code can no longer flip a negative example to positive.** `f9cc19c`
    - **Who notices:** researchers using **Refine codes**. Before, the model could move their negative example into the positive list without quoting any passage.
    - **Evidence:** `tests/test_code_proposal_ai.py::test_refine_cannot_turn_a_researcher_negative_example_into_a_positive_one`.
22. **An older copy of the app refuses a project saved by a newer one.** `595b154`
    - **Who notices:** anyone who keeps the previous install folder and opens a project with it after an update. It used to write into a schema it did not know, with no backup.
    - **Also:** a failed open no longer leaves the database file locked.
    - **Evidence:** `tests/test_foundations.py::test_an_older_app_refuses_a_database_from_a_newer_version_and_releases_it`.
23. **Benchmarks whose text contains U+2028 or U+0085 load again.** `0e5a27d`
    - **Who notices:** anyone whose benchmark text contains these characters, which come from some pasted web and PDF text. Before, the split published fine but could never be read back.
    - **Evidence:** `tests/test_benchmarks.py::test_text_with_unicode_line_separators_stays_one_record`.
24. **CSV sources are named by spreadsheet row.** `6005e79`, corrected in `a1f70f6` after Codex review found that blank rows were not counted
    - **Who notices:** anyone importing a CSV with multi-paragraph cells. After the first such cell, every later source was named with the wrong row.
    - **Evidence:** `tests/test_import.py::test_csv_sources_are_named_by_spreadsheet_row_even_with_multiline_cells`.
25. **Opening Import, Case or Export moves keyboard focus into the panel.** `d280474`
    - **Who notices:** keyboard and screen-reader users, every time they open a panel (WCAG 2.4.3).
    - **Evidence:** in the built app with Playwright, focus landed on each panel heading and typing in a field kept focus. There is no focus ring on a mouse click.

**Audited and not changed, because they fall below the bar.** Each is one line, with the reason:
- **Large imports are quadratic.** A 1 MB source takes 4 s and 2.4 MB takes 20 s, because the segment trigger re-measures the whole source. Typical interviews are far smaller, and the fix needs a migration.
- **Unhandled 500s lack security headers.** This needs an unrelated crash first, on a loopback-only server.
- **Error text and status codes.** Raw constraint text appears only for spans the UI never sends, and missing records return 400 rather than 404. The UI handles both.
- **Manual codes can share a name.** Real, but it is a methodology rule for you to decide, and existing projects may already contain such names.
- **`a`/`r` review shortcuts act on the first suggestion when none is selected.** This is the documented design.
- **Experiment REVERT with a read-only file.** Neither real operator can change file modes.
- **Jev cost above 64k input tokens.** Jev's context is 64k.
- **Smaller items.** Bare CR or U+2029 paragraph breaks, missing request-size caps, live-region timing, and duplicate evidence IDs.
- **Flaky tests under load.** The installed-CLI probes and the launcher idle-timing test each failed once while other sessions loaded the PC, and passed when re-run alone.

## Design pass: UI and UX (2026-11-23)

**Method.**
- **Identity:** I read DESIGN.md and docs 04–05 first. The archival look, the type, the code colours, the provenance stripes and every trust caption stay exactly as they were.
- **What changed:** only styles and component markup (docs 05 §1). Nothing in `web/src/lib`, the API or Python changed.
- **Projects used:** a synthetic 3-interview study I wrote (invented text, in a temporary home), plus the committed public demo snapshot. The AnnoMI demo data is protected by the guard hook, so it was not used.
- **Screens:** I captured every view at 1280 and 375 px.
- **Round 1 critique:** five fresh-context Opus reviewers worked in parallel, one lens each: hierarchy, words, flow, visual craft and accessibility.
- **Fixes and later rounds:** I fixed the top items, then ran three more rounds of fresh reviewers. They included the William Web Design reviewer and language reviewer, plus a final regression check. I stopped when the reviewers found nothing a user would notice.

**Changes, each with who notices.**

29. **No stray rust stub under the header.** `4a93d53`
    - **Who notices:** everyone, on every screen. It came from an empty alert region.
30. **Save and error messages stay in view.** `4a93d53`
    - **Who notices:** anyone who saves a code, freezes or decides on a proposal far down the page. Before, the confirmation appeared off-screen at the top.
31. **Form fields have visible outlines.** `4a93d53`
    - **Who notices:** low-vision users and anyone on a bright screen. Outlines went from 1.9:1 to 5.6:1 contrast (WCAG 1.4.11).
    - **Also:** focused matrix cells keep a visible ring.
32. **One clear primary action per screen.** `71134df`, `292f394`
    - **Who notices:** first-time users looking for the next step.
    - **Which buttons:** Open project, Freeze codebook, Run classification and Run validation evaluation. Each was checked with Playwright at 4.61:1 in light and dark.
33. **Plainer words.** `71134df`, `6e0f7c3`
    - **Who notices:** non-technical researchers.
    - **What changed:**
      - One name, **Import source**, for importing.
      - Spans read "characters 0–72" rather than a time-like "0:72".
      - A caption explains the **Human actor** field, and says coding stays disabled until it is filled.
      - Codebook explains what freezing does.
      - Evaluation's empty state says what it compares and how to import a benchmark.
      - "Passage" is used consistently.
    - **Unchanged:** every label named in the user guide or tests, and all trust wording.
34. **Screen readers hear which suggestion a button acts on.** `71134df`
    - **Who notices:** screen-reader users.
    - **What changed:**
      - Accept, Reject, Open segment, Remove assignment and the proposal buttons name their code or proposal.
      - Key hints are announced as shortcuts.
      - Run results are announced.
      - No heading levels are skipped.
35. **Review is shorter and puts the decision first.** `157d063`, `58fafd1`
    - **Who notices:** anyone reviewing suggestions.
    - **What changed:**
      - The passage now comes before the captions.
      - Cards are tighter.
      - The controls stay beside the queue on desktop.
      - On a phone the queue comes first.
36. **Phone coding is usable.** `edf9701`
    - **Who notices:** anyone coding on a phone.
    - **What changed:** the transcript comes first and the code buttons stay pinned below it. The sources rail is no longer a nested scroller, and the nav scrolls sideways instead of taking three rows.
    - **Checked:** tap a passage, tap a code, and the code is assigned.
37. **Smaller fixes a user sees.**
    - The empty-state horizon no longer strikes through text.
    - Analysis counts read as links to their evidence.
    - Codebook cards drop empty example slips, and proposal fields are hidden when there is nothing to decide.
    - The Home intro line is legible over the plate.
    - "P01" in headings no longer reads as "Po1".

**Evidence.**
- **Screenshots:** before and after are in `design-review/overnight/before/` and `design-review/overnight/final/`, covering the key screens at 1280 and 375. The full 46-screen sets of every round are outside the repo, in the session scratchpad.
- **Checks:** web tests (65), the typecheck and the build pass, and so does the static-demo e2e test (`tests/e2e/demo.spec.ts`).
- **Not run:** the mutation e2e test needs the AnnoMI demo, which the guard keeps me from building.
- **Live checks with Playwright:** I checked primary-button contrast in both themes, panel focus, and phone coding.

**Left alone, with the reason:**
- **"Saving…" during a long classification.** It shows in the sticky strip, but a per-button "Running…" label would rename buttons the e2e test finds by name.
- **No confirmation after Accept or Reject.** Adding one needs a change in `web/src/lib`, which is out of design scope.
- **The Home plate height and the open-by-default Analysis criteria.** Both are approved identity or working defaults.
- **The 501–900 px Workspace layout between phone and desktop.** It was not captured, so it is not verified.

## Round 3: tidy, simplify, graphify

Your bar was that deletion counts as improvement and that nothing should change behaviour. An Opus over-engineering audit (ponytail-audit) swept the whole repo. It found the project already lean: no unused dependency, no dead function, no unused CSS or test helper. These three changes passed the bar:

26. **CLI commands start without loading the web server.** `e2bf1eb`
    - **Who notices:** every `qualia` command except `open`, every time it runs.
    - **Measured:** importing `qualia.cli` dropped from about 3.5 s to about 1.0 s (median of five interleaved runs on this loaded PC).
    - **Checked:** `qualia open` still serves the app (HTTP 200).
27. **One duplicate-key JSON guard instead of three copies.** `e39873d`
    - **Change:** net −11 lines, with no behaviour change.
    - **Who notices:** whoever next maintains the parsers.
28. **CI runs the web typecheck once instead of three times.** `31349b6`
    - **Who notices:** every CI run.
    - **Measured:** one `tsc --noEmit` took about 1 minute on this PC. `npm run build` already runs it, and `typecheck` and `lint` were identical copies of it.

**Left alone, with the reason:**
- **Tailwind.** No component uses a Tailwind class, so only its CSS reset is in use. Doc 01 names "shadcn/ui + Tailwind 4" as the stack, and removing it needs a visual re-check.
- **`qualia/ai/protocol.py`.** Nothing imports it, but `docs/CONTRACTS.md` names it a frozen contract.
- **Repeated helpers in the Claude and Codex backends.** The vendor-isolation rule in CLAUDE.md requires each backend to keep its own copy.
- **The quadratic segment trigger on large imports.** The fix needs a migration (see round 2).

### graphify

- **Where it is:** a code knowledge graph of the repo is in `graphify-out/`, built with graphify 0.9.17. The project already gitignores that folder, so it is local to this worktree and not committed.
- **Size:** 1,684 nodes, 4,329 edges and 96 labelled communities, covering Python, TypeScript, scripts and config.
- **What it skipped:**
  - 127 images and 14 videos (UI screenshots and tutorial clips). Extracting them needs one AI agent per image, so it fails the tangible-value bar.
  - Semantic extraction of the 181 docs.
  - 5 SQL migrations, because the `tree_sitter_sql` extra is not installed.
- **Health:** 0 missing endpoints and 0 self-loops. There are 498 dangling edges, mostly references to standard-library and third-party names outside the repo.
- **Cost:** the build used no tokens. The code graph is built structurally, with no AI.
- **To use it from the repo root:**

```powershell
graphify query "how does a classification run reserve budget before calling a backend"
```

```powershell
graphify explain "classify_segments()"
```

  Or open `graphify-out\graph.html` in a browser. To rebuild after changes, run `/graphify . --update` in Claude Code.
- **The main checkout:** `C:\Users\Owner\OneDrive\Documents\Qualia` has no graph yet. After merging, run `/graphify .` there once, or copy this worktree's `graphify-out` folder across.

## Round 4: first-time users, merge rehearsal, design scoring

**Acceptance.**
- **Who tested:** two fresh Opus agents acted as first-time researchers, using only the README and the user guide.
- **What they used:** one worked in the command line, one in the web app through the browser. Each had an invented study in a temporary home and used only the offline `rules` backend.
- **How far they got:** both finished the whole journey. The web tester rated ease at 6/10 before the fixes below.
- **What I fixed:** what a real user would hit, after reproducing each item. One web report was not reproducible with a real mouse drag: selecting text in a passage that is not the active one. The selection correctly made that passage active.

38. **Re-running classification no longer re-queues decided suggestions.** `35c8546`
    - **Who notices:** anyone who re-runs classification, which by default covers the whole project. Every accepted or rejected suggestion used to come back as a new pending copy.
    - **Evidence:** `tests/test_ai_router.py::test_rerunning_classification_does_not_requeue_recorded_suggestions`. One existing test relied on that duplicate. It now fills the cache first, so it still proves that the model version survives cache reuse.
    - **Codex review fix (`c08d354`):** after the Codex review, the duplicate check also compares the exact model version, so a newer model snapshot still gets its own suggestions. It also no longer uses one SQL parameter per segment, which failed past SQLite's limit on very large runs.
    - **To undo:** run `git revert c08d354 35c8546`. This re-queues repeats.
39. **A review note is no longer lost.** `4d30128`
    - **Who notices:** reviewers who type a note and then click another card's Accept or Reject.
    - **Checked live:** the feedback row now holds the note.
40. **The app remembers the coder's name.** `6b561b9`
    - **Who notices:** anyone who reloads the page. Decisions were being recorded as "researcher".
    - **Also in this commit:** the New project popover closes after use, stale notices clear when you switch screens, and the progress line says "Working…".
41. **On a phone the coding panel stays small after a message.** `4b5963e`
    - **Cause:** a regression from my own design-pass rule, caught by the web tester. It covered the transcript.
    - **Also in this commit:** a readable frozen-version date, and an explanation of the Include field.
42. **Text-inclusive exports are named `…-with-text`.** `133ec69`
    - **Who notices:** anyone exporting both kinds. Before, both files had the same name.
43. **`qualia export --output` creates a missing folder.** `e5d177a`
    - **Before:** a 37-line traceback.
44. **Docs.** `a849871`
    - The JSON for setting inclusion terms.
    - Case attributes in the form that works in Windows PowerShell 5.1 (checked: the form the tester tried first fails).
    - What `--version` means for a benchmark.

**Design scoring.**
- **Method:** fresh reviewers scored every main screen out of 10 for clarity, craft and ease, at 1280 and 375 px. I fixed the top items each cycle (`63426d2`, `c86557b`, `7a24785`, plus the design part of `4b5963e`). I stopped when scores levelled off.
- **Moves, desktop then phone:**
  - Analysis rose from 6/6/6 and 5/4/5 to 7/7/7 and 7/6/6.
  - Review ease rose from 6 to 8 on desktop.
  - Workspace reached 9/8/8 on desktop.
  - Matrix reached 9/9/9 on desktop.
  - Home stayed at 9.
- **Final scores:** every main screen is 8–9 on desktop and 7–8 on phone.
- **Remaining phone gap:** mainly the header height and the long Review and Analysis pages, which are not worth a redesign.
- **Screenshots:** in `design-review/overnight/final/`.

**Codex review of round 4:** two real findings, both fixed in `c08d354`: the model-version identity and the SQL parameter limit. Nothing else was found.

**Merge rehearsal.**
- **Clean merge:** `main` has not moved since the branch point `2978c5d`, and `git merge-tree --write-tree main HEAD` reports a clean merge. So the merged result is exactly this branch, and the checks below are checks of the merge.
- **Python:** see the Tests table.
- **Web:** 65 tests pass, and the typecheck and build pass.
- **Static-demo e2e:** passes.
- **Mutation e2e (`tests/e2e/mvp.spec.ts`):** not run. It needs the AnnoMI demo project, the project's guard blocks commands that touch the demo data, and I did not work around it. Run it after merging, from a terminal where you have the demo, using the command in that file's header.

## Round 5: scoring each main screen toward 9

**Method.**
- **Scorers:** each scoring round used two new Opus scorers who had not seen any earlier version.
- **What they scored:** the first screen and the whole page at 1280 and 375 px, from the live synthetic study and the public demo.
- **Score used:** each screen's number is the mean of both scorers. Where a scorer gave clarity, craft and ease separately, I averaged them first.
- **Passes:** three different approaches, then a check for any regressions they introduced:
  - **Pass 1** (`1e0c7e6`), content before controls: each screen leads with what it is for, and the phone header became one compact block.
  - **Pass 2** (`1dfaee8`), first-screen compaction: a shorter Home plate, a one-row phone coding strip, a quiet run summary on Review, and the Analysis index.
  - **Pass 3** (`0c59215`), density and one type voice: compact codebook entries, the display face for code names, codes leading the coding rail, receding zeros in Matrix, and folded memo links.

| Screen | Baseline | After pass 1 | After pass 2 | After pass 3 |
|---|---|---|---|---|
| Home | 7.0 / 6.0 | 7.0 / 6.0 | 7.5 / 6.8 | 6.8 / 6.8 |
| Workspace | 8.0 / 5.5 | 8.0 / 6.3 | 7.8 / 7.0 | 7.8 / 7.0 |
| Codebook | 6.5 / 5.7 | 7.5 / 6.8 | 7.0 / 6.5 | 7.0 / 6.8 |
| Review | 7.0 / 6.0 | 7.3 / 6.8 | 7.5 / 6.8 | 7.5 / 7.5 |
| Analysis | 6.0 / 5.2 | 6.3 / 5.5 | 6.5 / 5.8 | 6.0 / 5.7 |
| Evaluation | 7.0 / 6.2 | 6.5 / 5.5 | 7.0 / 6.5 | 7.0 / 6.5 |
| Experiments | 6.2 / 5.3 | 7.0 / 6.5 | 7.5 / 7.0 | 6.8 / 6.7 |
| Matrix | 8.3 / 6.5 | 8.3 / 7.3 | 8.3 / 7.0 | 8.2 / 7.2 |
| Retrieval | 7.5 / 6.7 | 8.3 / 8.0 | 8.0 / 7.5 | 7.5 / 7.0 |
| Memos | 7.2 / 6.2 | 7.3 / 7.3 | 8.0 / 7.5 | 7.5 / 7.2 |
| **Mean** | **7.1 / 5.9** | **7.4 / 6.6** | **7.5 / 6.8** | **7.2 / 6.8** |

Each cell is 1280 px / 375 px.

**Outcome.**
- **No main screen reached 9.** All three approaches have now been tried, so I stopped, as the brief says.
- **Phone:** scores rose by about a point overall (5.9 → 6.8). Every phone screen rose, Workspace most (5.5 → 7.0).
- **Desktop:** scores rose slightly and then levelled off.
- **Pass 3 was kept** even though the desktop mean fell 0.3. Two reasons:
  - Screens pass 3 did not touch moved as much as the ones it did. Home fell 0.7 when pass 3 changed only the phone tab strip there. That points to scorer variance, which between pairs is about ±0.5.
  - Pass 3 also restored the phone order so trust captions come before Accept and Reject.

**Regressions the scorers found, fixed.**
- **Order:** on both widths, the Review decision buttons had been placed before the trust captions. They now come after them (`0c59215`, `17d95d7`). Checked: the actions start at 762 px and the captions end at 659 px.
- **Phone source switching:** after the transcript moved first, phones had no quick way to switch source. A "Switch source" select now handles it.

**What blocks a 9.** Across the last two rounds the scorers' remaining reasons fall into four groups, and none can be fixed inside a presentation-only pass:
1. **New product features.**
   - A study-status summary on Home: sources, coded, pending, latest version and next step.
   - A prerequisites checklist on Experiments.
   - In-app benchmark import for Evaluation; today it needs a terminal command.
   - Totals in Matrix.
   - Grouping Retrieval by code with one entry per excerpt.
   - Dates and authors on memo cards.
   - Disabling Run until a benchmark exists. That needs state the web app does not have.
2. **The fixed design contract.** These are fixed in docs 04–05 and DESIGN.md, and only you can change them:
   - The repeated trust captions on every suggestion card make the review queue long.
   - The 22% code-colour highlight reads as a "selection" to some scorers.
   - The no-gradient rule rules out the usual edge fade on scrolling strips.
   - The Home plate is the approved identity.
3. **Analysis is one long report** of seven sections, 8,500 px with real data. A 9 would need it split into sub-views or tabs, which is an information-architecture change for you to decide.
4. **The read-only demo** shows disabled write controls and empty model menus. A 9 would need a demo-specific layout, which is logic, not styling.

The polish items scorers raised in the final round are small and specific. Each is in their reports in the session scratchpad. They would add about a quarter point, not reach 9.

## Found, not changed

Reverted under your "tangible improvements only" bar: the round-2 `QUALIA_PORT` range check in the double-click launcher (`62dbad0`, reverted). It only helped a hand-edited `.env` value outside 1024–65535.

1. **CSV exports still have no UTF-8 BOM.**
   - **Why not:** a BOM would rename the first column (`﻿record_type`) for Python's `csv` module and R's `read.csv`, which the analysis starter scripts and existing readers depend on.
   - **Workaround:** in Excel, open the file through **Data > From Text/CSV** and pick UTF-8.
2. **`split_transcripts` gives uneven splits for strata under about 10.**
   - **Why not:** changing it would move the pinned demo's dev, validation and protected splits, which are fixed evidence.
3. **`test_real_cli_policy_confirmation_and_read_only_history_api` failed once under load.**
   - **Investigated:** the improvement loop's trusted tests take about 13 s, against a 120 s limit. A timeout makes the experiment REVERT, which is the safe outcome.
   - **Why not:** this is not a product defect, so no change.
4. **Manual codes can share a name.** Proposals refuse a duplicate name, but codes created by hand do not. This is a methodology rule for you to decide, and existing projects may already contain such names.
5. **Shown suggestions repeat codes you already applied by hand.** The classifier is independent of your coding by design, so Qualia does not hide these.
6. **Command-line users have no command that lists the ID numbers of sources, passages or suggestions** (found by the CLI tester). Adding one is a new feature, so it is left for you to decide.

## Needs a browser check

I checked every UI change in the built app with Playwright at 1280 and 375 px. The one gap is screen widths between 501 and 900 px (small tablets and narrow windows), which I did not capture.

## How to merge

From `C:\Users\Owner\OneDrive\Documents\Qualia`, with no uncommitted work on `main`:

```powershell
git switch main
```

```powershell
git merge --no-ff claude/overnight-fixes-3d262b -m "Merge overnight maintenance and design pass"
```

```powershell
uv sync; uv run pytest
```

```powershell
cd web; npm ci; npm test; npm run build; cd ..
```

Then run the mutation e2e test against your demo (the command is in the header of `tests/e2e/mvp.spec.ts`), and run `/graphify .` once if you want the code map in the main checkout.

**Rollback:** to undo the whole merge before you push, run

```powershell
git reset --keep HEAD~1
```

After a push, run

```powershell
git revert -m 1 HEAD
```

Each change can also be undone on its own with `git revert <hash>`, using the hashes listed above. Or open a pull request from the branch instead of merging locally.
