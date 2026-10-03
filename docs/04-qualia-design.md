# 04 — Qualia: Design System & Sources

*Structure first, skin second: doc 02 Phases 1–6 build a working app on plain shadcn + these tokens; doc 05 then restyles
it against §5. The one non-negotiable: design changes touch presentation only; computation and safety/trust rendering
rules are immutable — provenance markers, the "model-reported" label and KEEP/REVERT grammar may be styled, never
removed, reworded, softened or made conditional.*

## 1. Direction
**Archival-instrument, light-first, evidence-forward** — the owner's approved "archive of looking" style applied to a
research tool. Qualia should look like a field notebook and a specimen catalogue, not an AI product: its differentiator
is that every claim traces back to evidence, so the interface *looks like* careful observation — paper grounds, inked
keylines, catalogue drawers, mono provenance captions. Anti-reference: not another chat-first AI app; zero blue-purple
gradients, glow, glassmorphism, neural imagery, pills or uppercase eyebrows.
Feelings: **trustworthy** — a methods reviewer would accept a screenshot as an audit exhibit · **calm** — four hours of
coding without eye strain · **curious** — the experiment history reads like a lab notebook you want to page through.

## 2. Sources (looked up — borrow, don't reinvent)
- **archive-of-looking** (owner skill, approved 2026-10-02): palette, type roles, square corners, no shadows, the 63.3%
  horizon axis, the chart series, and `scripts/gen_art.py` plates (`title_dome`, `star_chart`, `paper`) for the landing
  and empty states — generated, original, no licensing questions.
- **shadcn/ui + Tailwind 4**: component base; restyle via CSS variables only. **Lucide** (lucide-react 1.51): line
  icons, always paired with a word.
- **Fonts (self-hosted, OFL-1.1, Fontsource 5.3):** Cormorant Garamond (display), Libre Franklin variable (text), IBM
  Plex Mono (captions, IDs, metrics) — the style's own web fallbacks, so every user sees the same thing.
- **Closest products:** NVivo/QualCoder for coding stripes beside the transcript (borrow the stripe idea, not the
  chrome); Exegete for approve-before-commit suggestions (borrow the review rhythm).
- **DESIGN.md references (awesome-design-md, MIT):** Notion — warm minimalism and serif headings (mine the reading
  surfaces); WIRED — paper-white broadsheet density and ink links (mine table/matrix density). Vocabulary only, never a
  brand's identity.
- **Claude Design:** deferred (owner hands-off, style already approved) — optional brief in §6.

## 3. Tokens (the contract doc 05 implements — `web/src/styles/tokens.css` is the only home for these values)
**Adjustable theme (light default / dark):** background ivory `#F3EFE4` / charcoal `#2C2A27` · surface (cards, rails)
cream `#E9E1CD` / night `#1C2127` · text ink `#1D1C1A` / ivory · secondary graphite `#3C3A35` / ivory 70% · caption
`#6B665C` / ivory 70% · keyline ink 30% / ivory 25% · accent (primary action, the payoff) rust `#A2573B` / ochre
`#B98A3E` (rust fails contrast on dark) · focus ring 2px Prussian `#236292` / sky `#A9C1D3`.
**FIXED semantics (product grammar — the theme never overrides these):**
- Code colours, in order: Prussian `#236292`, rust `#A2573B`, viridian `#2C9A88`, gamboge `#BA9232`, mineral green
  `#4E6A58`, dusty blue `#6E8496`, ochre `#B98A3E`, sage `#A5B096`; codes 9+ repeat with a hatched stripe. Text
  highlights use the code colour at 22% so ink stays ≥ 4.5:1. The code name always accompanies the colour.
- Provenance stripes (3px, left of the segment): human = solid · unreviewed model suggestion = dashed + mono caption
  `suggested · model-reported 0.82` · accepted model code = solid + mono `m` · rejected = only in the provenance popover.
- Decisions: KEEP = viridian rule + mono `KEEP` · REVERT = rust rule + mono `REVERT` · below threshold / disagreement
  = ochre-text `#8A6420` + icon + word · errors = rust + icon + word. Mono captions with a 3px rule — never pills.
