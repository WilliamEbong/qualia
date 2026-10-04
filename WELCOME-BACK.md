# Qualia - handoff (2026-10-04)

**Qualia is public and finished for this round.**

| What | Where |
|---|---|
| Repository | https://github.com/WilliamEbong/qualia |
| Online demo (read-only, no install) | https://williamebong.github.io/qualia/ |
| Windows download | https://github.com/WilliamEbong/qualia/releases/latest (v0.1.1) |
| User guide | docs/USER-GUIDE.md |

## What Qualia does now

- **Code transcripts** with your own codebook. Code by keyboard, keep memos, retrieve evidence, compare cases in a matrix, and analyse frequencies, co-occurrence and numbers. Export CSV, JSON, Python or R.
- **Review AI suggestions one keystroke at a time.** Each suggestion says why it is waiting, least certain first. AI can come from rules, your own Claude Code or Codex subscription, or Jev.
- **See honestly how good the AI is.** Evaluation shows 95% ranges, plain-language explanations, agreement words and a calibration table, plus how much of the AI's work to check for 90% precision.
- **Tune the AI without touching your methodology.** Experiments → **Tune thresholds** learns a cutoff per code and keeps it only if validation improves. On the demo with Jev, macro-F1 went from 0.523 to 0.567, and to 0.572 on confirmation.
- **A double-click app.** On your PC, the **Qualia** icon opens Qualia in its own window, in Chrome because that's your default browser. Closing the window shuts Qualia down within about three minutes. New users download the zip, unblock and extract it, and double-click **Install Qualia** once.

## State and evidence

- **Tests:** 566 Python tests passed (5 skipped, 6 live tests not run); 37 web tests; all CI checks green.
- **Publishing:** the release workflow built v0.1.0 and v0.1.1, and the Pages workflow deployed the demo.
- **Pre-public audit:** no secrets in any commit or file, no private research data, and all 101 screenshots clean.
- **Records:** decisions with their reasoning are in docs/answers/01–06, the full build log in docs/BUILD-STATE.md, and Spec Kit records for features 010–013 in specs/.

## Optional next steps

- **Security review:** run `/security-review` in Claude Code. You'd planned it before going public; my own audit found nothing, but an independent pass is still worthwhile.
- **Email privacy:** in GitHub → Settings → Emails, turn on "Keep my email addresses private" for future commits. Past commits keep your Gmail address.
- **Dependabot:** 7 Dependabot pull requests are open (dependency updates) and now public; review or merge them when convenient.
- **Faster project loading:** the suggested task "Shrink Qualia's 12 MB workspace payload" is waiting in the app. It would speed up opening large projects.
- **Leftovers:**
  - The folder `%USERPROFILE%\Qualia\.app-browser` is safe to delete.
  - An old Chrome tab titled "Qualia — research workspace" can be closed.
- **Later:** a native desktop app (signed installer, automatic updates, works on locked-down PCs) is the next big UX step if Qualia gains users.

## To start Qualia

Double-click the **Qualia** icon on your Desktop or in the Start menu. To stop it, close the window.
