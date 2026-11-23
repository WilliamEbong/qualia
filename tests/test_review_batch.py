"""Feature 020: batch review records every decision individually, all or nothing, with an append-only undo."""

from fastapi.testclient import TestClient

from qualia.io.imports import import_text
from qualia.server.app import create_app
from qualia.store.db import Store
from qualia.workspace import init_project


def setup(tmp_path, count=3):
    project = init_project('study', tmp_path)
    with Store(project / 'project.db') as db:
        import_text(db, project, 'one.txt', '\n\n'.join(f'Passage {n} text.' for n in range(count)), 'txt')
        code = db.save_code({'name': 'Waiting'})
        frozen = db.freeze_codebook()
        segments = [row['id'] for row in db.rows('SELECT id FROM segments ORDER BY id')]
        ids = db.record_suggestions([{'segment_id': segment, 'code_id': code, 'span_start': 0, 'span_end': 7,
                                      'actor_type': 'model', 'actor': 'fake', 'backend': 'fake', 'model': 'fake-v1',
                                      'cli_version': 'fixture', 'action': 'suggest', 'review_status': 'pending',
                                      'review_trigger': '[]', 'codebook_version_id': frozen['id'],
                                      'pipeline_version': 'pipeline', 'prompt_hash': 'prompt', 'score': 0.6,
                                      'rationale': 'Synthetic'} for segment in segments])
    client = TestClient(create_app(tmp_path, token='t'), base_url='http://127.0.0.1', headers={'X-Qualia-Token': 't'})
    return project, client, ids


def test_batch_accept_records_each_decision_like_a_single_review(tmp_path):
    project, client, ids = setup(tmp_path)
    response = client.post('/api/projects/study/review/batch',
                           json={'suggestion_ids': ids, 'decision': 'accept', 'actor': 'W. Ebong', 'note': 'clear delay talk'})
    assert response.status_code == 200, response.text
    events = response.json()['ids']
    assert len(events) == 3
    with Store(project / 'project.db') as db:
        rows = db.rows('SELECT * FROM coding_events WHERE action=? ORDER BY id', ('accept',))
        feedback = db.rows('SELECT * FROM feedback_events ORDER BY id')
        suggestions = {row['id']: row for row in db.rows('SELECT * FROM coding_events WHERE action=?', ('suggest',))}
        assert db.rows('SELECT * FROM pending_suggestions') == []
        assert len(db.rows('SELECT * FROM current_codings')) == 3
    assert [row['id'] for row in rows] == events
    for row in rows:
        original = suggestions[row['suggestion_id']]
        assert row['actor'] == row['reviewed_by'] == 'W. Ebong' and row['actor_type'] == 'human'
        assert row['review_status'] == 'accepted' and row['created_at']
        for field in ('segment_id', 'code_id', 'span_start', 'span_end', 'score', 'backend', 'model',
                      'cli_version', 'prompt_hash', 'rationale', 'codebook_version_id'):
            assert row[field] == original[field], field
    assert [(item['coding_event_id'], item['decision'], item['actor'], item['note']) for item in feedback] == \
        [(event, 'accept', 'W. Ebong', 'clear delay talk') for event in events]


def test_batch_is_all_or_nothing(tmp_path):
    project, client, ids = setup(tmp_path)
    assert client.post('/api/projects/study/review', json={'suggestion_id': ids[1], 'decision': 'reject',
                                                          'actor': 'r'}).status_code == 200
    response = client.post('/api/projects/study/review/batch', json={'suggestion_ids': ids, 'decision': 'accept', 'actor': 'r'})
    assert response.status_code == 400 and str(ids[1]) in response.json()['detail']
    with Store(project / 'project.db') as db:
        assert db.rows("SELECT id FROM coding_events WHERE action='accept'") == []
        assert len(db.rows('SELECT * FROM feedback_events')) == 1
        assert len(db.rows('SELECT * FROM pending_suggestions')) == 2


def test_batch_input_is_validated(tmp_path):
    _, client, ids = setup(tmp_path)
    url = '/api/projects/study/review/batch'
    for body in ({'suggestion_ids': [], 'decision': 'accept', 'actor': 'r'},
                 {'suggestion_ids': [ids[0], ids[0]], 'decision': 'accept', 'actor': 'r'},
                 {'suggestion_ids': list(range(1, 502)), 'decision': 'accept', 'actor': 'r'},
                 {'suggestion_ids': ids, 'decision': 'remove', 'actor': 'r'},
                 {'suggestion_ids': ids, 'decision': 'accept', 'actor': ''}):
        assert client.post(url, json=body).status_code == 422, body


def test_undo_appends_removals_and_keeps_the_accept_records(tmp_path):
    project, client, ids = setup(tmp_path)
    events = client.post('/api/projects/study/review/batch',
                         json={'suggestion_ids': ids, 'decision': 'accept', 'actor': 'r'}).json()['ids']
    # A non-accept id is refused and nothing is written.
    refused = client.post('/api/projects/study/review/batch/undo', json={'event_ids': [*events, ids[0]], 'actor': 'r'})
    assert refused.status_code == 400
    undone = client.post('/api/projects/study/review/batch/undo', json={'event_ids': events, 'actor': 'r'})
    assert undone.status_code == 200, undone.text
    assert len(undone.json()['ids']) == 3
    with Store(project / 'project.db') as db:
        assert db.rows('SELECT * FROM current_codings') == []
        assert len(db.rows("SELECT id FROM coding_events WHERE action='accept'")) == 3
        removals = db.rows("SELECT * FROM coding_events WHERE action='remove' ORDER BY id")
    assert all(row['actor'] == 'r' and row['actor_type'] == 'human' for row in removals)
    # Undoing again finds nothing still current, so it appends nothing.
    again = client.post('/api/projects/study/review/batch/undo', json={'event_ids': events, 'actor': 'r'})
    assert again.status_code == 200 and again.json()['ids'] == []
