# Read experiments and measured KEEP or REVERT decisions

Guide sections: 15
Target length: 3–4 min
Starting state: demo project (AnnoMI)

Recording note: Use the editable local demo with prepared benchmarks and a clean project Git baseline; explicitly select `fake` for both operator and validation classifier.

1. Select the local demonstration project in `Local project`, then select `Experiments`. — "Experiments measure changes to implementation configuration and prompts."
2. [card] Show `Before running: prepared validation benchmark, clean project Git baseline, enough local budget`. — "Save and review intended workspace changes before starting an experiment."
3. [card] [demo] From the application folder, show `uv run qualia improve --project demo --agent fake --backend fake --budget 1`. — "Use the fake operator and classifier to practice offline."
4. [card] [demo] Show the command's recorded outcome after it finishes, without substituting a promised decision. — "Qualia's measured policy decides KEEP or REVERT automatically."
5. [card] [demo] Show `uv run qualia history --project demo`. — "History retains the attempt and its measured decision."
6. [demo] Refresh the app with Ctrl+R, confirm the demo in `Local project`, then select `Experiments`. — "Completed attempts appear with their evidence in the experiment history."
7. [demo] Select the newest fake attempt under `Recorded attempts`. — "Read the recorded decision rather than assuming a gain was kept."
8. [demo] Inspect its `KEEP` or `REVERT` label and the reason below the attempt title. — "REVERT is a valid outcome, not an instruction to bypass the policy."
9. [demo] Read `Operator hypothesis`. — "The hypothesis is a proposed explanation rather than proof of improvement."
10. [demo] Inspect `Measured validation results` across `Baseline`, `Candidate` and `Confirmation`. — "A candidate gain alone does not establish a KEEP decision."
11. [demo] Compare macro F1 with exact code-set match in the measurement table. — "One improved metric is not a blanket claim of better qualitative judgment."
12. [demo] Inspect any `n/a` cells in `Measured validation results`. — "Unavailable measurements must not be inferred from the hypothesis."
13. [demo] Inspect `Changed files`. — "Experiments do not authorize changes to research code definitions or methodology."
14. [demo] [zoom] Expand `Experiment provenance` and inspect `Operator` and both backend/model fields. — "The recorded identities distinguish the operator from the validation classifier."
15. [demo] Inspect `Commit`, `Tag` and `Frozen codebook` in `Experiment provenance`. — "Kept changes receive a local commit and tag while rejected evidence remains."
16. [demo] Under `Tune suggestion thresholds`, set `Classifier to tune` to `fake · offline`. — "Threshold tuning fits cutoffs on dev data and measures them on validation data."
17. [demo] Leave `Model` on its task default; select `Tune thresholds` and wait. — "Tuning needs dev and validation benchmarks and a clean project Git state."
18. [demo] Inspect the newly selected attempt's decision and `Measured validation results`. — "Fake uses constant scores, so threshold tuning rarely helps it."
19. [card] Show `Pending recovery: preserve the workspace and recovery evidence; do not remove the lock`. — "An interrupted operation requires recovery rather than bypassing its safeguards."
