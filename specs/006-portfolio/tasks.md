# 006-portfolio tasks

All items are open. Dependencies: each task requires earlier tasks in its group and all previous groups unless the task explicitly says it is an independent verification. No parallel lane starts before main freezes its consumed contracts. Main owns pointer updates, analysis/convergence, commits and BUILD-STATE; workers report evidence.

## Setup

- [ ] [T001] Confirm Phase 7 design-review/final evidence and guard mode returned to build; verify redistribution licenses in DATA-LICENSES.md before selecting snapshot content.

## Foundational work

- [ ] [T002] Define snapshot whitelist/schema and no-sensitive-content fixtures in tests/test_snapshot.py; include forbidden token/vault/private-path/source cases.
- [ ] [T003] Implement scripts/build_snapshot.py using selected licensed demo data and existing export/store readers; validate deterministic output to demo/snapshot.json.

## User stories in priority order

- [ ] [T004] Verify or complete the VITE_DEMO data-source path in web/src/lib with main approval of any remaining contract work; test that writes, API, AI and token bootstrapping are absent.
- [ ] [T005] Exercise all static screens and disabled actions in tests/e2e/demo.spec.ts with API network requests captured and asserted zero.
- [ ] [T006] Write README.md positioning, architecture, install, evidence-based MVP and Decisions sections using actual results and design-review/final screenshots/GIF.
- [ ] [T007] Prepare .github/workflows/pages.yml with public-repository gate and Pages environment; validate repository-base assets and real URL handling without changing visibility.
- [ ] [T008] Validate approved docs/social-preview.png dimensions/horizon and add web/public/sitemap.xml with truthful known hosting targets; reuse Phase 7 artwork.

## Validation and completion

- [ ] [T009] Run data/secret scan of tracked files and built web/dist, Python/web checks and static build; verify DATA-LICENSES coverage for every shipped asset.
- [ ] [T010] Use Playwright MCP for 375px/1280px demo navigation, trust markers and zero API requests; save evidence in design-review/portfolio/ and run Lighthouse on vite preview.
- [ ] [T011] Main analyzes/converges the feature, records CI/scores and either tested artifact URLs or 'not deployed'; defer sacrificial blocked assets explicitly rather than declaring public completion.
