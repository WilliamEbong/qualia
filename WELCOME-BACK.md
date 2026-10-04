# Qualia — build in progress

Last session ended at2799152 after Jev activation. This recovery applied docs/answers/02-native-operators.md, completed the Claude operator, and verified the remaining strong Codex classifier. All owner approvals are recorded; Windows setup is present. No repeat setup or approval is needed.

Claude Opus5.5 improvement is enabled: actual restricted-tool probes passed, followed by one successful synthetic live experiment using Haiku validation. Macro-F1 stayed1.0→1.0, so Qualia correctly chose REVERT. Three invocations were recorded, methodology/codebook/coding unchanged, project Git clean. Two earlier scoped failures remain in synthetic audit ledgers. Native classification is independently verified for Claude Haiku and Codex Luna/Astra. Jev remains enabled for demo at the existing $1 daily local limit.

Codex file-editing improvement remains disabled. Actual Codex0.160.0 native Windows probes read outside files while verifying patches and allowed loopback despite network denial. The failure persists even with patch-only tools. See docs/research/agent-isolation.md section7 and ignored OWNER-NEEDED.md. No private research, secrets or system-permission changes were used to test this. P6.2/P10 remain incomplete; do not mark BUILD COMPLETE or bypass readiness.

Verification:445 offline Python tests passed,5 capability skips,6 live tests deselected; Ruff/data/protected-file/whitespace checks pass. Existing30 frontend tests and browser/design evidence remain applicable because this resume changed no frontend. The illustrated docs/USER-GUIDE.md includes Claude improvement steps and the remaining Codex limitation. Official Codex Security scanner was superseded, not passed; the owner plans Claude Code /security-review before public release.

Private main was verified at2799152 with green Checks; continued verified private pushes are approved. Current checkpoint CI is recorded in BUILD-STATE. Repository remains private; public deployment is not authorized.

Run `uv run qualia open` for the local app. For a prepared, explicitly egress-enabled study: `uv run qualia improve --project my-study --agent claude --budget 1`. Keep validation workload within the configured invocation budget. `--agent fake` remains the offline demonstration.

Resume: read BUILD-STATE and git log, then specs/005-improvement-loop T014. Codex activation requires a supported runtime or explicitly approved alternative isolation architecture with actual denied-read/allowed-write/tool/network proof first. Only afterward run the opted-in tests/live/test_native_improvement.py Codex case and Phase6 parity. Exact offline check: `.venv/Scripts/python.exe -m pytest -m "not live" -q -p no:cacheprovider`.
