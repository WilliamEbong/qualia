import json

import pytest

from qualia.ai.backends.fake import FakeBackend
from qualia.ai.backends.process import proposal_prompt
from qualia.ai.proposals import propose_from_evidence, propose_with_ai
from qualia.ai.schemas import ProposalValidationError, validate_proposals
from qualia.store.db import Store
from qualia.workspace import ROUTING, init_project

TEXT = 'I waited three hours for the doctor. Nobody told me why.'


class Fixture(FakeBackend):
    name = 'fixture'

    def __init__(self, external=True, response=None):
        self.external = external
        self.response = response
        self.calls = 0

    def propose(self, segments, schema, context):
        self.calls += 1
        self.context = context
        return self.response or super().propose(segments, schema, context)


@pytest.fixture
def project(tmp_path):
    path = init_project('study', tmp_path)
    (path / 'config/routing.yaml').write_text(json.dumps({**ROUTING, 'allow_external': True}),
                                              encoding='utf-8')
    return path


def seed(db):
    source = db.add('sources', {'name': 'a', 'text': TEXT, 'content_hash': 'a'})
    return db.add('segments', {'source_id': source, 'start': 0, 'end': len(TEXT), 'ordinal': 0})


def proposal(**values):
    return {'kind': 'new_code', 'target_code_id': None, 'name': 'Waiting', 'definition': 'd',
            'include': '', 'exclude': '', 'examples_pos': ['I waited three hours'], 'examples_neg': [],
            'rationale': 'r', 'evidence_segment_ids': ['1'], **values}


def response(*items):
    return {'proposals': list(items), 'input_tokens': 5, 'output_tokens': 7, 'cli_version': '1.0'}


def test_draft_stores_model_proposals_with_usage_and_egress_but_no_codes(project):
    backend = Fixture(response=response(proposal()))
    with Store(project / 'project.db') as db:
        segment = seed(db)
        result = propose_with_ai(db, project, 'draft', backend='fixture', segment_ids=[segment],
                                 focus=' waiting ', registry={'fixture': backend})
        assert result['status'] == 'completed' and len(result['proposal_ids']) == 1
        row = db.one('SELECT * FROM code_proposals')
        assert row['actor_type'] == 'model' and row['backend'] == 'fixture' and row['cli_version'] == '1.0'
        assert row['codebook_version_id'] is None and len(row['prompt_hash']) == 64
        assert json.loads(row['payload_json'])['status'] == 'active'
        assert json.loads(row['evidence_json']) == {'segment_ids': [1], 'focus': 'waiting', 'removed_examples': 0}
        assert backend.context['focus'] == 'waiting'
        assert db.one("SELECT purpose FROM egress_log")['purpose'] == 'codebook_proposal'
        assert {row['status'] for row in db.rows('SELECT status FROM usage_ledger')} == {'reserved', 'ok'}
        assert db.rows('SELECT * FROM codes') == [] and db.rows('SELECT * FROM coding_events') == []


def test_external_off_blocks_before_any_call_or_ledger_row(project):
    (project / 'config/routing.yaml').write_text(json.dumps(ROUTING), encoding='utf-8')
    backend = Fixture()
    with Store(project / 'project.db') as db:
        segment = seed(db)
        result = propose_with_ai(db, project, 'draft', backend='fixture', segment_ids=[segment],
                                 registry={'fixture': backend})
        assert result['status'] == 'blocked' and backend.calls == 0
        assert db.rows('SELECT * FROM usage_ledger') == [] and db.rows('SELECT * FROM egress_log') == []


def test_unquoted_examples_are_removed_and_normalized_quotes_stored_verbatim(project):
    examples = ['Nobody told me anything at all', '“i WAITED  three hours”']
    backend = Fixture(response=response(proposal(examples_pos=examples)))
    with Store(project / 'project.db') as db:
        segment = seed(db)
        result = propose_with_ai(db, project, 'draft', backend='fixture', segment_ids=[segment],
                                 registry={'fixture': backend})
        assert result['status'] == 'completed'
        row = db.one('SELECT * FROM code_proposals')
        assert json.loads(row['payload_json'])['examples_pos'] == ['I waited three hours']
        assert json.loads(row['evidence_json'])['removed_examples'] == 1
        assert '1 example(s) removed' in row['rationale']


