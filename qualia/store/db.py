"""The only SQL write boundary. External callers use these transaction methods."""

import hashlib
import json
import math
import os
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from qualia.core.codebook import validate_code

APPEND_ONLY = (
    'coding_events', 'feedback_events', 'experiments', 'evaluation_runs',
    'usage_ledger', 'egress_log', 'codebook_versions', 'sources', 'segments',
)
TABLES = (*APPEND_ONLY, 'cases', 'source_cases', 'attributes', 'codes', 'memos', 'result_cache')


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


class Store:
    def __init__(self, path: Path, operation_id: str | None = None):
        self.path = Path(path)
        self._project_root = self.path.parent.resolve()
        self.operation_id = operation_id
        self._check_operation()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, timeout=5, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.execute('PRAGMA busy_timeout=5000')
        self.connection.execute('PRAGMA journal_mode=WAL')
        self.migrate()
        stat = self.path.stat() if str(self.path) != ':memory:' else None
        self._file_identity = (stat.st_dev, stat.st_ino) if stat else None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.connection.close()

    def _check_operation(self):
        lock = self.path.parent / '.qualia-operation.lock'
        if self.operation_id and (not lock.is_file() or lock.read_text(encoding='utf-8') != self.operation_id):
            raise ValueError('exclusive operation lock is missing or changed')
        journal = self.path.parent.parent.parent / 'recovery' / self.path.parent.name / 'pending.json'
        if not self.operation_id and journal.exists():
            raise ValueError('project has an interrupted operation requiring recovery')
        if lock.exists():
            if not self.operation_id or lock.read_text(encoding='utf-8') != self.operation_id:
                raise ValueError('project has an active or interrupted operation')

    def backup_to(self, path: Path):
        self._check_operation()
        if self.connection.in_transaction:
            raise ValueError('database backup requires no active transaction')
        target = sqlite3.connect(path)
        try:
            self.connection.backup(target)
        finally:
            target.close()

    def restore_from(self, path: Path):
        self._check_operation()
        if not self.operation_id or self.connection.in_transaction or not path.is_file():
            raise ValueError('database restoration requires an exclusive operation and a valid backup')
        if self.path.parent.resolve() != self._project_root:
            raise ValueError('database directory changed during operation')
        source = sqlite3.connect(f'{path.resolve().as_uri()}?mode=ro', uri=True)
        stat = self.path.stat() if self.path.is_file() and not self.path.is_symlink() else None
        if stat and stat.st_nlink == 1 and (stat.st_dev, stat.st_ino) == self._file_identity:
            try:
                source.backup(self.connection)
            finally:
                source.close()
            return
        replacement = self.path.with_name('.qualia-restore-' + uuid.uuid4().hex + '.db')
        target = sqlite3.connect(replacement)
        try:
            source.backup(target)
        finally:
            target.close()
            source.close()
        self.connection.close()
        # Exact sibling sidecars only. Never follow an operator-created symlink.
        for suffix in ('-wal', '-shm'):
            sidecar = self.path.with_name(self.path.name + suffix)
            if sidecar.parent.resolve() != self._project_root:
                raise ValueError('database sidecar escapes project')
            if sidecar.is_file() or sidecar.is_symlink():
                sidecar.unlink()
        os.replace(replacement, self.path)
        self.connection = sqlite3.connect(self.path, timeout=5, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.execute('PRAGMA busy_timeout=5000')
        self.connection.execute('PRAGMA journal_mode=WAL')
        stat = self.path.stat()
        self._file_identity = (stat.st_dev, stat.st_ino)

    def fingerprint(self) -> str:
        """Trusted integrity digest; no row contents leave the Store boundary."""
        digest = hashlib.sha256()
        for statement in self.connection.iterdump():
            digest.update(statement.encode('utf-8'))
            digest.update(b'\n')
        digest.update(str(self.connection.execute('PRAGMA user_version').fetchone()[0]).encode())
        return digest.hexdigest()

    def migrate(self):
        version = self.connection.execute('PRAGMA user_version').fetchone()[0]
        migrations = sorted((Path(__file__).parent / 'migrations').glob('*.sql'))
        for file in migrations:
            number = int(file.name.split('_')[0])
            if number <= version:
                continue
            if version and str(self.path) != ':memory:':
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
        outer = not self.connection.in_transaction
        self.connection.execute('BEGIN IMMEDIATE' if outer else 'SAVEPOINT qualia_transaction')
        try:
            self._check_operation()
            yield self
            if outer:
                self.connection.commit()
            else:
                self.connection.execute('RELEASE qualia_transaction')
        except Exception:
            if outer:
                self.connection.rollback()
            else:
                self.connection.execute('ROLLBACK TO qualia_transaction')
                self.connection.execute('RELEASE qualia_transaction')
            raise

    @contextmanager
    def immediate(self):
        if self.connection.in_transaction:
            raise ValueError('admission requires an independent transaction')
        self.connection.execute('BEGIN IMMEDIATE')
        try:
            self._check_operation()
            yield self
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def reserve_attempt(self, *, backend, model, run_id, segment_hashes, external,
                        allow_external, daily_calls, run_segments, daily_usd=1.0,
                        reserved_usd=0.0, purpose='classification') -> int:
        """Called only by the usage coordinator, immediately before dispatch."""
        if external and not allow_external:
            raise ValueError('external AI disabled for this project')
        if any(type(value) is not int or value < 0 for value in (daily_calls, run_segments)):
            raise ValueError('invalid budget limits')
        if any(not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0
               for value in (reserved_usd, daily_usd)):
            raise ValueError('invalid cost limit')
        with self.immediate():
            daily = self.one("SELECT coalesce(sum(calls),0) AS calls FROM usage_ledger "
                             "WHERE substr(created_at,1,10)=date('now')")['calls']
            used = self.one('SELECT coalesce(sum(segments),0) AS segments FROM usage_ledger WHERE run_id=?',
                            (run_id,))['segments']
            cost = self.one("SELECT coalesce(sum(cost_usd),0) AS amount FROM usage_ledger "
                            "WHERE backend=? AND substr(created_at,1,10)=date('now')", (backend,))['amount']
            held = self.one("SELECT coalesce(sum(reserved_usd),0) AS amount FROM usage_ledger r "
                            "WHERE backend=? AND status='reserved' AND substr(created_at,1,10)=date('now') "
                            'AND NOT EXISTS(SELECT 1 FROM usage_ledger f WHERE f.reservation_id=r.id)',
                            (backend,))['amount']
            if daily + 1 > daily_calls or used + len(segment_hashes) > run_segments:
                raise ValueError('budget reached')
            if cost + held + reserved_usd > daily_usd:
                raise ValueError('budget reached: daily cost limit')
            row_id = self.add('usage_ledger', dict(backend=backend, model=model, calls=1,
                              segments=len(segment_hashes), status='reserved', run_id=run_id,
                              reserved_usd=reserved_usd))
            if external:
                self.add('egress_log', dict(backend=backend, model=model,
                         segment_hashes_json=canonical(segment_hashes), purpose=purpose,
                         reservation_id=row_id))
            return row_id

    def finish_attempt(self, reservation_id: int, *, input_tokens=0, output_tokens=0,
                       cost_usd=0.0, latency_ms=0.0, status='ok', cli_version=None) -> int:
        if status not in ('ok', 'error'):
            raise ValueError('completion status must be ok or error')
        if any(type(value) is not int or value < 0 for value in (input_tokens, output_tokens)):
            raise ValueError('invalid usage totals')
        if any(not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0
               for value in (cost_usd, latency_ms)):
            raise ValueError('invalid cost or latency')
        with self.immediate():
            reservation = self.one("SELECT * FROM usage_ledger WHERE id=? AND status='reserved'",
                                   (reservation_id,))
            if reservation is None:
                raise ValueError('attempt reservation not found')
            if self.one('SELECT id FROM usage_ledger WHERE reservation_id=?', (reservation_id,)):
                raise ValueError('attempt already finalized')
            return self.add('usage_ledger', dict(backend=reservation['backend'], model=reservation['model'],
                            run_id=reservation['run_id'], calls=0, segments=0, status=status,
                            input_tokens=input_tokens, output_tokens=output_tokens, cost_usd=cost_usd,
                            latency_ms=latency_ms, cli_version=cli_version, reservation_id=reservation_id))

    def record_suggestions(self, events: list[dict]) -> list[int]:
        if any(event.get('action') != 'suggest' for event in events):
            raise ValueError('suggestion events required')
        with self.transaction():
            return [self.add('coding_events', event) for event in events]

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
                'INSERT INTO result_cache(key,result_json) VALUES(?,?) '
                'ON CONFLICT(key) DO UPDATE SET result_json=excluded.result_json',
                (key, canonical(result)),
            )

    def review(self, suggestion_id: int, decision: str, actor: str, pipeline: str, note='') -> int:
        if decision not in ('accept', 'reject'):
            raise ValueError('review must accept or reject')
        if not actor.strip():
            raise ValueError('reviewer identity required')
        with self.immediate():
            suggestion = self.one('SELECT * FROM pending_suggestions WHERE id=?', (suggestion_id,))
            if suggestion is None:
                raise ValueError(f'suggestion {suggestion_id} is absent or already reviewed')
            values = {k: v for k, v in suggestion.items() if k not in ('id', 'created_at')}
            values.update(action=decision, actor_type='human', actor=actor, suggestion_id=suggestion_id,
                          reviewed_by=actor, review_status='accepted' if decision == 'accept' else 'rejected',
                          pipeline_version=pipeline)
            event = self.add('coding_events', values)
            self.add('feedback_events', {'coding_event_id': event, 'decision': decision,
                                        'actor': actor, 'note': note})
        return event

    def import_sources(self, records: list[dict], version_of: int | None = None) -> dict:
        """Commit a validated import and its case metadata as one unit."""
        source_ids = []
        new_sources = new_segments = 0
        with self.transaction():
            if version_of is not None and (type(version_of) is not int or not self.one(
                    'SELECT id FROM sources WHERE id=?', (version_of,))):
                raise ValueError(f'lineage source {version_of} not found')
            for record in records:
                digest = hashlib.sha256(record['text'].encode('utf-8')).hexdigest()
                existing = self.one('SELECT id FROM sources WHERE content_hash=?', (digest,))
                if existing:
                    source_id = existing['id']
                else:
                    source_id = self.add('sources', {'name': record['name'], 'text': record['text'],
                                                     'content_hash': digest, 'version_of': version_of})
                    for segment in record['segments']:
                        self.add('segments', {**segment, 'source_id': source_id})
                    new_sources += 1
                    new_segments += len(record['segments'])
                if source_id not in source_ids:
                    source_ids.append(source_id)
                case_id = None
                if record.get('case'):
                    case = self.one('SELECT id FROM cases WHERE name=?', (record['case'],))
                    case_id = case['id'] if case else self.save_case({'name': record['case']})
                    self.link_case(source_id, case_id)
                owner = {'case_id': case_id} if case_id else {'source_id': source_id}
                for key, value in record.get('attributes', {}).items():
                    self.save_attribute({**owner, 'key': key, 'value': value})
        return {'new_sources': new_sources, 'source_ids': source_ids, 'new_segments': new_segments}

    def save_code(self, values: dict, code_id: int | None = None) -> int:
        """Apply an explicit human draft edit; existing frozen versions remain untouched."""
        with self.transaction():
            record = validate_code(values, self.rows('SELECT * FROM codes'), code_id)
            for field in ('examples_pos', 'examples_neg'):
                if field in record:
                    record[field] = canonical(record[field])
            if code_id is None:
                return self.add('codes', record)
            self.update('codes', code_id, record)
            return code_id

    def assign(self, values: dict) -> int:
        """Append a manual span assignment/removal with complete supplied provenance."""
        record = {'actor_type': 'human', **values}
        if record['actor_type'] != 'human' or record.get('action') not in ('assign', 'remove'):
            raise ValueError('manual coding requires a human assign or remove action')
        for field in ('segment_id', 'code_id', 'codebook_version_id', 'span_start', 'span_end'):
            if type(record.get(field)) is not int:
                raise ValueError(f'coding {field} must be an integer')
        for field in ('actor', 'pipeline_version'):
            if not isinstance(record.get(field), str) or not record[field].strip():
                raise ValueError(f'coding {field} is required')
        try:
            return self.add('coding_events', record)
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"segment {record['segment_id']}: invalid coding record ({exc})") from None

    def save_memo(self, values: dict, memo_id: int | None = None) -> int:
        if not values or set(values) - {'title', 'text', 'segment_id', 'code_id'}:
            raise ValueError('invalid memo fields')
        if memo_id is None and not {'title', 'text'} <= set(values):
            raise ValueError('memo title and text are required')
        for field in ('title', 'text'):
            if field in values and not isinstance(values[field], str):
                raise ValueError(f'memo {field} must be text')
        for field, table in (('segment_id', 'segments'), ('code_id', 'codes')):
            value = values.get(field)
            if value is not None and (type(value) is not int or not self.one(
                    f'SELECT id FROM {table} WHERE id=?', (value,))):
                raise ValueError(f'memo {field} {value} not found')
        if memo_id is None:
            return self.add('memos', values)
        if not self.one('SELECT id FROM memos WHERE id=?', (memo_id,)):
            raise ValueError(f'memo {memo_id} not found')
        self.update('memos', memo_id, values)
        return memo_id

    def save_case(self, values: dict, case_id: int | None = None) -> int:
        if (set(values) - {'name', 'source_ids', 'attributes'} or 'name' not in values
                or not isinstance(values['name'], str) or not values['name'].strip()):
            raise ValueError('case name is required')
        sources = values.get('source_ids', [])
        attributes = values.get('attributes', {})
        if not isinstance(sources, list) or any(type(item) is not int for item in sources):
            raise ValueError('case source_ids must be integer IDs')
        if not isinstance(attributes, dict):
            raise ValueError('case attributes must be key/value pairs')
        if case_id is not None and not self.one('SELECT id FROM cases WHERE id=?', (case_id,)):
            raise ValueError(f'case {case_id} not found')
        try:
            with self.transaction():
                if case_id is None:
                    existing = self.one('SELECT id FROM cases WHERE name=?', (values['name'],))
                    case_id = existing['id'] if existing else self.add('cases', {'name': values['name']})
                else:
                    self.update('cases', case_id, {'name': values['name']})
                for source in sources:
                    self.link_case(source, case_id)
                for key, value in attributes.items():
                    self.save_attribute({'case_id': case_id, 'key': key, 'value': value})
            return case_id
        except sqlite3.IntegrityError:
            raise ValueError('case name already exists') from None

    def link_case(self, source_id: int, case_id: int):
        for table, row_id in (('sources', source_id), ('cases', case_id)):
            if type(row_id) is not int or not self.one(f'SELECT id FROM {table} WHERE id=?', (row_id,)):
                raise ValueError(f'{table} record {row_id} not found')
        with self.transaction():
            self.connection.execute('INSERT INTO source_cases(source_id,case_id) VALUES(?,?) '
                                    'ON CONFLICT DO NOTHING', (source_id, case_id))

    def save_attribute(self, values: dict, attribute_id: int | None = None) -> int:
        if set(values) - {'case_id', 'source_id', 'key', 'value'} or not {'key', 'value'} <= set(values):
            raise ValueError('invalid attribute fields')
        if (not isinstance(values['key'], str) or not values['key'].strip()
                or not isinstance(values['value'], str)):
            raise ValueError('attribute requires a nonempty key and text value')
        owners = [(field, values[field]) for field in ('case_id', 'source_id')
                  if values.get(field) is not None]
        if len(owners) != 1:
            raise ValueError('attribute requires exactly one case or source')
        field, owner = owners[0]
        table = 'cases' if field == 'case_id' else 'sources'
        if type(owner) is not int or not self.one(f'SELECT id FROM {table} WHERE id=?', (owner,)):
            raise ValueError(f'attribute {field} {owner} not found')
        with self.transaction():
            if attribute_id is None:
                existing = self.one(f'SELECT id FROM attributes WHERE {field}=? AND key=?',
                                    (owner, values['key']))
                attribute_id = existing['id'] if existing else None
            elif not self.one('SELECT id FROM attributes WHERE id=?', (attribute_id,)):
                raise ValueError(f'attribute {attribute_id} not found')
            record = {'case_id': None, 'source_id': None, **values}
            if attribute_id is None:
                return self.add('attributes', record)
            self.update('attributes', attribute_id, record)
            return attribute_id

    def retrieve(self, code_id: int | None = None, case_id: int | None = None) -> list[dict]:
        """Current coded spans; a multi-case source appears once per span in each filter."""
        query = ('SELECT c.*, g.source_id, s.name AS source_name, '
                 'g.start AS segment_start, g.end AS segment_end, '
                 'substr(s.text,g.start+1,g.end-g.start) AS segment_text, '
                 'substr(s.text,g.start+c.span_start+1,c.span_end-c.span_start) AS excerpt '
                 'FROM current_codings c JOIN segments g ON g.id=c.segment_id '
                 'JOIN sources s ON s.id=g.source_id WHERE 1=1')
        parameters = []
        if code_id is not None:
            query += ' AND c.code_id=?'
            parameters.append(code_id)
        if case_id is not None:
            query += ' AND EXISTS(SELECT 1 FROM source_cases sc WHERE sc.source_id=g.source_id AND sc.case_id=?)'
            parameters.append(case_id)
        return self.rows(query + ' ORDER BY c.segment_id,c.span_start,c.code_id,c.id', parameters)

    def matrix(self) -> list[dict]:
        return self.rows('SELECT c.code_id, sc.case_id, count(DISTINCT c.segment_id) AS count '
                         'FROM current_codings c JOIN segments g ON g.id=c.segment_id '
                         'JOIN source_cases sc ON sc.source_id=g.source_id '
                         'GROUP BY c.code_id,sc.case_id ORDER BY c.code_id,sc.case_id')
