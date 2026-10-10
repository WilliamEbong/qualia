# Qualia - handoff (2026-10-10)

**New: 13 video tutorials** in docs/media/tutorials/ (MP4 plus poster JPG each), listed in the README under "Video tutorials" and linked from the matching user-guide sections. They are silent and captioned, 1080p, and run 2:01 to 3:24. Each one is recorded from the real app by a script, using a scratch workspace (never your projects), the invented practice study or the public AnnoMI demo. AI scenes use the offline fake backend and say so on screen. Codex wrote the storyboards and reviewed the finished set, and all of its findings are fixed. The app itself is unchanged. To re-make one, see video/tutorials/README.md (for example `node tutorials/make.mjs 06` from `video/`). The full set adds about 102 MB to the repository. Details: docs/BUILD-STATE.md (P23).

## Earlier (2026-10-09)

**A 60-second explainer video** at docs/media/qualia-explainer.mp4 (poster: docs/media/qualia-explainer-poster.jpg), linked from the README. It is made with Remotion from the public demo data. The source and storyboard are in `video/` (see video/PLAN.md), and nothing in the app changed. To re-render it: `cd video`, `npm ci`, `npm run render`. It is pushed to main (03025e8); Checks and Public demo both passed. Details: docs/BUILD-STATE.md (P22).

## Earlier round (2026-10-07)

**The improvement round is finished, verified and pushed to main.** Details: docs/BUILD-STATE.md (P20) and docs/answers/07-improvement-round.md.

| What | Where |
|---|---|
| Repository | https://github.com/WilliamEbong/qualia |
| Online demo (read-only) | https://williamebong.github.io/qualia/ |
| Windows download | https://github.com/WilliamEbong/qualia/releases/latest (v0.2.0, includes this round) |
| User guide | docs/USER-GUIDE.md |

## What is new

- **Codebook proposals** (Codebook → Proposals):
  - **Draft new codes** from up to 20 passages, with an optional focus. This is inductive coding.
  - **Refine existing codes** from your review decisions.
  - **Find evidence in my reviews**, offline and without AI.
  - You accept a proposal into the draft codebook, editing it first if you like, or reject it with a note. Nothing changes your codebook without you.
  - Every AI example is checked against the passages and stored in the passages' own words.
- **Code while reading:** "Create, freeze and assign" in the coding panel.
- **Memos:** four kinds (analytic, reflexive, theme, method), links to cases and sources, a kind filter, and every earlier version kept.
- **Themes and reflexivity:** new guide sections explain the parent-code-plus-theme-memo pattern and how to keep a reflexive record.
- **CLI versions:** Claude Code and Codex now only need a minimum version (2.1.284 and 0.160.0). Updates no longer block work, and every run records the version it used.
- **Faster loading:** the demo workspace response shrank from 13.5 MB to 7.4 MB.
- **Bug fixes:**
  - Saving a new code or memo twice no longer creates duplicates.
  - The demo now shows code examples.
  - CLI edits no longer reset fields you didn't give.
  - Long analyses no longer block coding.

## Also new (2026-10-07, after v0.2.0; not yet in a release)

- **Model defaults by task:** Claude Haiku / GPT-6-Luna for high-volume classification, Opus / GPT-6.1-Sol for codebook proposals, Opus / GPT-6-Astra for uncertain passages.
- **Model picker:** every AI form has one, with one-line descriptions, a named default and an "Other exact model ID" option to pin a version.
- **Exact model recorded:** each suggestion and proposal records the exact model that answered, for example `claude-haiku-4-5-20251001`.
- **Repeatability check:** Evaluation can run the same passages twice and show how often the model agrees with itself.
- **Model experiments:** Experiments can measure a classification model switch and keep it only if validation improves.
- **Fixes:**
  - Explicit Claude requests always ran on Haiku because of a routing setting named "claude".
  - Using Evaluate in the app blocked later experiments.
  - Haiku sometimes returned out-of-range spans; the request now gives each passage's length.


- 686 Python tests passed (5 skipped, 8 live tests not run); 63 web tests passed. Ruff, the data guard, npm audit and pip-audit are clean.
- The static demo check passed, with no API calls.
- Live synthetic runs: Claude drafted 6 codes in 29 s and Codex drafted 2 in 9 s. No codes were written without a decision.
- Codex (gpt-6-astra) built the CLI-version change and then reviewed the whole round. It found 1 high and 2 medium issues, all fixed.

## Decided for you (2026-10-07)

- **Security review:** a checklist review plus the earlier Codex review found nothing open. The built-in `/security-review` command is still yours to run if you want a third pass.
- **Dependabot:** merged six of the seven updates after reviewing each one. #4 (the uv_build version range) is still open: Dependabot hasn't refreshed it since the old check failure, so its CI has never run on current code. Comment `@dependabot rebase` on it again later and merge it if it turns green.
- **Release:** v0.2.0 is published with the Windows download and "what's new" notes.

## Still yours

- **Email privacy:** in GitHub → Settings → Emails, turn on "Keep my email addresses private".
- **Leftover:** the folder `%USERPROFILE%\Qualia\.app-browser` is safe to delete.
- **Your demo project:** it upgrades its database to version 4 the next time you open it. A backup file is written first.

## To start Qualia

Double-click the **Qualia** icon. To stop it, close the window.
