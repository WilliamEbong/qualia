# Agent isolation audit — Phase 3 and Phase 5

**Latest status:** section 6 supersedes the preliminary native Windows profile recommendation; native enforcement remains unproved and setup is blocked by automatic approval review.

Audited 2026-10-03 against installed Codex 0.160.0, Claude Code 2.1.284, docs01/02, specs003/005, `qualia/ai/protocol.py`, `qualia/workspace.py`, and Store. This report changes no source contract or application code. No paid/model-service calls were made. Temporary localhost mock Responses requests used a fresh synthetic CODEX_HOME without credentials; they are not subscription-authentication tests.

## Decisions for the main lane

- Continue rules/fake classification, ledger/review/cache, evaluation, fake improvement, and independent work. External readiness must be separate from executable/auth availability.
- Codex classification can retain doc02's `-s read-only` and achieve an empty advertised tool surface using the supported per-run model catalog plus additive switches below. The localhost capture proves the candidate for installed 0.160.0 and gpt-6-luna; repeat for each enabled model/version and the production argv builder. Do not treat flags alone as proof.
- Codex operator confinement requires replacing doc02's literal `-s workspace-write` with the native granular permission profile below. This is an explicit runbook/argv acceptance adaptation for the main lane to resolve, not a silent source-doc edit. Parsing passed; native Windows enforcement has not passed in this nested sandbox. Keep the real operator unavailable until enforcement probes pass.
- Claude's existing no-tools classification remains viable. Its native `--restricted` mode plus Read/Edit/Write allowlisting offers a concrete operator alternative, also needing path-denial probes. Do not enable a real operator merely because its classifier works.
- Codex exec exposes no configurable provider-generation token cap in its installed help/schema. Bounded process time, response bytes, schema sizes and batches are enforceable, but they do not prove the doc01 generation-token bound. Preserve this as a precise unresolved requirement, not a fabricated `max_tokens` setting.

## 1. What stock Codex actually exposes

