# Requirements analysis

Six requirements, three success criteria, four tasks; coverage 100%.

- Principle I: memo history is append-only by trigger and written by the database itself, so no code path can skip it. Coding events from in-vivo coding go through the existing `assign` path with full provenance and a real frozen version.
- Principle II: in-vivo coding is an explicit human action; the freeze it performs is the same human freeze, labelled in the UI.
- Principles III–VII: no AI, egress, evaluation or dependency change. No CRITICAL issue.

Risk: the one-step freeze also captures unrelated draft edits; the caption says so, and the separate Freeze button remains for deliberate versioning.
