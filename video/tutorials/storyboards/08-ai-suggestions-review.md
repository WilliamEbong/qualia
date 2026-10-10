# Practice generating and reviewing suggestions

Guide sections: 12 (deterministic offline practice)
Target length: 3–4 min
Starting state: practice-study after codebook frozen

Recording note: Every classification in this tutorial uses `fake`; synthetic scores and rationales demonstrate the review workflow.

1. Select `practice-study` in `Local project`, then `Workspace`. — "Suggestions require a frozen codebook and imported passages."
2. Select the source containing the sister response. — "Start with one small source."
3. Select the navigation button `Review` with its displayed pending count. — "Classification proposes codes for you to review."
4. [demo] Expand `Backend availability and privacy` and inspect the `fake` entry. — "The fake backend is an offline deterministic demonstration."
5. [demo] Set `Backend` to `fake · offline`. — "Fake suggestions are practice output, not research-quality recommendations."
6. [demo] Set `Scope` to `Current source`; leave `Model` on its task default. — "Classification uses the project's latest frozen codebook."
7. [demo] Select `Run classification` and wait for the result. — "A suggestion does not become current coding until you accept it."
8. [demo] Inspect the classification result and pending suggestion cards. — "The result reports suggestions, segments, calls and cache hits."
9. Enter `researcher` in `Reviewer`. — "Your review identity becomes part of the decision history."
10. [demo] Select a suggestion by its displayed code name; read its excerpt and rationale. — "Read the passage and rationale together before deciding."
11. [demo] [zoom] Inspect the model-reported score and the caption explaining its review reason. — "Model-reported scores are not measured accuracy."
12. [demo] Inspect the validation ECE caption, including an unavailable result when shown. — "Missing calibration is not evidence of perfect accuracy."
13. [demo] Expand `Suggestion provenance` and inspect `Backend / model` and `Frozen codebook`. — "Provenance records the model and frozen definitions behind the suggestion."
14. [demo] Select `Open segment` to inspect the passage in context. — "Check the source context before accepting or rejecting a suggestion."
15. Return through the `Review` navigation button and enter `Practice acceptance after checking context.` in `Review note (optional)`. — "A review note records the reason for your decision."
16. [demo] Select the same suggestion, then choose `Accept` beside the `a` shortcut. — "Acceptance creates a current coding decision with the model identity and reviewer."
17. [demo] Select `Workspace`, then the reviewed segment; inspect `Current assignments` and `Provenance`. — "The original suggestion remains in history after review."
18. Select the source containing the short walk response, then return through `Review`. — "A second source lets you practice rejecting a suggestion."
19. [demo] Confirm `Backend` is `fake · offline`, choose `Current source` in `Scope` and select `Run classification`. — "Keep this practice run local and limited to the selected source."
20. [demo] Select a pending suggestion and read its excerpt, rationale and `Suggestion provenance`. — "Every suggestion still needs your decision, whatever its score."
21. Enter `Practice rejection after checking the passage.` in `Review note (optional)`; leave the field. — "Typing in a form does not trigger review shortcuts."
22. [demo] Select the suggestion's code-name button and press `r`. — "Rejection appends review evidence without creating a current assignment."
23. [demo] Open `Workspace`, select that source and inspect `Provenance`. — "Review resolves the same suggestion across any groups where it appeared."
