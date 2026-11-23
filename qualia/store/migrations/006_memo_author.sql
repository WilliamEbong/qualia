-- Who last saved a memo, when the app knows (display metadata; coding provenance stays in coding_events).
ALTER TABLE memos ADD COLUMN author TEXT;
