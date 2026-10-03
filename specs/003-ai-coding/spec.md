# 003-ai-coding — AI classification, routing, and human review

## Overview and scope

Add subscription-CLI and deterministic offline classification behind egress, availability and budget checks, then turn schema-validated suggestions into an auditable human review queue.

Only the suggestion/review/provenance parts of 3.5 are added here. Jev belongs to 007; evaluation ECE is populated by 004; experiments belong to 005. Until validation exists, the ECE caption must explicitly say unavailable rather than show a fabricated score.

Governing sources: docs/01–05 and constitution v1.0.0. This is a prepared feature; main activates it in phase order and runs analyze before implementation. No implementation or acceptance pass is claimed here.

## Authoritative workstreams (verbatim from doc02)

- **3.6 AI backends & routing [LB]** `ClassificationBackend.classify(segments, schema, context)`; claude_cli, codex_cli, rules, fake; router (task, availability, egress, budget, threshold); ledger; cache; egress_log; review triggers (below threshold, backend disagreement, QC sample); accept/reject → coding + feedback events.
- **3.5 Workspace UI [LB]** data, state and keyboard logic in `web/src/lib/`, markup in components (M4); doc 04 layout; span viewer; keyboard coding (↑/↓ segment, number = code, `a`/`r` accept/reject); codebook tree; right panel (codes, suggestions, model-reported score, provenance popover); memos; retrieval; matrix with heat shading + drill-down; review queue; experiment history.

## Functional requirements

- FR-001: Implement Claude CLI, Codex CLI, rules and fake backends under the frozen protocol; only the relevant vendor module launches that vendor for classification and later operator runs.
- FR-002: Launch CLI classification with doc02 §2 flags, stdin prompt, a fresh empty temporary cwd, bounded execution/output and no sampling settings. Disable all tools and inherited external integrations while preserving the user's CLI subscription login.
- FR-003: Validate every provider response with pydantic before storing suggestions; require known segment and code IDs, valid spans, finite bounded scores and complete provenance. Reject malformed or injected output with an offending segment identifier.
- FR-004: Route by task, availability, project egress permission, budget and escalation threshold. allow_external:false blocks every external backend before invocation; the offline rules/fake path works without network or CLIs.
- FR-005: Enforce batch size, segment-length, daily-call and run-segment limits before each attempted backend call, including retries. Report budget reached with zero calls when daily_calls is zero.
- FR-006: Use qualia/ai/ledger.py as the only usage-record orchestration path and Store as the only SQL writer. Record provider usage, model, CLI version, latency, status, run and per-attempt egress hashes/purpose without source text.
- FR-007: Cache validated results by segment hash, prompt hash, codebook version, backend and model; invalidate on any changed component and never reuse another codebook's predictions.
- FR-008: Append suggestion events with actor/backend/model/CLI version, score/rationale, frozen codebook, pipeline/prompt hashes and review trigger. Below-threshold, actual disagreement and QC samples enter the review queue.
- FR-009: Accept/reject by explicit user action or a/r keyboard shortcuts; atomically append coding and feedback events tied to the original suggestion. A duplicate or concurrent review cannot apply twice.
- FR-010: Display grouped review reasons, excerpts, suggested codes, model-reported scores, ECE availability and provenance. Suggested stripes are dashed; accepted suggestions are solid with mono m; rejection remains visible in provenance.
- FR-011: Keep all classification tests offline with fake/recorded process fixtures; separate subscription live smoke tests under the live marker so CI never calls a provider.

## User scenarios

- US1: An offline researcher runs rules classification and reviews suggestions; disabling external egress leaves manual reading/coding intact and explains why subscription backends are unavailable.
- US2: A researcher enables egress and selects a verified CLI model. Only bounded text is sent, provenance and usage are recorded, and rerunning identical classification uses the cache.
- US3: A reviewer accepts one suggestion and rejects another with keyboard shortcuts, then retries the same review request. Each suggestion has exactly one review and matching immutable feedback.

## Success criteria

- SC-001: Exact I4/I5/budget gates below pass with mocked CLI calls, schema/injection fixtures, no-network/PATH probes and actual tool-surface inspection.
- SC-002: Tests prove cache-key invalidation, per-attempt egress accounting, retry bounds and no provider invocation on blocked/budget-exhausted input.
- SC-003: Concurrency/repeat-review tests yield one accept/reject event and one associated feedback record; current coding/provenance remain consistent.
- SC-004: Playwright MCP verifies trigger groups, a/r shortcuts, dashed/solid/m states, model-reported labels and honest ECE availability with screenshots.
- SC-005: Offline Python/web/security checks pass; live calls are separately marked and recorded only when account availability and egress consent permit.

## Authoritative acceptance excerpts (verbatim from doc02)

- [ ] I4: grep `claude`/`codex` launches and `typesafe` outside their backend files → 0; argv tests assert §2 flags and no `--bare`; fresh temp cwd; injection fixture → schema-valid or rejected; malformed JSON → rejection naming the segment.
- [ ] I5: PATH without claude/codex + network blocked → project opens and reads; AI shows "unavailable"; `allow_external: false` → every external backend refused; one egress_log row per external call.
- [ ] Budget: daily_calls 0 → "budget reached", zero backend calls; 10,000-char segment → bounded, no crash.

Quoted shared gates retain their original scope. This feature proves its relevant part; later-phase responsibilities are stated above. Common I1/I6/I7 protections remain mandatory regressions, never exemptions.

## Informed assumptions

- Use the Phase 1 ClassificationBackend protocol exactly: available(), classify(segments, schema, context), and a result containing predictions, usage and CLI version. The main session approves any contract change.
- Defaults remain segments_per_call 20, max_segment_chars 4000, daily_calls 300, run_segments 2000, human_review_below 0.70 and qc_sample_rate 0.05. Oversized input is rejected with a segment-specific error before any backend call, rather than silently truncating evidence.
- Use verified account-visible cheap/strong model IDs from preflight. Backend availability is distinct from egress permission; show why a backend cannot run. An unavailable or exhausted external model never silently switches to a costlier one.
- Classification flags must include doc02 §2 exactly and may require additional verified isolation controls to eliminate inherited MCP/app tools. Prove the actual tool surface; disabling shell/search alone is not sufficient evidence.
- Every AI assignment is initially a suggestion. All suggestions are reviewable; queue trigger reasons distinguish below-threshold, disagreement and QC samples. A score is model-reported, never calibrated accuracy.
- QC sampling is reproducible from a stable run/segment seed. Disagreement is computed when two configured backends actually supplied predictions; do not make an extra paid call merely to invent a disagreement field.
- Log each attempted external request, including retries, and reserve/check budgets before dispatch. Cached responses avoid provider calls and are marked as cache hits. Errors retain status/type and record identity without echoing prompts, environment values or provider bodies.
