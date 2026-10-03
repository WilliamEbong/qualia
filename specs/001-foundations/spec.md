# 001 Foundations

## Overview
Establish an offline research workspace, immutable evidence storage, secure local server and repeatable development checks. Governing sources: docs 01–02 and constitution v1.0.0. Scope is Phase 1; subsequent phases supply import/coding and UI interactions.

## Authoritative phase workstreams (verbatim)
- **3.1 Repo & kit [LB]** uv project · `web/` Vite scaffold · Phase 0 kit · CI (ruff, pytest `-m "not live"`, tsc, lint, vitest, pip-audit, `npm audit --audit-level=high`, gitleaks, `scripts/check_no_data.py`) · Dependabot · README.md with a Decisions section · .gitignore (*.db, demo/data/, logs/, *.local, OWNER-*.md, graphify-out/) · LICENSE · `.env.example`.
- **3.2 Store & provenance [LB]** migrations + append-only triggers; `db.py` sole writer; `qualia init <name>` builds the workspace (doc 01 §4): `git init`, operator files from `qualia/templates/`, METHODOLOGY.md stub, config defaults, vault + manifest.
- **3.4 Server & API [LB]** Host allowlist {127.0.0.1, localhost}; `X-Qualia-Token` minted per launch, injected into the served page; CSP, nosniff, frame-ancestors none; `qualia open` = server + browser; `scripts/export_openapi.py`.

## Functional requirements
- FR-001: Initialize named workspaces outside the app checkout, with database, config, operator files, git repository and protected vault manifest. Reject path traversal and unsafe home paths; repeating init preserves existing data.
- FR-002: SQLite uses foreign keys, WAL, 5000ms busy timeout and numbered migrations tracked with user_version. Existing databases are backed up before upgrades; rerunning migration is a no-op.
- FR-003: Define doc01 §5 entities and append-only triggers for coding, feedback, experiments, evaluations, usage and egress, plus immutable sources and frozen versions. Required provenance and referential integrity are enforced by database constraints.
- FR-004: Expose a typed, local API with health/projects/workspace skeleton. Reject foreign Host with 403 and missing/wrong API token with 401. All responses carry security headers; served HTML injects the token without persistent browser storage.
- FR-005: Python CLI supports init/list/open; serve only 127.0.0.1. Browser scaffold builds offline with self-hostable assets. Export deterministic OpenAPI and generate TS types.
- FR-006: Supply test/lint/audit/secret/data CI, MIT license, env template and README decisions. Runtime dependencies must come from approved stack; dev tools as specified in CI are authorized.
- FR-007: Freeze database migration, API route shapes and ClassificationBackend protocol before parallel implementation lanes.

## Acceptance (verbatim gate items)
- I1: UPDATE/DELETE on each append-only table raises; an event missing segment/codebook/actor/pipeline is rejected.
- I7: Host `evil.example` → 403; missing/wrong token → 401; headers present; bound to 127.0.0.1.

## Scenarios and success criteria
- US1: Researcher runs `qualia init study`, then opens the project offline. SC-001: required files and schema exist outside checkout, and the second init changes no research data.
- US2: A caller tries to rewrite evidence or access the server from another Host. SC-002: negative tests prove FR-003/004 and the exact I1/I7 gates.
- US3: A contributor installs and checks the project. SC-003: Python tests/lint, web typecheck/build/test and data guard pass. CI runs the same checks and publishes no data.

## Assumptions
JSON syntax is used inside YAML configuration files: valid YAML 1.2, parsed with stdlib JSON to avoid adding an unapproved YAML runtime dependency. Local project slugs are lowercase ASCII letters/digits/hyphens. Init is explicit and idempotent. A GET of same-origin HTML bootstraps the per-launch token; all /api endpoints, including health, require it. No API cross-origin access is enabled. Protected hashes cover methodology, operator files, policy and protected vault; benchmark content is added in Phase 4.
