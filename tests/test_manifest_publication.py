"""Protected publication pins earlier hashes and never exports private rationales."""

import hashlib
import json

import pytest

import qualia.evaluation as evaluation
import qualia.io.benchmarks as benchmarks
import qualia.workspace as workspace
from qualia.ai.backends.fake import FakeBackend
from qualia.store.db import Store


def setup_project(tmp_path):
    project = workspace.init_project('study', tmp_path)
    with Store(project / 'project.db') as db:
        code = db.save_code({'name': 'Synthetic'})
        version = db.freeze_codebook()
    record = {'segment_id': 'private-1', 'transcript_id': 'private-transcript',
              'text': 'SYNTHETIC_VAULT_SENTINEL', 'codes': [code]}
    return project, record, version


def test_benchmark_publication_does_not_bless_concurrent_methodology_change(tmp_path, monkeypatch):
    project, record, version = setup_project(tmp_path)
    original = workspace.manifest_snapshot(project)
    extend = benchmarks.extend_manifest

    def raced(path, expected, additions):
        (path / 'METHODOLOGY.md').write_text('Synthetic concurrent edit', encoding='utf-8')
        return extend(path, expected, additions)

    monkeypatch.setattr(benchmarks, 'extend_manifest', raced)
    with pytest.raises(ValueError, match='manifest changed'):
        benchmarks.import_benchmark(project, [record], 'protected', version['id'], record['codes'])
    assert json.loads((workspace.vault_dir(project) / 'manifest.sha256').read_text()) == original
    assert not workspace.check_manifest(project)
    assert (workspace.vault_dir(project) / 'benchmarks/protected/records.jsonl').is_file()
    assert not (project / 'benchmarks/index.json').exists()


def test_edit_after_final_hash_check_still_cannot_be_blessed(tmp_path, monkeypatch):
    project, _, _ = setup_project(tmp_path)
    expected = workspace.manifest_snapshot(project)
    artifact = workspace.protected_artifact_path(project, 'evaluations/new.json')
    artifact.parent.mkdir()
    content = b'{"synthetic":true}'
    artifact.write_bytes(content)
    replace = workspace.os.replace

    def raced(source, target):
        (project / 'METHODOLOGY.md').write_text('Synthetic late edit', encoding='utf-8')
        return replace(source, target)

    monkeypatch.setattr(workspace.os, 'replace', raced)
    with pytest.raises(ValueError, match='manifest mismatch'):
        workspace.extend_manifest(project, expected, {'vault/evaluations/new.json': hashlib.sha256(content).hexdigest()})
    stored = json.loads((workspace.vault_dir(project) / 'manifest.sha256').read_text())
    assert stored['METHODOLOGY.md'] == expected['METHODOLOGY.md']
    assert not workspace.check_manifest(project)


def test_known_artifact_bytes_cannot_be_replaced_before_extension(tmp_path):
    project, _, _ = setup_project(tmp_path)
    expected = workspace.manifest_snapshot(project)
    artifact = workspace.protected_artifact_path(project, 'new.json')
    artifact.write_bytes(b'unexpected bytes')
    with pytest.raises(ValueError, match='manifest changed'):
        workspace.extend_manifest(project, expected, {'vault/new.json': hashlib.sha256(b'expected bytes').hexdigest()})
    with pytest.raises(ValueError, match='new artifacts'):
        workspace.extend_manifest(project, expected, {'METHODOLOGY.md': '0' * 64})


def test_protected_rationale_stays_in_manifested_vault_not_database_or_cache(tmp_path):
    project, record, version = setup_project(tmp_path)
    benchmarks.import_benchmark(project, [record], 'protected', version['id'], record['codes'])

    class EchoFake(FakeBackend):
        def classify(self, segments, schema, context):
            result = super().classify(segments, schema, context)
            result['predictions'][0]['codes'][0]['rationale'] = segments[0]['text']
            return result

    with Store(project / 'project.db') as db:
        result = evaluation.evaluate_project(db, project, split='protected', protected=True,
                                             backend='fake', registry={'fake': EchoFake()})
        assert db.one('SELECT predictions_json FROM evaluation_runs')['predictions_json'] == '[]'
        assert not db.rows('SELECT * FROM result_cache')
        assert record['text'] not in '\n'.join(db.connection.iterdump())
    assert result['metrics']['identity']['predictions_location'] == 'protected vault'
    artifacts = list((workspace.vault_dir(project) / 'evaluations').glob('*.json'))
    assert len(artifacts) == 1 and record['text'] in artifacts[0].read_text()
    assert workspace.check_manifest(project)


def test_protected_evaluation_preserves_partial_artifact_on_publication_tamper(tmp_path, monkeypatch):
    project, record, version = setup_project(tmp_path)
    benchmarks.import_benchmark(project, [record], 'protected', version['id'], record['codes'])
    expected = workspace.manifest_snapshot(project)
    extend = evaluation.extend_manifest

    def raced(path, pinned, additions):
        (path / 'METHODOLOGY.md').write_text('Synthetic concurrent edit', encoding='utf-8')
        return extend(path, pinned, additions)

    monkeypatch.setattr(evaluation, 'extend_manifest', raced)
    with Store(project / 'project.db') as db:
        with pytest.raises(ValueError, match='manifest changed'):
            evaluation.evaluate_project(db, project, split='protected', protected=True, backend='fake')
        assert not db.rows('SELECT * FROM evaluation_runs')
        assert not db.rows('SELECT * FROM result_cache')
    assert list((workspace.vault_dir(project) / 'evaluations').glob('*.json'))
    assert json.loads((workspace.vault_dir(project) / 'manifest.sha256').read_text()) == expected


@pytest.mark.parametrize('relative', ['../outside.json', '/outside.json', 'evaluations/../outside.json', 'C:/outside.json'])
def test_artifact_path_rejects_escape(tmp_path, relative):
    project, _, _ = setup_project(tmp_path)
    with pytest.raises(ValueError, match='artifact path'):
        workspace.protected_artifact_path(project, relative)


def test_artifact_parent_symlink_is_refused(tmp_path):
    project, _, _ = setup_project(tmp_path)
    outside = tmp_path / 'outside'
    outside.mkdir()
    link = workspace.vault_dir(project) / 'evaluations'
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip('Windows account does not permit symlink creation')
    with pytest.raises(ValueError, match='artifact path'):
        workspace.protected_artifact_path(project, 'evaluations/new.json')
    assert not workspace.check_manifest(project)
    assert not list(outside.iterdir())
