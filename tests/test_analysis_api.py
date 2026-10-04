import json

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from qualia.cli import app
from qualia.server.app import create_app
from qualia.store.db import Store


@pytest.fixture
def study(tmp_path, monkeypatch):
    monkeypatch.setenv('QUALIA_HOME', str(tmp_path))
    client = TestClient(create_app(tmp_path, token='analysis-test'), base_url='http://127.0.0.1',
                        headers={'X-Qualia-Token': 'analysis-test'})
    assert client.post('/api/projects', json={'name': 'study'}).status_code == 201
    prefix = '/api/projects/study'
    for name in ('Opportunity', 'Concern'):
        assert client.post(prefix + '/codes', json={'name': name}).status_code == 200
    client.post(prefix + '/codebook/freeze')
    for index in range(3):
        source = client.post(prefix + '/import', json={
            'name': f'Interview {index}', 'format': 'txt',
            'content': f'SYNTHETIC_TRANSCRIPT_SECRET_{index} opportunity and concern.',
        }).json()['source_ids'][0]
        assert client.post(prefix + '/cases', json={
            'name': f'Participant {index}', 'source_ids': [source],
            'attributes': {'age': str(20 + 10 * index), 'score': str(2 + 2 * index),
                           'group': 'A' if index < 2 else 'B'},
        }).status_code == 200
    data = client.get(prefix).json()
    for segment in data['segments']:
        for code in (1, 2):
            assert client.post(prefix + '/coding', json={
                'segment_id': segment['id'], 'code_id': code,
            }).status_code == 200
    return client, prefix, tmp_path / 'projects/study'


def test_analysis_api_counts_filters_numeric_and_nonmutation(study):
    client, prefix, project = study
    before_files = {p.relative_to(project).as_posix(): p.read_bytes()
                    for p in project.rglob('*') if p.is_file() and p.suffix != '.db'
                    and not p.name.startswith('project.db-')}
    with Store(project / 'project.db') as db:
        before = db.fingerprint()
    response = client.post(prefix + '/analysis', json={'group_by': 'group', 'numeric_fields': ['age', 'score']})
    assert response.status_code == 200, response.text
    report = response.json()
    assert report['segment_count'] == report['case_count'] == 3
    assert report['frequencies'][0]['segment_count'] == 3
    assert report['frequencies'][0]['case_percent'] == 100
    assert len(report['groups']) == 2
    assert report['numeric'][0]['mean'] == 30
    assert report['correlations'][0]['n'] == 3
    assert report['correlations'][0]['pearson_r'] == pytest.approx(1)
    assert len(report['selected_segment_ids']) == 3
    assert len(report['input_hash']) == 64
    selected = client.post(prefix + '/analysis', json={'query': 'secret_1', 'code_ids': [1, 2], 'code_match': 'all'}).json()
    assert selected['segment_count'] == selected['case_count'] == 1
    assert 'SECRET_1' in selected['excerpts'][0]['text']
    with Store(project / 'project.db') as db:
        assert db.fingerprint() == before
    assert all((project / path).read_bytes() == data for path, data in before_files.items())


def test_analysis_api_bounds_token_unknown_ids_and_exports(study):
    client, prefix, _ = study
    assert client.post(prefix + '/analysis', json={}, headers={'X-Qualia-Token': 'wrong'}).status_code == 401
    for options in ({'query': 'x' * 201}, {'code_ids': [1, 1]}, {'code_ids': [-1]},
                    {'code_ids': ['1']}, {'numeric_fields': ['x' * 101]}, {'vault': True}):
        assert client.post(prefix + '/analysis', json=options).status_code == 422
    for options in ({'source_id': 999}, {'code_ids': [999]}, {'numeric_fields': ['unknown']}):
        assert client.post(prefix + '/analysis', json=options).status_code == 400
    exported = client.post(prefix + '/analysis/export', json={
        'options': {'numeric_fields': ['age', 'score']}, 'format': 'json',
    })
    assert exported.status_code == 200, exported.text
    assert 'SYNTHETIC_TRANSCRIPT_SECRET' not in exported.json()['content']
    assert 'source_name' not in exported.json()['content']
    assert client.post(prefix + '/analysis/export', json={'format': 'html'}).status_code == 422


def test_analysis_cli_reproduces_read_only_report(study):
    _, _, _ = study
    result = CliRunner().invoke(app, ['analyze', '--project', 'study', '--numeric', 'age', '--numeric', 'score'])
    assert result.exit_code == 0, result.output
    exported = json.loads(result.output)
    assert 'SYNTHETIC_TRANSCRIPT_SECRET' not in result.output
    assert exported['text_excluded'] is True
    bad = CliRunner().invoke(app, ['analyze', '--project', 'study', '--format', 'html'])
    assert bad.exit_code != 0


def test_analysis_export_rejects_stale_displayed_input(study):
    client, prefix, _ = study
    report = client.post(prefix + '/analysis', json={}).json()
    payload = {'format': 'csv', 'expected_input_hash': report['input_hash']}
    assert client.post(prefix + '/analysis/export', json=payload).status_code == 200
    assert client.post(prefix + '/cases', json={
        'name': 'Participant 0', 'source_ids': [], 'attributes': {'age': '21'},
    }).status_code == 200
    stale = client.post(prefix + '/analysis/export', json=payload)
    assert stale.status_code == 409
    assert 'Refresh analysis' in stale.json()['detail']
    assert 'content' not in stale.json()
    fresh = client.post(prefix + '/analysis', json={}).json()
    payload['expected_input_hash'] = fresh['input_hash']
    assert client.post(prefix + '/analysis/export', json=payload).status_code == 200
    payload['expected_input_hash'] = 'invalid'
    assert client.post(prefix + '/analysis/export', json=payload).status_code == 422
