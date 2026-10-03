# 02 — Qualia: Build Instructions (autonomous runbook)

*Session model: UNATTENDED, driven by `scripts/run-build.ps1` — it relaunches a fresh Codex session (kickoff once, then
the recovery prompt) until BUILD-STATE's first line is `BUILD COMPLETE` or `OWNER-NEEDED.md` exists. Subagents read,
audit and test inside their file lane; the main session owns commits and contracts. Survives usage cutoffs via
BUILD-STATE. Why → doc 01 · owner steps → doc 03 · design → docs 04–05.*

## 0. Execution contract (Claude Code — read first)

- Read docs/01-qualia-context.md first; it defines the product, invariants, and module map. This
  doc defines only the WORK.
- Run UNATTENDED: never ask the owner anything covered here or in
  docs/03-qualia-owner.md. Ambiguity → the simpler option, logged in README Decisions.
- Invariants in docs/01-qualia-context.md §6 are ABSOLUTE.
- NEVER set temperature/top_p/top_k. max_tokens generous but bounded per config.
- Commit after every sub-step. If usage cuts out: commit, make
  WELCOME-BACK.md truthful, stop. Any later session resumes via the Phase 0 audit.
- Plugins (Superpowers, Ponytail, taste-skill, caveman, Spec Kit skills) may be active. Their guidance is welcome, but THIS DOC and
  CLAUDE.md outrank them. Minimalism applies to implementation, NEVER to deleting
  doc-mandated features.
- Live files win. If this doc and the actual repo/contract contradict each other, STOP
  and surface it — never silently pick a side.
- Batch the gates: bundle every pending question into ONE message to the owner.

