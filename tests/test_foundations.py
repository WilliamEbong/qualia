import sqlite3

import pytest
from fastapi.testclient import TestClient

from qualia.server.app import create_app
from qualia.store.db import APPEND_ONLY, Store
from qualia.workspace import check_manifest, init_project, project_dir


@pytest.fixture
def project(tmp_path):
    return init_project('study', tmp_path)


def seed(db):
    source = db.add('sources', {'name': 'test', 'text': 'hello', 'content_hash': 'test'})
    segment = db.add('segments', {'source_id': source, 'start': 0, 'end': 5, 'ordinal': 0})
    code = db.add('codes', {'name': 'Greeting'})
    version = db.freeze_codebook()['id']
    return {'segment_id': segment, 'code_id': code, 'codebook_version_id': version,
            'span_start': 0, 'span_end': 5, 'actor': 'researcher', 'actor_type': 'human',
            'action': 'assign', 'pipeline_version': 'config-hash'}


def test_migration_is_idempotent_and_settings(project):
    with Store(project / 'project.db') as db:
        db.migrate()
        db.migrate()
        assert db.connection.execute('PRAGMA user_version').fetchone()[0] == 1
        assert db.connection.execute('PRAGMA journal_mode').fetchone()[0] == 'wal'
        assert db.connection.execute('PRAGMA busy_timeout').fetchone()[0] == 5000
        event = seed(db)
        db.add('coding_events', event)
        assert len(db.rows('SELECT * FROM current_codings')) == 1


def test_every_append_only_table_rejects_update_delete(project):
    with Store(project / 'project.db') as db:
        event = seed(db)
        event_id = db.add('coding_events', event)
        for table, values in {
            'feedback_events': {'coding_event_id': event_id, 'decision': 'accept', 'actor': 'human'},
            'experiments': {'slug': 'trial', 'agent': 'fake', 'decision': 'REVERT', 'reason': 'test',
                            'before_json': '{}', 'after_json': '{}'},
            'evaluation_runs': {'split': 'validation', 'backend': 'fake', 'model': 'fake',
                                'pipeline_version': 'hash', 'metrics_json': '{}', 'predictions_json': '[]'},
            'usage_ledger': {'backend': 'fake', 'model': 'fake', 'calls': 1, 'segments': 1,
                             'status': 'ok', 'run_id': 'test'},
            'egress_log': {'backend': 'fake', 'model': 'fake', 'segment_hashes_json': '[]', 'purpose': 'test'},
        }.items():
            db.add(table, values)
        for table in APPEND_ONLY:
            for sql in (f'UPDATE {table} SET id=id', f'DELETE FROM {table}'):
                with pytest.raises(sqlite3.IntegrityError, match='append-only'):
                    db.connection.execute(sql)
                db.connection.rollback()


@pytest.mark.parametrize('field', ['segment_id', 'codebook_version_id', 'actor', 'pipeline_version'])
def test_required_provenance(project, field):
    with Store(project / 'project.db') as db:
        event = seed(db)
        del event[field]
        with pytest.raises(sqlite3.IntegrityError):
            db.add('coding_events', event)


def test_span_and_codebook_membership(project):
    with Store(project / 'project.db') as db:
        event = seed(db)
        with pytest.raises(sqlite3.IntegrityError, match='span exceeds'):
            db.add('coding_events', {**event, 'span_end': 6})
        code = db.add('codes', {'name': 'Later'})
        with pytest.raises(sqlite3.IntegrityError, match='absent from frozen'):
            db.add('coding_events', {**event, 'code_id': code})


def test_review_append_only_and_single_decision(project):
    with Store(project / 'project.db') as db:
        event = seed(db)
        event.update(action='suggest', actor_type='model', actor='fake', backend='fake', model='fake',
                     review_status='pending', score=0.8, cli_version='test', prompt_hash='hash')
        suggestion = db.add('coding_events', event)
        db.review(suggestion, 'accept', 'researcher', 'pipeline')
        assert len(db.rows('SELECT * FROM coding_events')) == 2
        assert len(db.rows('SELECT * FROM feedback_events')) == 1
        assert len(db.rows('SELECT * FROM current_codings')) == 1
        assert db.rows('SELECT * FROM pending_suggestions') == []
        with pytest.raises(ValueError, match='already reviewed'):
            db.review(suggestion, 'reject', 'researcher', 'pipeline')


def test_workspace_paths_manifest_and_idempotency(project, tmp_path):
    before = (project / 'project.db').read_bytes()
    assert init_project('study', tmp_path) == project
    assert (project / 'project.db').read_bytes() == before
    assert check_manifest(project)
    (project / 'METHODOLOGY.md').write_text('tampered', encoding='utf-8')
    assert not check_manifest(project)
    for slug in ('../escape', '/absolute', 'A name', 'a/b', '..'):
        with pytest.raises(ValueError):
            project_dir(slug, tmp_path)


def test_server_security_and_offline_workspace(project, tmp_path):
    client = TestClient(create_app(tmp_path, token='test-token'), base_url='http://127.0.0.1')
    assert client.get('/api/projects', headers={'host': 'evil.example'}).status_code == 403
    assert client.get('/api/projects').status_code == 401
    assert client.get('/api/projects', headers={'x-qualia-token': 'wrong'}).status_code == 401
    headers = {'x-qualia-token': 'test-token'}
    assert client.get('/api/projects', headers={**headers, 'origin': 'https://evil.example'}).status_code == 403
    response = client.get('/api/projects/study', headers=headers)
    assert response.status_code == 200
    assert response.json()['sources'] == []
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert "frame-ancestors 'none'" in response.headers['content-security-policy']
    assert 'test-token' in client.get('/').text
    assert client.get('/api/missing', headers=headers).status_code == 404


def test_read_boundary_and_model_provenance(project):
    with Store(project / 'project.db') as db:
        db.add('cases', {'name': 'original'})
        with pytest.raises(sqlite3.DatabaseError, match='not authorized'):
            db.rows("WITH x AS (SELECT 1) UPDATE cases SET name='changed' RETURNING name")
        assert db.rows('SELECT name FROM cases') == [{'name': 'original'}]
        event = seed(db)
        event.update(actor_type='model', backend='', model='')
        with pytest.raises(sqlite3.IntegrityError):
            db.add('coding_events', event)
