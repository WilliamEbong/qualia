# Foundations independent verification

Assessed 2026-10-03 against specs/001-foundations spec, plan and tasks, with constitution v1.0.0. The requested speckit-converge assessment was read-only: main session owns task/checkpoint updates. Prerequisite script returned the correct feature directory; no extensions.yml hooks were present.

Scope: 7 functional requirements, 3 success criteria, I1/I7, 6 plan work areas, 8 tasks, and all 7 constitution principles as applicable to Phase 1. Later-phase AI/evaluation/improvement obligations were not incorrectly treated as missing foundation features.

## Verified evidence

| Check | Result |
|---|---|
| Exact `.venv/Scripts/python.exe -m pytest -q` with scoped temp-directory access | Initial 11 passed in 9.41s; updated suite 21 passed in 8.78s |
| `python -m ruff check qualia tests scripts` | All checks passed |
| `python scripts/check_no_data.py` | No tracked research/local secret files |
| Parsed openapi.json compared with create_app().openapi() | Equal |
| CTE-prefixed UPDATE through Store.rows | Rejected: `not authorized`; original case unchanged |
| Null, empty and whitespace backend/model/cli_version/prompt_hash | All 12 probes rejected |
| Complete model provenance | Accepted |
| Append-only tables, missing provenance, frozen membership, span bounds | Foundation negative tests pass |
| Host/token/origin and response headers, offline workspace read | Foundation API tests pass |
| SQL writer search | SQL connections/writes remain in qualia/store/db.py |
| Sealed core search | No forbidden imports; updated suite includes AST boundary regression |
| Protected docs 02–05 and constitution diff from f1d8719 | Empty |
| Main-branch Checks CI for ae770eca67c974ee833926c8c5a157665d6c08c8 | Completed, success |

CI evidence: [Checks run 37157791283](https://github.com/WilliamEbong/qualia/actions/runs/37157791283). Newer Dependabot pull-request runs were deliberately excluded from the main-commit conclusion. Subsequent local regression additions require their own pushed-commit CI evidence; this result is explicitly tied to ae770eca.

Existing main-session browser evidence in BUILD-STATE records Playwright navigation to the foundation page and design-review/foundations.png. This assessment did not independently claim another rendered UI check. The main session owns web check reruns.

The observed warnings are non-failing: installed Starlette deprecates httpx TestClient, and pytest's mixed-sandbox cache path emits an access warning. All test bodies executed; neither warning was suppressed.

## Findings and remediation

F1 — Constitution VI / FR-006 / plan testing / T007: the initial data guard accepted project.db-wal, project.db-shm and project.db.v1.bak, which can contain research data. Main session repaired .db and .sqlite sidecar/backup detection, widened .gitignore and added focused guard tests. The updated suite passes. One equivalent extension variant, .sqlite3-wal/.sqlite3-shm/.sqlite3.v1.bak, was reported to main for the same narrow completion; its base .sqlite3 file was already forbidden.

Other prior findings are repaired in current implementation: read-query authorizer, conditional complete AI provenance, project/vault resolved containment, migration version advancement and preserving partial initialization on retry.

No other actionable implementation gap was identified within Phase 1. Combining the planned store/workspace/server tests in tests/test_foundations.py satisfies their intent. No unrequested implementation removal was proposed. Final convergence depends only on finishing the equivalent .sqlite3 guard variants and recording new-head checks/freeze in the main-session artifacts.
