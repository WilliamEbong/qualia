# Calibrated decisions scope — 2026-10-04

After a review of open-source projects built around TypeSafe's Jev model, the owner asked:

> I want to build all the beneficial features you found into qualia and still ensure that it is clean, stable, efficient, and without conflicts or errors

and later added:

> make sure we are not over engineering, I just want qualia to be an impressive, mature and most importantly useful tool and portfolio piece. I also want to ensure that it is efficient, clean, and stable. I want it to be very user friendly so effort has to be there for UX/UI.

The owner then answered three scoping questions in this chat:

1. **Local decision-model backend (Ollaya/Laya on this machine):** "Skip it for now".
2. **Declaring `scipy` for Wilson intervals versus hand-writing the formula:** "is breaking the rule a big deal? ensure that rules serve the purpose of a good product rather than prevent it. You're the expert, you decide for this one."
   Decision taken under that delegation: declare `scipy>=1.18,<1.19` as a direct dependency. It is already installed and locked as a scikit-learn requirement, so no new package is downloaded, and the "never hand-roll metrics" rule (C2) stays intact.
3. **How threshold tuning should work:** "I don't even know what this is, you decide".
   Decision taken under that delegation: a deterministic, no-AI improvement agent (`qualia improve --agent thresholds`) chooses per-code suggestion thresholds on the dev split, and Qualia's existing measured policy keeps or reverts the change on the validation split.

This authorizes features 010 (evaluation uncertainty) and 011 (per-code thresholds, thresholds agent and review UX), plus the Jev request-size batching fix. It does not authorize the local backend, new UI dependencies, score recalibration, credential, permission, visibility or billing changes.
