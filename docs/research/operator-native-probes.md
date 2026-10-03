# Native operator confinement probe — 2026-10-03

The installed Claude Code 2.1.284 passed a no-paid native file-tool probe. An ephemeral
127.0.0.1 server supplied synthetic streamed Read/Edit/Write calls; the unmodified
CLI enforced its own permissions against temporary files. No real authentication,
research data or model service was used. Request headers were not captured.

`tests/test_operator_backends.py` exercises the production argument/settings builders:
print JSON, exactly Read/Edit/Write, restricted mode, safe mode, dontAsk, no permission
prompts, strict MCP, empty settings sources, no browser/slash commands/session
persistence, four turns maximum and an explicit temporary settings file outside
the project. The schema serializer is not used for operator output.

Observed results:

- The advertised registry contains exactly Read, Edit and Write.
- Reading permitted routing configuration, editing it, writing a new prompt, writing
  the designated new report and writing an attempt-specific proposal all succeed.
- Reads of DB, frozen-codebook-shaped file, .env, .git/config, methodology, policy,
  agent files and old report are denied. Their synthetic secret markers appear in
  neither the outbound model context nor CLI result. Automatic loading of the
  protected agent files did not disclose their markers.
- Reads of absolute outside paths, traversal paths and a sibling vault are denied.
- Writes to those protected project files, old reports, absolute outside paths and
  traversal paths leave the targets unchanged.
- Inventory rejects mutable hardlinks and Windows junctions before any CLI launch.
  A symbolic-link test is present but skipped on this host because Windows denies
  unprivileged symlink creation. The exercised junction is a native Windows reparse
  point; no claim is made that the skipped symlink test ran.

Permissions are generated from the existing project inventory: nonmutable files
get explicit Edit denies, and nonmutable files other than IMPROVEMENT.md also get
Read denies. Sensitive DB/environment/codebook-shaped files remain denied even
inside prompt directories. A report must be a new experiments/NNNN.md path. The
only writable configuration is config/prompts/** and the exact routing/segmentation
files; the proposal directory is scoped to that report number. The trusted caller
must hold its project lock and verify/restore state around the operator.

This follows [native permission semantics](https://code.claude.com/docs/en/permissions)
and the [CLI flags](https://code.claude.com/docs/en/cli-reference). Read allows alone
are not a read allowlist, and Edit rules govern Write too. The probe verifies the
actual installed behavior rather than relying only on that documentation.

## Why both live operators remain disabled

The successful probe used **three inference requests**: read actions, write actions,
then final hypothesis. HTTP retries were zero. `--max-turns 4` bounds the number of
turns, while CLAUDE_CODE_MAX_OUTPUT_TOKENS bounds each request, not the aggregate.
The current shared operator return contract provides aggregate usage and version;
it does not expose each HTTP request before dispatch for an independent egress
reservation. A single ledger row cannot honestly represent three HTTP attempts.
The owner must approve a precise accounting adaptation, or the integration must
gain native per-request admission/visibility, before activation.

Both vendor modules expose operator_available() returning false,
OPERATOR_UNAVAILABLE_REASON, and the agreed module-level run_operator signature.
Claude's bounded implementation is complete behind that gate and fixture-tested.
Codex additionally retains its unresolved native Windows profile/setup,
generation-token-cap and authentication-recovery gates. No environment variable,
constructor option or task prompt bypasses readiness.

Latest operator check: 9 passed, 1 symbolic-link skip. The proof is limited to the
tested release, paths and file-tool surface; a CLI upgrade requires re-running it.
