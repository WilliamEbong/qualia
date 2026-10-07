# Qualia - handoff (2026-10-07)

**The improvement round is finished, verified and pushed to main.** Details: docs/BUILD-STATE.md (P20) and docs/answers/07-improvement-round.md.

| What | Where |
|---|---|
| Repository | https://github.com/WilliamEbong/qualia |
| Online demo (read-only) | https://williamebong.github.io/qualia/ |
| Windows download | https://github.com/WilliamEbong/qualia/releases/latest (still v0.1.1; this round is not released yet) |
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

## Evidence

- 674 Python tests passed (5 skipped, 8 live tests not run); 44 web tests passed. Ruff, the data guard, npm audit and pip-audit are clean.
- The static demo check passed, with no API calls.
- Live synthetic runs: Claude drafted 6 codes in 29 s and Codex drafted 2 in 9 s. No codes were written without a decision.
- Codex (gpt-6-astra) built the CLI-version change and then reviewed the whole round. It found 1 high and 2 medium issues, all fixed.

## Optional next steps

- **Release:** tag v0.1.2 (or v0.2.0) so the Windows download includes this round. I didn't tag it, because publishing a release is your call.
- **Security review:** run `/security-review` in Claude Code. It is still recommended.
- **Dependabot:** PR #8 is green; PRs #1–#6 need `@dependabot rebase` first.
- **Email privacy:** in GitHub → Settings → Emails, turn on "Keep my email addresses private".
- **Leftover:** the folder `%USERPROFILE%\Qualia\.app-browser` is safe to delete.
- **Your demo project:** it upgrades its database to version 4 the next time you open it. A backup file is written first.

## To start Qualia

Double-click the **Qualia** icon. To stop it, close the window.
