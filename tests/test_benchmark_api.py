"""Feature 019: benchmark status and in-app import, dev and validation only."""

import json

from fastapi.testclient import TestClient

from qualia.server.app import create_app
from qualia.store.db import Store
from qualia.workspace import init_project


def jsonl(*records):
    return ''.join(json.dumps(record) + '\n' for record in records)


def record(identity, transcript, codes):
    return {'segment_id': identity, 'text': f'Synthetic passage {identity}.', 'transcript_id': transcript,
            'codes': codes}


def setup(tmp_path):
    project = init_project('study', tmp_path)
    with Store(project / 'project.db') as db:
        first = db.save_code({'name': 'First'})
        db.freeze_codebook()
    client = TestClient(create_app(tmp_path, token='test'), base_url='http://127.0.0.1',
                        headers={'X-Qualia-Token': 'test'})
    return project, client, first


def test_status_and_import_of_dev_and_validation(tmp_path):
    project, client, code = setup(tmp_path)
    url = '/api/projects/study/benchmarks'
    assert client.get(url).json() == {'dev': None, 'validation': None}
    content = jsonl(record('v1', 't1', [code]), record('v2', 't1', []))
    imported = client.post(url, json={'split': 'validation', 'content': content})
    assert imported.status_code == 200, imported.text
    assert imported.json()['validation'] == {'records': 2, 'codebook_version_id': 1}
    # Identical bytes are a no-op; different content for a published split is refused.
    assert client.post(url, json={'split': 'validation', 'content': content}).status_code == 200
    changed = client.post(url, json={'split': 'validation', 'content': jsonl(record('v3', 't9', []))})
    assert changed.status_code == 400 and 'already published' in changed.json()['detail']
    assert client.get(url).json()['validation']['records'] == 2


def test_protected_split_and_invalid_files_are_refused_without_writes(tmp_path):
    project, client, code = setup(tmp_path)
    url = '/api/projects/study/benchmarks'
    protected = client.post(url, json={'split': 'protected', 'content': jsonl(record('p1', 't1', [code]))})
    assert protected.status_code == 422
    bad = client.post(url, json={'split': 'dev', 'content': '{"segment_id": "x"}\n'})
    assert bad.status_code == 400 and 'line 1' in bad.json()['detail']
    unknown = client.post(url, json={'split': 'dev', 'content': jsonl(record('d1', 't1', [999]))})
    assert unknown.status_code == 400
    assert client.post(url, json={'split': 'dev', 'version': 7, 'content': jsonl(record('d1', 't1', []))}).status_code == 400
    assert client.get(url).json() == {'dev': None, 'validation': None}
    assert not list((project / 'benchmarks').rglob('*.jsonl'))  # no records written
