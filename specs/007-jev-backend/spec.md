# 007-jev-backend — Optional TypeSafe Jev classification backend

## Overview and scope

Add an optional direct-httpx Jev adapter under the existing classification/router/ledger protocol, with strong schema validation and a documented account/key handoff that never blocks the core product.

Sacrificial backend, off by default. Account creation is already complete per the user, but billing/credit balance, key presence and live access remain unverified until checked. The owner enters the key in an ignored .env file; no signup/payment or secret collection occurs in chat.

Governing sources: docs/01–05 and constitution v1.0.0. This is a prepared feature; main activates it in phase order and runs analyze before implementation. No implementation or acceptance pass is claimed here.

## Authoritative workstreams (verbatim from doc02)

- **3.11 Jev [sacrificial]** httpx → `POST https://api.typesafe.ai/v1/systemone`, model `jev-1.13.0`, types choice/score/`noul`; off by default, egress-gated, $ in ledger; recorded-fixture contract tests; live test skips without the key.

## Functional requirements

- FR-001: Implement ClassificationBackend in qualia/ai/backends/jev.py using approved httpx and POST https://api.typesafe.ai/v1/systemone, pinning jev-1.13.0 and supporting choice/score/noul request/response shapes.
- FR-002: Read TYPESAFE_API_KEY solely inside the Jev module on the server side; never return, log, export or bundle it. Missing/placeholder key yields unavailable and live tests skip.
- FR-003: Require both project allow_external and explicit jev_enabled before any Jev request; initial defaults remain off. Offline manual/rules/fake use remains fully functional.
- FR-004: Bound segment/batch/question/request sizes locally and reject invalid input before egress. Do not set temperature/top_p/top_k or undocumented token fields.
- FR-005: Validate exact question/segment mappings, primitive types, allowed choices, finite bounded probabilities/scores, usage counts and returned model; reject malformed data naming the record without exposing raw content.
- FR-006: Translate valid results into standard predictions/provenance with honest score semantics and frozen codebook/pipeline/prompt identity; do not conflate confidence with empirical accuracy.
- FR-007: Account for actual token usage and USD through existing ledger/Store paths, enforce jev_daily_usd 1.00 before each attempted request, and emit one egress row per attempt.
- FR-008: Handle timeout, malformed JSON, authentication, validation and transient provider errors with bounded retries and redacted structured messages; a forced bad key must never appear in output.
- FR-009: Provide offline contract tests for all primitives and malformed/error responses plus accurately labeled sanitized recorded fixtures; optional live tests use synthetic text and skip without the owner's key.
- FR-010: Keep detailed owner instructions in docs/JEV-SETUP.md covering dashboard key creation, ignored .env placement, credits check, optional enablement, synthetic verification and disabling again; never claim account billing or ZDR is configured without evidence.

## User scenarios

- US1: A researcher opens Qualia with no Jev key. Jev is unavailable/off, all local features work and the setup guide explains the optional owner action.
- US2: The owner adds a key locally and explicitly enables egress and Jev for a non-sensitive project. A tiny synthetic classification produces validated suggestions, provenance, usage and an egress entry.
- US3: Jev returns mismatched question IDs, a malformed probability, 401 or transient throttling. The request fails safely or retries within bounds; no key or raw source text appears in diagnostics.

## Success criteria

- SC-001: Offline httpx fixture tests cover choice/score/noul success and schema/error cases, exact endpoint/request shape, no sampling fields and vendor/key isolation.
- SC-002: Egress-disabled, Jev-disabled, missing-key and zero-dollar/call-budget probes cause zero HTTP attempts; each permitted retry creates exactly one egress record.
- SC-003: Usage/cost fixtures reproduce the documented rate calculation without billing outputs; score/noul semantics and returned model provenance are preserved.
- SC-004: Forced-invalid-key output contains no key value. Live synthetic compatibility and recorded fixtures are either evidenced or explicitly deferred with the exact owner step.
- SC-005: All core offline checks/CI remain green and the Jev setup guide matches current official docs without asserting unverified balance, retention or console labels.

## Authoritative acceptance excerpts (verbatim from doc02)

- [ ] I4: grep `claude`/`codex` launches and `typesafe` outside their backend files → 0; argv tests assert §2 flags and no `--bare`; fresh temp cwd; injection fixture → schema-valid or rejected; malformed JSON → rejection naming the segment.
- [ ] I5: PATH without claude/codex + network blocked → project opens and reads; AI shows "unavailable"; `allow_external: false` → every external backend refused; one egress_log row per external call.
- [ ] Budget: daily_calls 0 → "budget reached", zero backend calls; 10,000-char segment → bounded, no crash.
- [ ] CI green on last push; forced bad TYPESAFE_API_KEY → error output contains no key value.

Quoted shared gates retain their original scope. This feature proves its relevant part; later-phase responsibilities are stated above. Common I1/I6/I7 protections remain mandatory regressions, never exemptions.

## Informed assumptions

- Use docs/research/jev.md's verified official HTTP contract and recheck before implementation/live use. Pin jev-1.13.0; preserve actual returned model identity. Only qualia/ai/backends/jev.py reads TYPESAFE_API_KEY or contacts api.typesafe.ai.
- POST /v1/systemone requires model, state and a nonempty questions mapping. Choice, score and noul are provider-specific types; noul is a probability, not boolean. Never substitute an OpenAI request shape or unsupported max_tokens field.
- Qualitative multi-label coding uses independent noul questions per applicable code; choice/score primitives are supported/tested where schema mappings require them, without changing the frozen codebook or inventing methodology. Instructions carry code definitions because provider question IDs are not visible to the model.
- Validate the safe documented intersection: nonempty instructions, string criteria descriptions and 2–10 score levels. Preserve raw probabilities separately from any derived confidence and label derived/model-reported values honestly.
- Pricing evidence currently says $0.042 per million input tokens and free outputs; recheck before live use. Reserve a conservative local bound before dispatch, and ledger actual usage after response. No automatic paid refills or billing changes are made.
- A hand-authored synthetic response is not a recorded provider fixture. Label fixture provenance, and keep the recorded-fixture acceptance pending until a sanitized actual response is available; lack of a key never blocks other phases.
- HTTP retries for transient limits are bounded and each attempted request passes router budget/egress accounting. Authentication/validation failures do not retry automatically or log raw response bodies that may echo data.
