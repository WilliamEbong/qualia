# Qualia implementation and handoff

Updated 2026-10-06. Qualia is public (https://github.com/WilliamEbong/qualia, release v0.1.1, static demo at https://williamebong.github.io/qualia/). Since release it gained codebook proposals (AI drafting and refinement plus an offline evidence check, all decided by a person), one-step create-freeze-assign coding, memo kinds, links and history, a 45% smaller workspace payload, and a minimum-version policy for the Claude Code and Codex CLIs. Native classification and both improvement operators remain verified as described below; Jev is live-verified and enabled for demo with its $1 daily local limit. See BUILD-STATE P20 for the latest evidence.

## Open and use it

The running local application is at [Qualia](http://127.0.0.1:8765/?project=demo). If it is stopped, open PowerShell and run:

```powershell
Set-Location "C:\Users\Owner\OneDrive\Documents\Qualia"
uv run qualia open
```

Use [the illustrated user guide](USER-GUIDE.md) for the complete step-by-step workflows and a small practice study. The default research folder is `%USERPROFILE%\Qualia`, separate from application source. Closing the browser does not stop the server; its terminal's Ctrl+C does. The separate [static preview](http://127.0.0.1:4173/qualia/) is a read-only public-data demonstration available while the preview process is running.

## What is available

| Area | Implemented behavior |
|---|---|
| Qualitative research | TXT/Markdown/mapped CSV import; immutable source revisions; cases and attributes; versioned/frozen codebooks; full-segment and overlapping-span coding; keyboard shortcuts; one-step create-freeze-assign coding; memos with kinds, case/source links and kept history; retrieval and case-code matrix |
| Codebook proposals | AI draft (inductive) and refine proposals via Claude/Codex with verbatim-checked examples, an offline evidence check over your review decisions, and acceptance into the draft codebook only by a named person; proposals and decisions are append-only and exported |
| Traceability | Append-only coding/review events with source spans, historical codebook identity, actor, backend/model and pipeline information; text-optional reproducibility bundles |
| Analysis and visualization | Filtered coding frequencies, case-group comparisons, co-occurrence/overlap/Jaccard, word counts, explicit numeric summaries, paired Pearson relationships and scatter plots; exact tables and contributing evidence links |
| Data science handoff | Case CSV, JSON metadata/provenance, SVG charts, and matching standard-library Python/base-R starters; no arbitrary script execution inside Qualia |
| Offline AI workflow | Rules and deterministic fake suggestions; accept/reject review; honest model-reported scores and matching-validation calibration evidence |
| Evaluation / experiments | Fixed benchmark metrics, protected split separation, validation-driven KEEP/REVERT, confirming evaluation, restricted fake operator and recovery records |
| Optional providers | Native subscription classification with current CLI versions (minimum-version floor, version recorded per run) and explicit project permission; Claude operator verified; Codex no-tools proposal operator live-verified; Jev adapter and setup controls installed |
| Presentation | Archive of Looking tokens/type/artwork, dark theme, accessible focus, responsive views, final screenshots, GIF and social image |

This is not complete NVivo parity. Audio/video coding, live multi-user collaboration, proprietary NVivo project import and advanced inference/model fitting remain outside this implementation. Descriptive statistics and reproducible exports support continued work in Python or R.

## How subscription AI is intended to work

You use **Qualia's interface**. A classification action calls the local server, which invokes your installed official Codex or Claude CLI. That CLI uses its own existing sign-in and returns structured results. Qualia validates them and presents reviewable suggestions. Each user sets up their own device and eligible subscription; no developer account or credentials are distributed. You do not need an AI desktop application open, and Qualia does not request or proxy subscription tokens. Optional Jev uses your separately configured API key.

**The Codex CLI itself was tested successfully.** Installed Codex0.160.0 returned valid synthetic classification twice with gpt-6-luna, including the restricted configuration; a separate gpt-6-astra delegation probe also passed. See [exact preflight evidence](research/preflight-ai.md). Claude's initial probe returned an authenticated quota limit. The subsequent owner decision resolves the two classification usage-policy gates; current public-router verification is recorded in [adapter evidence](research/cli-classification.md) and BUILD-STATE. Codex improvement now uses the separately approved no-tools mechanism; the failed direct file-tool route remains disabled. The [official documentation assessment](research/subscription-policy.md) distinguishes supported personal CLI use from account-sharing or service-hosting approval.

## Verification evidence

| Check | Result and scope |
|---|---|
| Python full offline suite |534 passed,5 skipped (four Windows capabilities, absent Rscript),6 live tests deselected;256.82s after Codex proposal integration |
| Frontend |30 tests pass; TypeScript and normal/static production builds pass |
| Analysis |Synthetic six-case fixture independently matched counts, mean37.4 and paired Pearson0.93715; stale export hash returns409; matching Python starter executed successfully |
| Browser |Actual import/coding/review/evaluation/fake KEEP/export workflow; five synchronized keyboard assignments; chart/evidence links and downloads; final desktop/mobile screenshots |
| Static demonstration |Ten views at375px/1280px, no page overflow, zero API requests;24 approved AnnoMI utterances; root and repository-base builds validated |
| Performance |Lighthouse13.5:96 performance,100 accessibility,CLS0.0001251722;[audit and repair evidence](../design-review/LOOP-REPORT.md) |
| Design boundary |295c712→fe7b8e8 protected functional diff empty;199 functional attributes unchanged; no new runtime dependencies |
| Hygiene |Gitleaks0 findings in checked current tree/history; npm0 vulnerabilities across249 dependencies; pip-audit0 across31 production dependencies; no tracked research storage |
| Remote CI | Private Checks passed at e95972e: [run37184680691](https://github.com/WilliamEbong/qualia/actions/runs/37184680691). This handoff-only follow-up changes no implementation. |
| External security review | Official scanner superseded by owner decision; the owner-run Claude `/security-review` was not performed before publishing and remains recommended. Independent Codex (gpt-6-astra) review of the 2026-10-06 changes is recorded in BUILD-STATE P20. |

Earlier native-classification checkpoint: full offline suite411 passed,5 skipped,4 live deselected; final router/ledger/API31 passed, including a subsequent safe-auth-error regression. Both **Codex gpt-6-luna and Claude haiku passed actual synthetic public-router classification** with one-invocation budgets, egress/usage records, validated output and zero coding events. Claude's512-token test fixture truncated; independent diagnosis increased only that fixture allowance to4096, below the unchanged8192 production ceiling. Earlier failed attempts were recorded and consumed subscription usage. See [live evidence](research/cli-classification.md#approved-policy-live-verification).

The GIF is a visual tour assembled from actual screenshots, not an interaction recording. The fake experiment demonstrates measured policy behavior, not trained-model quality: macro F1 improved0.01058468→0.24242447 while exact match fell. R code was reviewed but not executed because Rscript is unavailable. Browser hero-preload warnings on non-home routes are documented in the design report.

## Remaining actions that need you

### Jev setup completed

After the owner saved the key and authorized activation, two synthetic live requests passed. Their combined recorded cost was $0.00003570. Jev is enabled for demo with the existing $1 daily local limit; new projects remain off by default. Playwright confirmed that Jev is selectable and Run classification is enabled. No study data was sent and no billing settings were changed. Other devices and users can follow [Jev setup](JEV-SETUP.md).

### Codex improvement completed

Owner decision04 approved replacing direct file editing with no-tools proposals. Codex0.160.0 checks its version and native ChatGPT login, receives only a bounded permitted-file snapshot and returns strict JSON. Qualia validates the complete proposal before writing, including original file identity/hashes, exact paths, links, configuration and unchanged privacy/budget bounds. It then performs the existing trusted evaluation and KEEP/REVERT. The failed direct file-tool route stays disabled; no broader permissions or repeat setup is required.

The public synthetic Codex experiment passed in41.92s: Astra proposed one prompt replacement, Luna validation macro-F1/exact-match remained1.0 to1.0 and ECE0 to0; agreement was undefined for the one-record fixture. Qualia correctly recorded REVERT. Three admitted invocations retained usage: Luna baseline9717 input/58 output, Astra10594/172, Luna candidate9753/56. Methodology, frozen codebook and coding state stayed unchanged, and project Git was clean. This verifies integration without claiming a research-quality gain.

Claude improvement is also enabled and live-verified with Opus5.5 and Haiku validation. Its one-record result likewise remained1.0 to1.0 and correctly reverted. Both workflows use the user's existing subscription sign-in; no extra API key or approval for each candidate is needed. See [step-by-step improvement guide](USER-GUIDE.md#15-understand-improvement-experiments).

### Still recommended

Run your planned Claude Code `/security-review` on the public repository. The official scanner is superseded, not passed. No drive-wide ACL, firewall, credential or billing change was made.

## Checkpoints and cost

Functional baseline295c712 and final presentationfe7b8e8 preserve the implementation/design boundary. The final documentation commit follows them. `docs/BUILD-STATE.md` is the chronological evidence log; `WELCOME-BACK.md` is the concise resume entrypoint. Protected source documents02–05 and the constitution were not edited; only the permitted current-state section10 of doc01 was refreshed.

Offline fake/rules tests recorded no external egress. Two synthetic Jev requests recorded a combined cost of $0.00003570; this is local usage accounting, not a verification of the account balance. Successful early Codex probes used the existing subscription; total session-wide provider quota/cost is not available and is not represented as zero. The official security scanner was superseded after its preflight failure. No public hosting or paid billing change was performed. Current private push/CI evidence is in BUILD-STATE.