**Executor note:** binds whichever harness runs it — Codex CLI (V1) or Claude Code (later); for Codex, "CLAUDE.md"
means AGENTS.md (same content). "Plan mode" = write the plan into BUILD-STATE and proceed. "ONE message to the owner" =
`OWNER-NEEDED.md` at the repo root (the runner pushes it to the owner's phone). "STOP" = record it there, continue
unaffected work, end the session only when none remains.

## Standing rules (every phase)
```
Resumability (usage-limit survival — expected, not an emergency):
- The repo carries docs/BUILD-STATE.md: every phase's sub-steps pre-listed as
  checkboxes. At the START of a sub-step mark it [~] and commit; at completion mark [x]
  and commit with the work. A killed session must never strand more than a few minutes
  of work.
- WELCOME-BACK.md is rewritten truthful at every stop: what shipped, what's mid-flight,
  the exact resume command.
- A fresh session recovers by reading BUILD-STATE.md + git log (recovery prompt:
  doc 3 §5). Never leave the tree dirty at a gate.
```
```
Security defaults:
- Secrets live ONLY in gitignored .env files the owner fills by hand. NEVER ask for a
  key in chat, NEVER echo one, NEVER commit one. When a key is needed, create the env
  file with placeholders, tell the owner which doc-3 section to follow, and pause.
- Key separation is absolute: TYPESAFE_API_KEY (server-side only; read solely by qualia/ai/backends/jev.py) vs
  nothing public (the SPA holds no keys; the per-launch server token lives in memory only).
- Source-of-truth directories (docs/02–05, docs/01 except §10, qualia_project_spec.docx, .specify/memory/constitution.md after Phase 0, demo/data/) are READ-ONLY to this build.
- Anything destructive (drops, deletes, --prune, force-push) is an explicit HARD STOP.
- Structured error logging that can never print env values.
```
```
When blocked, climb this ladder — never thrash, never improvise a workaround the docs
didn't authorize, and never idle while in-contract work remains:
1. Re-read the relevant doc section and CLAUDE.md.
2. Retry once.
3. Run the autonomous repair loop (B12): diagnose → smallest in-contract fix →
   re-verify. Most issues die here.
4. If a pre-authorized simpler alternative is named for this item, take it and log it.
5. Sacrificial item → defer: record in BUILD-STATE with the reason, move on.
6. Load-bearing item → add it to the phase-gate batch (ONE message) and continue with
   unaffected work. Stop the session only when no in-contract work remains.
```
```
Blocked ≠ stalled. ANY failure — blocked action, failing test, red CI, failed
acceptance item, runtime error, failing gate script — enters this loop before any
escalation:
1. CAPTURE — the exact failing command/output/hook message → BUILD-STATE repair log.
2. DIAGNOSE — spin up the `diagnostician` subagent (read-only) with the evidence; it
   returns root cause + smallest in-contract fix + files + the proving command.
3. FIX — the lane owner applies the smallest fix consistent with ALL contracts and
   invariants. FORBIDDEN as fixes: weakening or deleting the failing test/check,
   editing .claude/hooks/* or settings.json, touching sacred paths, breaching any
   doc-1 invariant, silencing errors. Repair fixes causes, never detectors.
4. VERIFY — re-run the EXACT failing check (via the `verifier` subagent where one is
   defined for the gate).
5. BUDGET — max 3 cycles per issue; max 10 cycles per session (usage limits are real money). Every cycle logged, never silent.
Exit: fixed → continue (log only, no owner ping). Budget exhausted →
   sacrificial: defer with reason and continue;
   load-bearing, or any fix requiring a contract change: add to the phase-gate batch
   (ONE message) and continue with unaffected work.
Phase gates therefore receive a REPAIR LOG (what self-healed) plus the unresolved
batch — never a raw pile of failures waiting for the owner.
```
- **Also forbidden as fixes:** editing `.codex/rules/*`, `.codex/agents/*`, `scripts/run-build.ps1`, `scripts/prompts/*`.
- **Owner answers:** `OWNER-ANSWERS.md` present at session start → apply it, log it in BUILD-STATE, move it to
  `docs/answers/NN.md`.
- **Tests before merge:** every code phase lands with tests green in-session and CI green on push (`gh run list
  --limit 1`). Live-AI tests carry the `live` marker and stay out of CI.
- **Model discipline:** GPT-6 Astra, reasoning high, for every main session (schema, provenance, evaluation and the loop
  are judgment work); subagent lanes may run medium for scaffolding and styling.
- **Spec Kit per feature phase** (lean; Codex `$speckit-*`, Claude `/speckit-*`): (1) `$speckit-specify Feature
  directory: specs/<NNN-slug from §5>. <the phase's workstreams + acceptance items, verbatim>. Do not ask questions; use
  informed defaults; record assumptions in spec.md.` (2) `.specify/feature.json` must name that directory — write it if
  not. (3) `$speckit-plan` → `$speckit-tasks`. (4) `$speckit-analyze`: fix CRITICAL findings; ignore its closing
  question. (5) `$speckit-implement`; failure → B12 → re-run. (6) `$speckit-converge` → implement → converge until
  "Converged" or 3 rounds; leftovers → BUILD-STATE. NEVER run `$speckit-clarify`, `$speckit-checklist`,
  `$speckit-taskstoissues`, `specify workflow run`, `specify extension add git`, `specify integration upgrade`. Docs
  01–02 decide WHAT, Spec Kit decides HOW; on conflict, correct spec.md.
- **Library APIs:** context7 before coding against FastAPI, Typer, TanStack Table v9, Recogito, shadcn,
  openapi-typescript. Every UI change is verified with the playwright MCP (screenshot into BUILD-STATE).

Kickoff prompt (byte-identical in doc 03 §6 and `scripts/prompts/kickoff.md`):
```
Read C:\Users\Owner\OneDrive\Documents\Qualia\docs\01-qualia-context.md then C:\Users\Owner\OneDrive\Documents\Qualia\docs\02-qualia-build.md in full. Begin with the
preflight & assumption audit: verify tooling and .env, diff repo state against the doc,
classify each workstream, write/refresh CLAUDE.md, then present an adjusted plan
following the doc's phases, subagents, and acceptance pass. Honor all invariants in
docs/01-qualia-context.md §6; never set temperature/top_p/top_k; keep max_tokens bounded. Flag any
preflight failure with the exact fix and continue where safe.
```

## 1. Phase 0 — Preflight & assumption audit
```
Phase 0 — PREFLIGHT & ASSUMPTION AUDIT (always first)
1. Tooling audit — verify and PRINT A TABLE of required tools and versions
   (git, gh + auth, uv, Python 3.14, node, npm, codex — model list must include gpt-6-astra, claude + auth status, Windows PowerShell 5.1); record actual versions in BUILD-STATE. Run `claude mcp list` and
   classify the owner's toolbelt (playwright/context7/firecrawl at user scope) as
   present or absent — present means later phases USE it for UI verification and
   docs lookups; absent means the named fallbacks apply. NEVER install, re-add, or
   shadow belt servers at project scope, and never edit the user-level CLAUDE.md
   outside its toolbelt markers. Any failure → print the
   exact fix command; stop only if it blocks the current phase.
2. Env & connectivity audit — schema dry-run of .env; DB connectivity + applied
   migrations; 1-token ping on configured models (validate every tier ID); service pings.
3. Repo-vs-docs diff — inspect git log, files, WELCOME-BACK.md. Classify EVERY
   workstream: not-started | partial | done | done-differently. Done-differently that
   satisfies the intent → KEEP it and record it; do NOT redo work to match the letter
   of this doc.
4. Create/refresh the `.claude` project kit: CLAUDE.md in repo root (B8) plus
   settings.json, guard hook + config, and verifier agent (B11); schedule the
   guard-block probe as the first item of the next phase (hooks load at session start).
5. Write the adjusted plan (plan mode) mapping remaining work to phases.
Workaround rules (apply, don't relitigate): the "Pre-authorized adaptations" list below.
STOP-for-owner conditions: the "STOP-for-owner" list below.
```
**Phase 0 specifics.** Toolbelt check also covers `~/.codex/config.toml` `[mcp_servers.*]`. `.env` absent is normal.
Ping = one `claude -p` and one `codex exec` JSON classification with §2's tools-off flags; record latency and the
smallest model each CLI lists. Kit (step 4) also: AGENTS.md (same content as CLAUDE.md, keep the Spec Kit note, under
8 KiB) · `.codex/rules/qualia.rules` forbidding git push -f/--force, git reset --hard, git clean, git branch -D, rm -rf,
gh repo edit, gh repo delete · `.codex/agents/verifier.toml` + `diagnostician.toml` mirroring B11 (fetch the TOML shape
from the Codex subagents docs first) · guard alwaysProtected = the read-only list above; designProtected = doc 01 §4's
design-never-touches list. Step 5 also: `$speckit-constitution` from doc 01 §6 + §4
boundaries; BUILD-STATE with every §5 phase as checkboxes (Phase 7 = doc 05's phases); `gh repo create qualia
--private --source . --push`; probe whether subagents work inside `codex exec` (record yes/no).
**Pre-authorized adaptations:** name `qualia` taken → `qualia-research` · no git identity → repo-local user.name = gh
login, email = its GitHub noreply · no subagents in exec → lanes run sequentially · Recogito cannot reload saved spans →
CSS Custom Highlight API · a Spec Kit script fails under PowerShell 5.1 → do that step by hand · AnnoMI pin unreachable
→ Zenodo 15698094 · gitleaks-action wants a license key → run the gitleaks release binary · pinned version missing →
nearest release, logged.
**STOP-for-owner:** codex lacks gpt-6-astra · claude or codex logged out · gh unauthenticated · repo contradicts doc 01 §6.

## 2. Locked decisions
| Area | Decision |
|---|---|
| Session model | Unattended + runner. T1 says phase-per-session (off-menu stack); the owner's settled autonomy wins; fresh session per relaunch + stuck ladder + phone alert cover the risk. |
| Resumability | docs/BUILD-STATE.md + WELCOME-BACK.md; commit per sub-step. |
| Stack (T10 deviation, doc 01 §1/§12) | Python 3.14 (uv) · FastAPI + uvicorn `--host 127.0.0.1` · Typer · pydantic · sqlite3 (WAL, busy_timeout 5000, numbered SQL migrations, `PRAGMA user_version`, file backup before migrate) · scikit-learn · React 19 + Vite + typescript ~5.9.3 · Tailwind 4 + shadcn/ui + lucide-react · Fontsource (Cormorant Garamond, Libre Franklin variable, IBM Plex Mono) · TanStack Table v9 · Recogito text annotator · openapi-typescript from exported `openapi.json` · pytest, Vitest, @playwright/test. |
| Rendering | Request-time local; FastAPI serves `web/dist`. Demo = same SPA built with `VITE_DEMO=1` reading `demo/snapshot.json`. |
| Claude backend | `claude -p --output-format json --json-schema <schema> --model <cfg> --max-turns 2 --no-session-persistence --tools "" --disallowedTools "mcp__*" --strict-mcp-config --setting-sources ""`, prompt on stdin, cwd = fresh temp dir. NEVER `--bare` (drops subscription login). |
| Codex backend | `codex exec -s read-only --disable shell_tool -c web_search="disabled" --ephemeral --skip-git-repo-check --output-schema <f> -o <f> -m <cfg> -c model_reasoning_effort="low" -`, cwd = fresh temp dir. |
| Operator runs | `run_operator()` in the same files: Claude `-p` with Read/Edit/Write only; Codex `exec -s workspace-write`; cwd = project workspace; prompt = its IMPROVEMENT.md (spec Appendix B). |
| Bounds | `config/routing.yaml`: segments_per_call 20 · max_segment_chars 4000 · daily_calls 300 · run_segments 2000 · jev_daily_usd 1.00 · human_review_below 0.70 · qc_sample_rate 0.05. |
| Cost stack (T4) | `ledger.py` sole writer; `check_budget()` before every call; cache key = segment hash + prompt hash + codebook version + backend + model; cheapest tier default, strong tier on escalation; extra usage OFF (doc 03 §0). |
| Confidence | Shown as "model-reported" with validation ECE beside it. |
| Experiment policy | Protected `improvement.yaml`: primary validation macro-F1, min_delta 0.01, priority-code tolerance 0.02, challenge regressions 0, tests pass, calls ≤ 1.2× baseline. Candidate KEEP needs one confirming re-run. KEEP = commit + tag `exp-NNNN-<slug>`; REVERT = `git restore` + `git clean` limited to mutable paths, run by Qualia code. |
| Protected split | `QUALIA_HOME/vault/<slug>/` + manifest over vault, METHODOLOGY.md, IMPROVEMENT.md, improvement.yaml, operator files. Only `qualia evaluate --protected` reads it; `qualia improve` never calls it. |
| Lanes (T6) | After Phase 1 freezes contracts: ENGINE `qualia/{core,store,io,eval,improve}` · AI `qualia/ai` · SERVER `qualia/server`, `qualia/cli.py` · WEB `web/`. Contract changes (migrations, openapi.json, backend protocol) = main session only. |
| Design dial (T7) | `reviews: end-only`; hard gates (dependency outside this table, logic/schema change from design) → OWNER-NEEDED batch. |
| Marketing (T8) | README-as-artifact + read-only static demo (zero API, zero AI) + social preview PNG + sitemap; measurement = GitHub traffic insights; ultrareview deferred. |
| Data | AnnoMI via `scripts/fetch_demo.py` (pinned commit + SHA-256) into gitignored `demo/data/`; split by transcript 60/20/20 dev/validation/protected. |
| Alerts · license | ntfy topic in gitignored `scripts/ntfy-topic.local`, status text only · MIT + `DATA-LICENSES.md`. |

## 3. Workstreams (WHAT)
- **3.1 Repo & kit [LB]** uv project · `web/` Vite scaffold · Phase 0 kit · CI (ruff, pytest `-m "not live"`, tsc, lint, vitest, pip-audit, `npm audit --audit-level=high`, gitleaks, `scripts/check_no_data.py`) · Dependabot · README.md with a Decisions section · .gitignore (*.db, demo/data/, logs/, *.local, OWNER-*.md, graphify-out/) · LICENSE · `.env.example`.
- **3.2 Store & provenance [LB]** migrations + append-only triggers; `db.py` sole writer; `qualia init <name>` builds the workspace (doc 01 §4): `git init`, operator files from `qualia/templates/`, METHODOLOGY.md stub, config defaults, vault + manifest.
- **3.3 Import & domain [LB]** TXT/MD/CSV importers (content-hash idempotent); segmentation per `segmentation.yaml` (paragraph | utterance | sentence); cases + attributes from CSV columns; codebook CRUD + `qualia codebook freeze`.
- **3.4 Server & API [LB]** Host allowlist {127.0.0.1, localhost}; `X-Qualia-Token` minted per launch, injected into the served page; CSP, nosniff, frame-ancestors none; `qualia open` = server + browser; `scripts/export_openapi.py`.
- **3.5 Workspace UI [LB]** data, state and keyboard logic in `web/src/lib/`, markup in components (M4); doc 04 layout; span viewer; keyboard coding (↑/↓ segment, number = code, `a`/`r` accept/reject); codebook tree; right panel (codes, suggestions, model-reported score, provenance popover); memos; retrieval; matrix with heat shading + drill-down; review queue; experiment history.
- **3.6 AI backends & routing [LB]** `ClassificationBackend.classify(segments, schema, context)`; claude_cli, codex_cli, rules, fake; router (task, availability, egress, budget, threshold); ledger; cache; egress_log; review triggers (below threshold, backend disagreement, QC sample); accept/reject → coding + feedback events.
- **3.7 Evaluation [LB]** jsonl benchmarks + `qualia benchmark import`; bundle: per-code P/R/F1, macro/micro F1, exact/partial match, kappa (NaN → "n/a"), nominal alpha (`qualia/eval/alpha.py`), ECE, escalation rate, calls per 1k segments, latency; `qualia evaluate [--split validation | --protected]` → md + json.
- **3.8 Improvement loop [LB]** `qualia improve --agent claude|codex|fake [--budget N]`: snapshot → operator writes `experiments/NNNN.md` + edits mutable files → scope diff → manifest → evaluate → policy (+ confirm run) → KEEP/REVERT → `experiments` row. Methodology ideas → `experiments/proposals/`, never applied.
- **3.9 Export [LB]** `qualia export --format csv|json [--no-text]`; `--bundle reproducibility` (events, versions, experiments, evaluation runs, config hashes, CLI versions).
- **3.10 Demo data [LB]** `qualia demo`: AnnoMI project (cases = transcripts, attribute = mi_quality, codebook from AnnoMI's README definitions, human codes as human events, §2 splits); idempotent.
- **3.11 Jev [sacrificial]** httpx → `POST https://api.typesafe.ai/v1/systemone`, model `jev-1.13.0`, types choice/score/`noul`; off by default, egress-gated, $ in ledger; recorded-fixture contract tests; live test skips without the key.
- **3.12 Portfolio [sacrificial]** README (positioning "Qualitative coding you can audit", screenshots + GIF from `design-review/final/`, architecture diagram, MVP walkthrough, Decisions log); `scripts/build_snapshot.py` → `demo/snapshot.json` + static demo build + Pages workflow (activates once public); `docs/social-preview.png` 1280×640; sitemap. Re-check AnnoMI's license before the snapshot ships, else fallback data.
- **3.13 Hygiene [LB]** headers; audits; .env.example parity; zero TODO/FIXME; doc 01 §10; `codex review --base <phase-0 commit> "focus on security"` triaged; `npx @openai/codex-security scan` (login needed → OWNER batch).
- **3.14 Agent parity [LB]** `scripts/smoke-agents.ps1`: `qualia improve --budget 1` on the demo with each agent.
[LB] = load-bearing.

## 4. Environment additions
```
QUALIA_HOME=            # default %USERPROFILE%\Qualia — research projects live here, never in the repo
QUALIA_PORT=8765
TYPESAFE_API_KEY=       # optional — owner fills by hand (doc 03 §4); Jev stays off without it
```

## 5. Execution plan (WHEN)
| Phase | Work | Spec Kit feature | Lanes | Gate (verifier runs these §6 items) |
|---|---|---|---|---|
| 0 Preflight | kit, constitution, repo | — | main | preflight table, rules probe |
| 1 Foundations | 3.1, 3.2, 3.4 skeleton | 001-foundations | main | contracts FROZEN; I1, I7 |
| 2 Workspace | 3.3, 3.5 non-AI, 3.9 | 002-workspace | ENGINE ∥ SERVER ∥ WEB | idempotency, export |
| 3 AI coding | 3.6 + review UI | 003-ai-coding | AI ∥ WEB | I4, I5, budget |
| 4 Evaluation | 3.7, 3.10 | 004-evaluation | ENGINE ∥ WEB | metrics, alpha oracle |
| 5 Improvement | 3.8 + history UI | 005-improvement-loop | ENGINE ∥ WEB | I2, I3, MVP e2e |
| 6 Hygiene + parity | 3.13, 3.14 | — | main | I6, CI, secrets, parity |
| 7 Design pass | doc 05 | — | per doc 05 | doc 04 §5 checklist |
| 8 Portfolio [sacrificial] | 3.12 | 006-portfolio | WEB | public surface, Lighthouse |
| 9 Jev [sacrificial] | 3.11 | 007-jev-backend | AI | contract tests |
| 10 Final | §6 sweep, policy re-check (doc 01 §12), §7 | — | verifier | all §6 green → BUILD-STATE line 1 = `BUILD COMPLETE` |
Phases 8–9 can vanish without breaking 0–7.

## 6. Acceptance (EVIDENCE REQUIRED — paste output into BUILD-STATE)
- [ ] Preflight table; done-differently honored; `gh repo view --json visibility` → PRIVATE.
- [ ] `codex execpolicy check --rules .codex/rules/qualia.rules -- git push --force` (and reset --hard, clean -fd, rm -rf, gh repo edit) → forbidden.
- [ ] I1: UPDATE/DELETE on each append-only table raises; an event missing segment/codebook/actor/pipeline is rejected.
- [ ] I2: fake operator edits a code definition or METHODOLOGY.md → REVERT; codebook_versions hash unchanged.
- [ ] I3: grep `qualia/core` + `qualia/eval` for sqlite3|subprocess|httpx|fastapi|os.environ → 0; fake operator claims a gain but metrics drop → REVERT; edit outside mutable scope → REVERT "scope"; vault tampered → REVERT + flag; then `git -C <project> status --porcelain` empty and coding_events count unchanged.
- [ ] I4: grep `claude`/`codex` launches and `typesafe` outside their backend files → 0; argv tests assert §2 flags and no `--bare`; fresh temp cwd; injection fixture → schema-valid or rejected; malformed JSON → rejection naming the segment.
- [ ] I5: PATH without claude/codex + network blocked → project opens and reads; AI shows "unavailable"; `allow_external: false` → every external backend refused; one egress_log row per external call.
- [ ] I6: `scripts/check_no_data.py` fails CI on tracked *.db/vault/demo data; gitleaks clean.
- [ ] I7: Host `evil.example` → 403; missing/wrong token → 401; headers present; bound to 127.0.0.1.
- [ ] Budget: daily_calls 0 → "budget reached", zero backend calls; 10,000-char segment → bounded, no crash.
- [ ] Idempotency: same import twice → "0 new sources"; migrate twice → no-op; `qualia demo` twice → no duplicates.
- [ ] Metrics match hand-computed fixtures; own alpha = krippendorff oracle within 1e-9 on 3 fixtures.
- [ ] MVP success test (Playwright, FakeBackend): demo → code 5 segments by keyboard → AI code → accept/reject → `qualia improve --agent fake` scripted gain → KEEP + tag → bundle export where every event has segment/codebook/actor/pipeline. Screenshots.
- [ ] Parity (live, local): one experiments row each for claude and codex.
- [ ] CI green on last push; forced bad TYPESAFE_API_KEY → error output contains no key value.
- [ ] Demo build: zero `/api/` requests (Playwright network log); Lighthouse on `vite preview` → performance ≥ 90, accessibility ≥ 95.
- [ ] `git diff --stat <phase-0 commit>..HEAD -- docs/02* docs/03* docs/04* docs/05*` → empty; TODO/FIXME grep → 0.

## 7. Final report
```
Final report (print + WELCOME-BACK.md + docs/01-qualia-context.md current-state update):
per-workstream status · acceptance evidence · session spend · deferred items with
exact resume commands · the success numbers (MVP test pass, demo validation macro-F1 before → after one live experiment, agreement metrics, test counts, CI status) · live URLs.
```
Order: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → (8) → (9) → 10. Owner hands-on: ~20 min setup (doc 03 §0–§2), phone alerts
only when blocked, one public-flip decision at the end (doc 03 §8).
