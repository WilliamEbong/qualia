# Final design verification

Verified 2026-10-03 against docs 04–05. Functional baseline: `295c712`; D1/D2 checkpoint: `6dd5259`. The Archive of Looking direction uses original seed-3 plates, self-hosted licensed fonts, square keylines and the 63.3% horizon. No runtime dependency was added during the design pass.

## Screen evidence

| Screen | Before | Final | Result |
|---|---|---|---|
| Home | D0/ and D5/ | final/home-1280.png, final/home-375.png | Original dome, horizon and project drawers; no page overflow |
| Workspace | D0/ and D2/ | final/workspace-1280.png, final/workspace-375.png | Local AnnoMI provenance, reading measure and rails retained |
| Review | D0/ and D2/ | final/review-1280.png, final/review-375.png, final/review-dark.png | 34 pending suggestions retain dashed marks and model-reported captions |
| Experiments | D0/ and D3/ | final/experiments-1280.png, final/experiments-375.png, final/experiment-measurements.png | KEEP timeline, hypothesis and all three measurement columns retained |
| Codebook / Matrix | D0/ and D4/ | final/codebook-*.png, final/matrix-*.png | Catalogue slips and labeled heat counts; contained table scrolling |
| Analysis | analysis/ | final/analysis-*.png, final/scatter-*.png | Static frequencies plus separate synthetic numeric fixture; linked evidence and explicit denominators |

Home, Codebook, Matrix and Analysis overview images use the licensed 24-row static snapshot. Workspace, Review and Experiments use the local public AnnoMI demo, with clearly identified offline fake suggestions/experiment. Scatter images use six invented cases. No private study is pictured. `final/walkthrough.gif` is a five-frame visual tour, not a recording of unperformed interactions.

## Contract checks

1. All color literals and font-family declarations are in tokens.css. **Literal grep exception:** frozen `web/src/lib/analysis.ts:115` contains the property name `font-family` when copying computed styles into exported SVG. It supplies no font value and predates the design baseline. Protected functionality was not altered to conceal this match.
2. No rounded/shadow utility defaults or prohibited gradient/backdrop/uppercase/tracking treatments were introduced.
3. Fixed eight-code palette test passes. MCP verified solid human, dashed pending and solid-plus-m accepted marks; model scores keep their label.
4. Transcript computes to 17px with 27.2px line height and maximum 68ch.
5. All ten static views pass 375px and 1280px page-overflow checks. Local workspace, review and experiments pass both widths. Small tables/charts use their own scroll region. D6 checks found no visible control below the 40px target.
6. Actual keyboard Tab produces the 2px focus ring. Five distinct segments were keyboard-coded in the synthetic design-smoke project, waiting for each completed write before moving on; evidence: D6/keyboard-five.png. Research data was not used for that test.
7. Emulated reduced motion yields zero-duration interactive transitions.
8. Final Lighthouse 13.5.0: **performance 96, accessibility 100, CLS 0.0001251722**. JSON: D6/lighthouse.json. Initial final-design audit was 75 / 95 / 0.104621; D6/lighthouse-before.json preserves it.
9. Prohibited-treatment searches passed. See item 1 for the sole font-property-name exception.
10. Protected functional diff against 295c712 is empty. Independent review found all 199 functional attributes unchanged across the nine changed components; dependencies, handlers, API/library code, backend and tests stayed frozen. The temporary D0 guard-mode switch is restored after this checkpoint.

## One repair iteration

The first audit identified an oversized 592KB hero, loading-footer shift and insufficient light caption contrast. Iteration 1 added 7.7KB/22.7KB responsive derivatives with matching preload, reserved the loading viewport height, and darkened the adjustable caption token. Dark review uncertainty text also uses its existing semantic ochre token on ivory. Fixed code and decision colors did not change. Thirty frontend tests and TypeScript pass; normal and static production builds pass. The repeated audit meets the thresholds, so the loop stops after one iteration.

The independent Ponytail review found no blocking complexity; an existing duplicate reduced-motion rule is harmless and remains unchanged. Browsers may report an unused hero preload when navigation opens a non-home view; it is a small presentation resource, not a failed request. There were no observed browser errors. The static demo issued zero API requests across all ten views.

## Remaining boundaries

This proves presentation acceptance with the explicit literal-grep distinction above. It does not prove native provider activation, a completed official security scan, public hosting, or a remote push. Those separate gates are recorded in docs/BUILD-STATE.md and the final report. Automatic approval review requires explicit owner authorization before pushing private main; no push or public deployment was performed as part of this checkpoint.
