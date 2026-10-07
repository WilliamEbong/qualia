-- The exact model a provider reports for a run (e.g. the snapshot behind an alias), when known.
ALTER TABLE coding_events ADD COLUMN model_version TEXT;
ALTER TABLE code_proposals ADD COLUMN model_version TEXT;
