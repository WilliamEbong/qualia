# Foundations tasks

## Phase 1: Setup
- [ ] T001 Create approved Python project metadata, package and README/license in pyproject.toml, qualia/__init__.py, README.md, LICENSE (FR-006).
- [ ] T002 Create definitive migration and sole writer in qualia/store/migrations/001_initial.sql and qualia/store/db.py; test append-only/migrations in tests/test_store.py (FR-002/003, SC-002).
## Phase 2: Workspaces and server
- [ ] T003 Implement safe workspace init/templates and CLI init/list in qualia/workspace.py, qualia/templates/, qualia/cli.py; test path containment/idempotency in tests/test_workspace.py (FR-001/005, SC-001).
- [ ] T004 Implement local server security, typed skeleton, loopback open and tests in qualia/server/, tests/test_server.py (FR-004/005, SC-002).
- [ ] T005 Freeze backend protocol and exported API in qualia/ai/protocol.py, openapi.json, scripts/export_openapi.py (FR-007).
## Phase 3: Web and verification
- [ ] T006 Create web scaffold, generated API types and minimal smoke test in web/ (FR-005, SC-003).
- [ ] T007 Add CI/Dependabot, scripts/check_no_data.py and data guard test (FR-006, SC-003).
- [ ] T008 Run acceptance gates, private remote/CI verification, and convergence; record exact evidence in docs/BUILD-STATE.md (all SC).
