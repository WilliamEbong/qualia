# In-app threshold tuning

The owner asked that tuning be "built in to qualia" rather than a terminal-only command (2026-10-04, delegated to Claude). Feature 011 delivered `qualia improve --agent thresholds`; this feature exposes the same measured experiment in the Experiments view. No dependency or migration; one additive API route.

## Requirements

- FR001: `POST /api/projects/{slug}/tune-thresholds` with `{backend?, model?}` runs exactly `improve_project(project, agent='thresholds', budget=1, backend, model)` and returns the recorded experiment (existing `ExperimentResult` shape). Errors (no dev split, unclean project Git, budget, pending recovery) return the existing sanitized `ValueError` response; nothing is half-applied.
- FR002: The Experiments view offers a "Tune suggestion thresholds" form: backend select (from availability), optional model override, a plain explanation (no AI operator; up to 400 dev segments; kept only if validation improves; uses classification budget; can take minutes), and one button. It is disabled in the read-only snapshot, while busy, without a frozen codebook, or when the chosen backend is unavailable or blocked by project privacy, with the reason shown.
- FR003: After a run, the history reloads and the new attempt is selected, showing its KEEP/REVERT decision, hypothesis (threshold changes) and measurements. The terminal command remains documented as an alternative.
- FR004: The blocked-backend reason is computed by one shared lib helper used by both Evaluation and Experiments.

Constraints: unchanged experiment policy, locks, scope checks and budgets; the API is local, token-protected and binds 127.0.0.1 as today; components hold markup only.

## User scenarios

On the Experiments page, a researcher picks `jev`, presses **Tune thresholds**, waits, and sees "KEEP · experiment #2" with the per-code thresholds it chose, or "REVERT" with the measured reason. Without a dev benchmark they see the exact reason instead of a silent failure.

## Success criteria

- SC001: API tests prove KEEP through the route on a synthetic project, the sanitized error without a dev split, and the read-only/invalid-input behaviour of the existing app.
- SC002: Web tests cover the shared blocked-reason helper; typecheck/lint/build pass; OpenAPI and generated types are refreshed.
- SC003: Playwright screenshots of the form at 1280/375 (light/dark) without overflow; axe reports no violations on the Experiments view; a real button-driven run completes on a synthetic project.
- SC004: Full offline suite, Ruff, data guard, dependency audit and gitleaks pass.
