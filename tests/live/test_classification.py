"""Explicit opt-in smoke tests using synthetic text and the normal budget/egress router."""

import os

import pytest

from qualia.ai.router import classify_segments, default_registry
from qualia.store.db import Store
from qualia.workspace import ROUTING

pytestmark = pytest.mark.live


@pytest.mark.parametrize('backend,model', [('claude', 'haiku'), ('codex', 'gpt-6-luna'),
                                         ('codex', 'gpt-6-astra')])
def test_subscription_classification(tmp_path, backend, model):
    if os.environ.get('QUALIA_RUN_LIVE_CLASSIFICATION') != '1':
        pytest.skip('set QUALIA_RUN_LIVE_CLASSIFICATION=1 only for an authorized paid smoke test')
    registry = default_registry()
    provider = registry[backend]
    if not provider.available():
        pytest.skip(provider.unavailable_reason)
    # Claude's schema serializer needs room beyond the tiny 512-token fixture:
    # observed truncation consumed four generations without a valid result.
    output_limit = 4096 if backend == 'claude' else 512
    with Store(tmp_path / 'live-classification.db') as db:
        result = classify_segments(
            db, [{'id': 'synthetic-1', 'text': 'I feel hopeful.'}],
            [{'id': 1, 'name': 'Hope', 'status': 'active',
              'definition': 'Explicit expression of hope.'}],
            {**ROUTING, 'allow_external': True, 'daily_calls': 1, 'run_segments': 1,
             'max_retries': 0, 'max_output_tokens': output_limit, 'qc_sample_rate': 0},
            prompt='Apply the supplied codebook. Return the requested JSON schema.',
            codebook_version_id=1, pipeline_version='synthetic-live-smoke-v1',
            backend=backend, model=model, run_id='synthetic-live-smoke', registry=registry)
        rows = db.rows('SELECT * FROM usage_ledger WHERE reservation_id IS NOT NULL')
        assert result['calls'] == len(rows) == 1
        assert len(db.rows('SELECT * FROM egress_log')) == 1
        assert db.rows('SELECT * FROM egress_log')[0]['purpose'] == 'classification:cli_invocation'
        assert not db.rows('SELECT * FROM coding_events')
        assert result['status'] == 'completed', result['errors']
        assert result['predictions'][0]['segment_id'] == 'synthetic-1'
        assert rows[0]['input_tokens'] > 0 and rows[0]['output_tokens'] > 0
