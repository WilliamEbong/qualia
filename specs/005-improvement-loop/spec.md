# 005-improvement-loop — Protected implementation experiments and automatic decisions

## Overview and scope

Run bounded operator experiments against a fixed validation benchmark, let Qualia enforce KEEP/REVERT policy, and display reproducible before/after evidence without surrendering human methodology control.

Add experiment-history UI from 3.5 and the complete FakeBackend MVP sequence. Live two-agent parity remains the Phase 6 gate but this feature provides the operator interface and smoke-test prerequisites. Evaluation code, methodology, protected vault and frozen codebooks are never editable experiment inputs.

Governing sources: docs/01–05 and constitution v1.0.0. This is a prepared feature; main activates it in phase order and runs analyze before implementation. No implementation or acceptance pass is claimed here.

## Authoritative workstreams (verbatim from doc02)

- **3.8 Improvement loop [LB]** `qualia improve --agent claude|codex|fake [--budget N]`: snapshot → operator writes `experiments/NNNN.md` + edits mutable files → scope diff → manifest → evaluate → policy (+ confirm run) → KEEP/REVERT → `experiments` row. Methodology ideas → `experiments/proposals/`, never applied.
- **3.5 Workspace UI [LB]** data, state and keyboard logic in `web/src/lib/`, markup in components (M4); doc 04 layout; span viewer; keyboard coding (↑/↓ segment, number = code, `a`/`r` accept/reject); codebook tree; right panel (codes, suggestions, model-reported score, provenance popover); memos; retrieval; matrix with heat shading + drill-down; review queue; experiment history.

## Functional requirements

- FR-001: Provide qualia improve --agent claude|codex|fake --budget N with explicit finite nonnegative experiment count; zero budget launches no operator, invalid budget fails before mutation.
- FR-002: Require clean baseline and snapshot mutable/protected state, config hashes and validation baseline before each experiment. Never call protected evaluation or read protected test contents.
- FR-003: Implement run_operator in the existing Claude/Codex vendor files only: Claude print with Read/Edit/Write tools; Codex exec with no action tools in an empty temporary cwd, returning a strict hypothesis/edits proposal from a bounded permitted-file snapshot. Trusted Qualia code validates and applies all proposed replacements under the experiment lock. Bound process execution and preserve native subscription authentication. Owner decision04 supersedes direct Codex file editing; the failing file-tool route stays disabled.
- FR-004: Constrain candidate changes to mutable config, plus designated experiment-report/proposal outputs. Detect tracked and untracked changes, path escapes/symlinks and protected-hash mismatch; violations automatically REVERT.
- FR-005: Evaluate candidate validation predictions through the sealed evaluator without changing coding_events; compute KEEP/REVERT exclusively from protected policy, test results, budgets and measured metrics.
- FR-006: Require primary gain >=0.01, each priority-code regression <=0.02, no challenge regression, passing tests and calls <=1.2 times baseline; rerun any candidate that first qualifies and KEEP only if confirmation also qualifies.
- FR-007: On KEEP, commit the accepted candidate with a deterministic exp-NNNN-slug tag and append an experiment record containing hypothesis, changes, before/after, reason, agent, commit and tag.
- FR-008: On REVERT or operator failure, restore the project baseline safely, including unauthorized changes, remove only files newly created by that experiment and append a rejection record. Leave project Git status clean after committed experiment accounting.
- FR-009: Never apply code definition, frozen codebook, METHODOLOGY.md or protected-policy changes. Store methodology ideas only as proposals awaiting explicit approval.
- FR-010: Render experiment timeline/history, KEEP/REVERT text and fixed semantic colors, hypothesis, changed files, metrics and provenance without trusting an operator-written decision.
- FR-011: Expose experiment CLI/API summaries and reproducibility exports including both kept and reverted attempts; live external calls remain egress/budget-gated and attributable.
- FR-012: Complete the FakeBackend MVP path: demo, five keyboard codes, AI suggestions, accept/reject, a measured scripted-gain experiment and export with full event provenance.

## User scenarios

- US1: A researcher runs one fake candidate with a real measured validation gain. Policy and confirmation pass, producing KEEP, a tagged commit and a history entry with both metric sets.
- US2: An operator claims a gain but metrics regress, edits methodology or adds an out-of-scope file. Qualia rejects independently, restores the project baseline and records the reason.
- US3: A researcher opens the experiment timeline and exports a reproducibility bundle after an accepted/rejected suggestion. Every coding event and experiment resolves to its codebook/pipeline and recorded measurements.

## Success criteria

