# 007-jev-backend implementation plan

## Entry gate and technical context

Phase 9 runs only after its preceding required gates; this plan does not bypass the runbook order. Main activates this supplied directory in .specify/feature.json, then runs analyze. Reuse the approved Python 3.14/uv, FastAPI/Typer/pydantic, SQLite and React 19/Vite/TypeScript stack. Use only the dependencies listed in docs01/02; pinned-version absence uses the documented nearest-release adaptation with evidence. Verify current version-accurate APIs with Context7 before implementation. These documents specify behavior and boundaries; they do not assert unverified library signatures.

Main owns migrations, openapi.json and backend protocol. Reconcile against the live Phase 1 contract before implementation; never silently edit an established contract in a worker lane. Tests are offline by default; live tests use the live marker and never run in CI. Every UI change needs Playwright MCP verification. Record progress/repairs through main in BUILD-STATE, without touching sacred documents.

## Architecture and file responsibilities

1. Keep HTTP/auth/model details in qualia/ai/backends/jev.py. Reuse shared prediction schemas and ClassificationBackend; provider-specific schema classes may live in the vendor file to preserve isolation.
2. Integrate availability, jev_enabled and USD reservation into existing router/ledger paths; Store remains the only database writer. Any shared protocol/schema change belongs to main and must preserve the four existing backends.
3. tests/test_jev_backend.py uses httpx MockTransport and synthetic schemas; tests/fixtures/jev/ includes provenance notes separating synthetic and recorded responses. tests/live/test_jev.py is opt-in and synthetic only.
4. Update docs/JEV-SETUP.md and .env.example as needed without reading existing key values; frontend receives only availability/redacted errors, never environment contents.
5. Do not install the changing Jev SDK or add API-key backends beyond this explicitly approved adapter. New browser UI is unnecessary unless existing backend selection cannot expose availability.

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