- Matrix heat: Prussian at 0–60% alpha, the count always printed in mono.
**Type:** display Cormorant Garamond 400, never bold, sentence case, line-height 1.04 · text Libre Franklin 400/500
(500 is the only heavier weight) · mono IBM Plex Mono 400. Scale 12 / 13 / 15 / 17 / 20 / 24 / 32 / 44 px. UI text
15px/1.3; transcript 17px/1.6, measure ≤ 68ch; captions and provenance 13px mono/1.4.
**Space & shape:** 4-pt rhythm; radius 0 everywhere (round only for status dots and the timeline dots); no shadows —
depth from cream surfaces and 1px keylines; rails 280px left / 340px right.
**Motion:** UI 150ms, media fades 300ms, `cubic-bezier(0.3, 0, 0.7, 1)`; no bounce or springs; `prefers-reduced-motion`
→ no transitions. **Horizon:** a 1px ink-35% rule at 63.3% height on the landing hero, README banner, social preview
and empty states. **Taste dials:** VARIANCE low · MOTION low · DENSITY medium.

## 4. Per-screen specs
- **Workspace (daily driver, "the trust")** — left rail: sources, cases, code tree, memos; centre: transcript on ivory,
  speaker as mono caption, provenance stripes in the margin, keyboard focus outline on the active segment; right rail:
  codes on the segment, suggestions with model-reported score + validation ECE caption, provenance popover (actor ·
  backend · model · codebook version · pipeline hash · time, all mono). Excellence goes here first.
- **Review queue ("the trust")** — grouped by trigger (below threshold, disagreement, QC sample); each row = excerpt,
  suggested code, score with its caption, `a`/`r` hints in mono.
- **Codebook** — catalogue drawers: each code a thin-ruled box with its name in Cormorant; definition, include, exclude
  and examples as cream field-note slips; frozen versions listed as mono `cb_v14 · frozen 2026-10-12`.
- **Matrix** — code-by-case table, WIRED-dense, heat per §3, mono figures, click a cell → drawer of excerpts.
- **Experiments ("the wow")** — a horizontal timeline on the horizon rule, 16px dots (KEEP viridian, REVERT rust); open
  one → hypothesis as a field-note slip, changed files, a before → after metric table, the decision. The portfolio shot.
- **Landing / demo home** — title in Cormorant sitting on the horizon over a generated `title_dome` plate; one line of
  positioning ("Qualitative coding you can audit"); project picker as catalogue drawers.

## 5. Acceptance checklist (doc 05's loop critiques strictly against this list)
1. Hex colours and font-family appear only in `tokens.css` (grep `web/src` → 0 elsewhere).
2. No framework defaults: grep components for `rounded-` (except status/timeline dots) and `shadow-` → 0.
3. FIXED semantics: a Vitest test maps code index → the §3 order; Playwright asserts solid vs dashed stripes and the
   `model-reported` caption on every model suggestion.
4. Transcript: computed max-width ≤ 68ch, line-height ≥ 1.5 (Playwright computed style).
5. 375px viewport: landing and demo workspace have no horizontal scroll; tap targets ≥ 40px.
6. WCAG AA: visible 2px focus ring on keyboard focus (screenshot); keyboard coding e2e passes.
7. Reduced motion emulated → computed transition-duration 0s on interactive elements.
8. Demo build: Lighthouse accessibility ≥ 95, performance ≥ 90, CLS ≈ 0.
9. Never-list grep in `web/src`: `gradient`, `backdrop-blur`, `uppercase`, `tracking-` → 0.
10. Zero logic changes (`git diff --stat` over doc 01 §4's design-protected paths → empty), all tests green, and
    package.json gains nothing beyond the three Fontsource packages and lucide-react.

## 6. Owner hands-on steps (all optional — the style is already approved)
The build runs with **`use your judgment per doc 04 §3`** already in effect. Only if you want to explore:
1. (~20 min, outside a heavy build window — it shares your Claude usage) claude.ai/design → new project → paste:
   > Qualia — a local-first qualitative research workspace where AI codes interview transcripts and every decision
   > traces back to evidence. Direction: archival-instrument, light-first, evidence-forward — field notebook and
   > specimen catalogue, not an AI product. Never: chat-first layouts, blue-purple gradients, glow, pills, uppercase
   > labels. FIXED: provenance stripes (human solid, model suggestion dashed with "model-reported" score), KEEP viridian
   > / REVERT rust, square corners, no shadows. Mock: the coding workspace (three panels), the experiments timeline,
   > the codebook as catalogue drawers.
   Seeding variant: attach Notion's DESIGN.md and send "Create a design system from this DESIGN.md", then steer toward
   the direction above. Export as HTML into `docs/design/`; the next session uses it as reference. Claude Design
   unavailable or rolling out? Skip — the written direction in §1 carries it.
2. (~5 min, after BUILD COMPLETE) open the screenshots in `docs/BUILD-STATE.md` → anything off → write it plainly in
   `OWNER-ANSWERS.md` ("the rust is too loud on buttons") and relaunch; a design touch-up round follows.
