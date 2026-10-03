import pytest

from qualia.store.db import Store


def seed_coding(db):
    source = db.add('sources', {'name': 'Unicode', 'text': 'A😀BC', 'content_hash': 'unicode'})
    segment = db.add('segments', {'source_id': source, 'start': 0, 'end': 4, 'ordinal': 0})
    first = db.save_code({'name': 'First'})
    second = db.save_code({'name': 'Second'})
    version = db.freeze_codebook()['id']
    event = {'segment_id': segment, 'code_id': first, 'codebook_version_id': version,
             'span_start': 1, 'span_end': 3, 'action': 'assign', 'actor_type': 'human',
             'actor': 'researcher', 'pipeline_version': 'synthetic-pipeline'}
    return source, second, event


def test_overlapping_multicode_removal_and_memo():
    with Store(':memory:') as db:
        _, second, event = seed_coding(db)
        db.assign(event)
        db.assign({**event, 'code_id': second, 'span_start': 2, 'span_end': 4})
        assert len(db.rows('SELECT * FROM current_codings')) == 2
        assert {r['excerpt'] for r in db.retrieve()} == {'😀B', 'BC'}
        db.assign({**event, 'action': 'remove'})
        assert len(db.rows('SELECT * FROM coding_events')) == 3
        assert [r['code_id'] for r in db.retrieve()] == [second]
        memo = db.save_memo({'title': 'Observation', 'text': 'Synthetic note',
                             'segment_id': event['segment_id'], 'code_id': second})
        db.save_memo({'text': 'Revised note'}, memo)
        assert db.one('SELECT text FROM memos WHERE id=?', (memo,))['text'] == 'Revised note'


@pytest.mark.parametrize('changes', [{'actor_type': 'model'}, {'action': 'accept'},
                                      {'actor': ''}, {'span_start': 1.5}, {'pipeline_version': ''}])
def test_manual_coding_rejects_invalid_boundary(changes):
    with Store(':memory:') as db:
        _, _, event = seed_coding(db)
        with pytest.raises(ValueError):
            db.assign({**event, **changes})
        assert db.rows('SELECT * FROM coding_events') == []


def test_missing_memo_and_code_updates_fail_loudly():
    with Store(':memory:') as db:
        with pytest.raises(ValueError, match='memo.*99'):
            db.save_memo({'text': 'note'}, 99)
        with pytest.raises(ValueError, match='code.*99'):
            db.save_code({'name': 'new'}, 99)
