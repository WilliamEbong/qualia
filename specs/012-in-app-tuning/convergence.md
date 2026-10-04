# In-app threshold tuning convergence

Four requirements, four success criteria and four tasks reviewed. Scoped feature converged.

- FR001: `POST /api/projects/{slug}/tune-thresholds` runs `improve_project(agent='thresholds', budget=1)`. API tests: KEEP through the real app on a synthetic project (code threshold 0.65 committed); extra fields rejected with 422; missing dev split returns the sanitized 400 `dev benchmark has not been imported` with project Git clean. openapi.json and web/src/api/schema.d.ts regenerated (LF normalized).
- FR002–003: Experiments shows a "Tune suggestion thresholds" form (classifier select defaulting to the project's configured backend, model override, plain explanation, blocked reasons). A Playwright button click on a full-size scratch copy of the demo completed in 21 s and selected the new attempt (REVERT, no change for the rules baseline). Screenshots design-review/P15/tune-*.png and experiments-*.png at 1280/375 light/dark, no overflow or console errors.
- FR004: `backendBlockedReason` is shared by Evaluation and Experiments (web test covers read-only, checking, unavailable, privacy-blocked and ready cases).
- SC003 accessibility: axe-core 4.13 (WCAG 2.0/2.1 A/AA plus best practice) reports no violations on Experiments, Evaluation, Review and Codebook at 1280/375 in light and dark after this session's fixes. Lighthouse 13.5 on the live app: accessibility 96 → fixed the flagged role-less `aria-label`; performance 59 mobile / 74 desktop simulated, 89 with real local timing (FCP 0.2 s, LCP 1.2 s, CLS 0). The simulated score is driven by a 12.3 MB workspace JSON payload; a follow-up task records it (gzip rejected for loopback CPU cost).
- Real use: the owner-approved Jev run on the actual demo kept per-code thresholds on measured evidence (macro F1 0.523 → 0.567 → 0.572 confirmation; ECE 0.050 → 0.038; $0.346; experiment 2, tag exp-0002-measured-gain). The real data exposed a 99.94% review share rendered as "100%"; fixed to "more than 99%".

Not claimed: Lighthouse performance ≥ 90 under simulated throttling for the full demo payload.
