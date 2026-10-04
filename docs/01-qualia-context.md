# 01 — Qualia: Context, Architecture & Tech Stack

*Single source of truth for WHAT Qualia is and WHERE it stands. v1; input was `qualia_project_spec.docx` v0.1 — where
they differ this suite wins (browser UI first, Tauri later · app repo separate from research projects · Qualia, not the
agent, decides keep/revert). 02 = build runbook (Codex executes) · 03 = owner guide · 04 = design direction ·
05 = design-build pass. Live vault/repo files always win over this doc — doc 02's preflight re-verifies everything.*

## 1. What this product is
A local-first, model-agnostic qualitative research workspace: import transcripts, code them by hand or with AI, review
uncertain AI coding, measure the AI coder against human codes, and let an agent (Codex or Claude Code) improve the
coder's *implementation* under a protected benchmark. Core principle: **autonomous improvement of implementation; human
control of methodology.** Owner: non-technical builder; all code comes from Codex/Claude Code via these docs. Public
portfolio piece — the docs, specs and commit history ARE part of the product.

## 2. Goals (priority order — conflicts resolve by this ranking)
1. **Trustworthy core:** every decision traces to segment + codebook version + actor + pipeline; methodology is human.
2. **MVP loop works:** seed-code by hand → AI codes the rest → review → agent experiment improves validation → reproduce.
3. **Model-agnostic:** Codex and Claude Code run one protocol; runtime AI uses the user's own subscription CLIs.
4. **Portfolio + usable by others:** a stranger grasps it in 60 seconds and can install it.
5. **Local-first privacy:** opens offline; per-project egress policy; research data never enters the public repo.

## 3. Scope
**V1 in:** (1) local project workspaces · (2) TXT/MD/CSV import · (3) cases + attributes · (4) hierarchical codebook
with frozen versions · (5) manual + keyboard span coding, multi-code · (6) memos · (7) retrieval + code-by-case matrix ·
(8) schema-validated AI coding via Claude Code/Codex CLIs · (9) review queue · (10) append-only provenance · (11)
benchmark splits + `qualia evaluate` · (12) improvement loop with automatic keep/revert, run by both harnesses · (13)
CSV/JSON + reproducibility export · (14) Jev backend [sacrificial] · (15) README + static demo [sacrificial].
**OUT:** DOCX/PDF, DuckDB, framework matrices, charts, analytic/methodology assistants, Tauri, multi-user, audio,
plugin SDK, API-key backends — the V1.5 shortlist: open coding → draft codebook, DOCX/PDF, QualCoder import, MCP server.

## 4. Architecture
```
TXT/MD/CSV ─► qualia/io (adapters) ─► qualia/store/db.py (ONLY writer) ─► project.db (SQLite, WAL)
CLI `qualia` · FastAPI 127.0.0.1 (serves web/dist) ─► qualia/core (sealed) · qualia/eval (sealed)
qualia/ai/router ─► ledger · budget · cache ─► backends/{claude_cli, codex_cli, jev, rules, fake}
qualia improve ─► operator agent IN project workspace ─► qualia/improve/experiment.py:
  scope diff → hash check → evaluate → policy → git commit+tag (KEEP) | git restore (REVERT)
```
**Rendering:** request-time, local; no SSR. Static Pages demo = SPA build reading a snapshot JSON (no API, no AI).
**App repo (public) = code only.** Projects live under `QUALIA_HOME` (default `%USERPROFILE%\Qualia`), outside the
checkout, so a push can never carry research data. `projects/<slug>/`: project.db (gitignored) · `config/{prompts/,
routing.yaml, segmentation.yaml}` = MUTABLE scope · `benchmarks/{dev,validation}/` · `experiments/` · protected:
METHODOLOGY.md, IMPROVEMENT.md, AGENTS.md, CLAUDE.md, improvement.yaml · own `.git`. `vault/<slug>/`: protected test
split + manifest.sha256. **Sealed:** `qualia/core/`, `qualia/eval/` import no sqlite3/subprocess/httpx/fastapi/
os.environ. **Single-vendor files:** `qualia/ai/backends/claude_cli.py` (only launcher of `claude`, for classification
AND operator runs), `codex_cli.py` (only `codex`), `jev.py` (only api.typesafe.ai). **Adapters** (pydantic, fail loud
naming the record): `qualia/io/`, `qualia/ai/schemas.py`, `qualia/server/api_models.py`.
**Sacred paths** — read-only to the build: `docs/02–05`, `docs/01` except §10, `qualia_project_spec.docx`,
`.specify/memory/constitution.md` after Phase 0, `demo/data/`. Design work never touches `qualia/`, `tests/`,
`web/src/api/` (generated), `web/src/lib/` (web data, state and keyboard logic — components hold markup only),
`qualia/store/migrations/`, `scripts/`.