- SC-001: Exact I2 and I3 gates pass: methodology/frozen codebooks remain unchanged, metric regressions override agent claims, scope/vault violations reject, project status is clean and coding_events count is unchanged by evaluation.
- SC-002: Boundary tests cover every policy threshold, failed tests, call ratio, failed confirmation, zero baseline calls, zero budget, operator failure, path escape and untracked output.
- SC-003: A successful scripted gain creates one KEEP record, commit and exp tag; rejected attempts record their cause and preserve pre-existing project data.
- SC-004: Playwright FakeBackend MVP sequence passes end-to-end with screenshots; exported events all carry segment/codebook/actor/pipeline.
- SC-005: Experiment UI MCP screenshots verify timeline, exact KEEP/REVERT language and real before/after values; offline gates pass and Phase 6 live parity prerequisites are documented.

## Authoritative acceptance excerpts (verbatim from doc02)

- [ ] I2: fake operator edits a code definition or METHODOLOGY.md → REVERT; codebook_versions hash unchanged.
- [ ] I3: grep `qualia/core` + `qualia/eval` for sqlite3|subprocess|httpx|fastapi|os.environ → 0; fake operator claims a gain but metrics drop → REVERT; edit outside mutable scope → REVERT "scope"; vault tampered → REVERT + flag; then `git -C <project> status --porcelain` empty and coding_events count unchanged.
- [ ] MVP success test (Playwright, FakeBackend): demo → code 5 segments by keyboard → AI code → accept/reject → `qualia improve --agent fake` scripted gain → KEEP + tag → bundle export where every event has segment/codebook/actor/pipeline. Screenshots.

Quoted shared gates retain their original scope. This feature proves its relevant part; later-phase responsibilities are stated above. Common I1/I6/I7 protections remain mandatory regressions, never exemptions.

## Informed assumptions

- Mutable experiment scope is exactly project config/prompts/**, config/routing.yaml and config/segmentation.yaml. Experiment hypothesis/report and proposal artifacts are allowed outputs under experiments, not additional optimization scope.
- Require a clean project Git baseline before starting an experiment. Preserve all pre-existing files and decline to start when unrelated changes exist; do not use cleanup as an excuse to discard user work.
- Snapshot all affected project paths and protected file hashes before launching an operator. On scope violation, restore the complete unauthorized tracked/untracked change set from the snapshot so rejected methodology/codebook edits do not remain; never clean outside the project or pre-existing snapshot.
- Protected-vault tampering triggers REVERT and a tamper flag. The improvement loop must not read protected content to repair it; preserve evidence and require an explicit owner-controlled vault restoration outside the loop.
- Policy uses validation macro-F1 min_delta 0.01, priority-code tolerance 0.02, zero challenge regressions, tests pass and calls at most 1.2 times baseline. For baseline calls zero, only zero-call candidates pass unless a human changes the protected policy.
- KEEP requires a second candidate evaluation using the same fixed benchmark and policy. Both candidate and confirmation must pass; operator claims never override measured metrics or the protected policy.
- Changing segmentation config during an experiment affects only its implementation evaluation against fixed benchmark identities; it does not rewrite imported source text, stored human segments or gold labels.
- The fake operator scripts deterministic gain, regression, out-of-scope and methodology attacks for tests. Live operators use the installed unmodified subscription CLIs only; their outputs are untrusted.

## Owner-approved completion (2026-10-04)

Apply docs/answers/01-native-usage.md and 02-native-operators.md: native admission counts bounded CLI invocations; Codex uses the tested custom permission profile instead of literal workspace-write. Claude improvement uses the verified Opus alias and Codex gpt-6-astra, independently of the evaluation backend. Real path-confinement evidence is required before each vendor is activated. Native setup is owner-run; no ACL or credential workaround. The official scanner is superseded by the later owner-run Claude security review. No other invariant changes.

Later decision04 supersedes the Codex custom-profile mechanism and its activation gate above: Codex requires actual no-tools capture plus trusted application scope evidence; Claude's existing file confinement is unchanged. Supply only existing regular prompt text files and the two mutable JSON configuration files, bounded to64 files,64KiB each and128KiB total serialized input. Proposals contain at most16 replacements and128KiB combined UTF-8 content. Exact canonical inventory membership, original SHA-256 and file identity must match; refuse links/junctions/reparse points/hardlinks, hidden or credential/database/recovery filenames, unknown fields, duplicates, stale inputs and any privacy/budget changes before the first write. No new files, deletion, rename, commands or code execution. Complete dispatch text is hashed in the admitted egress record. Malformed/rejected/failed applications retain available CLI usage and REVERT through normal recovery. Actual production no-tools capture, malicious proposal tests and one public synthetic live Codex experiment are mandatory before availability is claimed.
