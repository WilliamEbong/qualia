import json

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from qualia.ai.backends.fake import FakeBackend
from qualia.cli import app
from qualia.evaluation import evaluate_project, report_markdown, write_reports
from qualia.io.benchmarks import import_benchmark
from qualia.server.app import create_app
from qualia.store.db import Store
from qualia.workspace import init_project, vault_dir


def setup_project(tmp_path):
    project = init_project('study', tmp_path / 'home')
    with Store(project / 'project.db') as db:
        code = db.save_code({'name': 'Possibility'})
        frozen = db.freeze_codebook()
    records = [dict(segment_id='example-1', text='Synthetic possibility.', codes=[code], transcript_id='t1')]
    import_benchmark(project, records, 'validation', frozen['id'], [code])
    return project, records, frozen


def test_evaluation_complete_provenance_no_gold_sent_or_coding_writes(tmp_path):
    project, records, frozen = setup_project(tmp_path)

    class InspectFake(FakeBackend):
        def classify(self, segments, schema, context):
            assert segments == [{'id': 'example-1', 'text': 'Synthetic possibility.'}]
            assert all(set(row) == {'id', 'text'} for row in segments)
            assert not any(key in context for key in ('gold', 'records', 'coders', 'references'))
            return super().classify(segments, schema, context)

    with Store(project / 'project.db') as db:
        result = evaluate_project(db, project, backend='fake', registry={'fake': InspectFake()})
        metrics = result['metrics']
        assert metrics['macro_f1'] == 1
        assert metrics['kappa'] is None
        assert metrics['ece'] == pytest.approx(0.4)
        assert metrics['identity']['cli_versions'] == ['fake-v1']
        assert len(metrics['identity']['benchmark_hash']) == 64
        assert metrics['calls'] == 1
        assert not db.rows('SELECT * FROM coding_events')
        stored = db.one('SELECT * FROM evaluation_runs')
        assert stored['codebook_version_id'] == frozen['id']
        assert len(json.loads(stored['predictions_json'])) == 1
        again = evaluate_project(db, project, backend='fake', registry={'fake': InspectFake()})
        assert again['metrics']['calls'] == 0
        assert again['metrics']['cache_hits'] == 1
        assert len(db.rows('SELECT * FROM evaluation_runs')) == 2
    assert 'candidates' not in result
    report = report_markdown(result)
    assert '| kappa | n/a |' in report and '| review_share |' in report
    assert '| Precision 95% CI |' in report and '| [' in report
    paths = write_reports(result, project / 'reports')
    assert all(path.is_file() for path in paths)
    assert json.loads(paths[0].read_text()) == result


def test_failed_evaluation_does_not_publish_optimistic_metrics(tmp_path):
    project, _, _ = setup_project(tmp_path)

    class Broken(FakeBackend):
        def classify(self, *args):
            return {'predictions': [], 'input_tokens': 0, 'output_tokens': 0, 'cli_version': 'fake-v1'}

    with Store(project / 'project.db') as db:
        with pytest.raises(ValueError, match='evaluation incomplete'):
            evaluate_project(db, project, backend='fake', registry={'fake': Broken()})
        assert not db.rows('SELECT * FROM evaluation_runs')
        assert not db.rows('SELECT * FROM coding_events')
        assert db.one("SELECT calls FROM usage_ledger WHERE status='reserved'")['calls'] == 1


def test_validation_api_cannot_select_protected_and_never_returns_predictions(tmp_path):
    project, records, frozen = setup_project(tmp_path)
    protected = [{**records[0], 'segment_id': 'secret-2', 'transcript_id': 't2', 'text': 'Protected sentinel.'}]
    import_benchmark(project, protected, 'protected', frozen['id'], records[0]['codes'])
    client = TestClient(create_app(home=tmp_path / 'home', token='test'), base_url='http://localhost',
                        headers={'x-qualia-token': 'test'})
    assert client.post('/api/projects/study/evaluate', json={'protected': True}).status_code == 422
    assert client.post('/api/projects/study/evaluate', json={'split': 'protected'}).status_code == 422
    response = client.post('/api/projects/study/evaluate', json={'backend': 'fake'})
    assert response.status_code == 200, response.text
    assert response.json()['split'] == 'validation'
    assert 'predictions' not in response.text
    with Store(project / 'project.db') as db:
        evaluate_project(db, project, split='protected', protected=True, backend='fake')
    workspace = client.get('/api/projects/study').json()
    assert len(workspace['evaluation_runs']) == 1
    assert 'Protected sentinel' not in json.dumps(workspace)
    assert 'predictions_json' not in json.dumps(workspace)


def test_protected_cli_explicit_and_tampering_blocks(tmp_path, monkeypatch):
    project, records, frozen = setup_project(tmp_path)
    import_benchmark(project, [{**records[0], 'segment_id': 'p', 'transcript_id': 'pt'}],
                     'protected', frozen['id'], records[0]['codes'])
    monkeypatch.setenv('QUALIA_HOME', str(tmp_path / 'home'))
    runner = CliRunner()
    forbidden = runner.invoke(app, ['evaluate', '--project', 'study', '--split', 'protected', '--backend', 'fake'])
    assert forbidden.exit_code != 0
    allowed = runner.invoke(app, ['evaluate', '--project', 'study', '--protected', '--backend', 'fake'])
    assert allowed.exit_code == 0, allowed.output
    (vault_dir(project) / 'manifest.sha256').write_text('{}', encoding='utf-8')
    tampered = runner.invoke(app, ['evaluate', '--project', 'study', '--protected', '--backend', 'fake'])
    assert tampered.exit_code != 0
    assert 'manifest' in tampered.output.lower()


def test_candidates_are_returned_only_on_request_and_never_stored(tmp_path):
    project, records, _ = setup_project(tmp_path)
    with Store(project / 'project.db') as db:
        result = evaluate_project(db, project, backend='fake', with_candidates=True)
        assert result['references'] == records and result['code_ids'] == records[0]['codes']
        assert result['candidates'][0]['segment_id'] == 'example-1'
        stored = json.loads(db.one('SELECT metrics_json FROM evaluation_runs')['metrics_json'])
        assert 'candidates' not in stored
