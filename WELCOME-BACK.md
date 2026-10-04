# Qualia — build in progress

The offline research workspace, review, evaluation, guarded fake improvement loop, and mixed-methods/data-science analysis are built. Full offline regression: 390 passed; browser checks cover analytics, chart/evidence links, exports, and the static demo without API calls. Native Claude/Codex activation remains gated; no live parity claim is made.

Current work: finish the final analysis refresh check, commit the functional baseline, activate the preauthorized D0 design guard, then complete the presentation pass and final documentation. The detailed user guide is drafted at docs/USER-GUIDE.md. Source documents 02–05 and the constitution remain unchanged. See docs/BUILD-STATE.md for exact evidence.

Run `uv run qualia open` to use the populated demo. Jev is installed but off with a blank key; follow docs/JEV-SETUP.md. Research projects live under %USERPROFILE%\Qualia, outside this checkout. Do not paste a key into chat.

Last pushed checkpoint: 8029a36, private CI success. Newer local commits are preserved; automatic review requires explicit owner approval before another main push. The owner authorized the optional official source security review, but its Windows drive-ancestor permission check blocked analysis; no permissions were modified. Native setup/accounting decisions and exact owner steps are in ignored OWNER-NEEDED.md.

Resume in this folder with `codex` and scripts/prompts/recovery.md. The existing runner is scripts/run-build.ps1; its known model override is `-Model gpt-6-astra`. Do not mark BUILD COMPLETE until all load-bearing checks have evidence.