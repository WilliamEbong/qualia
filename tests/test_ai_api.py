import json

from fastapi.testclient import TestClient

from qualia.server.app import create_app
from qualia.store.db import Store
from qualia.workspace import project_dir


def test_offline_classification_review_cache_and_egress_api(tmp_path):
    client = TestClient(create_app(home=tmp_path, token='test'), base_url='http://localhost',
                        headers={'x-qualia-token': 'test'})
    assert client.post('/api/projects', json={'name': 'study'}).status_code == 201
    base = '/api/projects/study'
    assert client.post(base + '/import', json={'name': 'synthetic.txt', 'format': 'txt',
                                              'content': 'A new possibility.\n\nAnother possibility.'}).status_code == 200
    assert client.post(base + '/codes', json={'name': 'Possibility'}).status_code == 200
    assert client.post(base + '/codebook/freeze').status_code == 200
    availability = client.get(base + '/ai/availability')
    assert availability.status_code == 200, availability.text
    assert availability.json()['allow_external'] is False
    assert any(item['name'] == 'fake' and item['available'] for item in availability.json()['backends'])
    result = client.post(base + '/classify', json={'backend': 'fake'})
    assert result.status_code == 200, result.text
    assert result.json()['status'] == 'completed'
    assert result.json()['calls'] == 1
    suggestions = client.get(base).json()['suggestions']
    assert len(suggestions) == 2
    assert all(item['actor_type'] == 'model' for item in suggestions)
    review = dict(suggestion_id=suggestions[0]['id'], decision='accept', actor='reviewer')
    assert client.post(base + '/review', json=review).status_code == 200
    assert client.post(base + '/review', json=review).status_code == 400
    assert client.post(base + '/review', json={**review, 'suggestion_id': suggestions[1]['id'],
                                             'decision': 'reject'}).status_code == 200
    after = client.get(base).json()
    assert len(after['current_codings']) == 1
    assert after['current_codings'][0]['backend'] == 'fake'
    cached = client.post(base + '/classify', json={'backend': 'fake'}).json()
    assert cached['calls'] == 0
    assert cached['cache_hits'] == 2
    blocked = client.post(base + '/classify', json={'backend': 'claude'}).json()
    assert blocked['calls'] == 0
    assert blocked['status'] in ('blocked', 'unavailable')
    with Store(project_dir('study', tmp_path) / 'project.db') as db:
        assert not db.rows('SELECT * FROM egress_log')
        assert len(db.rows('SELECT * FROM feedback_events')) == 2
    exported = json.loads(client.get(base + '/export?bundle=reproducibility').json()['content'])
    assert all(item['pipeline_version'] and item['codebook_version_id'] for item in exported['coding_events'])
