CREATE TABLE sources (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL CHECK(length(name)>0),
 content_hash TEXT NOT NULL UNIQUE, text TEXT NOT NULL,
 version_of INTEGER REFERENCES sources(id),
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE segments (
 id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL REFERENCES sources(id),
 start INTEGER NOT NULL CHECK(start>=0), end INTEGER NOT NULL CHECK(end>start),
 ordinal INTEGER NOT NULL CHECK(ordinal>=0), speaker TEXT,
 UNIQUE(source_id,ordinal)
);
CREATE INDEX segments_source ON segments(source_id,ordinal);
CREATE TRIGGER segment_bounds BEFORE INSERT ON segments BEGIN
 SELECT CASE WHEN NEW.end > (SELECT length(text) FROM sources WHERE id=NEW.source_id)
 THEN RAISE(ABORT,'segment exceeds source') END;
END;
CREATE TABLE cases (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE CHECK(length(name)>0));
CREATE TABLE source_cases (
 source_id INTEGER NOT NULL REFERENCES sources(id), case_id INTEGER NOT NULL REFERENCES cases(id),
 PRIMARY KEY(source_id,case_id)
);
CREATE TABLE attributes (
 id INTEGER PRIMARY KEY, case_id INTEGER REFERENCES cases(id), source_id INTEGER REFERENCES sources(id),
 key TEXT NOT NULL, value TEXT NOT NULL,
 CHECK((case_id IS NOT NULL)+(source_id IS NOT NULL)=1)
);
CREATE INDEX attributes_key ON attributes(key);
CREATE TABLE codes (
 id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES codes(id),
 name TEXT NOT NULL CHECK(length(trim(name))>0), status TEXT NOT NULL DEFAULT 'active'
 CHECK(status IN ('active','archived')), definition TEXT NOT NULL DEFAULT '',
 include TEXT NOT NULL DEFAULT '', exclude TEXT NOT NULL DEFAULT '',
 examples_pos TEXT NOT NULL DEFAULT '[]' CHECK(json_valid(examples_pos)),
 examples_neg TEXT NOT NULL DEFAULT '[]' CHECK(json_valid(examples_neg)),
 CHECK(parent_id IS NULL OR parent_id<>id)
);
CREATE TABLE codebook_versions (
 id INTEGER PRIMARY KEY, snapshot_json TEXT NOT NULL CHECK(json_valid(snapshot_json)),
 hash TEXT NOT NULL UNIQUE,
 frozen_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE experiments (
 id INTEGER PRIMARY KEY, slug TEXT NOT NULL, agent TEXT NOT NULL,
 decision TEXT NOT NULL CHECK(decision IN ('KEEP','REVERT')),
 reason TEXT NOT NULL, hypothesis TEXT NOT NULL DEFAULT '',
 before_json TEXT NOT NULL CHECK(json_valid(before_json)),
 after_json TEXT NOT NULL CHECK(json_valid(after_json)),
 changed_files_json TEXT NOT NULL DEFAULT '[]' CHECK(json_valid(changed_files_json)),
 commit_hash TEXT, tag TEXT,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE coding_events (
 id INTEGER PRIMARY KEY, segment_id INTEGER NOT NULL REFERENCES segments(id),
 span_start INTEGER NOT NULL CHECK(span_start>=0), span_end INTEGER NOT NULL CHECK(span_end>span_start),
 code_id INTEGER NOT NULL REFERENCES codes(id),
 action TEXT NOT NULL CHECK(action IN ('assign','remove','suggest','accept','reject')),
 actor_type TEXT NOT NULL CHECK(actor_type IN ('human','model')), actor TEXT NOT NULL CHECK(length(trim(actor))>0),
 backend TEXT, model TEXT, cli_version TEXT, score REAL CHECK(score>=0 AND score<=1), rationale TEXT,
 codebook_version_id INTEGER NOT NULL REFERENCES codebook_versions(id),
 pipeline_version TEXT NOT NULL CHECK(length(trim(pipeline_version))>0), prompt_hash TEXT NOT NULL DEFAULT '',
 experiment_id INTEGER REFERENCES experiments(id), suggestion_id INTEGER REFERENCES coding_events(id),
 review_status TEXT NOT NULL DEFAULT 'none' CHECK(review_status IN ('none','pending','accepted','rejected')),
 review_trigger TEXT, reviewed_by TEXT,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 CHECK(actor_type='human' OR (backend IS NOT NULL AND length(trim(backend))>0
 AND model IS NOT NULL AND length(trim(model))>0
 AND cli_version IS NOT NULL AND length(trim(cli_version))>0 AND length(trim(prompt_hash))>0)),
 CHECK(action NOT IN ('accept','reject') OR (suggestion_id IS NOT NULL AND reviewed_by IS NOT NULL)),
 CHECK(action<>'suggest' OR (actor_type='model' AND review_status='pending'))
);
CREATE INDEX coding_code ON coding_events(code_id);
CREATE INDEX coding_segment ON coding_events(segment_id);
CREATE INDEX coding_review ON coding_events(review_status);
CREATE UNIQUE INDEX coding_review_once ON coding_events(suggestion_id) WHERE action IN ('accept','reject');
CREATE TRIGGER coding_span BEFORE INSERT ON coding_events BEGIN
 SELECT CASE WHEN NEW.span_end > (SELECT end-start FROM segments WHERE id=NEW.segment_id)
 THEN RAISE(ABORT,'coding event span exceeds segment') END;
 SELECT CASE WHEN NOT EXISTS (
 SELECT 1 FROM codebook_versions, json_each(snapshot_json) AS code
 WHERE codebook_versions.id=NEW.codebook_version_id AND json_extract(code.value,'$.id')=NEW.code_id
 ) THEN RAISE(ABORT,'code absent from frozen version') END;
 SELECT CASE WHEN NEW.action IN ('accept','reject') AND NOT EXISTS (
 SELECT 1 FROM coding_events e WHERE e.id=NEW.suggestion_id AND e.action='suggest'
 AND e.segment_id=NEW.segment_id AND e.code_id=NEW.code_id
 AND e.span_start=NEW.span_start AND e.span_end=NEW.span_end
 AND e.codebook_version_id=NEW.codebook_version_id
 ) THEN RAISE(ABORT,'review does not match suggestion') END;
END;
CREATE VIEW current_codings AS
 SELECT * FROM (
 SELECT *, row_number() OVER(PARTITION BY segment_id,code_id,span_start,span_end ORDER BY id DESC) AS rank
 FROM coding_events WHERE action IN ('assign','remove','accept')
 ) WHERE rank=1 AND action IN ('assign','accept');
CREATE VIEW pending_suggestions AS
 SELECT e.* FROM coding_events e WHERE e.action='suggest' AND NOT EXISTS (
 SELECT 1 FROM coding_events r WHERE r.suggestion_id=e.id AND r.action IN ('accept','reject'));
CREATE TABLE memos (
 id INTEGER PRIMARY KEY, title TEXT NOT NULL, text TEXT NOT NULL,
 segment_id INTEGER REFERENCES segments(id), code_id INTEGER REFERENCES codes(id),
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE feedback_events (
 id INTEGER PRIMARY KEY, coding_event_id INTEGER NOT NULL REFERENCES coding_events(id),
 decision TEXT NOT NULL CHECK(decision IN ('accept','reject')), actor TEXT NOT NULL CHECK(length(actor)>0),
 note TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE evaluation_runs (
 id INTEGER PRIMARY KEY, split TEXT NOT NULL CHECK(split IN ('dev','validation','protected')),
 backend TEXT NOT NULL, model TEXT NOT NULL, codebook_version_id INTEGER REFERENCES codebook_versions(id),
 pipeline_version TEXT NOT NULL, metrics_json TEXT NOT NULL CHECK(json_valid(metrics_json)),
 predictions_json TEXT NOT NULL CHECK(json_valid(predictions_json)),
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE usage_ledger (
 id INTEGER PRIMARY KEY, backend TEXT NOT NULL, model TEXT NOT NULL,
 calls INTEGER NOT NULL CHECK(calls>=0), segments INTEGER NOT NULL CHECK(segments>=0),
 input_tokens INTEGER NOT NULL DEFAULT 0 CHECK(input_tokens>=0),
 output_tokens INTEGER NOT NULL DEFAULT 0 CHECK(output_tokens>=0),
 cost_usd REAL NOT NULL DEFAULT 0 CHECK(cost_usd>=0), latency_ms REAL NOT NULL DEFAULT 0,
 status TEXT NOT NULL, run_id TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE egress_log (
 id INTEGER PRIMARY KEY, backend TEXT NOT NULL, model TEXT NOT NULL,
 segment_hashes_json TEXT NOT NULL CHECK(json_valid(segment_hashes_json)), purpose TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE result_cache (
 key TEXT PRIMARY KEY, result_json TEXT NOT NULL CHECK(json_valid(result_json)),
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
