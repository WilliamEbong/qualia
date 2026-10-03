# Qualia Constitution

Qualia is a local-first, model-agnostic qualitative research workspace. Its governing rule:
**autonomous improvement of implementation; human control of methodology.** The source documents are
`docs/01-qualia-context.md` (what and why) and `docs/02-qualia-build.md` (the work); this constitution
restates their non-negotiables so every Spec Kit feature is checked against them.

## Core Principles

### I. Provenance Is Append-Only and Complete (NON-NEGOTIABLE)
Coding events, feedback events, experiments, evaluation runs, the usage ledger and the egress log MUST
be append-only, enforced by SQLite triggers that abort UPDATE and DELETE. Every coding event MUST record
its segment, codebook version, actor and pipeline version. Current coding state is derived from events,
never stored in place of them.

### II. Methodology Belongs to the Researcher (NON-NEGOTIABLE)
No automated path may edit code definitions, frozen codebook versions or METHODOLOGY.md. Agents may
propose methodology changes as records awaiting approval; they MUST NOT apply them.

### III. Evaluation Is Ordinary Code, Fixed During Experiments (NON-NEGOTIABLE)
Metrics MUST be computed only in `qualia/eval/` by deterministic code; model self-report never counts.
Qualia's acceptance policy, not agent output, decides KEEP or REVERT. A change outside the mutable scope
or a protected-hash mismatch MUST auto-REVERT. The protected test split lives outside the project
workspace and the improvement loop never reads it.

### IV. Vendor Isolation and No-Tools Runtime
Each external AI vendor is invoked from exactly one file under `qualia/ai/backends/`. Classification
calls MUST run with tools disabled in an empty temporary directory, and every AI output MUST be
schema-validated before use. `qualia/core/` and `qualia/eval/` stay sealed: no sqlite3, subprocess,
httpx, fastapi or environment access. Every external data shape passes a pydantic adapter that fails
loudly and names the offending record.

### V. Local-First and Egress-Gated
A project MUST open and remain readable with no network and no AI CLIs installed. `allow_external: false`
blocks every external backend at the router, and every external call writes an egress-log row. The local
server binds 127.0.0.1 only, rejects foreign Host headers and requires a per-launch token.

### VI. No Research Data or Secrets in the Public Repo
Research projects live under `QUALIA_HOME`, outside the repository. CI MUST fail on tracked databases,
vault files or demo data, and on any secret found by gitleaks. Qualia never reads, stores or proxies a
user's Claude or ChatGPT login tokens; it only invokes the user's own unmodified CLIs.

### VII. Evidence Over Claims, Simplicity Over Cleverness
Every acceptance item is proven by a command, fixture, probe or screenshot. Tests land with the code
(offline by default; live-AI tests carry the `live` marker and stay out of CI). Never hand-roll what a
maintained library does; never add abstractions, dependencies or configuration nobody needs yet.

## Technology Constraints
Python 3.14 via uv; FastAPI, Typer and pydantic; stdlib sqlite3 with numbered SQL migrations; scikit-learn
for metrics; React 19 + Vite + TypeScript with shadcn/ui, Tailwind 4 and TanStack Table v9. Any dependency
not listed in `docs/02-qualia-build.md` §2 needs an owner gate. Windows 10 with PowerShell 5.1 is the
reference machine: no unix-only scripts.

## Development Workflow
Each build phase runs as one Spec Kit feature: specify → plan → tasks → analyze → implement → converge.
Docs 01–02 decide WHAT; Spec Kit artifacts decide HOW; on conflict the docs win and spec.md is corrected.
Progress is tracked in `docs/BUILD-STATE.md` with a commit per sub-step. Failures go through the repair
loop in doc 02 before any owner escalation; a fix may never weaken a test, check or guard.

## Governance
This constitution and docs 01–05 outrank all plugin and skill guidance. It changes only through an owner
decision recorded in `docs/answers/` and a matching amendment to doc 01. Converge treats any violation of
a principle above as CRITICAL.

**Version**: 1.0.0 | **Ratified**: 2026-10-03 | **Last Amended**: 2026-10-03
