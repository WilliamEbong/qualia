import json

from fastapi.testclient import TestClient

from qualia.server.app import create_app
from qualia.store.db import Store
from qualia.workspace import init_project


def test_workspace_only_exposes_validation_summaries(tmp_path):
    project = init_project('study', tmp_path)
    with Store(project / 'project.db') as db:
        for split in ('validation', 'protected'):
            db.add('evaluation_runs', dict(split=split, backend='fake', model='fake',
                   pipeline_version='fixture', metrics_json='{"macro_f1":0.5}',
                   predictions_json='[{"text":"SYNTHETIC_PRIVATE_PREDICTION"}]'))
    client = TestClient(create_app(tmp_path, token='test'), base_url='http://127.0.0.1',
                        headers={'X-Qualia-Token': 'test'})
    response = client.get('/api/projects/study')
    assert response.status_code == 200
    assert 'SYNTHETIC_PRIVATE_PREDICTION' not in response.text
    rows = response.json()['evaluation_runs']
    assert len(rows) == 1 and rows[0]['split'] == 'validation'
    assert 'predictions_json' not in rows[0]


def test_human_workflow_and_exports(tmp_path):
    client = TestClient(create_app(tmp_path, token='test'), base_url='http://127.0.0.1',
                        headers={'X-Qualia-Token': 'test'})
    assert client.post('/api/projects', json={'name': 'study'}).status_code == 201
    prefix = '/api/projects/study'
    record = {'name': 'Interview.txt', 'format': 'txt', 'content': 'Hello 😀 friend.\n\nI need time.'}
    first = client.post(prefix + '/import', json=record)
    assert first.status_code == 200, first.text
    assert first.json()['new_sources'] == 1
    assert client.post(prefix + '/import', json=record).json()['new_sources'] == 0
    code = client.post(prefix + '/codes', json={'name': 'Connection', 'definition': 'Relating to others'})
    assert code.status_code == 200, code.text
    code_id = code.json()['id']
    assert client.post(prefix + '/codebook/freeze').status_code == 200
    snapshot = client.get(prefix).json()
    segment_id = snapshot['segments'][0]['id']
    coding = {'segment_id': segment_id, 'code_id': code_id, 'span_start': 6, 'span_end': 7}
    assigned = client.post(prefix + '/coding', json=coding)
    assert assigned.status_code == 200, assigned.text
    memo = client.post(prefix + '/memos', json={'title': 'Context', 'text': 'A reflective note',
                                                'segment_id': segment_id})
    assert memo.status_code == 200, memo.text
    case = client.post(prefix + '/cases', json={'name': 'Participant A',
                                               'source_ids': first.json()['source_ids'],
                                               'attributes': {'group': 'A'}})
    assert case.status_code == 200, case.text
    updated = client.put(prefix + f"/cases/{case.json()['id']}",
                         json={'name': 'Participant B', 'attributes': {'group': 'B'}})
    assert updated.status_code == 200, updated.text
    snapshot = client.get(prefix).json()
    assert snapshot['cases'][0]['name'] == 'Participant B'
    assert snapshot['attributes'][0]['value'] == 'B'
    matrix = client.get(prefix + '/matrix').json()
    assert any(c['code_id'] == code_id and c['count'] == 1 for c in matrix)
    excerpts = client.get(prefix + '/retrieval', params={'code_id': code_id}).json()
    assert excerpts
    exported = client.get(prefix + '/export').json()
    assert 'Hello' not in exported['content']
    assert '😀' not in exported['content']
    parsed = json.loads(exported['content'])
    assert parsed
    bundle = client.get(prefix + '/export?bundle=reproducibility').json()
    assert 'vault' not in json.dumps(json.loads(bundle['content'])).lower()
    assert client.post(prefix + '/coding', json={**coding, 'action': 'remove'}).status_code == 200
    assert client.get(prefix).json()['current_codings'] == []


def test_invalid_input_retains_server_protections(tmp_path):
    client = TestClient(create_app(tmp_path, token='test'), base_url='http://127.0.0.1',
                        headers={'X-Qualia-Token': 'test'})
    assert client.post('/api/projects', json={'name': '../outside'}).status_code == 422
    client.post('/api/projects', json={'name': 'study'})
    prefix = '/api/projects/study'
    bad = client.post(prefix + '/import', json={'name': 'bad.txt', 'format': 'txt', 'content': ''})
    assert bad.status_code == 422
    assert bad.headers['x-frame-options'] == 'DENY'
    assert client.get(prefix).json()['sources'] == []
    assert client.post(prefix + '/coding', json={'segment_id': -1, 'code_id': 1}).status_code == 422