def test_structural_errors_store_nothing_and_finish_the_attempt_as_error(project):
    backend = Fixture(response=response(proposal(evidence_segment_ids=['99'])))
    with Store(project / 'project.db') as db:
        segment = seed(db)
        result = propose_with_ai(db, project, 'draft', backend='fixture', segment_ids=[segment],
                                 registry={'fixture': backend})
        assert result['status'] == 'error' and 'proposal 1' in result['errors'][0]
        assert db.rows('SELECT * FROM code_proposals') == []
        assert db.one("SELECT status FROM usage_ledger WHERE reservation_id IS NOT NULL")['status'] == 'error'


def test_backends_without_propose_are_refused(project):
    with Store(project / 'project.db') as db:
        segment = seed(db)
        result = propose_with_ai(db, project, 'draft', backend='rules', segment_ids=[segment])
        assert result['status'] == 'unavailable' and 'cannot propose' in result['errors'][0]
        with pytest.raises(ValueError, match='distinct segments'):
            propose_with_ai(db, project, 'draft', backend='fake', segment_ids=[])
        with pytest.raises(ValueError, match='at most 500'):
            propose_with_ai(db, project, 'draft', backend='fake', segment_ids=[segment], focus='x' * 501)


def test_refine_sends_review_evidence_and_fake_revision_is_accepted(project):
    with Store(project / 'project.db') as db:
        segment = seed(db)
        code = db.save_code({'name': 'Waiting', 'examples_pos': ['researcher example']})
        version = db.freeze_codebook()['id']
        event = db.add('coding_events', {'segment_id': segment, 'code_id': code, 'span_start': 0,
                       'span_end': 5, 'action': 'suggest', 'actor_type': 'model', 'actor': 'fake',
                       'backend': 'fake', 'model': 'fake', 'cli_version': 'x', 'prompt_hash': 'h',
                       'review_status': 'pending', 'codebook_version_id': version,
                       'pipeline_version': 'p'})
        db.review(event, 'reject', 'researcher', 'p', 'only the delay, not the doctor')
        backend = Fixture(external=False)
        result = propose_with_ai(db, project, 'refine', backend='fixture', code_ids=[code],
                                 registry={'fixture': backend})
        assert result['status'] == 'completed'
        [sent] = backend.context['refine']
        assert sent['rejected_segment_ids'] == [str(segment)] and sent['review_notes'] == [
            'only the delay, not the doctor']
        row = db.one('SELECT * FROM code_proposals')
        assert row['kind'] == 'revise_code' and row['target_code_id'] == code
        assert db.rows('SELECT * FROM egress_log') == []
        decided = db.decide_code_proposal(row['id'], 'accept', 'researcher')
        assert decided['code_id'] == code
        assert 'directly' in db.one('SELECT definition FROM codes')['definition']


@pytest.mark.parametrize('item,reason', [
    (proposal(kind='revise_code', target_code_id=1), 'only new_code'),
    (proposal(target_code_id=1), 'cannot name a target'),
    (proposal(evidence_segment_ids=['9']), 'not supplied'),
    (proposal(name='support'), 'collides'),
])
def test_validation_names_the_failing_proposal(item, reason):
    codes = [{'id': 1, 'name': 'Support', 'examples_pos': '[]', 'examples_neg': '[]'}]
    with pytest.raises(ProposalValidationError, match=f'proposal 2: .*{reason}'):
        validate_proposals(response(proposal(name='Fine'), item), 'draft', [{'id': '1', 'text': TEXT}], codes)


def test_revision_may_keep_existing_examples_and_prompt_is_bounded():
    codes = [{'id': 1, 'name': 'Support', 'examples_pos': '["kept"]', 'examples_neg': '[]'}]
    revision = proposal(kind='revise_code', target_code_id=1, name='Support', examples_pos=['kept'])
    assert validate_proposals(response(revision), 'refine', [{'id': '1', 'text': TEXT}], codes, {1})
    prompt = proposal_prompt([{'id': '1', 'text': TEXT}], {}, {'prompt': 'p', 'codebook': []})
    assert 'Copy every example exactly' in prompt and TEXT in prompt
    with pytest.raises(Exception):
        proposal_prompt([{'id': str(n), 'text': 'x'} for n in range(21)], {}, {'prompt': 'p'})


