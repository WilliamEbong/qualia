"""Synthetic CSV fixtures only; no private data or real AnnoMI excerpts."""

import csv
import hashlib
import io
import json
import sqlite3

import pytest

from qualia.io import demo
from qualia.io.benchmarks import split_transcripts
from qualia.store.db import Store, canonical
from qualia.workspace import init_project
from scripts.build_snapshot import build_snapshot


@pytest.fixture
def fixture_demo(tmp_path, monkeypatch):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=demo.COLUMNS, lineterminator='\r\n')
    writer.writeheader()
    for transcript in range(10):
        for utterance, speaker in enumerate(['therapist', 'client']):
            writer.writerow(dict(transcript_id=str(transcript), mi_quality='high',
                video_title=f'Synthetic {transcript}', video_url='https://example.invalid/demo',
                topic='Synthetic', utterance_id=str(utterance), interlocutor=speaker,
                timestamp=f'00:00:0{utterance}', utterance_text=f'{transcript} {speaker} A😀B\r\nline',
                main_therapist_behaviour='question' if speaker == 'therapist' else 'n/a',
                client_talk_type='change' if speaker == 'client' else 'n/a'))
    raw = stream.getvalue().encode()
    monkeypatch.setattr(demo, 'SOURCE_SHA256', hashlib.sha256(raw).hexdigest())
    csv_path = tmp_path/'AnnoMI-simple.csv'
    csv_path.write_bytes(raw)
    project = init_project('demo', tmp_path)
    with Store(project/'project.db') as db:
        demo.import_demo(db, project, raw)
    return project, csv_path


def test_snapshot_is_deterministic_complete_dev_only_and_never_reads_vault(fixture_demo, monkeypatch):
    project, csv_path = fixture_demo
    from pathlib import Path
    original = Path.open
    def guarded(path, *args, **kwargs):
        assert 'vault' not in path.parts
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', guarded)
    snapshot = build_snapshot(project, csv_path)
    assert canonical(snapshot) == canonical(build_snapshot(project, csv_path))
    workspace = snapshot['project']
    assert set(snapshot) == {'format_version', 'project', 'attribution', 'analysis', 'analysis_exports'}
    assert snapshot['analysis']['segment_count'] == 4
    assert snapshot['analysis']['selected_segment_ids'] == sorted(row['id'] for row in workspace['segments'])
    assert set(snapshot['analysis_exports']) == {'json', 'csv', 'python', 'r'}
    assert len(workspace['sources']) == 2
    assert len(workspace['segments']) == len(workspace['coding_events']) == 4
    dev = {row['transcript_id'] for row in split_transcripts(demo._parse(csv_path.read_bytes()))['dev']}
    assert all(source['name'].split()[-1] in dev for source in workspace['sources'])
    assert all(len([s for s in workspace['segments'] if s['source_id'] == source['id']]) == 2
               for source in workspace['sources'])
    assert len(workspace['codes']) == 7
    assert not workspace['routing']['allow_external'] and not workspace['routing']['jev_enabled']
    assert all(not workspace[key] for key in ('memos', 'suggestions', 'experiments', 'evaluation_runs'))
    assert workspace['current_codings'] == workspace['coding_events']
    assert all(attr['key'] == 'mi_quality' for attr in workspace['attributes'])
    assert str(project) not in canonical(snapshot)


def test_snapshot_ignores_private_additions_and_uses_frozen_codes(fixture_demo):
    project, csv_path = fixture_demo
    before = build_snapshot(project, csv_path)
    with Store(project/'project.db') as db:
        db.connection.execute("UPDATE codes SET definition='SECRET_USER_DRAFT'")
        db.add('memos', {'title': 'SECRET_USER_MEMO', 'text': r'C:\private\research'})
        db.save_attribute({'source_id': 1, 'key': 'private_path', 'value': 'SECRET_TOKEN'})
        db.add('sources', {'name': 'Private', 'text': 'SECRET_PRIVATE', 'content_hash': 'private'})
    assert before == build_snapshot(project, csv_path)
    assert 'SECRET' not in canonical(before)


@pytest.mark.parametrize('field,value', [
    ('source_commit', 'private'), ('source_sha256', '0'*64),
    ('source_url', 'file:///C:/secret'), ('codebook_hash', '0'*64),
    ('split_seed', 'different'), ('format_version', 2),
])
def test_snapshot_rejects_marker_tampering(fixture_demo, field, value):
    project, csv_path = fixture_demo
    path = project/'.annomi-demo.json'
    marker = json.loads(path.read_bytes())
    marker[field] = value
    path.write_text(canonical(marker))
    with pytest.raises(ValueError, match='pinned public'):
        build_snapshot(project, csv_path)


