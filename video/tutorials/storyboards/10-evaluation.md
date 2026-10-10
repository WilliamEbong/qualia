# Evaluate a classifier against reference labels

Guide sections: 14
Target length: 3–4 min
Starting state: demo project (AnnoMI)

Recording note: Use the editable local demonstration project and its prepared validation benchmark; all runs use `fake`, and all displayed metrics are demonstration results.

1. Select the locally installed demonstration project in `Local project`, then select `Evaluation`. — "Evaluation measures predictions against separately supplied reference labels."
2. Inspect `Evaluate validation split`. — "Evaluation predictions do not become research coding assignments."
3. [demo] Set `Evaluation backend` to `fake · offline`. — "Fake is a synthetic test backend for practicing the workflow."
4. [demo] Leave `Model` on its task default and select `Run validation evaluation`. — "A successful evaluation requires complete coverage of the validation records."
5. [demo] Wait for completion, then inspect the selected entry in `Recorded validation run`. — "The local demo validation split contains 1,258 utterances."
6. [demo] Read `Macro F1` and its explanation. — "Macro F1 averages over every code, so rare codes count equally."
7. [demo] Read `Micro F1` and compare it with `Macro F1`. — "Micro F1 pools code decisions, giving common codes more weight."
8. [demo] Read `Exact code-set match` and `Partial match (Jaccard)`. — "Exact and partial matching answer different questions."
9. [demo] Inspect `Cohen kappa`, `Nominal alpha` and the `Alpha basis` caption. — "Reference-versus-prediction agreement is not human intercoder reliability."
10. [demo] Inspect `Per-code performance`, including `Precision`, `Recall`, `F1` and `Support`. — "Read performance together with the number of reference examples for each code."
11. [demo] [zoom] Inspect any bracketed ranges beside per-code results. — "Wide 95 percent Wilson intervals signal fewer examples and more uncertainty."
12. [demo] Read `Validation ECE` and the review-workload sentence below the metrics. — "Calibration describes this validation set rather than guaranteed future accuracy."
13. [demo] Expand `Evaluation provenance and metric definitions`. — "Provenance binds the result to its benchmark, codebook and classifier identity."
14. [demo] Inspect `Backend / model`, `Frozen codebook` and `Benchmark hash` without reproducing their values in a card. — "Use the recorded identities when comparing or reproducing a run."
15. [demo] Inspect `Calibration by score band` when present, including `Mean score` and `Correct`. — "Compare model-reported scores with how often suggestions matched the reference."
16. [demo] Under `Check repeatability`, set `Passages in the sample (1–200)` to `50`. — "Repeatability asks whether the same model makes the same decisions twice."
17. [demo] Confirm `Evaluation backend` remains `fake · offline`; select `Check repeatability`. — "The check classifies the same sample twice without stored answers."
18. [demo] Read the `Identical code sets` result and `Run-to-run agreement by code` table. — "The sample stays the same for a project so comparisons are fair."
19. [demo] Inspect `Same decision` and `Kappa between runs`, including any `n/a` values. — "Kappa is unavailable when neither run varies for a code."
20. [demo] Return to the selected `Recorded validation run` and its metric explanations. — "Deterministic fake results demonstrate the workflow rather than model quality."
