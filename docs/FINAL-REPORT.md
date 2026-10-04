# Qualia implementation and handoff

Verified 2026-10-03, America/Denver. The local research application, analytics, presentation and user documentation are implemented and verified. **The overall build remains in progress:** native Claude/Codex activation and the official external security scan have unresolved requirements. Jev's live test needs your key. No public release or latest private-main push is claimed.

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
| Qualitative research | TXT/Markdown/mapped CSV import; immutable source revisions; cases and attributes; versioned/frozen codebooks; full-segment and overlapping-span coding; keyboard shortcuts; memos, retrieval and case-code matrix |
| Traceability | Append-only coding/review events with source spans, historical codebook identity, actor, backend/model and pipeline information; text-optional reproducibility bundles |
| Analysis and visualization | Filtered coding frequencies, case-group comparisons, co-occurrence/overlap/Jaccard, word counts, explicit numeric summaries, paired Pearson relationships and scatter plots; exact tables and contributing evidence links |
| Data science handoff | Case CSV, JSON metadata/provenance, SVG charts, and matching standard-library Python/base-R starters; no arbitrary script execution inside Qualia |
| Offline AI workflow | Rules and deterministic fake suggestions; accept/reject review; honest model-reported scores and matching-validation calibration evidence |
| Evaluation / experiments | Fixed benchmark metrics, protected split separation, validation-driven KEEP/REVERT, confirming evaluation, restricted fake operator and recovery records |
| Optional providers | Native adapters installed but disabled; Jev adapter, local enable/check/disable controls and detailed setup guide installed |
| Presentation | Archive of Looking tokens/type/artwork, dark theme, accessible focus, responsive views, final screenshots, GIF and social image |

This is not complete NVivo parity. Audio/video coding, live multi-user collaboration, proprietary NVivo project import and advanced inference/model fitting remain outside this implementation. Descriptive statistics and reproducible exports support continued work in Python or R.

## How subscription AI is intended to work

You use **Qualia's interface**. A classification action would call the local server, which invokes your installed official Codex or Claude CLI. That CLI uses its own existing sign-in and returns structured results. Qualia validates them and presents reviewable suggestions. You do not need an AI desktop application open, and Qualia does not request or proxy subscription tokens.

**The Codex CLI itself was tested successfully.** Installed Codex0.160.0 returned valid synthetic classification twice with gpt-6-luna, including the restricted configuration; a separate gpt-6-astra delegation probe also passed. See [exact preflight evidence](research/preflight-ai.md). Claude's initial live probe returned an authenticated quota limit. These results do not establish the complete Qualia native workflow: both production native paths remain unavailable pending the specific requirements below. The [current official documentation assessment](research/subscription-policy.md) distinguishes supported personal CLI use from account-sharing or service-hosting approval.

## Verification evidence

| Check | Result and scope |
|---|---|
| Python full offline suite |390 passed,5 skipped (four Windows capabilities, absent Rscript),4 live tests deselected;158.23s at final functional checkpoint |
| Frontend |30 tests pass; TypeScript and normal/static production builds pass |
| Analysis |Synthetic six-case fixture independently matched counts, mean37.4 and paired Pearson0.93715; stale export hash returns409; matching Python starter executed successfully |
| Browser |Actual import/coding/review/evaluation/fake KEEP/export workflow; five synchronized keyboard assignments; chart/evidence links and downloads; final desktop/mobile screenshots |
| Static demonstration |Ten views at375px/1280px, no page overflow, zero API requests;24 approved AnnoMI utterances; root and repository-base builds validated |
| Performance |Lighthouse13.5:96 performance,100 accessibility,CLS0.0001251722;[audit and repair evidence](../design-review/LOOP-REPORT.md) |
| Design boundary |295c712→fe7b8e8 protected functional diff empty;199 functional attributes unchanged; no new runtime dependencies |
| Hygiene |Gitleaks0 findings in checked current tree/history; npm0 vulnerabilities across249 dependencies; pip-audit0 across31 production dependencies; no tracked research storage |
| Remote CI |Last pushed8029a36 passed; newer local commits have local evidence and have not run remote CI |
| External security review |Authorized bounded scan stopped before model analysis because of Windows credential-home ancestor permissions; no completed scan or clean-security verdict claimed |

