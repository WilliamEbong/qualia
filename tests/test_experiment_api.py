import json
import subprocess

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from qualia.cli import app
from qualia.io.benchmarks import import_benchmark
from qualia.server.app import create_app
from qualia.store.db import Store
from qualia.workspace import ROUTING, init_project


def test_real_cli_policy_confirmation_and_read_only_history_api(tmp_path, monkeypatch):
    monkeypatch.setenv('QUALIA_HOME', str(tmp_path / 'home'))
    path = init_project('study', tmp_path / 'home')
    (path / 'config/routing.yaml').write_text(json.dumps({**ROUTING, 'backend': 'fake', 'model': 'fake-v1'}))
    with Store(path / 'project.db') as db:
        db.save_code({'name': 'First'})
        db.save_code({'name': 'Second'})
        version = db.freeze_codebook()['id']
        import_benchmark(path, [{'segment_id': 'one', 'text': 'Synthetic possibility.', 'codes': [2],
                                 'transcript_id': 't'}], 'validation', version, [1, 2])
    subprocess.run(['git', '-C', str(path), 'add', '.'], check=True, capture_output=True)
    subprocess.run(['git', '-C', str(path), '-c', 'user.name=Qualia', '-c', 'user.email=qualia@localhost',
                    'commit', '-qm', 'Synthetic benchmark'], check=True, capture_output=True)
    runner = CliRunner()
    zero = runner.invoke(app, ['improve', '--project', 'study', '--agent', 'fake', '--budget', '0'])
    assert zero.exit_code == 0 and json.loads(zero.output) == []
    result = runner.invoke(app, ['improve', '--project', 'study', '--agent', 'fake'])
    assert result.exit_code == 0, result.output
    rows = json.loads(result.output)
    assert rows[0]['decision'] == 'KEEP'
    after = json.loads(rows[0]['after_json'])
    assert after['metrics']['macro_f1'] > json.loads(rows[0]['before_json'])['metrics']['macro_f1']
    assert after['confirmation']['metrics']['calls'] == 1
    client = TestClient(create_app(home=tmp_path / 'home', token='test'), base_url='http://localhost',
                        headers={'x-qualia-token': 'test'})
    history = client.get('/api/projects/study/experiments')
    assert history.status_code == 200
    assert history.json() == rows
    assert client.post('/api/projects/study/experiments', json={'decision': 'KEEP'}).status_code == 405
    assert client.get('/api/projects/study').json()['coding_events'] == []


def test_in_app_evaluation_reports_do_not_block_experiments(tmp_path):
    from qualia.improve.experiment import improve_project

    path = init_project('study', tmp_path)
    (path / 'config/routing.yaml').write_text(json.dumps({**ROUTING, 'backend': 'fake', 'model': 'fake-v1'}))
    with Store(path / 'project.db') as db:
        db.save_code({'name': 'First'})
        db.save_code({'name': 'Second'})
        version = db.freeze_codebook()['id']
        import_benchmark(path, [{'segment_id': 'one', 'text': 'Synthetic possibility.', 'codes': [2],
                                 'transcript_id': 't'}], 'validation', version, [1, 2])
    subprocess.run(['git', '-C', str(path), 'add', '.'], check=True, capture_output=True)
    subprocess.run(['git', '-C', str(path), '-c', 'user.name=Qualia', '-c', 'user.email=qualia@localhost',
                    'commit', '-qm', 'Synthetic benchmark'], check=True, capture_output=True)
    client = TestClient(create_app(home=tmp_path, token='test'), base_url='http://localhost',
                        headers={'x-qualia-token': 'test'})
    assert client.post('/api/projects/study/evaluate', json={}).status_code == 200
    assert (path / 'reports').is_dir()
    [row] = improve_project(path, agent='fake', budget=1)
    assert row['decision'] == 'KEEP'
    tracked = subprocess.run(['git', '-C', str(path), 'ls-files', 'reports'], capture_output=True, text=True).stdout
    assert tracked == ''
