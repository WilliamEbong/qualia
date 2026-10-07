import json
import sqlite3

import pytest

from qualia.store.db import Store


def proposal(**values):
    return {'batch_id': 'batch', 'mode': 'evidence', 'kind': 'new_code', 'actor_type': 'rule',
            'payload_json': json.dumps({'name': 'Waiting', 'definition': 'Time spent waiting.'}),
            **values}


def test_proposal_tables_reject_edits_and_requires_model_provenance():
    with Store(':memory:') as db:
        assert db.connection.execute('PRAGMA user_version').fetchone()[0] >= 3
        [row] = db.record_code_proposals([proposal()])
        for sql in ('UPDATE code_proposals SET rationale=1', 'DELETE FROM code_proposals'):
            with pytest.raises(sqlite3.IntegrityError, match='append-only'):
                db.connection.execute(sql)
            db.connection.rollback()
        with pytest.raises(sqlite3.IntegrityError):
            db.record_code_proposals([proposal(actor_type='model', backend='fake', model='fake')])
        with pytest.raises(sqlite3.IntegrityError):
            db.record_code_proposals([proposal(kind='revise_code')])
        db.decide_code_proposal(row, 'reject', 'researcher', 'not useful')
        with pytest.raises(sqlite3.IntegrityError, match='append-only'):
            db.connection.execute('DELETE FROM code_proposal_decisions')
        db.connection.rollback()


def test_accept_new_code_with_human_edits_changes_only_the_draft():
    with Store(':memory:') as db:
        existing = db.save_code({'name': 'Support'})
        frozen = db.freeze_codebook()
        [row] = db.record_code_proposals([proposal()])
        result = db.decide_code_proposal(row, 'accept', 'researcher', '',
                                         {'name': 'Waiting time', 'examples_pos': ['I waited.']})
        code = db.one('SELECT * FROM codes WHERE id=?', (result['code_id'],))
        assert code['name'] == 'Waiting time' and code['definition'] == 'Time spent waiting.'
        assert json.loads(code['examples_pos']) == ['I waited.']
        assert db.one('SELECT * FROM codebook_versions WHERE id=?', (frozen['id'],)) == frozen
        assert len(db.rows('SELECT * FROM codebook_versions')) == 1
        assert db.rows('SELECT * FROM coding_events') == []
        decision = db.one('SELECT * FROM code_proposal_decisions')
        assert json.loads(decision['applied_json'])['name'] == 'Waiting time'
        assert existing != result['code_id']
        with pytest.raises(ValueError, match='already decided'):
            db.decide_code_proposal(row, 'reject', 'researcher')


def test_accept_revision_applies_only_changed_fields():
    with Store(':memory:') as db:
        code = db.save_code({'name': 'Support', 'definition': 'Help.', 'examples_neg': ['old']})
        payload = {'name': 'Support', 'definition': 'Help.', 'examples_neg': ['old', 'new']}
        [row] = db.record_code_proposals([proposal(kind='revise_code', target_code_id=code,
                                                   payload_json=json.dumps(payload))])
        result = db.decide_code_proposal(row, 'accept', 'researcher')
        assert result['code_id'] == code
        decision = db.one('SELECT * FROM code_proposal_decisions')
        assert json.loads(decision['applied_json']) == {'examples_neg': ['old', 'new']}
        assert json.loads(db.one('SELECT examples_neg FROM codes')['examples_neg']) == ['old', 'new']


def test_decision_validation_and_reject_leaves_codebook_alone():
    with Store(':memory:') as db:
        [row] = db.record_code_proposals([proposal()])
        for args in (('maybe', 'researcher'), ('accept', ' ')):
            with pytest.raises(ValueError):
                db.decide_code_proposal(row, *args)
        with pytest.raises(ValueError, match='invalid proposal values'):
            db.decide_code_proposal(row, 'accept', 'researcher', '', {'id': 4})
        with pytest.raises(ValueError, match='not found'):
            db.decide_code_proposal(99, 'reject', 'researcher')
        db.decide_code_proposal(row, 'reject', 'researcher', 'too broad')
        assert db.rows('SELECT * FROM codes') == []
        [listed] = db.code_proposals()
        assert listed['decision'] == 'reject' and listed['decision_note'] == 'too broad'
