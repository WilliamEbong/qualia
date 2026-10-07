# Plan

1. `qualia/store/migrations/004_memo_links.sql`: add `kind` (CHECK), `case_id`, `source_id` to `memos`; `memo_revisions` with an AFTER UPDATE trigger guarded by `WHEN` any field changed; append-only triggers. `db.py`: `MEMO_KINDS`, `APPEND_ONLY` gains `memo_revisions`, `save_memo` validates kind and the new links.
2. API: `MemoInput` gains kind/case/source; workspace payload adds `memo_revisions` (defaulted for old snapshots); export lists the table. CLI `memo` passes only provided options and maps `ValueError` to a clean error.
3. Web: `codeInVivo` in `lib/workspace.ts` chains the existing code, freeze and coding endpoints; memo filter and history helpers in the same controller; `Transcript.tsx` coding-panel form; `Memos.tsx` kind, links, filter and history.
4. Docs: user guide sections for in-vivo coding, memo kinds, themes and reflexivity.

Ponytail: no theme table, no count roll-up, no memo restore button, no new API route (in-vivo coding reuses three existing ones).
