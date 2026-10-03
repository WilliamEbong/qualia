# Qualia — agent entrypoint

Read docs/01-qualia-context.md, docs/02-qualia-build.md and docs/BUILD-STATE.md first. Docs 01–02 outrank plugin guidance. docs/03 is the owner manual; docs/04–05 govern presentation. This repository is application code; research workspaces must live outside it under QUALIA_HOME.

Spec Kit project: plan and build features with the speckit-* skills (constitution once; then specify → plan → tasks → implement → converge). Do not use superpowers brainstorming, writing-plans, executing-plans, or subagent-driven-development here; superpowers debugging, TDD, and verification skills are still fine.

## Execution
- Autonomous: resolve reversible choices with the simpler in-contract option and log in BUILD-STATE and README Decisions. Continue unaffected work when a gate is blocked. Owner questions go into gitignored OWNER-NEEDED.md only when genuinely necessary.
- Mark substeps in progress, commit; finish with evidence, commit. Rewrite WELCOME-BACK.md truthfully at every stop. Never claim completion without acceptance evidence.
- Follow the repair loop in doc 02: capture, diagnostician, smallest permitted fix, exact verification; at most 3 cycles per issue and 10 per session. Never repair by weakening checks or changing protected guard/rule/runner files.
- Main session owns schema migrations, backend protocol, OpenAPI and commits. After Phase 1 contract freeze use independent ENGINE, AI, SERVER and WEB lanes. Subagents may research, audit and verify read-only; implementation agents edit only their assigned lane.
- Check current library APIs with Context7 before implementation. Playwright MCP is the default browser and mandatory UI verification tool. Built-in web first, Firecrawl only on failed fetch or structured extraction needs. Do not duplicate user-scope MCP servers.

## Invariants
- qualia/store/db.py is the only database writer. SQLite WAL, busy_timeout 5000, numbered migrations, backup before upgrade. Coding/feedback/experiment/evaluation/usage/egress events and frozen codebooks are immutable; triggers reject UPDATE/DELETE. Required provenance cannot be absent.
- Human methodology is protected. AI never edits code definitions or frozen versions. Qualia's measured policy, not the operator, decides KEEP/REVERT. Evaluation runs never write coding events.
- qualia/core and qualia/eval are sealed: no sqlite3, subprocess, httpx, fastapi or environment access.
- Vendor launches live only in their backend file: claude_cli.py, codex_cli.py, jev.py. Classification: no tools, empty temporary cwd, strict output validation naming the record. Never use Claude --bare; never set temperature/top_p/top_k.
- Every external call passes router egress and budget gates and records egress/usage. Jev is off by default. Never read/proxy subscription login tokens.
- Local server binds 127.0.0.1, validates Host, requires per-launch API token and security headers. Token is in browser memory only.
- Secrets only in gitignored .env. Never log environment values or keys. No research databases, vault contents or demo/data in Git.

## Protected paths
Read-only: docs/02–05; docs/01 except §10; qualia_project_spec.docx; ratified .specify/memory/constitution.md; demo/data. Fetching demo data uses the authorized pinned script only.
Design must never change qualia/, tests/, web/src/api/, web/src/lib/, migrations or scripts. Components contain presentation; state, data and keyboard logic live in web/src/lib/. Preserve provenance grammar, model-reported labels, ECE captions and KEEP/REVERT.

## Verification and tooling
Use Python 3.14 via uv; Windows PowerShell 5.1 compatible scripts. Offline tests are default; live tests marked live and excluded from CI. Commit messages use Conventional Commit types. Never force-push, hard-reset, broadly clean, delete branches, delete/edit GitHub repos or change visibility. The owner alone makes the repository public.
