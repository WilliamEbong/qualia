# 05 — Qualia: Design Implementation Runbook

*Doc 02's Phase 7. Same discipline as doc 02: unattended under the runner, fresh session per relaunch, BUILD-STATE
ritual, OWNER-NEEDED instead of questions, subagents read-only except in their screen lane, Ponytail active — design ≠
bloat. Small commits, constantly. Doc 04 is the spec; this doc is the work.*

## 1. Immutable guardrails (checked before every commit)
- **Restyle contract (absolute).** Editable ONLY: `web/src/styles/**`, markup and classNames in `web/src/components/**`
  and `web/src/pages/**`, `web/index.html`, `web/public/**`, CSS/Tailwind config, `DESIGN.md`, `design-review/**`,
  README images, `docs/social-preview.png`. Untouchable: everything in doc 01 §4's design-never-touches list, plus
  `.codex/`, `.claude/`, `.githooks/`, `docs/0*.md`. **Machine-enforced:** D0 flips `.claude/hooks/guard-config.json`
  to `"mode": "design"` — the Claude guard hook and the `.githooks/pre-commit` gate (Codex) then reject untouchable-path
  edits/commits for the rest of the run. *If a visual change seems to require a logic change: STOP and record it in
  DESIGN-NOTES.md instead of doing it.*
- **Trust rendering is load-bearing:** provenance stripes, the `model-reported` label, ECE captions, KEEP/REVERT
  grammar, review-trigger reasons and egress notices may be *styled*, never removed, reworded, softened or made
  conditional.
- **Dependencies:** nothing beyond doc 04 §2 (three Fontsource packages, lucide-react) without an OWNER-NEEDED gate;
  prefer tokens/CSS over components, components over libraries. taste-skill is INSTALLED AND ACTIVE (gpt-taste variant
  under Codex) on a leash: doc 04 + DESIGN.md outrank it, dials exactly as doc 04 §3 (VARIANCE low · MOTION low ·
  DENSITY medium), and any animation library it proposes goes through the dependency gate.
- Tests + typecheck green at every commit; BUILD-STATE updated per sub-step.

## 2. Review dial + kickoff
Dial: **`reviews: end-only`** (owner hands-off). Hard gates in every mode → OWNER-NEEDED batch, never a stall: any new
dependency, anything touching the untouchable list. No one-time taste A/B gates (style pre-approved). Kickoff — the
runner reaches this doc through doc 02 Phase 7; for a manual session, paste from the project folder:
```
Read C:\Users\Owner\OneDrive\Documents\Qualia\docs\04-qualia-design.md then C:\Users\Owner\OneDrive\Documents\Qualia\docs\05-qualia-design-build.md in full, with reviews: end-only. First read docs/BUILD-STATE.md and git log to confirm where things stand, then continue from the first unchecked D-phase item. Apply taste-skill with the dials stated in doc 4 §3. Honor every guardrail in doc 05 §1 and all invariants in docs/01-qualia-context.md §6. Update BUILD-STATE.md and commit at every sub-step so a usage cutoff loses nothing.
```

## 3. D0 — Baseline & harness
1. Flip guard-config to `"mode": "design"`. Write `.githooks/pre-commit` (Node, zero dependencies, reads the same
   guard-config, rejects staged paths under designProtected) and `git config core.hooksPath .githooks`.
2. Prove it: stage a one-line edit under `qualia/` and commit → rejected (paste the output into BUILD-STATE); unstage.
3. Verify taste-skill is loadable (list available skills); missing → log it and continue on doc 04 alone — never assume
   it fired.
4. Screenshot harness: toolbelt playwright MCP (present per Phase 0) → capture landing, workspace, review queue,
   codebook, matrix, experiments at 375px and 1280px on the demo project into `design-review/D0/`; commit. Fallback if
   it fails: the `@playwright/test` e2e suite already in the repo takes the same shots.

## 4. D1 — Tokens & theme
Inputs in order: `docs/design/` export (if the owner made one, doc 04 §6) → else doc 04 §3 under `use your judgment`.
Install the three Fontsource packages; create `web/src/styles/tokens.css` as the single home of every value; map shadcn
CSS variables onto it (radius 0, shadows none); light default, dark via `prefers-color-scheme` plus a remembered
toggle; FIXED semantics as named variables (`--code-1`…`--code-8`, `--stripe-human`, `--stripe-suggested`,
`--decision-keep`, `--decision-revert`, `--uncertain`). Generate plates (pre-authorized):
`uv run --with numpy --with pillow python "$HOME/.claude/skills/archive-of-looking/scripts/gen_art.py" --out
web/public/plates --only title_dome,star_chart,paper --seed 3` — script missing → plain ivory ground + horizon rule.
Distill doc 04 §§3–5 into repo-root **DESIGN.md** (Stitch format: atmosphere, palette roles, type rules, component
states, do/don'ts). This phase alone visibly transforms the app. Shots → `design-review/D1/`.

## 5. D2–D5 — Screen phases (trust and wow first; one screen lane each when subagents run)
- **D2 Workspace + review queue** (the trust): rails, transcript measure, provenance stripes and popover, suggestion
  cards, keyboard focus outline.
- **D3 Experiments** (the wow): horizon timeline, KEEP/REVERT dots, field-note hypothesis slip, before → after table.
- **D4 Codebook + matrix:** catalogue drawers and slips; WIRED-dense matrix with heat and mono figures.
- **D5 Landing/demo home:** title on the horizon over `title_dome`; positioning line; project drawers.
Each: restyle markup/classNames only, behavior identical, shots to `design-review/D<n>/`.

## 6. D6 — Motion, a11y, polish
Transitions within doc 04 §3; focus rings; contrast to AA by fixing TOKENS, never one-offs; empty, loading and error
states (empty states use the horizon + `star_chart`); 404; 375px pass.

## 7. D7 — Audit & ship
Run doc 04 §5 item by item against fresh shots and the demo build (`vite preview`); Lighthouse scores pasted;
`git diff --stat <D0 commit>..HEAD` over every untouchable path → empty; a Ponytail review of the whole design diff
(cut what isn't earning its place); capture final shots into `design-review/final/` and
`docs/social-preview.png` (1280×640, horizon at 63.3%) for doc 02 Phase 8; update BUILD-STATE and WELCOME-BACK. No
deploy step: Pages activates when the owner goes public (doc 03 §8).

## 8. Autonomous improvement loop (after the audit)
Per screen, max 3 iterations, stop early when green:
1. Screenshot the screen at both breakpoints.
2. Critique **strictly against doc 04 §5** — each item pass/fail with one line of evidence. *"I'd prefer" is not a fail.*
3. Fix only failed items, inside §1. One commit per iteration (`Design-loop <screen> i<N>: <items fixed>`).
4. Tests + typecheck green, or the iteration reverts.
Exit: all green or budget spent → `design-review/LOOP-REPORT.md`: per-screen before/after, items fixed, items remaining
(why), and recommendations needing a human or a new dependency — **proposed, not taken**. Push. Then flip
guard-config back to `"mode": "build"` and return to doc 02 Phase 8.

## 9. After this doc
Future design work = edit doc 04, rerun the matching D-phase. Next product beats come from doc 01 §3's V1.5 list.
