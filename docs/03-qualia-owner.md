# 03 — Qualia: Owner's Manual

*Your side of the build: setup before launch, the one launch command, what to do when your phone buzzes, the
usage-limit ritual, checking the result, going public, and troubleshooting. Nothing here needs code. Hands-on time:
~15 min today at the PC + ~2 min on your phone · then nothing until an alert · ~10 min testing at the end + ~3 min to
go public. Optional Jev setup: ~10 min, any time.*

## §0 Before launch — the backstops (today, ~10 min)
**0.1 Paid extra usage OFF (~2 min).** The backstop no bug can bypass: when your plan's limit is hit, work pauses
instead of billing you. Claude: claude.ai → Settings → Usage — if an "extra usage" switch is on, turn it off. ChatGPT:
chatgpt.com/codex/settings/usage — if credit auto-reload is on, turn it off.
**0.2 Check your ChatGPT plan (~1 min).** The build model (GPT-6 Astra) is scarce on Plus: roughly 5–45 messages per 5
hours (OpenAI pricing page, 2026-10-03). **Variant A (recommended): Pro** — no 5-hour limit, the build can finish in a
day or two. **Variant B: Plus** — same result, slower: the runner simply waits out each limit and resumes.
**0.3 Update Codex (~3 min).** Your installed Codex (0.144.6) does not list GPT-6 Astra. Windows key → type `powershell`
→ Enter, then paste these one at a time:
```
npm install -g @openai/codex@latest
```
```
codex debug models
```
Good = the list includes `gpt-6-astra`. If not, close PowerShell, reopen, and run the second line again.
**0.4 Let Codex trust the project folder (~1 min).** Needed so the project's safety rules load.
**Variant A (recommended):** paste, then answer "yes"/"trust" if Codex asks about trusting this folder, then type `/exit`:
```
cd "C:\Users\Owner\OneDrive\Documents\Qualia"; codex
```
**Variant B:** Notepad → File → Open → `C:\Users\Owner\.codex\config.toml` (set the file-type dropdown to All Files) →
paste at the very end → Save:
```
[projects.'C:\Users\Owner\OneDrive\Documents\Qualia']
trust_level = "trusted"
```
**0.5 Phone alerts (~2 min, phone).** Install the free **ntfy** app (App Store / Google Play) → tap **+** → subscribe to
the topic name Claude gave you in chat (it is also in `scripts\ntfy-topic.local`). Treat that name like a password —
anyone who knows it can read the alerts. Alerts carry status text only, never research data.
**0.6 Power (~1 min).** Plug the PC in and leave the lid open. The runner keeps the PC awake while its window is open.

## §1 Tool check (~2 min)
Paste into PowerShell:
```
git --version; gh auth status; uv --version; node --version; codex --version; claude --version
```
Good = six versions and "Logged in to github.com". A line in red → §9. Your Codex plugins (Superpowers, Ponytail,
taste-skill) are already installed; nothing to add.

## §2 Launch (~1 min, then walk away)
```
cd "C:\Users\Owner\OneDrive\Documents\Qualia"; powershell -ExecutionPolicy Bypass -File scripts\run-build.ps1
```
Leave the window open. It starts Codex with the kickoff prompt (§6), then keeps relaunching fresh sessions until the
build is done or it needs you. It creates a PRIVATE GitHub repo `qualia` on your account — nothing goes public until
you choose to (§8). Same command to relaunch at any time; it picks up where it stopped.

## §3 Keys and secrets
**"Any prompt asking for a key in chat gets refused — it goes in the file."** The core build needs no keys at all: it
uses your existing Claude and ChatGPT logins. The only optional key is Jev (§4). Save every key in your password manager.