The GIF is a visual tour assembled from actual screenshots, not an interaction recording. The fake experiment demonstrates measured policy behavior, not trained-model quality: macro F1 improved0.01058468→0.24242447 while exact match fell. R code was reviewed but not executed because Rscript is unavailable. Browser hero-preload warnings on non-home routes are documented in the design report.

## Remaining actions that need you

### 1. Jev key and credits

Follow [Jev setup](JEV-SETUP.md): check your TypeSafe balance, create a dedicated key and save it only in this repository's ignored `.env` as `TYPESAFE_API_KEY`. Keep automatic refills off unless deliberately chosen. Then run the guide's zero-network readiness check and tiny synthetic live test. You can instead tell the agent, “The Jev key is saved in .env; run the synthetic live check.” Never paste the key into chat. No live Jev call or billing change was made during this build.

### 2. Decide the native CLI requirements

The original runbook requires controls the installed CLI versions cannot provide exactly. These are concrete choices, not another login request:

1. Authorize native Windows sandbox setup. It creates persistent account/ACL/firewall configuration and needs Administrator/UAC execution. The proposed command is `codex sandbox setup --elevated --current-user`. After authorization, setup and synthetic denied-read/allowed-write checks must pass before activation.
2. Authorize a tested custom native operator permission profile in place of the runbook's workspace-write flag. Database, vault, secrets, recovery files and protected methodology must remain inaccessible; no fallback exposing research paths is acceptable.
3. Choose whether Codex may use finite deadlines, input/output byte limits, schema limits and batch/call budgets despite lacking a provider generation-token cap. These controls do not provide an exact generation or billing cap. Otherwise Codex remains off until that capability exists.
4. Choose whether native CLIs may use conservative per-process/turn-budget accounting. Codex can retry authentication internally; Claude can issue multiple model requests in one invocation. Neither supplies a synchronous pre-request admission hook for every internal request. This differs from the original exact per-HTTP ledger rule; direct Jev remains accountable per request.

These approvals would permit further implementation/testing, not immediate blanket activation. Leave native paths disabled if you want the original stricter requirements unchanged. The optional private live Claude diagnostic also needs explicit authorization before it can use subscription quota; it has not run.

### 3. Private repository checkpoint

Authorize pushing the verified local commits to the existing **private main** branch if you want remote backup and fresh CI. This does not make the repository public. Public release is a separate owner action; the Pages workflow remains gated.

### 4. Official security scanner environment

The authorized scanner rejects a Windows credential-home ancestor because its validator finds an applicable replacement/Modify permission at `C:\`. The `.codex` state ancestors pass, but every path on that drive still includes the root. No ACL or credential changes were made. An administrator must review the drive permission policy, or supply an already-private path on another volume whose complete ancestor chain passes. Do not weaken the scanner check or change drive-wide ACLs casually. This finding is a scanner preflight limitation, not evidence of a compromise or an application vulnerability.

**Why work stopped at these actions:** automatic approval review rejected the persistent native sandbox setup, the private-main push and the optional private live Claude diagnostic without explicit authorization for their respective system changes, shared-branch mutation and quota use. The official security scan was authorized, then independently blocked by its own permission validation. All unaffected implementation, design and documentation work continued.

## Checkpoints and cost

Functional baseline295c712 and final presentationfe7b8e8 preserve the implementation/design boundary. The final documentation commit follows them. `docs/BUILD-STATE.md` is the chronological evidence log; `WELCOME-BACK.md` is the concise resume entrypoint. Protected source documents02–05 and the constitution were not edited; only the permitted current-state section10 of doc01 was refreshed.

Offline fake/rules tests recorded no external egress. No Jev usage charge was incurred. Successful early Codex probes used the existing subscription; total session-wide provider quota/cost is not available and is not represented as zero. The security scanner failed before analysis. No public hosting, paid billing change or latest remote push was performed.
