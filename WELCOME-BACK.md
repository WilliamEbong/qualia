# Qualia - threshold tuning proven on real data, now built into the app

You asked me to try tuning, check Lighthouse and keep these tools inside Qualia. All three are done, verified and pushed to private main.

## Headline: tuning measurably improved the demo

On your demo, with Jev, `Tune thresholds` learned one score threshold per code from 400 dev segments:

| Code | reflection | question | therapist_input | other | change | sustain | neutral |
|---|---|---|---|---|---|---|---|
| Threshold | 0.20 | 0.70 | 0.60 | 0.45 | 0.20 | 0.25 | 0.35 |

Qualia then measured the change on the 1,258-segment validation split and **kept it** (experiment 2, tag `exp-0002-measured-gain`).

| Measure | Before | After | Fresh confirmation |
|---|---|---|---|
| Macro F1 | 0.523 | 0.567 | 0.572 |
| Exact code-set match | 0.365 | 0.405 | 0.399 |
| Calibration error (lower is better) | 0.050 | 0.038 | 0.036 |

- **Cost:** $0.346 in Jev usage for the day (420 requests). The run took 13 minutes.
- **Your research coding:** no coding was changed.
- **Where to see it:** open Experiments to see the result, and the Codebook now shows each code's "AI suggests at score ≥ …". The Evaluation page shows the real ranges and calibration table. For example, Jev suggestions in the 0.8–0.9 band were right 87% of the time; in the 0.2–0.3 band, 19%.

## Built into the app

- **Tune button.** Experiments → **Tune suggestion thresholds** → pick a classifier → **Tune thresholds**. It runs the same measured experiment as the terminal command. If something blocks it, such as a missing dev benchmark or an unclean project, it says exactly why.
- **Real-data wording fix.** The review sentence had shown "100% of them" for 99.94%; it now says "more than 99%".

## Lighthouse and accessibility

Lighthouse was low risk. I ran Google's official tool from a temporary folder; nothing was added to Qualia.

- **Accessibility:** scored 96. I fixed the issue it found.
- **axe-core audit** (the engine Lighthouse uses) found two more problems, both now fixed:
  - Wide tables on phones couldn't be scrolled by keyboard.
  - The frequency chart hid its clickable bars from screen readers.

  axe now reports no violations on Experiments, Evaluation, Review and Codebook, at desktop and phone width, light and dark.
- **Speed:** really fast locally: first paint 0.2 s, main content 1.2 s, no layout shift. Lighthouse's simulated slow-network score is low (59–74) only because opening the demo downloads a 12 MB data file. Compressing it would slow local use, so I left it. A suggested follow-up task to shrink that payload is waiting in the app for you to start or dismiss.

## Changes to your demo workspace (outside the repo)

All were made as commits in the demo's own Git history:
- Committed your existing Jev-enable setting.
- Moved my two earlier report files out to the session scratchpad.
- Raised the daily call limit to 800 for the run, then restored it to 300.
- The tuned thresholds are kept, as Qualia's policy decided.

## Checks

- Full offline suite: 561 passed, 5 skipped, 6 live tests deselected.
- Web: 37 tests, typecheck and build pass.
- Ruff, data guard, dependency audit and secret scan are clean.
- The CI result for the final push is in the last BUILD-STATE entry.
- Specs 010–012 have convergence records.

## Still yours

- **Stale servers.** Two old `qualia open --no-browser` servers from 2026-10-03 still hold `qualia.exe`. Close them, then run:
  ```powershell
  uv sync
  uv run qualia open
  ```
- **Security review.** The planned Claude Code `/security-review` before going public is unchanged.
