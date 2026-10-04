# Requirements analysis

Six functional requirements and four success criteria map to six dependency-ordered tasks; coverage 100%.

- Principle II: thresholds are implementation configuration in the mutable routing file; code definitions, frozen codebooks and METHODOLOGY.md are untouched. The agent never proposes methodology.
- Principle III: tuning math is deterministic sklearn code in sealed `qualia/eval`; KEEP/REVERT stays with the existing policy on the validation split; the dev split is fitting data and the protected split is never read. A dev evaluation row is appended (append-only) before the experiment's database pin, so the scope check still detects any operator-time database change.
- Principle IV: Jev remains the only file contacting TypeSafe; returning all probabilities widens no egress (same request, same answers). Every displayed score remains model-reported.
- Principle V/VII: no new external call path, dependency or default configuration; with no `code_thresholds`, outputs equal today's (Jev filtered at 0.5 by the router instead of the adapter).
- Cache: raw output is cached; thresholds are re-applied per read. Existing cached Jev entries (≥0.5 only) give identical results under defaults, and any threshold change alters routing.yaml and therefore `pipeline_version`, so stale entries are never reused under new thresholds.

Ambiguity resolved: thresholds apply to every backend that answers (one measured pipeline). Risk recorded: with default budgets Jev cannot evaluate the whole demo dev split, so live tuning needs a small project or owner-raised limits; the agent fails closed with "evaluation incomplete". No CRITICAL issue.
