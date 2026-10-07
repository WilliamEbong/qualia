"""Explicit opt-in smoke test: one synthetic draft-proposal invocation per subscription CLI."""

import json
import os

import pytest

from qualia.ai.proposals import propose_with_ai
from qualia.store.db import Store
from qualia.workspace import ROUTING, init_project

pytestmark = pytest.mark.live
TEXT = 'I waited three hours for the doctor and nobody told me why. It made me feel invisible.'


@pytest.mark.parametrize('backend', ['claude', 'codex'])
def test_subscription_draft_proposals(tmp_path, backend):
    if os.environ.get('QUALIA_RUN_LIVE_PROPOSALS') != '1':
        pytest.skip('set QUALIA_RUN_LIVE_PROPOSALS=1 only for an authorized paid smoke test')
    project = init_project('live', tmp_path)
    (project / 'config/routing.yaml').write_text(
        json.dumps({**ROUTING, 'allow_external': True, 'daily_calls': 1}), encoding='utf-8')
    with Store(project / 'project.db') as db:
        source = db.add('sources', {'name': 'synthetic', 'text': TEXT, 'content_hash': 'synthetic'})
        segment = db.add('segments', {'source_id': source, 'start': 0, 'end': len(TEXT), 'ordinal': 0})
        result = propose_with_ai(db, project, 'draft', backend=backend, segment_ids=[segment],
                                 focus='experiences of waiting for care')
        if result['status'] == 'unavailable':
            pytest.skip(result['errors'][0])
        assert result['status'] == 'completed', result['errors']
        rows = db.rows('SELECT * FROM code_proposals')
        assert rows and all(row['cli_version'] and row['actor_type'] == 'model' for row in rows)
        for row in rows:
            assert all(example in TEXT for example in json.loads(row['payload_json'])['examples_pos'])
        assert db.one('SELECT purpose FROM egress_log')['purpose'] == 'codebook_proposal:cli_invocation'
        assert db.rows('SELECT * FROM codes') == [] and db.rows('SELECT * FROM coding_events') == []
