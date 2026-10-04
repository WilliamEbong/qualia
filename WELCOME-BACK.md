# Qualia — build in progress

The offline research workspace, review, evaluation, guarded fake improvement loop, and mixed-methods/data-science analysis are built. Full offline regression: 390 passed; browser checks cover analytics, chart/evidence links, exports, and the static demo without API calls. Native Claude/Codex activation remains gated; no live parity claim is made.

Final local work is saved: functional baseline295c712, presentation checkpointfe7b8e8. Its protected functional diff is empty; design guard returned to build mode. Final web checks:30 tests, TypeScript and normal/static builds pass. Lighthouse96 performance/100 accessibility/CLS0.000125. The illustrated [user guide](docs/USER-GUIDE.md) and [final report](docs/FINAL-REPORT.md) explain all workflows and the remaining owner steps. Source documents02–05 and constitution remain unchanged.

Run `uv run qualia open` to use the populated demo. Codex's standalone synthetic classification and delegation probes passed with existing sign-in; Qualia's native integration is still disabled pending its stricter engineering gates. Jev is installed but off with a blank key; follow docs/JEV-SETUP.md. Research projects live under %USERPROFILE%\Qualia, outside this checkout. Do not paste a key into chat. The static demonstration is prepared locally, not deployed.

Last pushed checkpoint: 8029a36, private CI success. Newer local commits are preserved; automatic review requires explicit owner approval before another main push. The owner authorized the optional official source security review, but its Windows drive-ancestor permission check blocked analysis; no permissions were modified. Native setup/accounting decisions and exact owner steps are in ignored OWNER-NEEDED.md.

Resume in this folder with `codex` and scripts/prompts/recovery.md. The existing runner is scripts/run-build.ps1; its known model override is `-Model gpt-6-astra`. Do not mark BUILD COMPLETE until all load-bearing checks have evidence.
