# Requirements analysis

Six functional requirements and four success criteria map to six dependency-ordered tasks; coverage 100%.

- Principle III: all new metric math lives in sealed `qualia/eval/metrics.py`, is deterministic and uses maintained libraries (scipy Wilson interval, sklearn precision–recall curve). Model self-report still never counts as accuracy; review figures are derived from correctness against references.
- Principle VII / technology constraints: scipy is a new direct declaration, gated by owner decision05; it is already in the lock as a scikit-learn requirement, so nothing new is installed. The 90% target is a constant, not configuration.
- Principles I, II, IV–VI: no event, methodology, vendor, egress or data-path change. `evaluation_runs` stays append-only; new keys live in the existing JSON column; old rows are read as-is.
- Design docs 04/05: trust grammar unchanged; new text is additive; logic stays in `web/src/lib/`.

Ambiguity resolved without owner input: "review below the cutoff" uses `score < cutoff` because sklearn thresholds mean `score >= threshold` is kept. Kappa band words follow Landis & Koch (1977); alpha bands follow Krippendorff (2004). No CRITICAL issue.
