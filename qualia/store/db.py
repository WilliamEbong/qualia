"""The only SQL write boundary. External callers use these transaction methods."""

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

APPEND_ONLY = (
    'coding_events', 'feedback_events', 'experiments', 'evaluation_runs',
    'usage_ledger', 'egress_log', 'codebook_versions', 'sources', 'segments',
)
TABLES = (*APPEND_ONLY, 'cases', 'source_cases', 'attributes', 'codes', 'memos', 'result_cache')


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, timeout=5, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.execute('PRAGMA busy_timeout=5000')
        self.connection.execute('PRAGMA journal_mode=WAL')
        self.migrate()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.connection.close()

    def migrate(self):
        version = self.connection.execute('PRAGMA user_version').fetchone()[0]
        migrations = sorted((Path(__file__).parent / 'migrations').glob('*.sql'))
        for file in migrations:
            number = int(file.name.split('_')[0])
            if number <= version:
                continue
            if version:
                backup = sqlite3.connect(str(self.path) + f'.v{version}.bak')
                try:
                    self.connection.backup(backup)
                finally:
                    backup.close()
            sql = file.read_text(encoding='utf-8')
            if number == 1:
                for table in APPEND_ONLY:
                    for action in ('UPDATE', 'DELETE'):
                        sql += (
                            f'\nCREATE TRIGGER {table}_{action.lower()} BEFORE {action} ON {table}'
                            f" BEGIN SELECT RAISE(ABORT,'{table} is append-only'); END;"
                        )
            try:
                self.connection.executescript(f'BEGIN IMMEDIATE;\n{sql}\nPRAGMA user_version={number};\nCOMMIT;')
            except Exception:
                self.connection.rollback()
                raise
            version = number

    @contextmanager
    def transaction(self):
        # Callers compose store methods atomically; SQLite serializes independent connections.
        self.connection.execute('SAVEPOINT qualia_transaction')
        try:
            yield self
            self.connection.execute('RELEASE qualia_transaction')
        except Exception:
            self.connection.execute('ROLLBACK TO qualia_transaction')
            self.connection.execute('RELEASE qualia_transaction')
            raise

    def rows(self, query: str, parameters=()) -> list[dict]:
        if not query.lstrip().upper().startswith(('SELECT ', 'WITH ')):
            raise ValueError('read query required')
        allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION,
                   sqlite3.SQLITE_RECURSIVE}
        self.connection.set_authorizer(
            lambda action, *args: sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY)
        try:
            return [dict(row) for row in self.connection.execute(query, parameters).fetchall()]
        finally:
            self.connection.set_authorizer(None)

    def one(self, query: str, parameters=()) -> dict | None:
        rows = self.rows(query, parameters)
        return rows[0] if rows else None

    def add(self, table: str, values: dict) -> int:
        self._validate_columns(table, values)
        with self.transaction():
            cursor = self.connection.execute(
                f'INSERT INTO {table} ({",".join(chr(34)+k+chr(34) for k in values)})'
                f' VALUES ({",".join("?" for _ in values)})', tuple(values.values()),
            )
        return cursor.lastrowid

    def update(self, table: str, row_id: int, values: dict):
        if table not in ('codes', 'memos', 'cases', 'attributes'):
            raise ValueError('table cannot be updated')
        self._validate_columns(table, values)
        with self.transaction():
            self.connection.execute(
                f'UPDATE {table} SET {",".join(chr(34)+k+chr(34)+"=?" for k in values)} WHERE id=?',
                (*values.values(), row_id),
            )

    def _validate_columns(self, table, values):
        if table not in TABLES or not values:
            raise ValueError('invalid table or empty record')
        columns = {r[1] for r in self.connection.execute(f'PRAGMA table_info({table})')}
        if not set(values) <= columns:
            raise ValueError(f'invalid {table} fields')

    def freeze_codebook(self) -> dict:
        snapshot = canonical(self.rows('SELECT * FROM codes ORDER BY id'))
        digest = hashlib.sha256(snapshot.encode()).hexdigest()
        existing = self.one('SELECT * FROM codebook_versions WHERE hash=?', (digest,))
        if existing:
            return existing
        row_id = self.add('codebook_versions', {'snapshot_json': snapshot, 'hash': digest})
        return self.one('SELECT * FROM codebook_versions WHERE id=?', (row_id,))

    def cache_put(self, key: str, result: dict):
        with self.transaction():
            self.connection.execute(
                'INSERT INTO result_cache(key,result_json) VALUES(?,?) ON CONFLICT(key) DO NOTHING',
                (key, canonical(result)),
            )

    def review(self, suggestion_id: int, decision: str, actor: str, pipeline: str, note='') -> int:
        if decision not in ('accept', 'reject'):
            raise ValueError('review must accept or reject')
        suggestion = self.one('SELECT * FROM pending_suggestions WHERE id=?', (suggestion_id,))
        if suggestion is None:
            raise ValueError(f'suggestion {suggestion_id} is absent or already reviewed')
        values = {k: v for k, v in suggestion.items() if k not in ('id', 'created_at')}
        values.update(action=decision, actor_type='human', actor=actor, suggestion_id=suggestion_id,
                      reviewed_by=actor, review_status='accepted' if decision == 'accept' else 'rejected',
                      pipeline_version=pipeline)
        with self.transaction():
            event = self.add('coding_events', values)
            self.add('feedback_events', {'coding_event_id': event, 'decision': decision,
                                        'actor': actor, 'note': note})
        return event
