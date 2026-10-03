"""Opt-in synthetic Jev request through normal policy, budget and egress accounting."""

import os

import pytest

from qualia.ai.backends.jev import INPUT_RATE, MODEL, RESERVED_INPUT_TOKENS, JevBackend
from qualia.ai.router import classify_segments
from qualia.store.db import Store
from qualia.workspace import ROUTING

pytestmark = pytest.mark.live


def test_synthetic_jev_live(tmp_path):
    if os.environ.get('QUALIA_RUN_LIVE_JEV') != '1':
        pytest.skip('set QUALIA_RUN_LIVE_JEV=1 only for an authorized synthetic paid check')
    if not JevBackend().available():
        pytest.skip('Jev key missing or placeholder; save it privately using docs/JEV-SETUP.md')
    with Store(tmp_path / 'synthetic-jev-live.db') as db:
        result = classify_segments(db, [{'id': 'synthetic-1', 'text': 'A positive change is possible.'}],
            [{'id': 1, 'name': 'Possibility', 'status': 'active',
              'definition': 'Language describing a possible positive change.'}],
            {**ROUTING, 'allow_external': True, 'jev_enabled': True, 'daily_calls': 1,
             'run_segments': 1, 'max_retries': 0, 'qc_sample_rate': 0,
             'jev_daily_usd': RESERVED_INPUT_TOKENS * INPUT_RATE},
            prompt='Apply the supplied codebook to the synthetic sentence.',
            codebook_version_id=1, pipeline_version='synthetic-jev-smoke-v1',
            backend='jev', model=MODEL, run_id='synthetic-jev-live')
        rows = db.rows('SELECT * FROM usage_ledger WHERE reservation_id IS NOT NULL')
        assert result['calls'] == len(rows) == 1
        assert len(db.rows('SELECT * FROM egress_log')) == 1
        assert not db.rows('SELECT * FROM coding_events')
        assert result['status'] == 'completed', result['errors']
        assert result['predictions'][0]['segment_id'] == 'synthetic-1'
        assert rows[0]['input_tokens'] > 0 and rows[0]['output_tokens'] >= 0
        assert MODEL in rows[0]['cli_version']
        assert rows[0]['cost_usd'] == pytest.approx(rows[0]['input_tokens'] * INPUT_RATE)
