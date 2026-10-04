# Plan

SERVER lane `qualia/server/evaluation_routes.py` (the experiment history route already lives there), OpenAPI via `scripts/export_openapi.py` + `npm run api`, WEB lane `web/src/lib/{evaluation-state,evaluation,experiments}.ts`, `web/src/components/{App,Experiments}.tsx`.

1. Route `tune-thresholds` reusing `EvaluateInput` and `ExperimentResult`; a plain `def` so FastAPI runs it in its worker thread like `evaluate`.
2. `backendBlockedReason(readOnly, provider, allowExternal, readOnlyText)` in `evaluation-state.ts`; `useEvaluation` and `useExperiments` call it.
3. `useExperiments(w, review)`: backend state reset per project, `tune` submit through `w.run`, reload, select the returned id.
4. `Experiments.tsx`: form card above the history (both empty and populated states), existing classes (`editor`, `caption`).
5. Tests: `tests/test_evaluation.py` API cases; `web/src/lib/evaluation.test.ts` helper cases. Docs: USER-GUIDE §15, README, CONTRACTS, BUILD-STATE.
