import json
from pathlib import Path

import pytest

from qualia.io.benchmarks import import_benchmark, load_benchmark, split_transcripts
from qualia.workspace import check_manifest, init_project, vault_dir


def record(identity='s1', transcript='t1', **changes):
    return {'segment_id': identity, 'text': 'Synthetic benchmark', 'codes': [1],
            'transcript_id': transcript, **changes}


def test_import_repeats_identically_and_refuses_changed_split(tmp_path):
    project = init_project('bench', tmp_path)
    metadata = import_benchmark(project, [record()], 'validation', 1, [1, 2])
    assert metadata['counts'] == {'records': 1, 'transcripts': 1}
    assert import_benchmark(project, [record()], 'validation', 1, [1, 2]) == metadata
    assert load_benchmark(project) == ([record()], metadata)
    with pytest.raises(ValueError, match='already published'):
        import_benchmark(project, [record(text='Changed')], 'validation', 1, [1, 2])


@pytest.mark.parametrize('records', [[record(codes=[999])], [record(), record()],
                                    [record(codes=[True])], [record(coders=[[1], [999]])],
                                    [record(text='')], [record(extra='secret')]])
def test_invalid_records_publish_nothing(tmp_path, records):
    project = init_project('bench', tmp_path)
    with pytest.raises(ValueError, match='validation.jsonl: line'):
        import_benchmark(project, records, 'validation', 1, [1, 2])
    assert not (project/'benchmarks/validation/records.jsonl').exists()


def test_protected_requires_explicit_access_and_verified_manifest(tmp_path):
    project = init_project('bench', tmp_path)
    import_benchmark(project, [record()], 'protected', 1, [1])
    assert check_manifest(project)
    with pytest.raises(ValueError, match='explicit protected'):
        load_benchmark(project, 'protected')
    assert load_benchmark(project, 'protected', protected=True)[0] == [record()]
    file = vault_dir(project)/'benchmarks/protected/records.jsonl'
    file.write_text('tampered')
    with pytest.raises(ValueError, match='manifest'):
        load_benchmark(project, 'protected', protected=True)
    with pytest.raises(ValueError, match='manifest'):
        import_benchmark(project, [record()], 'protected', 1, [1])


def test_ordinary_load_and_cross_split_checks_never_read_vault(tmp_path, monkeypatch):
    project = init_project('bench', tmp_path)
    import_benchmark(project, [record('hidden', 'protected-transcript')], 'protected', 1, [1])
    import_benchmark(project, [record('visible', 'validation-transcript')], 'validation', 1, [1])
    original = Path.read_bytes
    def guarded(path):
        assert 'vault' not in path.parts, 'ordinary operation accessed protected vault'
        return original(path)
    monkeypatch.setattr(Path, 'read_bytes', guarded)
    assert load_benchmark(project)[0][0]['segment_id'] == 'visible'
    with pytest.raises(ValueError, match='transcript overlap'):
        import_benchmark(project, [record('dev', 'protected-transcript')], 'dev', 1, [1])
    index = (project/'benchmarks/index.json').read_text()
    assert 'protected-transcript' not in index and 'Synthetic benchmark' not in index


def test_public_payload_or_metadata_tampering_fails(tmp_path):
    project = init_project('bench', tmp_path)
    import_benchmark(project, [record()], 'validation', 1, [1])
    metadata = project/'benchmarks/validation/metadata.json'
    value = json.loads(metadata.read_text())
    value['codebook_version_id'] = 2
    metadata.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='metadata'):
        load_benchmark(project)


def test_transcript_splits_are_deterministic_disjoint_and_complete():
    rows = [record(f'{i}:{j}', str(i), mi_quality='high' if i < 110 else 'low')
            for i in range(133) for j in range(2)]
    result = split_transcripts(rows)
    assert result == split_transcripts(list(reversed(rows)))
    ids = {split: {row['transcript_id'] for row in values} for split, values in result.items()}
    assert {split: len(values) for split, values in ids.items()} == {'dev': 80, 'validation': 26, 'protected': 27}
    assert not ids['dev'] & ids['validation'] and not ids['dev'] & ids['protected']
    assert not ids['validation'] & ids['protected']
    assert sum(map(len, result.values())) == len(rows)


def test_segment_identity_overlap_and_missing_index_fail_closed(tmp_path):
    project = init_project('bench', tmp_path)
    import_benchmark(project, [record()], 'validation', 1, [1])
    with pytest.raises(ValueError, match='segment identity overlap'):
        import_benchmark(project, [record(transcript='different')], 'dev', 1, [1])
    (project/'benchmarks/index.json').unlink()
    with pytest.raises(ValueError, match='index is missing'):
        load_benchmark(project)


def test_benchmark_file_symlink_cannot_read_protected_payload(tmp_path):
    project = init_project('bench', tmp_path)
    import_benchmark(project, [record()], 'validation', 1, [1])
    file = project/'benchmarks/validation/records.jsonl'
    file.unlink()
    hidden = vault_dir(project)/'secret.jsonl'
    hidden.write_text('protected text must never be read')
    try:
        file.symlink_to(hidden)
    except OSError:
        pytest.skip('Windows test account does not permit symlink creation')
    with pytest.raises(ValueError, match='path escapes'):
        load_benchmark(project)


@pytest.mark.parametrize('raw', [b'{"segment_id":"s1","segment_id":"s2"}\n', b'not JSON\n', b'\xff'])
def test_malformed_bytes_name_line_and_publish_nothing(tmp_path, raw):
    project = init_project('bench', tmp_path)
    with pytest.raises(ValueError, match='validation.jsonl: line 1'):
        import_benchmark(project, raw, 'validation', 1, [1])
    assert not (project/'benchmarks/validation/records.jsonl').exists()
