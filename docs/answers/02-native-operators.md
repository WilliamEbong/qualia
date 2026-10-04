# Owner decisions

2026-10-03/04: In-app user replied Yes to authorization for the official Codex security review of Qualia application source using their own ChatGPT login, with possible code disclosure to OpenAI/quota use. Research workspaces and local secrets must be excluded. This authorizes that source review only; no answer was given to sandbox setup, native runtime/accounting exceptions, or private-main push.

2026-10-04 (owner, via Claude Code planning chat):
1. Self-improvement loop: the owner wants it enabled for BOTH Claude and Codex. Approved: replace doc02's literal `-s workspace-write` operator flag with the tested native custom permission profile (`qualia-operator`) described in docs/research/agent-isolation.md §3. Database, vault, secrets, recovery files and protected methodology stay inaccessible; no fallback that exposes research paths.
2. Native Windows sandbox setup: approved. The owner runs `codex sandbox setup --elevated --current-user` personally in an Administrator PowerShell (UAC). Before activating the Codex operator, verify the setup exists and that the synthetic denied-read / allowed-write probes pass; if setup has not been run yet, finish the Claude operator first and record the Codex operator as waiting on that one owner step.
3. Claude operator: implement and verify it now (restricted mode, Read/Edit/Write only, working directory limited to what the operator may change; prove path denials with probes).
4. Private-main push: approved. The 11 local commits were pushed to origin/main by the planning session (8029a36..2799152). Keep pushing verified checkpoints to private main; the repository stays private and nothing is deployed publicly.
5. Official Codex Security scanner: drop it. Do NOT change C:\ or any drive-wide permissions. Replace it with Claude Code's `/security-review`, which the owner runs in the Claude Code improvement stage before going public. Record the scan as superseded, not as passed.
After these, finish P6.2 live parity (one live experiment each for Claude and Codex) and the remaining Phase 10 checks, then write BUILD COMPLETE only when every load-bearing check has evidence.
