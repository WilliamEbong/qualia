# Improvement round and CLI version floor — 2026-10-06

The owner asked how Qualia supports codes, codebooks, inductive/deductive coding, cases, memos, themes and reflexivity, then wrote:

> come up with an improvement plan including the code book stuff, use spec kit and ponytail, update readme and user guide and anything else needed. Then look for issues, inefficiencies, fixes, improvements. Update demo if necessary, or leave it if not, I'll leave the judgement calls to you, build autonomously, dont return to me until done, research instead of guess, I'm going to bed, commit and push when done, then write a summary of what you did and why

During the run the owner added:

> remove the exact-version allowlist for the Claude Code and Codex CLIs ... Replace it with a minimum-version floor only, set to the currently audited versions ... A newer or unknown version must never block ... Record the detected CLI version in each suggestion's provenance or egress record ... Keep the runtime safeguards ... If a newer CLI rejects a flag Qualia passes, fail with a plain error that names the flag

> also loop codex astra into this build ... you have explicit permission to do the necessary things needs to complete this build within reason, use your judgement

Decisions taken under these instructions:

- Feature 014 codebook proposals and feature 015 inductive and reflexive workflow were specified with Spec Kit (`specs/014-*`, `specs/015-*`). Proposals are records awaiting a human decision; acceptance changes only the draft codebook (constitution II unchanged).
- The exact CLI version match is replaced by a minimum floor (Claude Code 2.1.284, Codex 0.160.0). This supersedes the "audited version" wording in decisions 01, 02 and 04 for version checks only; every other safeguard in those decisions (no action tools, empty working folder, schema validation, limits, subscription sign-in, `allow_external`) stays. The detected version is recorded on each suggestion and usage row.
- Codex (gpt-6-astra) implemented the version-floor lane in the backend files and their tests; the main session reviewed it, moved shared helpers into `process.py`, added router messages, and made every commit.

Follow-up (2026-10-07): offered the three optional owner actions (release, security review, Dependabot), the owner replied "Decide for me". Decisions and outcomes:

- **Security review first:** a checklist review of the server, AI and store surfaces (Host/Origin/token checks, parameterized SQL, React escaping, error messages, secrets, CSP, AI output paths) found no new issues; together with the independent Codex review (findings fixed in 9f7f647) this covers the round. The built-in Claude Code `/security-review` command is user-triggered and remains available to the owner.
- **Dependabot:** after a first-hand review of each diff and its green checks, merged #8 (configure-pages 6), #3 (checkout 7), #2 (setup-uv 7), #6 (gitleaks-action 3), #1 (setup-node 7) and #5 (vitest 5, dev only; tests, build and audit green). #4 (uv_build upper bound <0.13) stays open: its only checks predate the gitleaks permission fix and Dependabot had not rebased it, so a build-backend change would merge untested.
- **Release:** version 0.2.0 (new features and database migrations) tagged after green CI; the release workflow published "Qualia v0.2.0" with Qualia-v0.2.0.zip and the notes list what is new.