def test_evidence_mode_is_offline_and_not_repeated_while_pending(project):
    with Store(project / 'project.db') as db:
        segment = seed(db)
        code = db.save_code({'name': 'Waiting'})
        version = db.freeze_codebook()['id']
        for start in (0, 5):
            event = db.add('coding_events', {'segment_id': segment, 'code_id': code, 'span_start': start,
                           'span_end': start + 5, 'action': 'suggest', 'actor_type': 'model',
                           'actor': 'fake', 'backend': 'fake', 'model': 'fake', 'cli_version': 'x',
                           'prompt_hash': 'h', 'review_status': 'pending',
                           'codebook_version_id': version, 'pipeline_version': 'p'})
            db.review(event, 'reject', 'researcher', 'p')
        first = propose_from_evidence(db)
        assert len(first['proposal_ids']) == 1
        assert db.rows('SELECT * FROM usage_ledger') == [] and db.rows('SELECT * FROM egress_log') == []
        assert propose_from_evidence(db)['proposal_ids'] == []
        payload = json.loads(db.one('SELECT payload_json FROM code_proposals')['payload_json'])
        assert payload['examples_neg'] == [TEXT[5:10], TEXT[0:5]]


def test_api_cli_and_export_round_trip(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from typer.testing import CliRunner

    from qualia.cli import app
    from qualia.server.app import create_app

    home = tmp_path / 'home'
    monkeypatch.setenv('QUALIA_HOME', str(home))
    client = TestClient(create_app(home, token='t'), base_url='http://127.0.0.1',
                        headers={'X-Qualia-Token': 't'})
    assert client.post('/api/projects', json={'name': 'study'}).status_code == 201
    assert client.post('/api/projects/study/import', json={
        'name': 'a.txt', 'content': TEXT, 'format': 'txt'}).status_code == 200
    base = '/api/projects/study/codebook/proposals'
    run = client.post(f'{base}/ai', json={'mode': 'draft', 'backend': 'fake', 'segment_ids': [1],
                                          'focus': 'waiting'}).json()
    assert run['status'] == 'completed' and run['backend'] == 'fake'
    [first] = run['proposal_ids']
    accepted = client.post(f'{base}/{first}/decision', json={
        'decision': 'accept', 'actor': 'researcher', 'values': {'name': 'Waiting', 'definition': None}})
    assert accepted.status_code == 200, accepted.text
    workspace = client.get('/api/projects/study').json()
    [listed] = workspace['code_proposals']
    assert listed['decision'] == 'accept' and listed['resulting_code_id'] == accepted.json()['code_id']
    assert workspace['codes'][0]['name'] == 'Waiting'
    assert workspace['codes'][0]['definition'] == 'Synthetic draft code for offline demonstration.'
    again = client.post(f'{base}/{first}/decision', json={'decision': 'reject', 'actor': 'researcher'})
    assert again.status_code == 400 and 'already decided' in again.text
    assert client.post(f'{base}/ai', json={'mode': 'draft', 'segment_ids': [1], 'extra': 1}).status_code == 422
    assert client.post(f'{base}/evidence').json()['proposal_ids'] == []

    runner = CliRunner()
    result = runner.invoke(app, ['codebook', 'propose', '--mode', 'draft', '--backend', 'fake',
                                 '--segments', '1', '--project', 'study'])
    assert result.exit_code == 0, result.output
    pending = json.loads(runner.invoke(app, ['codebook', 'proposals', '--project', 'study']).output)
    assert len(pending) == 1 and pending[0]['decision'] is None
    result = runner.invoke(app, ['codebook', 'decide', str(pending[0]['id']), 'reject', '--actor',
                                 'researcher', '--note', 'duplicate', '--project', 'study'])
    assert result.exit_code == 0, result.output
    assert len(json.loads(runner.invoke(app, ['codebook', 'proposals', '--all', '--project', 'study']).output)) == 2
    result = runner.invoke(app, ['codebook', 'propose', '--mode', 'draft', '--backend', 'rules',
                                 '--segments', '1', '--project', 'study'])
    assert result.exit_code == 1 and 'cannot propose' in result.output
    exported = json.loads(runner.invoke(app, ['export', '--project', 'study']).output)
    assert len(exported['code_proposals']) == 2 and len(exported['code_proposal_decisions']) == 2
    assert 'definition' not in json.loads(exported['code_proposals'][0]['payload_json'])
    assert 'note' not in exported['code_proposal_decisions'][1]
