from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from qualia.ai import ledger
from qualia.ai.backends.fake import FakeBackend
from qualia.ai.schemas import routing_config
from qualia.io.imports import import_text
from qualia.store.db import Store
from qualia.workspace import init_project


def test_ledger_reservations_serialize_at_external_budget(tmp_path):
    path = tmp_path / 'project.db'
    with Store(path):
        pass
    barrier = Barrier(2)
    provider = FakeBackend()
    provider.external = True
    config = routing_config({'allow_external': True, 'daily_calls': 1})

    def reserve(_):
        with Store(path) as db:
            barrier.wait(timeout=10)
            try:
                return ledger.reserve(db, backend=provider, model='fake-v1', run_id='concurrent',
                                      segments=[{'id': 's1', 'text': 'Synthetic text'}],
                                      config=config, purpose='classification')
            except ValueError as exc:
                return str(exc)

    with ThreadPoolExecutor(2) as workers:
        results = list(workers.map(reserve, range(2)))
    assert sum(type(value) is int for value in results) == 1
    assert results.count('budget reached') == 1
    with Store(path) as db:
        assert len(db.rows('SELECT * FROM egress_log')) == 1
        assert 'Synthetic text' not in str(db.rows('SELECT * FROM egress_log'))
        assert db.one('SELECT sum(calls) AS n FROM usage_ledger')['n'] == 1


@pytest.mark.parametrize('failed', [True, False])
def test_unknown_actual_cost_preserves_reserved_ceiling(failed):
    config = routing_config({'allow_external': True})
    provider = FakeBackend()
    provider.external = True
    with Store(':memory:') as db:
        reservation = ledger.reserve(db, backend=provider, model='priced', run_id='run',
                                     segments=[{'text': 'Synthetic'}], config=config,
                                     purpose='classification', reserved_usd=0.8)
        ledger.finish(db, reservation, error=ValueError('safe') if failed else None,
                      reserved_usd=0.8)
        row = db.one('SELECT * FROM usage_ledger WHERE reservation_id=?', (reservation,))
        assert row['cost_usd'] == 0.8
        assert row['status'] == ('error' if failed else 'ok')
        with pytest.raises(ValueError, match='cost limit'):
            ledger.reserve(db, backend=provider, model='priced', run_id='run',
                           segments=[{'text': 'Next'}], config=config,
                           purpose='classification', reserved_usd=0.3)


def test_concurrent_opposing_reviews_apply_once(tmp_path):
    project = init_project('review', tmp_path)
    path = project / 'project.db'
    with Store(path) as db:
        import_text(db, project, 'synthetic', 'Synthetic text', 'txt')
        code = db.save_code({'name': 'Synthetic'})
        frozen = db.freeze_codebook()
        suggestion = db.record_suggestions([{'segment_id': 1, 'code_id': code,
                     'span_start': 0, 'span_end': 9, 'actor_type': 'model', 'actor': 'fake',
                     'backend': 'fake', 'model': 'fake-v1', 'cli_version': 'fixture',
                     'action': 'suggest', 'review_status': 'pending', 'review_trigger': '[]',
                     'codebook_version_id': frozen['id'], 'pipeline_version': 'pipeline',
                     'prompt_hash': 'prompt', 'score': 0.6, 'rationale': 'Synthetic'}])[0]
    barrier = Barrier(2)

    def review(action):
        with Store(path) as db:
            barrier.wait(timeout=10)
            try:
                return db.review(suggestion, action, 'reviewer', 'pipeline')
            except ValueError as exc:
                return str(exc)

    with ThreadPoolExecutor(2) as workers:
        outcomes = list(workers.map(review, ['accept', 'reject']))
    assert sum(type(value) is int for value in outcomes) == 1
    with Store(path) as db:
        assert len(db.rows('SELECT * FROM feedback_events')) == 1
        assert len(db.rows('SELECT * FROM coding_events')) == 2
        assert not db.rows('SELECT * FROM pending_suggestions')