## 5. Data model (definitive = `qualia/store/migrations/*.sql`; the contract beats this doc)
- `sources` content_hash UNIQUE, text immutable (re-import = new row `version_of`) · `segments` source_id, start, end,
  ordinal, speaker? idx(source_id, ordinal) · `cases`, `source_cases` (M:N), `attributes` owner, key, value idx(key).
- `codes` parent_id, name, status, definition, include, exclude, examples_pos/neg · `codebook_versions` snapshot_json,
  hash, frozen_at (immutable).
- `coding_events` APPEND-ONLY: segment_id, span, code_id, action (assign|remove|suggest|accept|reject), actor_type,
  actor, backend, model, cli_version, score? (model-reported), rationale?, codebook_version_id, pipeline_version (hash
  of config/), prompt_hash, experiment_id?, review_status, reviewed_by — idx(code_id), (segment_id), (review_status).
  Current coding = a view over events.
- `memos` · APPEND-ONLY `feedback_events`, `experiments`, `evaluation_runs`, `usage_ledger`, `egress_log`. Evaluation
  predictions live in `evaluation_runs`, never `coding_events`. Not exported unless flagged: source text, vault.

## 6. Key invariants (never violate — checks in doc 02 §6)
1. **Provenance is append-only and complete:** UPDATE/DELETE on append-only tables aborts (SQLite triggers); every
   coding event has segment, codebook version, actor, pipeline version.
2. **Methodology is the researcher's:** no automated path edits code definitions, frozen codebook versions or
   METHODOLOGY.md; methodology ideas are proposals awaiting approval.
3. **Evaluation is ordinary code, fixed during experiments:** metrics only in `qualia/eval/`; Qualia's policy decides
   KEEP/REVERT, never agent output; a diff outside mutable scope or a protected-hash mismatch auto-REVERTs.
4. **Vendor isolation, no-tools runtime:** one file per AI vendor; classification runs tools-disabled in an empty temp
   dir; every AI output is schema-validated before use.
5. **Local-first, egress-gated:** a project opens with no network and no AI CLIs; `allow_external: false` blocks every
   external backend at the router; every external call writes `egress_log`.
6. **The public repo carries no research data or secrets.**
7. **The local server is local:** binds 127.0.0.1, rejects foreign Host headers, requires a per-launch token.

## 7. Open-source leverage
| need | use | why |
|---|---|---|
| CLI / API / validation | Typer 0.27 · FastAPI 0.142 + uvicorn 0.54 · pydantic 2.13 | mainstream; cp314 wheels |
| storage | stdlib sqlite3 + numbered SQL migrations | triggers enforce invariant 1; no ORM |
| metrics | scikit-learn 1.9 (P/R/F1, kappa, calibration) | never hand-roll (C2) |
| Krippendorff alpha | own ~25-line nominal alpha; `krippendorff` 0.8.2 dev-only oracle | package is GPL-3.0 — must not ship |
| span coding | @recogito/text-annotator 4.3.6 + @recogito/react-text-annotator | only maintained React-19 lib with overlaps |
| UI kit / matrix | shadcn/ui + Tailwind 4 · TanStack Table **v9** | v9 API differs from v8 — context7 first |
| API types | openapi-typescript 7.13, typescript pinned ~5.9.3 | its peer dep rejects TS 6 |
| tests · Jev | pytest 9 · Vitest · @playwright/test 1.63 · httpx | Jev SDK 0.7.x churns (6 releases in 17 days) |
| data | AnnoMI: 133 MI transcripts, 9,699 expert-coded utterances, high/low quality | public domain per its paper; fetched by pinned script (repo has no LICENSE) |
Public data may sit in training sets: the protected split guards against the *optimizer*, not memorization. Fallback
data: Zenodo 15698094 (CC BY 4.0, two coders). **Build-vs-borrow:** closest is **Exegete** (alpha MCP server over
QualCoder, driven by Claude Code/Codex, approval-before-commit, kappa); it lacks immutable provenance, a protected
benchmark, keep/revert and enforced egress. **Borrow ideas, keep the custom build:** approval-before-commit (review
queue), MCP tool shapes + QualCoder import (V1.5), quallmer's validation metrics (our bundle). Others: reference only.

