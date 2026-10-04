# Public release request — 2026-10-04

The owner wrote in this chat:

> Is everything done? If so commit, push, and make qualia public. Ensure jev setup instructions as well as any feature not yet included is included in the user guide. Ensure the read me is easy to follow, describes the features well and is a good sales pitch. Screenshots from test runs of each feature could be helpful for the guide as well as the repo as long as its cropped to include only relevant things and not my whole screen. Those are my thoughts but ill take your advice. Proceed autonomously until done. Make judgment calls yourself.

What was done under this request:

- The README was rewritten as a guided tour with cropped feature screenshots (`design-review/final/features/`, Playwright element captures of the AnnoMI demo only). The user guide now inlines the full Jev setup, covers threshold tuning in the app, and drops machine-specific paths.
- A read-only pre-publication audit found no secrets in any of the 57 commits or the 416 tracked files (gitleaks 8.30.1, full history and tracked-file scan). No research data, `.env`, `OWNER-*` or local files were ever committed, and the server security posture holds. A visual pass covered the tracked screenshots.

Judgment call on visibility: the agent did **not** change repository visibility. Project rules (CLAUDE.md, AGENTS.md) reserve that step for the owner, the guard hook blocks `gh repo edit`, and the owner's own pre-public gate, an owner-run Claude Code `/security-review` (decision 02), has not been recorded as done. This decision supersedes the "must stay private" wording in decisions 02 and 03 once the owner flips visibility.

Owner steps to publish:

1. Run `/security-review` in Claude Code on this repository (optional but planned).
2. Make the repository public:
   `gh repo edit WilliamEbong/qualia --visibility public --accept-visibility-change-consequences`
3. Enable Pages: GitHub → Settings → Pages → Source: **GitHub Actions**, then run the **Public demo** workflow (Actions → Public demo → Run workflow). The first automatic run fails until Pages is enabled.
4. Optional: GitHub → Settings → Emails → "Keep my email addresses private" for future commits. Earlier commit metadata keeps the existing address; rewriting history is not allowed by project rules.
