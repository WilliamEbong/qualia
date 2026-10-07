-- Memo kinds and links to cases and sources; every edit keeps the replaced version.
ALTER TABLE memos ADD COLUMN kind TEXT NOT NULL DEFAULT 'analytic'
 CHECK(kind IN ('analytic','reflexive','theme','method'));
ALTER TABLE memos ADD COLUMN case_id INTEGER REFERENCES cases(id);
ALTER TABLE memos ADD COLUMN source_id INTEGER REFERENCES sources(id);
CREATE TABLE memo_revisions (
 id INTEGER PRIMARY KEY, memo_id INTEGER NOT NULL REFERENCES memos(id),
 title TEXT NOT NULL, text TEXT NOT NULL, kind TEXT NOT NULL,
 segment_id INTEGER, code_id INTEGER, case_id INTEGER, source_id INTEGER,
 replaced_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX memo_revisions_memo ON memo_revisions(memo_id);
CREATE TRIGGER memo_history AFTER UPDATE ON memos
 WHEN OLD.title IS NOT NEW.title OR OLD.text IS NOT NEW.text OR OLD.kind IS NOT NEW.kind
 OR OLD.segment_id IS NOT NEW.segment_id OR OLD.code_id IS NOT NEW.code_id
 OR OLD.case_id IS NOT NEW.case_id OR OLD.source_id IS NOT NEW.source_id BEGIN
 INSERT INTO memo_revisions(memo_id,title,text,kind,segment_id,code_id,case_id,source_id)
 VALUES(OLD.id,OLD.title,OLD.text,OLD.kind,OLD.segment_id,OLD.code_id,OLD.case_id,OLD.source_id);
END;
CREATE TRIGGER memo_revisions_update BEFORE UPDATE ON memo_revisions
 BEGIN SELECT RAISE(ABORT,'memo_revisions is append-only'); END;
CREATE TRIGGER memo_revisions_delete BEFORE DELETE ON memo_revisions
 BEGIN SELECT RAISE(ABORT,'memo_revisions is append-only'); END;