@pytest.mark.parametrize('target', ['source', 'event', 'frozen', 'quality', 'provenance'])
def test_snapshot_rejects_private_content_even_if_local_hashes_are_updated(fixture_demo, target):
    project, csv_path = fixture_demo
    baseline = build_snapshot(project, csv_path)['project']
    marker_path = project/'.annomi-demo.json'
    marker = json.loads(marker_path.read_bytes())
    with sqlite3.connect(project/'project.db') as connection:
        # Deliberately corrupt this isolated fixture, bypassing immutable table triggers.
        for (name,) in connection.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
            connection.execute('DROP TRIGGER "'+name+'"')
        if target == 'source':
            identity = baseline['sources'][0]['name'].split()[-1]
            digest = hashlib.sha256(b'SECRET').hexdigest()
            connection.execute('UPDATE sources SET text=?,content_hash=? WHERE id=?',
                               ('SECRET', digest, baseline['sources'][0]['id']))
            marker['sources'][identity]['content_hash'] = digest
        elif target == 'event':
            connection.execute('UPDATE coding_events SET actor=? WHERE id=?',
                               ('SECRET', baseline['coding_events'][0]['id']))
        elif target == 'frozen':
            frozen = json.loads(baseline['codebook_versions'][0]['snapshot_json'])
            frozen[0]['definition'] = 'SECRET'
            raw = canonical(frozen)
            marker['codebook_hash'] = hashlib.sha256(raw.encode()).hexdigest()
            connection.execute('UPDATE codebook_versions SET snapshot_json=?,hash=?',
                               (raw, marker['codebook_hash']))
        elif target == 'quality':
            connection.execute('UPDATE attributes SET value=? WHERE id=?',
                               ('SECRET', baseline['attributes'][0]['id']))
        else:
            connection.execute("UPDATE attributes SET value='SECRET' WHERE key='source_sha256'")
    marker_path.write_text(canonical(marker))
    with pytest.raises(ValueError, match='pinned public') as error:
        build_snapshot(project, csv_path)
    assert 'SECRET' not in str(error.value) and str(project) not in str(error.value)


def test_snapshot_rejects_unpinned_csv_and_modified_public_benchmark(fixture_demo):
    project, csv_path = fixture_demo
    raw = csv_path.read_bytes()
    csv_path.write_bytes(raw+b'private')
    with pytest.raises(ValueError):
        build_snapshot(project, csv_path)
    csv_path.write_bytes(raw)
    records = project/'benchmarks/dev/records.jsonl'
    records.write_bytes(records.read_bytes()+b'private')
    with pytest.raises(ValueError):
        build_snapshot(project, csv_path)


def test_snapshot_rejects_linked_marker(fixture_demo, monkeypatch):
    project, csv_path = fixture_demo
    from pathlib import Path
    original = Path.is_symlink
    monkeypatch.setattr(Path, 'is_symlink', lambda path: path.name == '.annomi-demo.json' or original(path))
    with pytest.raises(ValueError):
        build_snapshot(project, csv_path)


def test_cli_writes_exact_workspace_envelope_without_modifying_project(fixture_demo, monkeypatch, tmp_path):
    import sys

    from qualia.server.api_models import Workspace
    from scripts.build_snapshot import main
    project, csv_path = fixture_demo
    output = tmp_path/'public/snapshot.json'
    db_before = (project/'project.db').read_bytes()
    monkeypatch.setattr(sys, 'argv', ['build_snapshot', '--project-path', str(project),
                                   '--output', str(output), '--csv-path', str(csv_path)])
    main()
    raw = output.read_bytes()
    assert json.loads(raw) == build_snapshot(project, csv_path)
    Workspace.model_validate(json.loads(raw)['project'])
    main()
    assert raw == output.read_bytes()
    assert db_before == (project/'project.db').read_bytes()


def test_cli_rejects_output_inside_research_project(fixture_demo, monkeypatch):
    import sys

    from scripts.build_snapshot import main
    project, csv_path = fixture_demo
    output = project/'.annomi-demo.json'
    before = output.read_bytes()
    monkeypatch.setattr(sys, 'argv', ['build_snapshot', '--project-path', str(project),
                                   '--output', str(output), '--csv-path', str(csv_path)])
    with pytest.raises(ValueError):
        main()
    assert output.read_bytes() == before
