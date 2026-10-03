import csv
import hashlib
import io
import json

import pytest

from qualia.io import demo
from qualia.io.benchmarks import load_benchmark
from qualia.store.db import Store
from qualia.workspace import check_manifest, init_project


def source_bytes():
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=demo.COLUMNS, lineterminator='\r\n')
    writer.writeheader()
    for transcript in range(10):
        for utterance, speaker in enumerate(['therapist', 'client']):
            writer.writerow(dict(transcript_id=str(transcript), mi_quality='high',
                                 video_title=f'Video {transcript}', video_url=f'https://example.invalid/{transcript}',
                                 topic='Synthetic', utterance_id=str(utterance), interlocutor=speaker,
                                 timestamp=f'00:00:0{utterance}', utterance_text=f'{transcript} {speaker}, A😀B\r\nQuoted line',
                                 main_therapist_behaviour='question' if speaker == 'therapist' else 'n/a',
                                 client_talk_type='change' if speaker == 'client' else 'n/a'))
    return stream.getvalue().encode('utf-8')


def test_demo_idempotence_offsets_provenance_and_protected_separation(tmp_path, monkeypatch):
    raw = source_bytes()
    monkeypatch.setattr(demo, 'SOURCE_SHA256', hashlib.sha256(raw).hexdigest())
    project = init_project('demo', tmp_path)
    with Store(project/'project.db') as db:
        first = demo.import_demo(db, project, raw)
        assert first['new_sources'] == 8 and first['new_segments'] == first['new_events'] == 16
        before = {table: db.one(f'SELECT count(*) AS n FROM {table}')['n'] for table in
                  ['sources', 'segments', 'cases', 'codes', 'codebook_versions', 'coding_events']}
        second = demo.import_demo(db, project, raw)
        assert second['new_sources'] == second['new_segments'] == second['new_events'] == 0
        assert before == {table: db.one(f'SELECT count(*) AS n FROM {table}')['n'] for table in before}
        assert before['codes'] == 7 and before['cases'] == 8
        rows = db.retrieve()
        assert len(rows) == 16
        assert all(row['excerpt'].endswith('A😀B\r\nQuoted line') for row in rows)
        assert all(row['actor_type'] == 'human' and 'AnnoMI' in row['actor'] for row in rows)
        protected, _ = load_benchmark(project, 'protected', protected=True)
        visible_text = '\n'.join(row['text'] for row in db.rows('SELECT text FROM sources'))
        assert all(record['text'] not in visible_text for record in protected)
        assert check_manifest(project)
        marker = json.loads((project/'.annomi-demo.json').read_text())
        assert marker['source_sha256'] == demo.SOURCE_SHA256
        assert len(marker['segments']) == 16


def test_changed_source_or_unmarked_existing_project_refused(tmp_path, monkeypatch):
    raw = source_bytes()
    monkeypatch.setattr(demo, 'SOURCE_SHA256', hashlib.sha256(raw).hexdigest())
    project = init_project('demo', tmp_path)
    with Store(project/'project.db') as db:
        with pytest.raises(ValueError, match='checksum'):
            demo.import_demo(db, project, raw+b'changed')
        assert not db.rows('SELECT * FROM sources')
        db.save_code({'name': 'Existing methodology'})
        with pytest.raises(ValueError, match='empty project'):
            demo.import_demo(db, project, raw)


def test_demo_rejects_invalid_labels_before_writes(tmp_path, monkeypatch):
    raw = source_bytes().replace(b',question,n/a', b',invented,n/a')
    monkeypatch.setattr(demo, 'SOURCE_SHA256', hashlib.sha256(raw).hexdigest())
    project = init_project('demo', tmp_path)
    with Store(project/'project.db') as db:
        with pytest.raises(ValueError, match='row'):
            demo.import_demo(db, project, raw)
        assert not db.rows('SELECT * FROM codes')


def test_pinned_fetch_is_noop_for_verified_existing_bytes_and_rejects_mismatch(tmp_path, monkeypatch):
    from scripts import fetch_demo
    raw = b'synthetic pinned bytes'
    monkeypatch.setattr(fetch_demo, 'SOURCE_SHA256', hashlib.sha256(raw).hexdigest())
    target = tmp_path/'AnnoMI-simple.csv'
    target.write_bytes(raw)
    monkeypatch.setattr(fetch_demo.urllib.request, 'urlopen', lambda *a, **k: pytest.fail('unexpected network call'))
    assert fetch_demo.fetch_demo(target) == target
    target.write_bytes(b'different')
    with pytest.raises(ValueError, match='checksum'):
        fetch_demo.fetch_demo(target)
    assert target.read_bytes() == b'different'


def test_fetch_checks_hash_before_creating_destination(tmp_path, monkeypatch):
    from scripts import fetch_demo
    class Response(io.BytesIO):
        def geturl(self):
            return fetch_demo.SOURCE_URL
    target = tmp_path/'data/AnnoMI-simple.csv'
    monkeypatch.setattr(fetch_demo.urllib.request, 'urlopen', lambda *a, **k: Response(b'wrong bytes'))
    with pytest.raises(ValueError, match='checksum'):
        fetch_demo.fetch_demo(target)
    assert not target.exists()


def test_partial_demo_publication_reimport_refuses_duplication(tmp_path, monkeypatch):
    raw = source_bytes()
    monkeypatch.setattr(demo, 'SOURCE_SHA256', hashlib.sha256(raw).hexdigest())
    project = init_project('demo', tmp_path)
    def failed_publication(*args, **kwargs):
        raise OSError('synthetic disk failure')
    monkeypatch.setattr(demo, 'import_benchmark', failed_publication)
    with Store(project/'project.db') as db:
        with pytest.raises(OSError, match='synthetic disk failure'):
            demo.import_demo(db, project, raw)
        before = db.one('SELECT count(*) AS n FROM coding_events')['n']
        with pytest.raises(ValueError, match='empty project'):
            demo.import_demo(db, project, raw)
        assert db.one('SELECT count(*) AS n FROM coding_events')['n'] == before