## 8. Frameworks verdict (docs 01–05, constitution, AGENTS.md/CLAUDE.md outrank all plugin guidance)
**Use:** Spec Kit 1.0.13 lean · Ponytail (implementation only, never deleting doc-mandated features) · Codex rules ·
Codex subagents · `codex review` (security focus) at gates. **With mitigation:** Superpowers (debugging/TDD/verification
only; Spec Kit plans) · taste-skill (doc 04 + DESIGN.md outrank it) · Codex Security scan pre-public (v0.x).
**Defer:** graphify, `/security-review`, Claude Design → Claude Code stage · ultrareview → post-V1 PRs (~$5–25/run).
**Skip:** ultraplan (removed) · security-review Action (API-billed, not injection-hardened) · Codex hooks, cc-safety-net
(rules + sandbox cover it) · GSD (archived) · claude-squad (tmux) · karpathy-skills (in conduct rules) · tdd-guard.

## 9. Cost policy (honest)
Runtime AI = the user's Claude/ChatGPT subscriptions via their own CLIs (no per-call bill) + optional Jev at $0.042 per
million input tokens, output free (docs.typesafe.ai, 2026-10-03). The real cost is **quota**: Codex Plus/Business gives
~5–45 Astra messages per 5 hours; Pro has no 5-hour limit (OpenAI pricing, 2026-10-03). Layers: `check_budget()` before
every backend call (bounds in `config/routing.yaml`) · cheapest tier by default · result cache · subscription limits
as backstop with paid extra usage OFF (doc 03 §0). Single write-path: `qualia/ai/ledger.py`.

## 10. Current state (update each session)
IMPLEMENTED LOCALLY: research workspace, coding/review/evaluation, guarded improvement, mixed-methods analysis/visualization and reproducible exports; Archive of Looking presentation and illustrated user guide. Native classification uses own-account official CLIs with approved invocation accounting, five-segment batches and no automatic retries; public-router Haiku/Luna/Astra checks passed. Claude Opus5.5 improvement now passes restricted-file probes and a synthetic live experiment (Haiku macro-F1 1.0→1.0, correct REVERT). Codex improvement remains disabled: installed Windows runtime reads outside project during patch verification and failed loopback denial. Setup and owner approvals are present; no permission workaround. Jev is live-verified and enabled for demo at the existing $1 daily local limit. Official scanner superseded by owner-run Claude security review before public release; private-main checkpoints are approved. Full current acceptance and CI evidence are in BUILD-STATE. No public deployment or BUILD COMPLETE claim.

## 11. Tooling conventions
Executor: Codex CLI, GPT-6 Astra, reasoning high (0.144.6 lacks Astra — doc 03 §0 updates). Improvement: Claude Code,
Opus 5.5. Driver `scripts/run-build.ps1`. Windows 10, PowerShell 5.1, no pwsh — no unix-only scripts; Python via `uv`.
Toolbelt (playwright, context7, firecrawl) is present for both harnesses — use it, never shadow it at project scope.

## 12. Decided vs open
**Decided:** build V1 with Codex GPT-6 Astra, improve with Claude Code Opus 5.5 · runtime AI via Claude + Codex
subscriptions (own unmodified CLIs; never OAuth tokens) · public GitHub portfolio repo (private until the owner flips
it) · research projects in a local folder outside the repo · Spec Kit + these docs · autonomous build, subagents, owner
only when genuinely blocked · stack by Claude: Python 3.14 engine + CLI + local web UI, Tauri later · local-first ·
methodology rule · SQLite · CLI = agent interface · spec §21 MVP · thin AGENTS.md/CLAUDE.md · Jev optional, off · MIT.
**Open:** plan tiers (build speed) → doc 03 §0 · subscription-CLI policy re-check → Phase 10 gate · Jev account →
owner, any time, never blocks · Codex subagents inside `codex exec` → Phase 0 probe.
