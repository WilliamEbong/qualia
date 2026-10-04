# Qualia - calibrated decisions shipped (decision05)

Everything you asked for overnight is built, tested and committed. The scope came from the open-source Jev ecosystem review and is recorded in docs/answers/05-calibrated-decisions.md: no local model backend; scipy declared; threshold tuning as a no-AI agent.

## What changed

1. **Bug fix: Jev works on the demo again.** With the demo's 7-code codebook, the default 20-segment batch exceeded Qualia's 64 KB Jev request bound, so every demo Jev call failed. The router now shrinks a batch until the provider accepts it. A live check sent 20 real demo segments in 2 calls, cost $0.00136 and created no coding events.
2. **Evaluation explains itself (feature 010).**
   - Per-code precision and recall show 95% ranges, for example `0.750 (0.30–0.95)`.
   - Every metric has a one-line plain-language explanation.
   - Kappa and alpha get cited words such as "substantial" or "tentative".
   - A sentence says how much of the AI's work to review to reach 90% precision, next to your current review threshold.
   - A calibration table shows how often each score band was right.
3. **Per-code thresholds and a no-AI tuning agent (feature 011).**
   - `code_thresholds` in a project's routing sets the minimum score for each code to be suggested. Jev's 0.5 cutoff now lives in the router, and thresholds apply to cached scores, so changing them needs no new AI calls.
   - `uv run qualia improve --project my-study --agent thresholds` fits one threshold per code on up to 400 dev segments. Qualia's existing policy then keeps it only if validation improves.
4. **Review is friendlier.**
   - Each suggestion says why it waits, for example *Below review threshold (current threshold 0.70)*.
   - The least certain suggestions come first.
   - The Codebook shows any tuned threshold.
   - The empty Experiments page explains how to run an agent.

The user guide covers all of this in §1 (glossary), §12 (review), §14 (reading results) and §15 ("Tune per-code suggestion thresholds without AI").

## Evidence

- **Tests:** full offline suite 559 passed, 5 skipped, 6 live deselected. Ruff, data guard, pip-audit, gitleaks and the web checks (typecheck, 36 tests, build) all pass. An independent read-only review of the diff found no correctness bugs.
- **Screenshots:** 16 at 1280/375 in light and dark, in design-review/P15/. No horizontal overflow and no console errors. New text meets WCAG AA contrast.
- **Thresholds agent:** reaches KEEP in a synthetic test. On a full-size scratch copy of the demo with the keyword rules backend, it correctly found no useful change and recorded REVERT in about 30 seconds.
- **Specs:** specs/010-evaluation-uncertainty and specs/011-decision-thresholds hold spec, plan, tasks, analysis and convergence.
- **Not claimed:**
  - No Lighthouse score; Lighthouse is not installed and I did not download it unattended.
  - No real-data accuracy gain from thresholds; I did not spend money running Jev tuning on the demo.

## Things to know

- **Restart your Qualia server.** Two stale `qualia open --no-browser` servers from 2026-10-03 hold `qualia.exe`, so `uv sync` could not refresh the project entry. All dependencies are installed and everything works. I was not permitted to stop those processes. Close them, then run:
  ```powershell
  uv sync
  uv run qualia open
  ```
  Two more servers that I started (ports 8790 and 8791) are stopped at handoff.
- **Demo workspace (outside the repo).** It already had an uncommitted `config/routing.yaml` change from your Jev enable on 2026-10-03. I left that alone. My work there added:
  - evaluation run #4 (rules) and its two report files in `reports/`;
  - usage and egress rows from the $0.00136 live check.

  Nothing was committed or deleted there. Experiments on the demo need a clean Git state first.
- **Push.** Pushed to the private main branch under the standing approval. CI status is in the final BUILD-STATE entry. The repository remains PRIVATE.

## Remaining owner action

The planned Claude Code `/security-review` before making the repository public is unchanged. Resume from docs/BUILD-STATE.md and git log.
