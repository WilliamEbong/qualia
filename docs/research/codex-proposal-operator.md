# Proposed Codex improvement mechanism

2026-10-04. Status: owner-approved design (decision04); implementation in progress, not yet enabled. The installed and current stable official CLI are both 0.160.0. Existing native no-action-tool localhost probes passed 4 tests in 10.78s for the current classifier transport; these are foundation evidence, not a completed proposal-operator test.

## User experience

The researcher still selects Codex for an automatic improvement experiment using their own signed-in official CLI subscription. No API key, container, additional account or Windows permission change is required. Qualia proposes, measures and records each experiment automatically; this is not a request to manually approve every edit.

## Exact proposed change

1. Qualia snapshots the project under its existing operation lock and admits one operator invocation through the usage/egress ledger, hashing the complete supplied dispatch text including permitted file contents.
2. Trusted code supplies a bounded snapshot of permitted prompt/configuration files to the existing audited Codex CLI with no action tools, a fresh empty working directory, native ChatGPT sign-in, strict output schema and existing time/byte limits. Database, vault, credentials, benchmark labels, recovery artifacts and protected methodology files are not provided.
3. Codex returns JSON containing a hypothesis and a bounded list of edits. It cannot browse, read arbitrary paths, run commands or apply patches itself. The Windows file-tool path that failed testing stays disabled.
4. Qualia treats every proposed edit as untrusted. It checks exact allowlisted paths, original-content hashes, regular-file/no-link identity, permitted file types, size limits, duplicate paths, configuration schema and unchanged privacy/budget bounds. Reject the complete proposal before applying anything if any item fails. Do not execute model-supplied commands or code.
5. Trusted application code writes only validated replacement text to permitted implementation files, generates the experiment report, then invokes the existing scope/manifest checks, tests, evaluation, confirmation and KEEP/REVERT logic. Protected data and human methodology remain unchanged. Failures retain available usage and trigger normal restoration.

The default operator model remains gpt-6-astra. Classifier selection stays separate. Repeated experiments remain bounded by existing run/daily invocation budgets; there is no new autonomous tool loop or hidden application retry.

## Required verification before activation

- Actual native wire capture of the production proposal builder has no action tools for each supported model/version; unexpected tool events fail.
- Strict output parsing rejects malformed JSON, unknown fields, excessive edits/content and missing usage.
- Adversarial proposals cannot escape the exact input file list, traverse directories, use absolute/UNC/drive/ADS paths, target links, change stale files, alter budgets or touch protected paths; rejection leaves files unchanged.
- Existing database/methodology/vault/snapshot/rollback/KEEP/REVERT tests continue to pass.
- Public normal-path synthetic Codex experiment records one operator invocation plus bounded evaluation calls, unchanged research provenance and a clean final project tree.
- Independent review, full offline regression and updated user guide before enabling or claiming parity.

## Recorded owner decision

The owner approved replacing only Codex's direct file-editing operator mechanism (including the previously approved native custom permission profile) with the no-action-tools proposal and trusted-application mechanism described above; see decision04. The original runbook requires an operator running inside the project and writing mutable files; this approval changes those mechanics. It preserves own-subscription use, vendor isolation, immutable provenance, methodology protection, explicit egress/budget admission and Qualia-owned KEEP/REVERT. Claude's verified operator is unchanged. Protected source docs are not edited.

This is an alternative implementation, not a claim that Codex0.160.0's native read/network failures were repaired. Do not activate that failing tool path as a fallback.

## Sources

- [Official non-interactive execution and structured output](https://learn.chatgpt.com/docs/non-interactive-mode): --output-schema, JSONL events and native authentication.
- Existing version-pinned source and actual failure evidence: [agent isolation audit](agent-isolation.md#7-resume-evidence--native-windows-enforcement-2026-10-04).
- Existing privacy, budgets and experiment contracts: docs01/02, specs005 and docs/answers/01-native-usage.md.