## §4 Optional: Jev (any time, ~10 min — the build never waits for it)
Jev is a cheap, fast classifier ($0.042 per million input tokens, output free). It is US-hosted and has no zero-
retention option by default, so use it only on non-sensitive or de-identified projects; Qualia keeps it OFF unless you
switch it on per project. Creating the account and adding billing are yours — an agent must not sign up or pay for you.
1. Browser → console.typesafe.ai → "Continue with Google" or "Email me a code".
2. Add billing (new accounts get no free credit, per TypeSafe's co-founder on X — unverified on the console).
3. Sidebar → **API Keys** → create a key → copy it → save it in your password manager.
4. Notepad → paste the line below with your key → File → Save As → folder `C:\Users\Owner\OneDrive\Documents\Qualia`,
   file name `.env`, "Save as type: All Files":
```
TYPESAFE_API_KEY=paste-your-key-here
```
5. Nothing else: the next session detects it, and the Jev phase runs its live test.

## §5 Usage-limit recovery ritual (expected, not an emergency)
Nothing is lost when a limit hits — every step is committed. The runner waits 30 minutes and retries by itself. If you
ever drive a session by hand instead: open PowerShell in the project folder, start `codex`, and paste:
```
Read docs/BUILD-STATE.md and git log --oneline -15. Report exactly where the last
session stopped, then resume docs/02-qualia-build.md from the first unchecked item of the current
phase. Same HARD STOPS and BUILD-STATE ritual as always.
```
Tips: start the build early in a fresh usage window; a fresh session beats a long, tired one — the runner already
works this way.

## §6 Kickoff & gates
The runner sends this kickoff once (you never paste it unless running by hand from the project folder):
```
Read C:\Users\Owner\OneDrive\Documents\Qualia\docs\01-qualia-context.md then C:\Users\Owner\OneDrive\Documents\Qualia\docs\02-qualia-build.md in full. Begin with the
preflight & assumption audit: verify tooling and .env, diff repo state against the doc,
classify each workstream, write/refresh CLAUDE.md, then present an adjusted plan
following the doc's phases, subagents, and acceptance pass. Honor all invariants in
docs/01-qualia-context.md §6; never set temperature/top_p/top_k; keep max_tokens bounded. Flag any
preflight failure with the exact fix and continue where safe.
```
**What good looks like** (open `docs\BUILD-STATE.md` any time; each phase pastes its evidence there):
P0 tool table all ✅, repo PRIVATE · P1 tests green, "contracts frozen" · P2 second import says "0 new sources" ·
P3 prompt-injection test passes · P4 metrics match the reference numbers · P5 end-to-end screenshots, an experiment
tagged KEEP · P6 CI green, one experiment each from Claude and Codex · P7 design checklist ticked · P8 demo makes zero API
calls, Lighthouse ≥ 90/95 · P9 Jev tests (or "deferred") · P10 first line says `BUILD COMPLETE`.
Optional before launch day: `/code-review ultra` in Claude Code — a paid deep review (~$5–25 in usage credits). Default:
skip for V1 (it caps at 8,000 changed lines); worth it on later, smaller changes.

## §7 When your phone buzzes
- **"Qualia: owner needed"** → open `OWNER-NEEDED.md` in the project folder (Notepad). Write your answer under each
  question → File → Save As `OWNER-ANSWERS.md` (All Files) → delete `OWNER-NEEDED.md` → relaunch with §2. Typical
  causes and one-line fixes: Codex lacks Astra → §0.3 · logged out → run `codex login`, or `claude` then type `/login`
  · security scan wants a login → `npx @openai/codex-security login` · "no progress" stall → just relaunch once; if it
  stalls again, screenshot the newest file in `logs\` into a Claude chat.
- **"Qualia: build complete"** → §8.  **"Qualia: runner stopped"** → relaunch with §2.

## §8 After the build (~10 min testing + ~3 min going public)
1. PowerShell in the project folder → `uv run qualia demo` → then `uv run qualia open`. Good = a browser tab opens on
   the demo project with transcripts on the left. Research projects live in `%USERPROFILE%\Qualia` (`QUALIA_HOME`).
2. Click a transcript → press ↓ to move between segments → press a number to apply a code. Good = a coloured stripe.
3. Run AI coding on a few segments → open the review queue → accept one, reject one. Open the code-by-case matrix.
4. `uv run qualia improve --agent claude --budget 1` → the experiment history shows KEEP or REVERT with numbers.
5. Go public (your decision): github.com → your `qualia` repo → Settings → General → Danger Zone → Change visibility →
   Public. Then Settings → Pages → Source: GitHub Actions. Then Settings → General → Social preview → upload
   `docs\social-preview.png`.
6. Next stage (Claude Code improvement): start a planning chat with "amend the docs: Claude Code improvement stage".
Anything off → paste the symptom verbatim into a Codex or Claude Code session in the project folder.
If you use Obsidian: the project folder opens as a vault — `docs\`, AGENTS.md, CLAUDE.md and BUILD-STATE.md are the map.

## §9 Troubleshooting quick hits
- No alerts for hours and the PC slept → runner window closed or lid shut → relaunch §2.
- `codex` / `uv` / `gh` "not recognized" → reinstall that tool, close and reopen PowerShell.
- "running scripts is disabled" → you started the runner without `-ExecutionPolicy Bypass` → use the exact §2 line.
- Browser says the port is busy → add `QUALIA_PORT=8766` to `.env` → `uv run qualia open` again.
- Logs say "usage limit" → expected; the runner waits (§5).
- A session says an action was **blocked by a rule or guard** → it tried something destructive or a protected file;
  that's the system working — if the change is genuinely needed it lands in OWNER-NEEDED.md.
- Anything confusing → screenshot it into a Claude chat. Codex executes, the chat diagnoses.
