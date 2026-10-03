# Foundations implementation plan

Python 3.14, uv, Typer, FastAPI/Pydantic, SQLite stdlib; React 19/Vite/TypeScript 5.9 scaffold. Context7 checked FastAPI middleware/request models/TestClient and Typer commands/options before implementation. Verify actual package releases during install; log nearest-release adaptations.

1. `pyproject.toml`, `qualia/__init__.py`, approved dependencies/dev tools, MIT license and README.
2. `qualia/store/migrations/001_initial.sql`: definitive schema with immutable provenance, source/version triggers, indexes, current coding view. `qualia/store/db.py`: only SQL write path, connection/migration helpers and domain transaction methods. `qualia/core/models.py`: sealed domain records, no IO.
3. `qualia/workspace.py`, `qualia/templates/`: path containment, defaults, manifests and safe idempotent init. .env contains only approved config names; only Jev backend will read its key. Workspaces have their own Git identity inherited or repo-local fallback and initial protected commit.
4. `qualia/server/api_models.py`, `app.py`: request/response adapters; token/Host/header middleware and static-serving skeleton. `qualia/cli.py`: init/list/open with loopback bind. `scripts/export_openapi.py`, `openapi.json` contract and `qualia/ai/protocol.py` frozen input/output signature.
5. `web/` scaffold with React, Vite, TS and plain shadcn-compatible base. API types generated from OpenAPI; data/state logic goes in lib, components markup only. No final design pass here.
6. `tests/test_store.py`, `tests/test_server.py`, `tests/test_workspace.py`; offline fixtures use synthetic content only. CI includes approved checks and database/data detection. End with acceptance evidence and convergence.

Constitution check: all seven principles preserved; sole writer and sealed boundaries enforced by tests. No live calls in offline tests; no exports/public visibility changes. Avoid abstractions beyond explicit backend protocol. Main session owns all contracts; freeze before Phase 2 lanes.
