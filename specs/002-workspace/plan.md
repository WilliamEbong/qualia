# 002-workspace implementation plan

## Entry gate and technical context

Phase 2 runs only after its preceding required gates; this plan does not bypass the runbook order. Main activates this supplied directory in .specify/feature.json, then runs analyze. Reuse the approved Python 3.14/uv, FastAPI/Typer/pydantic, SQLite and React 19/Vite/TypeScript stack. Use only the dependencies listed in docs01/02; pinned-version absence uses the documented nearest-release adaptation with evidence. Verify current version-accurate APIs with Context7 before implementation. These documents specify behavior and boundaries; they do not assert unverified library signatures.

Main owns migrations, openapi.json and backend protocol. Reconcile against the live Phase 1 contract before implementation; never silently edit an established contract in a worker lane. Tests are offline by default; live tests use the live marker and never run in CI. Every UI change needs Playwright MCP verification. Record progress/repairs through main in BUILD-STATE, without touching sacred documents.

## Architecture and file responsibilities

1. ENGINE: qualia/io/{imports,exporters}.py adapts external records; qualia/core/{segmentation,codebook}.py contains pure rules. Extend Store transaction methods in qualia/store/db.py without direct SQL writes elsewhere.
2. SERVER: extend qualia/server/api_models.py and app.py plus qualia/cli.py for import, cases, codebook, coding, memos, retrieval, matrix and export. Main session owns any migration or API contract amendment and regenerates openapi.json/types before WEB consumes it.
3. WEB: web/src/lib/workspace.ts owns state/data/selection and keyboard logic; web/src/components and pages render rails, transcript, drawers and forms. Keep API transport in existing client.ts and generated types under web/src/api.
4. Spike Recogito saved-span restoration before integration; record a reproducible failure before selecting the pre-authorized CSS Custom Highlight fallback. Verify version-accurate APIs through Context7 before coding.
5. Use synthetic test content under tests; real imports and generated bundles go to project workspace or test temp directories outside the app checkout. No sample research databases are tracked.
6. Planned mutations use import {name, content, format: txt|md|csv}, code CRUD {name,parent_id,definition,include,exclude,examples_pos,examples_neg,status}, explicit codebook freeze, coding {segment_id,code_id,span_start,span_end,action:assign|remove,actor}, memos and export formats. The server supplies required frozen-version/pipeline provenance. Offsets are Unicode code points; adapt browser UTF-16 selections at the boundary. Main finalizes these shapes before generated-type consumers implement them.

## Constitution check

- I: Append-only evidence and required provenance stay enforced by Store/SQLite; never update historic coding, feedback, usage, egress, experiment or evaluation records.
- II: Codebook/methodology changes require explicit human action; automated paths use frozen versions.
- III: Evaluation remains sealed deterministic code; protected test contents never enter the optimizer.
- IV: Vendor launch/auth/HTTP isolation and schema validation remain mandatory; classification has no tools.
- V: Offline reading/manual work persists; external calls require project policy, availability and budget, with one egress record per attempt; localhost Host/token/headers remain effective.
- VI: No secrets, research DBs, protected vaults or raw demo data in Git; authorized public snapshots require a separate license check.
- VII: Verify stated behavior with fixtures, commands and browser evidence. No new dependency or speculative feature is authorized by this plan.

## Validation and handoff

Implement tasks in listed dependency order; a main-owned contract update must finish before consumers change. Re-run exact failed checks during repair. Use the spec success criteria and verbatim excerpts as the gate checklist, then run converge (at most three rounds per runbook), record unresolved issues honestly and preserve the resumable state. Phase-specific test files and evidence locations appear in tasks.md; filenames may follow an equivalent existing owner without adding duplicate abstractions.
