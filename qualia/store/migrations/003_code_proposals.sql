-- Codebook proposals are records awaiting a human decision; neither table is ever edited.
CREATE TABLE code_proposals (
 id INTEGER PRIMARY KEY, batch_id TEXT NOT NULL CHECK(length(trim(batch_id))>0),
 mode TEXT NOT NULL CHECK(mode IN ('draft','refine','evidence')),
 kind TEXT NOT NULL CHECK(kind IN ('new_code','revise_code')),
 target_code_id INTEGER REFERENCES codes(id),
 payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
 rationale TEXT NOT NULL DEFAULT '',
 evidence_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(evidence_json)),
 actor_type TEXT NOT NULL CHECK(actor_type IN ('model','rule')),
 backend TEXT, model TEXT, cli_version TEXT, prompt_hash TEXT NOT NULL DEFAULT '',
 codebook_version_id INTEGER REFERENCES codebook_versions(id),
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 CHECK(kind='new_code' OR target_code_id IS NOT NULL),
 CHECK(actor_type='rule' OR (backend IS NOT NULL AND length(trim(backend))>0
 AND model IS NOT NULL AND length(trim(model))>0
 AND cli_version IS NOT NULL AND length(trim(cli_version))>0 AND length(trim(prompt_hash))>0))
);
CREATE INDEX code_proposals_batch ON code_proposals(batch_id);
CREATE TABLE code_proposal_decisions (
 id INTEGER PRIMARY KEY, proposal_id INTEGER NOT NULL UNIQUE REFERENCES code_proposals(id),
 decision TEXT NOT NULL CHECK(decision IN ('accept','reject')),
 actor TEXT NOT NULL CHECK(length(trim(actor))>0), note TEXT NOT NULL DEFAULT '',
 applied_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(applied_json)),
 code_id INTEGER REFERENCES codes(id),
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 CHECK(decision='reject' OR code_id IS NOT NULL)
);
CREATE TRIGGER code_proposals_update BEFORE UPDATE ON code_proposals
 BEGIN SELECT RAISE(ABORT,'code_proposals is append-only'); END;
CREATE TRIGGER code_proposals_delete BEFORE DELETE ON code_proposals
 BEGIN SELECT RAISE(ABORT,'code_proposals is append-only'); END;
CREATE TRIGGER code_proposal_decisions_update BEFORE UPDATE ON code_proposal_decisions
 BEGIN SELECT RAISE(ABORT,'code_proposal_decisions is append-only'); END;
CREATE TRIGGER code_proposal_decisions_delete BEFORE DELETE ON code_proposal_decisions
 BEGIN SELECT RAISE(ABORT,'code_proposal_decisions is append-only'); END;
