-- Immutable reservation and completion rows keep budgets safe across processes.
ALTER TABLE usage_ledger ADD COLUMN cli_version TEXT;
ALTER TABLE usage_ledger ADD COLUMN reservation_id INTEGER REFERENCES usage_ledger(id);
ALTER TABLE usage_ledger ADD COLUMN reserved_usd REAL NOT NULL DEFAULT 0 CHECK(reserved_usd>=0);
ALTER TABLE egress_log ADD COLUMN reservation_id INTEGER REFERENCES usage_ledger(id);
CREATE UNIQUE INDEX usage_one_completion ON usage_ledger(reservation_id) WHERE reservation_id IS NOT NULL;
CREATE UNIQUE INDEX egress_one_attempt ON egress_log(reservation_id) WHERE reservation_id IS NOT NULL;
