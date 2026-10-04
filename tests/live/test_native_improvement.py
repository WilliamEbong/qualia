"""Opt-in native experiments on tiny invented workspaces, never research projects."""

import hashlib
import importlib
import json
import os
import subprocess

import pytest

from qualia.ai.backends.process import BackendError
from qualia.improve.experiment import improve_project
from qualia.io.benchmarks import import_benchmark
from qualia.store.db import Store
from qualia.workspace import ROUTING, init_project

pytestmark = pytest.mark.live


@pytest.mark.parametrize('agent,model', [('claude', 'haiku'), ('codex', 'gpt-6-luna')])
def test_native_experiment_preserves_methodology_and_records_usage(tmp_path, monkeypatch, agent, model):
    if os.environ.get('QUALIA_RUN_LIVE_IMPROVEMENT') != '1':
        pytest.skip('explicit authorization and QUALIA_RUN_LIVE_IMPROVEMENT=1 required')
    module = importlib.import_module(f'qualia.ai.backends.{agent}_cli')
    run_operator = module.run_operator
    failures = []

    def observed_operator(*args, **kwargs):
        try:
            return run_operator(*args, **kwargs)
        except BackendError as error:
            failures.append({'code': error.code, 'input_tokens': error.input_tokens,
                             'output_tokens': error.output_tokens, 'cli_version': error.cli_version})
            raise

    monkeypatch.setattr(module, 'run_operator', observed_operator)
    project = init_project(f'live-{agent}', tmp_path)
    config = {**ROUTING, 'allow_external': True, 'backend': agent, 'model': model,
              'daily_calls': 4, 'run_segments': 3, 'max_retries': 0,
              'qc_sample_rate': 0}
    (project / 'config/routing.yaml').write_text(json.dumps(config), encoding='utf-8')
    with Store(project / 'project.db') as db:
        db.save_code({'name': 'Hope', 'definition': 'An explicit expression of hope.'})
        version = db.freeze_codebook()['id']
        codebook = db.one('SELECT snapshot_json FROM codebook_versions WHERE id=?', (version,))
    import_benchmark(project, [
        {'segment_id': 'synthetic-1', 'text': 'I feel hopeful.', 'codes': [1],
         'transcript_id': 'synthetic-transcript'}], 'validation', version, [1])
    for arguments in [('add', '.'), ('-c', 'user.name=Qualia', '-c', 'user.email=qualia@localhost',
                                    'commit', '-qm', 'Synthetic live experiment baseline')]:
        subprocess.run(['git', '-C', str(project), *arguments], check=True,
                       capture_output=True, timeout=20)
    before = hashlib.sha256((project / 'METHODOLOGY.md').read_bytes()).hexdigest()
    rows = improve_project(project, agent=agent, budget=1, backend=agent, model=model)
    assert len(rows) == 1 and rows[0]['agent'] == agent
    assert rows[0]['decision'] in ('KEEP', 'REVERT')
    assert hashlib.sha256((project / 'METHODOLOGY.md').read_bytes()).hexdigest() == before
    with Store(project / 'project.db') as db:
        assert db.one('SELECT snapshot_json FROM codebook_versions WHERE id=?', (version,)) == codebook
        assert not db.rows('SELECT * FROM coding_events')
        assert len(db.rows('SELECT * FROM experiments')) == 1
        egress = db.rows('SELECT * FROM egress_log')
        assert 2 <= len(egress) <= 4
        operators = [row for row in egress if row['purpose'] == 'operator:cli_invocation']
        assert len(operators) == 1
        usage = db.rows("SELECT * FROM usage_ledger WHERE run_id LIKE 'operator-%' AND reservation_id IS NOT NULL")
        assert len(usage) == 1 and usage[0]['status'] == 'ok', failures
        assert usage[0]['input_tokens'] > 0 and usage[0]['output_tokens'] > 0
    status = subprocess.run(['git', '-C', str(project), 'status', '--porcelain'], check=True,
                            capture_output=True, timeout=20)
    assert status.stdout == b''
