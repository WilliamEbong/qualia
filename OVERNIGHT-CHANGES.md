# Overnight maintenance pass: 2026-11-22

Branch `claude/overnight-fixes-3d262b`, based on `main` at `2978c5d`. It has not been pushed or merged, and nothing was released, tagged or version-bumped.

This was a fix-only pass. It added no features, made no redesign and changed no decision you had made. Each fix is a defect we could demonstrate, with a test that failed before the change and passes after it. Opus did the work in this session, three read-only Opus subagents audited the code, and Codex reviewed the branch diff.

## Tests

| | Before | After |
|---|---|---|
| Python (`uv run pytest`) | 682 passed, 5 skipped, 4 failed, 4 errors | 688 passed, 5 skipped, the same 4 failed and 4 errors |
| Web (`npm test`) | 63 passed | 63 passed |
| `tsc --noEmit`, `ruff check` | clean | clean |
| `pip-audit` / `npm audit` | 17 known vulnerabilities in 3 packages / 1 moderate | 0 / 0 |

The 4 failures and 4 errors before the pass all come from one cause on this PC, and this branch leaves them as they were (see "Found, not changed" #1).

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

## Found, not changed

These are listed with evidence and a recommendation. Each one either fell below the confidence bar or needs a decision from you.

1. **Installed Codex CLI 0.170.0 changed its request format, which fails 8 local-only tests on this PC.**
   - **Affected tests:** `test_installed_codex_advertises_no_tools_to_localhost` (4 cases) and the `native_proposal_wire` teardown in `test_codex_operator.py` (4 errors). They run only when Codex is installed, so CI does not run them.
   - **What changed:** a local probe of the real request shows Codex 0.170.0 no longer sends an `additional_tools` input item at all. It also sends no `tools` key, so the safety property (no tools offered) still holds.
   - **Why not changed:** the tests insist the item exists, and fixing them means editing test assertions.
   - **Recommendation:** accept either "no `additional_tools` item" or "every `additional_tools` item is empty", and keep the `not body.get('tools')` check.
2. **Text-inclusive workspace CSV exports add an apostrophe to any value that starts with `= + - @`** (`qualia/io/exporters.py` `_csv_cell`).
   - **Effect:** this guards against spreadsheet formula injection, but the change can't be undone. Unlike the analysis export, there is no escape-flag column. A transcript that starts with "- I waited…" exports with a leading `'`, so its segment offsets no longer match.
   - **Recommendation:** add an `_escaped` flag column as the analysis export does. This changes the export format, so it is your call.
3. **A transient Jev failure that is retried counts its segments twice against `run_segments`** (`qualia/ai/router.py` retry loop → `reserve_attempt`).
   - **Effect:** with `run_segments` equal to the run size and `max_retries=1`, one transient error ends the run with "budget reached".
   - **Why not changed:** spec 003 FR-005 enforces limits "before each attempted backend call, including retries", so counting re-sent segments is one valid reading.
   - **Recommendation:** decide whether `run_segments` means distinct segments or segments sent.
4. **Escalation re-sends every segment where the model found no code** (`router.py:280`, `min(..., default=0.0)`).
   - **Effect:** with `escalate_below` set, "no code" counts as uncertain, so most of a typical corpus goes to the strong tier.
   - **Recommendation:** decide whether an empty answer should escalate. If not, change the default to `1.0`.
5. **The offline `rules` backend uses up `daily_calls`.**
   - **Effect:** 301 rules runs block the 302nd. The guide's suggested first-trial `daily_calls: 10` would then block offline work too.
   - **Why not changed:** the spec applies the daily-call limit to every backend call.
   - **Recommendation:** exempt backends with `external=False` from `daily_calls` if you agree.
6. **`tune_thresholds` can replace a better current threshold with a worse grid value** (`qualia/eval/metrics.py`).
   - **Effect:** in one example, current 0.73 gives dev F1 1.0, and the tuner picks 0.5 with F1 0.667.
   - **Why not changed:** it matches the specs/011 plan (`{**current, **tuned}`), and validation KEEP/REVERT guards the result.
   - **Recommendation:** compare against the current value and keep the better one.
7. **Some counts read "1 segments" or "1 pending suggestions" in the UI** (Review, Evaluation, Codebook, matrix labels).
   - **Status:** already known from the previous handoff, and a separate task was offered.
   - **Why not changed:** it changes visible copy across components and needs a browser check, and no browser was allowed tonight.
8. **`test_real_cli_policy_confirmation_and_read_only_history_api` failed once and then passed.**
   - **What happened:** it failed during one full run while other overnight sessions were loading the PC; that run took 39 minutes, against the usual 9. It passed on its own (in 7 min 50 s) and in the final full run.
   - **Likely cause:** the improvement loop's internal test subprocess has a 120-second timeout (`qualia/improve/experiment.py` `_run_tests`).
   - **Why not changed:** the cause was not proven.
9. **Suspicions with no demonstration:**
   - CSV exports have no UTF-8 BOM, so Excel may garble accented text.
   - `launcher.py` does not range-check `QUALIA_PORT`.
   - Jev retries have no backoff.
   - One oversized Jev segment stops a whole run with "cost estimate unavailable".
   - `workspace.ts` caps example quotes at 500 UTF-16 units, not code points.
   - `split_transcripts` gives uneven splits for strata under about 10. The pinned demo is unaffected, and changing this would move its splits.

## Needs a browser check

None of the changes above alter the UI. The only one you could see there is #4: a request with an impossible ID now shows a 400 message rather than a server error. No browser was used tonight.

## How to merge

```powershell
git switch main
git merge --no-ff claude/overnight-fixes-3d262b
uv sync
uv run pytest
```

```powershell
cd web; npm ci; npm test
```

Or open a pull request from the branch. Each commit can be reverted on its own with `git revert <hash>`.
