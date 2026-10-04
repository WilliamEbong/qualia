# Qualia - now a double-click app

## What's new: no more terminal

- **Your Qualia icon** is on your Desktop and in the Start menu. Double-click it: Qualia opens in its own window, with no tabs, no address bar and no black terminal window.
- **To stop Qualia, just close its window.** It notices and shuts itself down within about three minutes; nothing keeps running in the background. Opening the icon again in that time simply reopens the window.
- **For other people:** they download one zip from GitHub Releases, unblock and extract it, and double-click **Install Qualia** once. It installs everything Qualia needs, adds the demo and creates the icon. No Git, Node or commands needed. The README and user guide §2 now lead with this path; the developer path is still documented.

I tested this end to end on this PC three ways: from a package built like the release, from the actual zip GitHub built, and from your own Qualia folder. Each time the window opened cleanly and Qualia shut itself down after the window closed.

One thing I changed along the way: my first version gave Qualia its own browser profile. That made Edge show its "Sync your profile" and onboarding windows, and it kept Edge running. I replaced it before release with a simpler approach that uses your normal Edge, so there are no prompts.

## Checks

- 566 Python tests passed (5 skipped, 6 live tests not run); 37 web tests, typecheck and build pass.
- Ruff, data guard and the secret scan are clean.
- The release workflow builds the download zip on GitHub.
- Final CI status and the v0.1.0 release are recorded at the end of BUILD-STATE.

## Small leftovers

- **Unused folder:** `%USERPROFILE%\Qualia\.app-browser` is left over from the first version. It's safe to delete; my safety rules block deleting folders.
- **Old browser tab:** a Chrome tab titled "Qualia — research workspace" from an earlier session may still be open. Close it.

## Still yours: making Qualia public

Nothing changed here; the steps are in docs/answers/06-public-release.md:

1. Optional: run `/security-review` in Claude Code.
2. Make it public:
   ```powershell
   gh repo edit WilliamEbong/qualia --visibility public --accept-visibility-change-consequences
   ```
3. On GitHub: Settings → Pages → Source: **GitHub Actions**, then Actions → **Public demo** → **Run workflow**.
4. Optional: Settings → Emails → "Keep my email addresses private".

Once public, the Releases page holds the download zip that the README points to.
