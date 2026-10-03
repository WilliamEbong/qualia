# 006-portfolio — Auditable public portfolio and static demo

## Overview and scope

Explain the finished product through its README and a read-only static demonstration built from a licensed snapshot, with no API, AI, secrets or private research data.

Sacrificial phase after core, hygiene and doc05 design gates. Repository remains private; prepare Pages workflow but do not change visibility, repository settings or activate a public deployment. Screenshots/social preview come from the completed design pass. No product features or design-protected logic changes are smuggled into presentation work.

Governing sources: docs/01–05 and constitution v1.0.0. This is a prepared feature; main activates it in phase order and runs analyze before implementation. No implementation or acceptance pass is claimed here.

## Authoritative workstreams (verbatim from doc02)

- **3.12 Portfolio [sacrificial]** README (positioning "Qualitative coding you can audit", screenshots + GIF from `design-review/final/`, architecture diagram, MVP walkthrough, Decisions log); `scripts/build_snapshot.py` → `demo/snapshot.json` + static demo build + Pages workflow (activates once public); `docs/social-preview.png` 1280×640; sitemap. Re-check AnnoMI's license before the snapshot ships, else fallback data.

## Functional requirements

- FR-001: Write README positioning 'Qualitative coding you can audit', architecture diagram, install/run workflow, MVP walkthrough, actual evidence, screenshots/GIF, limitations and Decisions log.
- FR-002: Build deterministic demo/snapshot.json using scripts/build_snapshot.py from a selected licensed demo project; exclude secrets, launch tokens, vault, absolute machine paths and private source data.
- FR-003: Build the same SPA with VITE_DEMO=1 reading the snapshot; perform zero /api/ requests, start no AI/backend subprocesses and offer no mutation paths.
- FR-004: Preserve provenance, model-reported/ECE captions, review reasons and KEEP/REVERT semantics in the static artifact; missing measurements are shown as unavailable.
- FR-005: Provide a GitHub Pages workflow ready to run only when the repository is public and the owner enables Pages; keep the repository private throughout the build.
- FR-006: Produce/validate docs/social-preview.png at 1280×640 and the approved horizon at 63.3%, plus a correct sitemap and discoverable demo link only when a real URL exists.
- FR-007: Verify static artifact security/data contents, working project-base asset navigation and responsive/accessibility behavior at 375px/1280px.
- FR-008: Achieve Lighthouse performance >=90 and accessibility >=95 with approximately zero CLS on vite preview and preserve all completed application tests.

## User scenarios

- US1: A stranger reads the README, understands the trust/researcher-control distinction within its opening section, installs the CLI and follows the documented demo walkthrough.
- US2: A visitor explores the static demo's transcript, provenance, matrix and experiment history with the network API unavailable; no write or AI action is possible.
- US3: The owner later makes the repository public and enables Pages; the prepared workflow builds the verified static artifact without embedding credentials or private workspaces.

## Success criteria

- SC-001: Playwright network evidence proves zero /api/ requests across all demo screens; controls cannot mutate or invoke AI; console/asset navigation is clean at the project base.
- SC-002: Snapshot validation and data/secret scans pass; DATA-LICENSES documents verified redistribution terms for every shipped dataset asset.
- SC-003: Lighthouse scores meet the exact performance/accessibility gate at vite preview; screenshots demonstrate 375px/1280px behavior and fixed trust markers.
- SC-004: README commands match the tested install/MVP flow and its measurements cite real evidence; social PNG dimensions are 1280×640; sitemap/link targets reflect actual hosting state.
- SC-005: CI remains green and sacred source-document diff is empty; no gh repo edit/delete or public flip is performed.

## Authoritative acceptance excerpts (verbatim from doc02)

- [ ] CI green on last push; forced bad TYPESAFE_API_KEY → error output contains no key value.
- [ ] Demo build: zero `/api/` requests (Playwright network log); Lighthouse on `vite preview` → performance ≥ 90, accessibility ≥ 95.
- [ ] `git diff --stat <phase-0 commit>..HEAD -- docs/02* docs/03* docs/04* docs/05*` → empty; TODO/FIXME grep → 0.

Quoted shared gates retain their original scope. This feature proves its relevant part; later-phase responsibilities are stated above. Common I1/I6/I7 protections remain mandatory regressions, never exemptions.

## Informed assumptions

- Reuse final approved screenshots and GIF evidence under design-review/final; never fabricate performance, improvement, agreement or usage results in marketing copy.
- Static demo reads a schema-validated demo/snapshot.json derived only from the explicitly licensed public demo dataset. Recheck distribution rights before tracking excerpts; an unavailable or unsuitable source defers the public snapshot rather than exposing another project.
- The runtime API/demo data-source seam belongs in the earlier feature implementation, with state logic in web/src/lib. This phase builds/validates its VITE_DEMO=1 path; if missing, treat it as a main-owned implementation change after design mode is off, not a restyle edit.
- Read-only demo disables imports, writes, AI, improvement and secret/token initialization; links and navigation may show existing recorded history. Explain the read-only nature in the UI.
- Use repository-relative asset bases suitable for GitHub Pages project hosting and a static sitemap based on the eventual known URL; do not invent a live URL before deployment.
- Only GitHub traffic insights are planned for measurement; no analytics SDK, consent banner, remote font CDN or additional service is introduced.
