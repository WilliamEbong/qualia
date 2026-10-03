from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from qualia.store.db import Store


def attempt(db, **changes):
    values = dict(backend='synthetic', model='fixture', run_id='run', segment_hashes=['hash'],
                  external=True, allow_external=True, daily_calls=1, run_segments=10)
    return db.reserve_attempt(**(values | changes))


def test_reservations_serialize_concurrent_budget_checks(tmp_path):
    path = tmp_path / 'ledger.db'
    with Store(path):
        pass
    barrier = Barrier(2)

    def reserve():
        with Store(path) as db:
            barrier.wait()
            try:
                return attempt(db)
            except ValueError as exc:
                return str(exc)

    with ThreadPoolExecutor(2) as workers:
        results = list(workers.map(lambda _: reserve(), range(2)))
    assert sum(type(value) is int for value in results) == 1
    assert 'budget reached' in results
    with Store(path) as db:
        assert len(db.rows('SELECT * FROM egress_log')) == 1
        row = db.one('SELECT * FROM usage_ledger')
        db.finish_attempt(row['id'], input_tokens=100, output_tokens=20, cli_version='fixture')
        with pytest.raises(ValueError, match='already finalized'):
            db.finish_attempt(row['id'])
        assert db.one('SELECT sum(calls) AS n FROM usage_ledger')['n'] == 1


def test_outstanding_cost_hold_and_failed_admission_are_durable(tmp_path):
    with Store(tmp_path / 'ledger.db') as db:
        first = attempt(db, daily_calls=10, reserved_usd=0.8)
        with pytest.raises(ValueError, match='cost limit'):
            attempt(db, daily_calls=10, reserved_usd=0.3)
        assert len(db.rows('SELECT * FROM egress_log')) == 1
        db.finish_attempt(first, cost_usd=0.1)
        assert attempt(db, daily_calls=10, reserved_usd=0.3) > first
        with pytest.raises(ValueError, match='disabled'):
            attempt(db, allow_external=False)
        with pytest.raises(ValueError, match='invalid cost'):
            attempt(db, reserved_usd=float('nan'))
