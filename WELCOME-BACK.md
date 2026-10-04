# Qualia - Codex improvement implemented and live-verified

The owner approved decision04: Codex now returns no-tools structured proposals using the user's own ChatGPT CLI sign-in. Qualia validates permitted existing-file replacements, applies them under its experiment lock, runs trusted tests/evaluation and automatically keeps or reverts. The failed direct file-tool route remains disabled; no repeat sandbox setup or Windows permission change is needed. Claude's verified restricted-file workflow is unchanged.

Implementation checkpoint0fcc799 follows plan3c95045. The bounded public Codex live test passed in41.92s: Astra proposed classify.txt, Luna macro-F1/exact-match stayed1.0 to1.0, ECE0 to0, agreement undefined. Correct REVERT restored the prompt, preserved methodology/frozen codebook/coding state and left Git clean. Three admitted invocations retained usage. This is integration evidence, not an accuracy-gain claim.

Verification:534 offline Python tests passed,5 capability skips,6 live tests deselected,256.82s. Operator47 and proposal/coordinator72 (1skip) pass; native production no-tools wire captures, authentication rejection, malicious proposals and partial-write recovery verified. Ruff/data/secret/protected-file checks pass. No frontend changed; prior30 frontend tests and MCP evidence remain applicable.

Read docs/USER-GUIDE.md section15 for the complete workflow. On a prepared clean study with a validation benchmark and external processing enabled, run:

```powershell
uv run qualia improve --project my-study --agent codex --budget 1
uv run qualia history --project my-study
```

Astra is the operator; evaluation uses project routing or explicit --backend/--model. Existing daily limits apply to baseline/operator/candidate/confirmation. Jev remains enabled for demo at its existing limit and is optional for other projects.

Private checkpoint e95972e is pushed and Checks37184680691 passed: https://github.com/WilliamEbong/qualia/actions/runs/37184680691. Repository remains PRIVATE and Public demo was skipped. This final documentation-only follow-up records the completed verification; its own Checks status is reported at handoff. Feature005/P14 has no remaining implementation work.

Remaining owner release action: the planned Claude Code /security-review before making the repository public. No public visibility/deployment or external security pass is claimed. OWNER-NEEDED.md records only that release action. Resume from docs/BUILD-STATE.md and git log; do not repeat completed native setup or tests without a new reason.
