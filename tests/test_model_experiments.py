import json
import subprocess

import pytest
from fastapi.testclient import TestClient

from qualia.ai.backends.fake import FakeBackend
from qualia.eval.metrics import run_agreement
from qualia.evaluation import repeatability
from qualia.improve.experiment import improve_project
from qualia.io.benchmarks import import_benchmark
from qualia.server.app import create_app
from qualia.store.db import Store
from qualia.workspace import ROUTING, init_project, read_config


def prediction(segment, *codes):
    return {'segment_id': segment, 'codes': [{'code_id': code} for code in codes]}


def test_run_agreement_counts_identical_sets_and_per_code_kappa():
    first = [prediction('a', 1), prediction('b', 1, 2), prediction('c'), prediction('d', 2)]
    second = [prediction('a', 1), prediction('b', 1), prediction('c'), prediction('d', 2)]
    result = run_agreement(first, second, [1, 2, 3])
    assert result['segments'] == 4 and result['identical_sets'] == 0.75
    one, two, three = result['per_code']
    assert one['agreement'] == 1.0 and one['kappa'] == 1.0
    assert two['agreement'] == 0.75 and two['first_count'] == 2 and two['second_count'] == 1
    assert three['agreement'] == 1.0 and three['kappa'] is None


@pytest.fixture
def project(tmp_path):
    path = init_project('study', tmp_path)
    (path / 'config/routing.yaml').write_text(json.dumps({**ROUTING, 'backend': 'rules', 'model': 'rules-v1'}),
                                              encoding='utf-8')
    with Store(path / 'project.db') as db:
        for index, text in enumerate(('A clear possibility.', 'Nothing relevant.', 'Another possibility.')):
            source = db.add('sources', {'name': f's{index}', 'text': text, 'content_hash': f'h{index}'})
            db.add('segments', {'source_id': source, 'start': 0, 'end': len(text), 'ordinal': 0})
        db.save_code({'name': 'Possibility', 'include': 'possibility'})
        db.save_code({'name': 'Other'})
        version = db.freeze_codebook()['id']
        import_benchmark(path, [{'segment_id': 'one', 'text': 'Synthetic possibility.', 'codes': [2],
                                 'transcript_id': 't'}], 'validation', version, [1, 2])
    subprocess.run(['git', '-C', str(path), 'add', '.'], check=True, capture_output=True)
    subprocess.run(['git', '-C', str(path), '-c', 'user.name=Qualia', '-c', 'user.email=qualia@localhost',
                    'commit', '-qm', 'Synthetic benchmark'], check=True, capture_output=True)
    return path


def test_repeatability_runs_twice_without_cache_and_reports_disagreement(project):
    class Flaky(FakeBackend):
        name = 'flaky'
        calls = 0

        def classify(self, segments, schema, context):
            Flaky.calls += 1
            mode = 'all' if Flaky.calls == 1 else 'first'
            return super().classify(segments, schema, {**context, 'fake_mode': mode})

    with Store(project / 'project.db') as db:
        steady = repeatability(db, project, backend='fake', segments=3)
        assert steady['identical_sets'] == 1.0 and steady['segments'] == 3 and steady['calls'] == 2
        varying = repeatability(db, project, backend='flaky', model='flaky-v1', segments=3,
                                registry={'flaky': Flaky()})
        assert varying['identical_sets'] == 0.0
        assert db.rows('SELECT * FROM coding_events') == [] and db.rows('SELECT * FROM result_cache') == []
        with pytest.raises(ValueError, match='1 to 200'):
            repeatability(db, project, segments=0)


def test_model_experiment_is_measured_and_validated_before_any_call(project):
    with pytest.raises(ValueError, match='valid model ID'):
        improve_project(project, agent='model', candidate_backend='claude', candidate_model='bad model!')
    with pytest.raises(ValueError, match='candidate model'):
        improve_project(project, agent='model', backend='fake', candidate_backend='fake',
                        candidate_model='fake-v1')
    with Store(project / 'project.db') as db:
        assert db.rows('SELECT * FROM evaluation_runs') == []
    [row] = improve_project(project, agent='model', candidate_backend='fake', candidate_model='fake-v1')
    assert row['agent'] == 'model' and 'fake / fake-v1 instead of rules / rules-v1' in row['hypothesis']
    config = read_config(project)
    if row['decision'] == 'KEEP':
        assert (config['backend'], config['model']) == ('fake', 'fake-v1')
    else:
        assert (config['backend'], config['model']) == ('rules', 'rules-v1')


def test_api_routes_for_repeatability_and_model_experiment(project, tmp_path):
    client = TestClient(create_app(home=tmp_path, token='t'), base_url='http://localhost',
                        headers={'x-qualia-token': 't'})
    result = client.post('/api/projects/study/repeatability', json={'backend': 'fake', 'segments': 2})
    assert result.status_code == 200 and result.json()['identical_sets'] == 1.0
    assert client.post('/api/projects/study/repeatability', json={'segments': 500}).status_code == 422
    assert client.post('/api/projects/study/experiments/model',
                       json={'backend': 'fake', 'model': 'x y'}).status_code == 422
    experiment = client.post('/api/projects/study/experiments/model',
                             json={'backend': 'fake', 'model': 'fake-v1'})
    assert experiment.status_code == 200 and experiment.json()['agent'] == 'model'
