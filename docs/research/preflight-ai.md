# Phase 0 AI preflight evidence

Verified 2026-10-03. Synthetic inputs only; no research data, secrets, authentication files or configuration contents were read or included.

## CLI and models

- Claude Code 2.1.284 and Codex 0.160.0 help verified the command options.
- Claude official documentation lists `haiku` for efficient simple tasks; Haiku 4.5 is the lowest-priced current family. Strong alias `opus` maps to Opus 5.5 on Anthropic. Account-specific resolution remains unverified because quota prevented generation.
- Codex `gpt-6-luna` succeeded and its banner confirmed the model. `gpt-6-astra` was accepted for the successful delegation probe.
- Native CLI entrypoints were invoked through Python subprocess argument arrays, preserving empty Claude arguments. Prompts used stdin; working directories were fresh and empty. Codex schema/output files lived outside the working directory. Classification timeout: 90 seconds; delegation timeout: 120 seconds.
- No temperature/top_p/top_k, `--bare`, credential reads or permission-bypass flags were used.

Sources: [Claude model configuration](https://code.claude.com/docs/en/model-config), [Claude model comparison](https://platform.claude.com/docs/en/models/overview), [Codex subagents](https://developers.openai.com/codex/subagents).

## Synthetic classification

Schema: required `record_id` (enum `synthetic-001`) and `label` (enum `positive`, `negative`), with additional properties forbidden. Input: classify synthetic record synthetic-001, “I feel happy.”

| Invocation | Seconds | Exit | Result |
|---|---:|---:|---|
| Claude haiku, literal doc 02 flags | 3.94 | 1 | Quota error; no model usage or structured output |
| Claude exact retry | 4.06 | 1 | Same quota error |
| Codex gpt-6-luna, literal doc 02 flags | 11.58 | 0 | Valid positive classification |
| Codex gpt-6-luna, additive isolation | 4.16 | 0 | Valid positive classification; no MCP startup |

Claude response on both attempts: `You've hit your session limit · resets 6:10pm (America/Denver)`.

This is an authenticated service quota response, not missing login. No credential or local-setting repair is appropriate. Claude generation and strong-tier validation remain pending after the reset; continue independent work.

Successful Codex output:

```json
{"record_id":"synthetic-001","label":"positive"}
```

Baseline argv, with generated schema/output placeholders:

```text
claude -p --output-format json --json-schema <schema> --model haiku --max-turns 2 --no-session-persistence --tools "" --disallowedTools "mcp__*" --strict-mcp-config --setting-sources ""
codex exec -s read-only --disable shell_tool -c web_search="disabled" --ephemeral --skip-git-repo-check --output-schema <schema-file> -o <output-file> -m gpt-6-luna -c model_reasoning_effort="low" -
```

## Codex isolation finding

The literal Codex flags initialized user MCP integrations, including an n8n server that reported authentication required. Those flags alone do not establish the broader no-tools classification invariant.

Codex 0.160.0 help documents `--ignore-user-config`: skip user config while retaining authentication. Adding the following preserved subscription authentication, passed the same schema classification, and removed observed MCP startup:

```text
--ignore-user-config -c agents.enabled=false
```

These are additive restrictions; every mandated flag remains. Protected docs and user configuration were not edited. Application argv/isolation tests should cover these additions. This demonstrates an isolation improvement, not proof that every possible future CLI tool is disabled.

## Subagents inside codex exec

Result: **YES**. Selected model `gpt-6-astra`; 17.45 seconds; exit 0. A synthetic task requested exactly one child to compute 2 + 2 without tools. Read-only sandbox, shell/web disabled, ephemeral mode and fresh empty cwd were retained. Additions:

```text
--ignore-user-config -c agents.enabled=true -c agents.max_concurrent_threads_per_session=1 --json
```

Validated result:

```json
{"delegated":true,"answer":4,"reason":"One subagent calculated 2+2 without tools and returned 4."}
```

JSONL reported `collab_tool_call`, tool `wait`, progressing to `completed`. A stderr subagent-hook warning about locating the ephemeral parent transcript corroborated a child lifecycle. JSONL exposed no separate spawn event or child model field, so the evidence does not independently enumerate all child events.

A benign PowerShell shell-snapshot warning occurred with shell disabled; both isolated classification and delegation succeeded.

## Repair notes and remaining evidence

- One exact Claude retry confirmed external quota; no local repair attempted.
- Evidence-writing first attempt failed in the orchestration JavaScript parser because Markdown backticks were embedded in a raw template. No command ran and no file was changed. Replaced with a structured apply_patch call, preserving literal text. Parent session also diagnosed and fixed its encoding/here-string command issues; those are tooling issues, not application failures.
- Pending: Claude classification after reset, Claude strong tier, and application-level isolation/egress/budget/provenance tests.

## Resume evidence — 2026-10-04

Installed versions remain Codex0.160.0 and Claude2.1.284; safe status checks confirm own ChatGPT and first-party claude.ai subscription sign-in. Normal public-router `tests/live/test_classification.py -k gpt-6-astra -m live` passed1 test in12.25s, one synthetic record and one admitted invocation. This closes the missing strong Codex classification check. Prior Haiku/Luna and no-action-tool evidence is retained. Operator tests are separate and must not be inferred from classification success.