`exec --help` supports `--ignore-user-config`, `--strict-config`, `--ephemeral`, stdin `-`, output schema and output file. `--ignore-user-config` expressly retains CODEX_HOME for authentication. Neither help nor the version-pinned schema exposes a global tools-none switch or max_output_tokens. `tools.update_plan.enabled` and `tools.experimental_request_user_input.enabled` are real settings. `model_catalog_json` is a startup-loaded catalog override; `tool_output_token_limit` is not a generation cap. [0.160.0 config schema](https://raw.githubusercontent.com/openai/codex/rust-v0.160.0/codex-rs/core/config.schema.json), [exec CLI source](https://raw.githubusercontent.com/openai/codex/rust-v0.160.0/codex-rs/exec/src/cli.rs).

The source registers apply_patch from model metadata independently of shell_tool; clock and asynchronous user input can also come from model metadata. ToolPolicy exists internally but no deny-all selector was found in exec's public arguments/config. Model tool_mode takes precedence over code-mode feature flags. Thus read-only limits effects but is not tools-off. [Tool registration](https://raw.githubusercontent.com/openai/codex/rust-v0.160.0/codex-rs/core/src/tools/spec_plan.rs), [tool-mode selection](https://raw.githubusercontent.com/openai/codex/rust-v0.160.0/codex-rs/core/src/tools/mod.rs).

Safe inspection of local catalog selected fields found both gpt-6-luna and gpt-6-astra advertise freeform apply_patch, unified_exec shell type, experimental send_user_message_async/clock and code_mode_only. No auth file or user-config values were printed.

### Actual no-paid request capture

Stock installed native CLI sent synthetic prompts to an ephemeral 127.0.0.1 HTTP server. The server recorded only request shape/tool names, then intentionally returned HTTP400 to stop. Exit1 was expected; no model inference occurred. Config used a temporary provider with `wire_api="responses"`, `requires_openai_auth=false`, retries0 and request compression disabled. No provider/auth override from this probe belongs in production.

| Variant | Actual advertised names inside input[type=additional_tools].tools |
|---|---|
| Shell/search off, ignore user config, agents disabled | functions.exec, functions.wait, functions.request_user_input_async, clock.sleep |
| Full additive disables below, original catalog | functions.exec, functions.wait, functions.request_user_input_async |
| Full disables plus restricted catalog below | Empty list |

**The current wire format carries tools in an `additional_tools` input item. Checking only top-level `tools` falsely passes all three variants.** Nested code-mode instructions may describe further tools; the empty-list variant avoids that ambiguity. These captures use a synthetic provider; they do not prove subscription auth, managed-config behavior or future CLI versions.

### Candidate classification recipe

Invoke with an argv array; quoted TOML strings below represent one argument value, not shell syntax. Preserve every mandated classification flag:

```text
codex exec --ignore-user-config --strict-config -s read-only
  --disable shell_tool -c web_search="disabled"
  --ephemeral --skip-git-repo-check
  --output-schema <absolute-schema> -o <absolute-result>
  -m <verified-model> -c model_reasoning_effort="low"
  -c agents.enabled=false
  -c tools.update_plan.enabled=false
  -c tools.experimental_request_user_input.enabled=false
  -c project_doc_max_bytes=0
  -c model_catalog_json="<absolute-temporary-catalog>"
  -
```

Also append `--disable <name>` for each of: apps, plugins, browser_use, browser_use_external, browser_use_full_cdp_access, computer_use, in_app_browser, image_generation, view_image, multi_agent, multi_agent_v2, code_mode, code_mode_only, code_mode_host, hooks, goals, memories, sleep_tool, tool_suggest, skill_search, workspace_dependencies, request_permissions_tool, send_message_to_user_async. All were recognized by 0.160.0. `enable_request_compression=false` was only needed to inspect mock HTTP bodies.

Build a private temporary catalog `{ "models": [<selected-current-model-record>] }`; retain the genuine model identity, model instructions and remaining capabilities, changing only:

```json
{
  "apply_patch_tool_type": null,
  "experimental_supported_tools": [],
  "shell_type": "disabled",
  "tool_mode": "direct",
  "supports_search_tool": false
}
```

These fields/types exist in [0.160.0 model metadata](https://raw.githubusercontent.com/openai/codex/rust-v0.160.0/codex-rs/protocol/src/openai_models.rs). This is a documented configuration input, not a patched CLI. Do not mutate global cache/config or invent a model record. Fail closed on missing catalog/model, changed CLI version, failed strict config, or nonempty tool-registry capture. Keep auth home at its real default in production; never copy credentials into the temporary cwd. Do not erase CODEX_HOME to achieve isolation. Preserve an explicitly configured credential-store selection if necessary without displaying any credential contents.

Before any live activation, production-builder tests must cover both configured cheap/strong models, all request tool locations, inherited integrations, unknown CLI versions, and empty cwd. A malicious synthetic response calling a nonexistent function must be rejected without dispatch. Any managed integration that remains available fails the readiness gate. Never redirect real subscription requests to the mock server.

## 2. Bounds, retries and Windows execution

Use bounded stdin payloads, a monotonic process deadline, bounded concurrent pipe readers and an output-file size ceiling. Count UTF-8 bytes and schema collection/string limits; do not pretend bytes equal model tokens. On limit/timeout terminate the exact child process tree and reject its result. Do not collect unbounded stdout/stderr with capture_output in production. Runtime usage must retain observed totals even when output fails validation.

Claude supports `CLAUDE_CODE_MAX_OUTPUT_TOKENS`; use the configured ceiling, plus its max-turns limit, output-size/deadline checks. Its env reference also documents internal retries and structured-output retries. Use CLAUDE_CODE_MAX_RETRIES=0, clear CLAUDE_CODE_RETRY_WATCHDOG, and use MAX_STRUCTURED_OUTPUT_RETRIES=1 (the documented value counts attempts, including the first); verify one-request-per-dispatch behavior, or explicitly model/observe additional attempts; do not count a multi-request CLI process as one network request. [Claude environment variables](https://code.claude.com/docs/en/env-vars). For Codex, verify provider request_max_retries/stream_max_retries=0 with the request-capture test. A pre-dispatch usage reservation must precede every application retry. A prompt request to be brief is not a token cap.

The installed `codex` command resolves to codex.ps1, which Python shell=False cannot invoke as an executable. Use verified node.exe plus the official `@openai/codex/bin/codex.js` wrapper (which supplies vendor PATH), or the verified installed native codex.exe. Current native location is `%APPDATA%/npm/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe`. Claude's npm shim targets `%APPDATA%/npm/node_modules/@anthropic-ai/claude-code/bin/claude.exe`. Discover/validate these paths, not hardcode this user's home. Pass stdin and an argv list with shell=False. No transcript, key or complete environment belongs in logs. Remove inherited API-key/provider override variables for subscription-only classification without printing them; preserve normal CLI login stores and OS runtime paths.

## 3. Concrete operator permission alternatives

### Codex native profile — proposed runbook adaptation

The documented native profile parser supports exact path read/write/deny entries. `-s`/sandbox_mode takes precedence over default_permissions; do not pass both. Native Windows elevated enforcement is stronger; unsupported unelevated carveouts must fail rather than degrade. Network sandboxing covers sandboxed commands, not every independent CLI integration. [Codex permissions](https://developers.openai.com/codex/permissions/).

This exact profile shape passed installed `exec --strict-config` and the CLI printed `sandbox: custom permissions` before sending the synthetic localhost request. That proves parsing/selection, not OS enforcement. Render concrete resolved absolute paths where indicated and a unique exact report/proposal directory per attempt:

```toml
default_permissions = "qualia-operator"

[permissions.qualia-operator.filesystem]
":root" = "deny"
":minimal" = "read"
":tmpdir" = "deny"
":slash_tmp" = "deny"

[permissions.qualia-operator.filesystem.":workspace_roots"]
"." = "read"
"config/prompts" = "write"
"config/routing.yaml" = "write"
"config/segmentation.yaml" = "write"
"experiments/0001.md" = "write"
"experiments/proposals/0001" = "write"
"project.db" = "deny"
"project.db-wal" = "deny"
"project.db-shm" = "deny"
".git" = "deny"
".env" = "deny"

[permissions.qualia-operator.network]
enabled = false
```

Also deny each discovered secret/DB backup path, the absolute vault, trusted snapshot directory and auth home explicitly. Root deny provides the outside-project baseline; explicit entries make regression intent testable. Reject symlinks/junctions/reparse points and hard-linked mutable files before launch. Do not use unbounded glob expansion as the sole secret protection. Do not give write access to all experiments, the project root, arbitrary temp paths or auth home. Precreate only required report/proposal paths through the trusted orchestrator.

Selection argv: `codex exec --ignore-user-config --strict-config --ephemeral -c approval_policy="never" -c default_permissions="qualia-operator" ... -`. Supply each profile leaf as a `-c key=value` argument, using an actual TOML serializer for path keys/inline tables. Set cwd to the project; leave `-s`, sandbox_mode, --approve-for-me and bypass flags absent. Retain external-integration disables from classification; allow only the needed native editing mechanism and remove model metadata tools that would expose other capabilities. The exact available operator tool list needs its own fixture capture. The official --ignore-user-config auth behavior remains applicable; no custom authentication wrapper is needed.

This changes only doc02's literal operator sandbox argument and corresponding argv tests. It does not change the filesystem/methodology/benchmark invariants. Do not fake compliance by keeping `-s workspace-write` alongside the profile, or by writing custom Windows ACL changes around the CLI. No additional wrapper framework is recommended.

No-paid enforcement command shape is `codex sandbox -P qualia-operator -C <synthetic-project> -- <verified-python.exe> <synthetic-probe.py>`, with the same generated profile in a temporary CODEX_HOME and no real data. The installed Windows `sandbox --help` confirms -P and -C. Test writes to the three mutable locations/report; reads of allowed sanitized context; refusal of database, sibling vault, auth-shaped sentinel and backup reads; refusal of protected-file, .git, sibling and existing-report writes; and refused command network. A nested sandbox probe earlier failed CreateRestrictedToken with error87 before a target ran, so it supplies no enforcement evidence. Run the exact fixture at the host boundary through scoped tooling; if native enforcement cannot represent it, leave Codex operator disabled and report the concrete failure. Parsing and simulated mocks cannot certify Windows enforcement.

### Claude built-in restricted file tools

Candidate additive argv, preserving print mode and subscription login:

```text
claude -p --tools Read,Edit,Write --restricted
  --permission-mode dontAsk --permission-prompts none
  --strict-mcp-config --setting-sources ""
  --disallowedTools mcp__* --no-chrome --disable-slash-commands
  --no-session-persistence --max-turns <finite-limit>
  --settings <trusted-generated-settings-json>
```

The installed help and [Claude CLI reference](https://code.claude.com/docs/en/cli-reference) confirm restricted mode confines file tools to working directories, ignores ordinary settings, still accepts explicit settings and does not use bare's auth removal. Use no --add-dir. The prompt supplies trusted IMPROVEMENT.md and sanitized codebook/dev evidence. Explicit settings live outside the operator's cwd; do not write or weaken the build project's hook files. Optional --safe-mode disables customizations while retaining authentication; prove the final combination rather than assume it removes all builtin capabilities.

Use generated permissions with scoped Edit allows for `config/prompts/**`, exactly routing.yaml/segmentation.yaml, exactly the new report and attempt proposal directory. Use explicit Read denies for every project.db/sidecar/backup, .git and secret path; also explicit Edit denies for protected files. CLI relative patterns resolve against cwd; `/...` rules in a settings file resolve against that file's directory, so avoid that ambiguous anchor here. A representative settings fragment is:

```json
{
  "permissions": {
    "allow": [
      "Edit(./config/prompts/**)",
      "Edit(./config/routing.yaml)",
      "Edit(./config/segmentation.yaml)",
      "Edit(./experiments/0001.md)",
      "Edit(./experiments/proposals/0001/**)"
    ],
    "deny": [
      "Read(./project.db*)", "Read(./.git/**)", "Read(./.env*)",
      "Edit(./METHODOLOGY.md)", "Edit(./IMPROVEMENT.md)",
      "Edit(./AGENTS.md)", "Edit(./CLAUDE.md)", "Edit(./improvement.yaml)"
    ]
  }
}
```

Read allows are not a read allowlist: dontAsk still permits otherwise automatic in-workspace reads. Edit(path) governs Write as well; Write(path) rules are ignored. Denies take priority and check symlink/junction targets. Restricted mode supplies the outside-cwd boundary; explicit denies cover sensitive in-project files. [Claude permission semantics](https://code.claude.com/docs/en/permissions).

Run actual tools against only synthetic sentinels: successful config/report edits; denied DB/vault/auth/backup reads; denied methodology/old-report/.git edits; denied path traversal, junction and absolute outside-path reads. A model saying it complied is not evidence; assert sentinel content never appears in response/transcript and denied targets remain unchanged. No implementation may fall back to unrestricted mode if flags/settings fail.

## 4. Snapshot and rollback that covers the actual workspace

Current foundation facts: project Git ignores `*.db*` and `.env*`; frozen codebooks, human coding and mutable code definitions are inside ignored project.db. Git status cannot see these changes. Store's append-only triggers do not protect against an operator that can rewrite the DB or drop triggers. `check_manifest` trusts the current manifest file, so an attacker able to replace both protected content and manifest can redefine that baseline. Pin the manifest independently before launch. Never call write_manifest during an experiment to bless changes.

Recommended sequence within the existing experiment orchestrator and Store, without another framework:

1. Acquire one project operation lock for snapshot through decision/restore. Refuse dirty Git, inconsistent manifest, unresolved recovery marker or nonregular mutable paths. Block concurrent UI/import/review writes; otherwise rollback could erase legitimate new human work. Pin HEAD, protected policy, manifest bytes/hash, codebook snapshot identity and research-table digests. Include full coding_events content/hash, not only row count.
2. Inventory all project paths, including ignored files and file kinds, without following reparse points. Snapshot the pre-existing regular files needed for recovery to a trusted location outside the operator's readable/writable roots. Include protected files, allowed configs, existing reports and Git metadata. Preserve ignored data and secrets without logging or committing them. The vault is excluded from optimizer context and recovery payloads; only the trusted verifier compares its opaque manifest hashes.
3. Record/reserve operator egress through the ledger before dispatch, then create a consistent SQLite backup through Store using sqlite3.Connection.backup. This accounts for WAL contents. Close/quiesce all application handles before operator launch; prevent trusted DB mutations during its execution. Do not copy only the live database file and ignore its WAL. [Python SQLite backup](https://docs.python.org/3.14/library/sqlite3.html#sqlite3.Connection.backup).
4. Launch the confined operator with only sanitized context. Freeze egress/budget/security ceilings from protected baseline policy outside the mutable routing config. A candidate cannot turn external access on, raise spending limits, name arbitrary executables/providers, read a vault path or change the benchmark. Candidate segmentation must never rewrite human source segments or gold labels.
5. Fully stop the child/process tree, then compare inventory, protected bytes, pinned manifest, Git metadata and database logical contents/schema to the independent baseline. Allow only the named mutable files and designated new report/proposal artifacts. Existing experiment reports remain immutable. Detect deletions, ignored changes, manifest replacement, code-definition/frozen-version edits and same-count coding-event substitution. Do this before trusting candidate reports or evaluating.
6. On any operator violation/error, restore project files and DB through trusted Store/orchestrator code. Restore from the independent DB backup with all handles closed; handle stale WAL/SHM as part of that controlled restore and recheck integrity/schema/research digests. Never unlink or replace a database while another connection uses it. [SQLite corruption cautions](https://www.sqlite.org/howtocorrupt.html). Remove only paths proven newly created by this experiment within the resolved project root. Do not use global git clean -fdx or lose pre-existing ignored files. Recover Git metadata if it changed, but OS/tool confinement should prohibit that first.
7. After trust is restored, append actual usage/error accounting via ledger, evaluate only the fixed validation benchmark, apply protected thresholds and confirmation, and record the decision. On KEEP commit only accepted config plus the trusted experiment report, create the tag, and append the experiment row. On REVERT restore config and commit a trusted rejection report so status is clean. Do not commit rejected operator text verbatim as trusted accounting. Do not erase egress evidence during restoration.
8. Maintain a small durable attempt/recovery record outside operator access. A crash between snapshot, process termination, restore, Git commit/tag and DB accounting must resume to one consistent decision; interrupted attempts default to REVERT. Report KEEP only after commit/tag/row agree. This is a journal for existing steps, not a new orchestration framework.

For vault tampering: REVERT + tamper flag, stop subsequent improvements and preserve evidence. Do not silently reconstruct or rebaseline the vault inside improve. Project status can still be clean because vault is outside the project; that must never hide the tamper flag. The protected-split wording and existing manifest hashing need one explicit interpretation: the trusted verifier may hash opaque bytes, while only evaluate --protected parses/evaluates protected examples. If “only reads” is literal even for hashing, the runbook's own manifest check conflicts; main should record that narrow interpretation rather than expose holdout text to the optimizer.

## 5. Required proving tests

| Proof | Minimum assertion |
|---|---|
| Tool surface | Every configured model/version with production argv has empty top-level and additional_tools tool lists; unknown function response never dispatches. |
| Authentication | Same installed subscription login works without copying tokens, --bare, API-key substitution or global configuration edits. Synthetic mock does not claim this. |
| Bounds and attempts | Oversize input/output, hanging child/descendant, malformed JSON and internal/application retries stay bounded; no unreserved provider call; failed result retains ledger evidence. |
| Windows invocation | Space/non-ASCII paths and quotes in transcript work through argv/stdin without .cmd/.ps1 shell interpolation. |
| Real confinement | Native denied reads/writes above fail; legal config/report edits succeed; vault sentinel never reaches output. No fallback on unsupported policy. |
| Ignored DB attack | Fake operator changes code definition, drops trigger, replaces frozen record or alters coding event while retaining count: REVERT, identical restored research digest. |
| Filesystem attack | Methodology/delete/new outside-scope/old report/ignored file/.git/manifest/path-escape/link attacks reject; pre-existing ignored files survive. |
| Vault attack | Replaced vault data plus forged manifest still fails the pinned baseline; no write_manifest repair; tamper flag persists. |
| Policy integrity | Mutable routing cannot raise egress/spend ceilings; fake claimed gain loses to measured regression; all thresholds/confirmation tested. |
| Recovery/accounting | Inject interruption at each boundary; one decision/tag/row, no lost egress row, no lost human event, clean final Git status. |

The stricter production isolation controls are additive for classification and Claude's file-only operator. Codex granular operator permissions replace a literal runbook flag, and an enforced Codex generation-token ceiling remains unavailable in the inspected public CLI configuration. These are the concrete unresolved items; they do not block the offline feature implementation or fixture-based gates.

### Host-boundary native Windows probe result

After the nested error87, repeated a narrow probe through scoped host execution using only new synthetic files, no credentials and no network/model call. Exact command shape: native `codex.exe sandbox -P qualia-operator -C <temp-project> -- C:/Python314/python.exe -c <sentinel-probe>`, temporary CODEX_HOME config with `windows.sandbox="unelevated"`, root deny/minimal read/project read/routing write/DB deny. Result: exit1, empty stdout, target never started, and:

```text
windows sandbox failed: Restricted read-only access requires the elevated Windows sandbox backend
```

This is a verified fail-closed refusal, not a successful denied-read/allowed-edit test. The concrete next prerequisite is the CLI's built-in elevated Windows sandbox setup and the same sentinel probe under `windows.sandbox="elevated"`; this audit did not install or alter sandbox users, ACLs, firewall or credentials. Keep native operator readiness false until those probes pass. The configuration must still omit -s so the granular profile applies.

## 6. Follow-up: native elevated setup and generation bounds

**This section supersedes the root-deny native Windows candidate in section 3.** The root-deny profile parses, but installed 0.160.0 does not enforce that shape on native Windows, even with elevated selected. Actual pre-dispatch error:

```text
elevated Windows sandbox requires effective `:root` read access
```

The version-pinned [Windows permission resolver](https://raw.githubusercontent.com/openai/codex/rust-v0.160.0/codex-rs/windows-sandbox-rs/src/resolved_permissions.rs) contains this explicit validation. A native candidate must retain root read and use explicit read-deny paths for vault, snapshot, database, authentication and other sensitive locations; it cannot claim filesystem-wide read allowlisting. If that scope is insufficient, leave Codex operator unavailable. Do not silently weaken the protected-vault or methodology requirements.

### Actual host evidence

| Probe | Result |
|---|---|
| OS version | Windows 10 Home 10.0.19045; official support is best effort, not the preferred Windows 11 baseline. |
| Host tool Windows administrator token | False, even when the execution tool runs outside its own sandbox. Tool escalation and Windows UAC elevation are distinct. |
| Existing native setup | .sandbox/setup_marker.json exists; desktop commands use helper 0.159.2, whereas audited npm CLI is 0.160.0. Marker presence alone does not certify the newer CLI's granular policy. |
| Elevated root-deny/minimal-read fixture | Exit1 before target execution: effective root read required. Synthetic DB/methodology unchanged. |
| Elevated root-read + home-deny + project/config exceptions fixture | Reached npm setup refresh, then exceeded 40-second deadline without sentinel target output. This is not evidence of either read denial or successful setup. |
| Cleanup | Identified orphan setup helper by npm executable path, parent PID and probe time; stopped only that helper. Left the desktop's independent command runner untouched. |
| Native setup help | `codex sandbox setup --help` confirms --elevated, --current-user, --user, --codex-home. Help is surfaced with an Error prefix but contains the actual parser options. |
| Attempted native setup | Automatic approval review rejected `codex sandbox setup --elevated --current-user` before execution because it changes persistent sandbox accounts/ACL security and requires explicit authorization for that system-level action. No alternate route was attempted. |

The narrower probe used a temporary synthetic project and vault; no protected research contents, auth secrets or model service were accessed. Its broad user-home deny was not proven operational. An eventual retry should begin with exact synthetic vault/DB/snapshot denies and widen the protected-path set only while preserving passing sentinel probes. Read-deny rules must cover the entire real vault, every trusted recovery artifact and every confidential project file before runtime readiness. Do not activate a partial deny list.

### Concrete native setup prerequisite

The built-in setup is the only proposed host change. Official guidance describes administrator-approved sandbox users, filesystem permissions, firewall and logon-right setup. Existing enterprise restrictions can prevent it. [Windows sandbox setup and troubleshooting](https://developers.openai.com/codex/windows/).

Once the owner explicitly approves this persistent native setup, the owner can:

1. Open PowerShell as Administrator under the Owner account and approve Windows UAC.
2. Run `codex --version` and confirm the npm CLI 0.160.0, then `codex sandbox setup --elevated --current-user`.
3. If the elevated shell belongs to a different administrator account, target Owner explicitly instead: `codex sandbox setup --elevated --user "$env:COMPUTERNAME\Owner" --codex-home "C:\Users\Owner\.codex"`.
4. Keep the completion/error text, without sharing .sandbox-secrets contents. A successful setup reports completion and persists only its windows.sandbox selection through Codex's config editor. Then rerun the isolated sentinel tests before enabling an operator.

These exact arguments and persistence behavior come from the [0.160.0 setup command](https://raw.githubusercontent.com/openai/codex/rust-v0.160.0/codex-rs/cli/src/sandbox_setup.rs). Its [provisioning implementation](https://raw.githubusercontent.com/openai/codex/rust-v0.160.0/codex-rs/windows-sandbox-rs/src/setup.rs) explicitly requires an elevated process for this command; launching it from an ordinary host shell does not automatically supply Windows administrator rights. No manual ACL, firewall, user/group or authentication edits are recommended. Do not use unelevated fallback for the operator because its required restricted reads already failed.

This is a genuine owner/setup gate: automatic approval review rejected the action, and unattended tool escalation does not grant Windows administrator rights. The required approval is for the native persistent sandbox setup, not for the application implementation. All offline tasks continue.

### Generation-token cap: source-level conclusion

The installed CLI help, version-pinned config schema, genuine model metadata and actual localhost HTTP capture expose no max_output_tokens generation cap. The [0.160.0 Responses request types](https://raw.githubusercontent.com/openai/codex/rust-v0.160.0/codex-rs/codex-api/src/common.rs) confirm that neither HTTP ResponsesApiRequest nor WebSocket ResponseCreateWsRequest contains that field. This is stronger evidence than old issue comments or similarly named tool-output settings.

| Mechanism | What can be claimed |
|---|---|
| Prompt brevity / model_verbosity | Guidance only; not a hard bound. |
| Bounded JSON schema, accepted output bytes, parser limits | Bounds accepted application data, not hidden reasoning or generated tokens. |
| stdout/stderr/file ceiling and child-tree timeout | Bounds local resource exposure and elapsed work; cancellation is not a guaranteed provider token/billing ceiling. |
| tool_output_token_limit / shell max_output_tokens | Tool-result truncation, irrelevant to tools-off classification generation. |
| Model context-window metadata | Context sizing, not a documented output-generation cap. Do not falsify it. |
| Native Codex provider max_tokens setting | No verified public setting in 0.160.0; do not invent one or rely on ignored config keys. |

Do not introduce an API-key backend, intercept subscription traffic, patch the CLI or add a request-rewriting proxy to manufacture a cap: those change the locked architecture. Two honest gate choices remain: (A) leave live Codex classification/operator disabled until the native CLI supports the required cap, while fake/rules/Claude implementation continues; or (B) explicitly approve a Codex-only requirement adaptation accepting finite batch/input/output/deadline/call-budget controls instead of a guaranteed provider-generation token ceiling. Option B changes the bounded-max_tokens requirement and must be recorded as such; it does not make token usage fixed or pre-known. The no-tools requirement is independent and must still pass its real wire-format fixture.

### Concrete outstanding gate items

- **G1 — host setup:** approval for the native persistent elevated sandbox setup, administrator execution, then actual allowed-edit/denied-read/denied-write sentinel evidence. Current state: blocked by auto-review; no passing native enforcement claim.
- **G2 — operator argv:** replace literal `-s workspace-write` with the supported custom permission profile (no -s), proven for the installed Windows backend. Current state: contract adaptation needed; profile parsing alone passed.
- **G3 — native read scope:** explicit deny protection rather than unsupported root-deny allowlisting; no protected split, recovery snapshot, DB or credentials may be exposed. Current state: narrower native profile not yet proven.
- **G4 — generation bound:** retain native max_tokens invariant and disable live Codex, or explicitly accept the bounded-local-runtime alternative above. Current state: native provider-token cap absent in verified 0.160.0.
