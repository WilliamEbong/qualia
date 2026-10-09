# Qualia explainer video — plan

A 60-second silent explainer for the README and the demo, made with Remotion. It is a portfolio asset, not an app
feature: it lives in `video/`, has its own `package.json`, and changes nothing in `qualia/`, `web/`, `tests/` or
`scripts/`. CI does not build it.

## Decisions
- **Remotion 4.0.529**, pinned exactly (published 2026-09-25, at least two weeks old). Free for individuals under the
  Remotion licence; the owner is an individual. Rendered locally with the Remotion CLI.
- **1920×1080, 30 fps, 60 s, H.264 MP4, no audio.** All meaning is in on-screen text, so it works muted and
  autoplays anywhere. No voiceover or music: nothing to license.
- **Qualia's own look (doc 04 tokens), not a new style:** ivory ground, Cormorant Garamond display (400, never bold),
  Libre Franklin text, IBM Plex Mono captions, square corners, no shadows, 1px keylines, the horizon rule at 63.3%
  height. Fonts come from the same Fontsource packages the web app uses, loaded with `@remotion/fonts` so rendering
  waits for them. The `title_dome` plate is read from `web/public` via `Config.setPublicDir` (no copied binaries).
- **Motion stays low:** fades and short slides with `cubic-bezier(0.3, 0, 0.7, 1)`; no springs, bounce or glow.
- **Honest data only.** Transcript lines and expert codes come from `demo/snapshot.json` (public-domain AnnoMI demo).
  The provenance card shows one recorded event verbatim. Experiment numbers are the real, published Jev tuning
  result from the README; the REVERT is the project's real synthetic live experiment (macro F1 1.0 → 1.0). The one invented value, the AI suggestion score in scene 4, is the same deterministic fixture value the
  real review screenshot shows (0.60 below a 0.70 threshold) and is labelled as a synthetic demonstration with no matching validation ECE.
- **Product grammar preserved:** human = solid 3px stripe; model suggestion = dashed stripe + mono
  `suggested · model-reported 0.60`; accepted model code = solid + mono `m`; KEEP viridian, REVERT rust, always with
  the word. Code colours by index (reflection = Prussian, neutral = ochre).
- Output: `video/out/` (gitignored). The final MP4 and a poster frame are copied to `docs/media/` and linked from the
  README with one line.

## Storyboard (frames at 30 fps; 1800 frames = 60 s; revised after the Codex plan review)
| # | Frames | Scene | On screen |
|---|---|---|---|
| 1 | 0–119 | Title | `title_dome` plate; "Qualia" in Cormorant above the horizon; mono "Qualitative coding you can audit." |
| 2 | 120–254 | Premise | "AI can code your interviews." then "Qualia makes it show its work." |
| 3 | 255–854 | You code, then AI suggests and you decide | Real AnnoMI transcript 125, first four lines with their real expert codes. Key caps `1` (reflection) and `7` (neutral) press; solid stripes, 22% highlights, `human · codebook v1 (frozen)`. Then the second therapist line gets a dashed stripe, `suggested · model-reported 0.60` and ochre `! Below review threshold (0.70)`; `a` presses; solid stripe with mono `m`, `accepted by you`. Corner caption: `demonstration · synthetic suggestion · no matching validation ECE yet`. |
| 4 | 855–1124 | Every decision keeps its evidence | The first therapist line's recorded event, verbatim from the snapshot: passage, code · assign, actor, codebook v1 · frozen · `8209f1f2`, pipeline `12420d5b`, recorded time. Then: model suggestions also record backend, model, prompt and model-reported score; the history is append-only. |
| 5 | 1125–1544 | Improvements are measured, not claimed | Timeline: REVERT (rust) "synthetic live check · macro F1 1.000 → 1.000"; KEEP (viridian) "threshold tuning · AnnoMI demo". Table Before / After / Fresh confirmation for macro F1, exact code-set match and calibration error, with direction labels and "Threshold tuning, no AI agent involved · AnnoMI demo · Jev · 1,258 validation segments". Then "Qualia's measured policy decides KEEP or REVERT, never the AI agent." |
| 6 | 1545–1799 | Close | "Runs on your computer. External AI stays off until you allow it." / "Every external call is budgeted and logged." Then the plate, "Qualia", tagline and both URLs. |

All motion is frame-driven (`useCurrentFrame` + `interpolate` with the doc 04 easing); nothing uses CSS transitions.

## Verification
1. `npx tsc --noEmit` in `video/` passes.
2. `remotion still` at one frame per scene; inspect each image for layout, clipping, fonts and grammar.
3. Full render; `ffprobe` confirms 1920×1080, 30 fps, 60 s, H.264, no audio stream; file under 15 MB.
4. Repo checks unaffected: `git status` shows only `video/`, `docs/media/`, README, BUILD-STATE and WELCOME-BACK.
5. Codex reviews this plan before building and the result after rendering.

## Rebuild
```
cd video
npm ci
npm run render    # out/qualia-explainer.mp4
npm run poster    # out/qualia-explainer-poster.png
```
