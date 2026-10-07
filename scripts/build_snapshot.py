"""Publish two verified public AnnoMI dev transcripts, never arbitrary workspace data."""

import argparse
import hashlib
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

from qualia.io import demo
from qualia.io.benchmarks import load_benchmark, split_transcripts
from qualia.store.db import canonical
from qualia.workspace import ROUTING, pipeline_hash


def _require(condition):
    if not condition:
        raise ValueError('snapshot evidence does not match the pinned public AnnoMI import')


def _path(path):
    path = Path(path).absolute()
    for item in (path, *path.parents):
        _require(not item.is_symlink() and not item.is_junction())
    _require(path.resolve() == path)
    _require(not path.is_file() or path.stat().st_nlink == 1)
    return path


def _pairs(items):
    result = {}
    for key, value in items:
        _require(key not in result)
        result[key] = value
    return result


def _json(raw):
    return json.loads(raw, object_pairs_hook=_pairs)


def _timestamp(value):
    _require(isinstance(value, str) and re.fullmatch(
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z', value))
    return value


def build_snapshot(project_path, csv_path=None):
    """Read only local, checksum-pinned input. Return the static Workspace envelope."""
    try:
        return _build(Path(project_path), csv_path)
    except (OSError, sqlite3.Error, ValueError, KeyError, TypeError, IndexError):
        # Never echo a private path, corrupt record, or credential in build output.
        raise ValueError('snapshot evidence does not match the pinned public AnnoMI import') from None


def _build(project, csv_path):
    project = _path(project)
    csv_path = _path(csv_path or Path(__file__).resolve().parents[1]/'demo/data/AnnoMI-simple.csv')
    _require(csv_path.stat().st_size <= 4_000_000)
    raw = csv_path.read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == demo.SOURCE_SHA256)
    records = demo._parse(raw)
    dev = split_transcripts(records)['dev']
    marker = _json(_path(project/'.annomi-demo.json').read_bytes())
    _require(all(marker[key] == value for key, value in {
        'format_version': 1, 'source_commit': demo.SOURCE_COMMIT,
        'source_sha256': demo.SOURCE_SHA256, 'source_url': demo.SOURCE_URL,
        'split_seed': 'qualia-annomi-v1',
    }.items()))
    _require(type(marker['format_version']) is int)
    for relative in ('benchmarks/index.json', 'benchmarks/dev/records.jsonl',
                     'benchmarks/dev/metadata.json'):
        _path(project/relative)
    # load_benchmark('dev') reads only public files, never the protected manifest.
    benchmark, metadata = load_benchmark(project, 'dev')
    _require(metadata == marker['splits']['dev'])
    groups = defaultdict(list)
    for row in dev:
        groups[row['transcript_id']].append(row)
    selected = sorted(groups, key=lambda identity: (
        sum(len(row['utterance_text']) for row in groups[identity]), int(identity)))[:2]
    _require(len(selected) == 2)
    # Hash the current pipeline without exporting any configuration values or paths.
    for path in (project/'config').rglob('*'):
        _path(path)
    pipeline = pipeline_hash(project)
    db_path = _path(project/'project.db')
    connection = sqlite3.connect(db_path.as_uri()+'?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute('BEGIN')
        def rows(query, args=()):
            return [dict(row) for row in connection.execute(query, args)]

        def one(query, args=()):
            found = rows(query, args)
            _require(len(found) == 1)
            return found[0]

        version = one('SELECT * FROM codebook_versions WHERE id=?',
                      (marker['codebook_version_id'],))
        _require(version['hash'] == marker['codebook_hash'] == hashlib.sha256(
            version['snapshot_json'].encode()).hexdigest())
        frozen = _json(version['snapshot_json'])
        expected_codes = [dict(id=i, parent_id=None, name=name, status='active',
                               definition=definition+' '+demo.ATTRIBUTION,
                               include='', exclude='', examples_pos='[]', examples_neg='[]')
                          for i, (name, definition) in enumerate(demo.DEFINITIONS.items(), 1)]
        _require(frozen == expected_codes)
        _timestamp(version['frozen_at'])
        code_ids = {row['name']: row['id'] for row in frozen}
        expected_benchmark = [dict(segment_id=row['segment_id'],
                                   transcript_id='annomi:'+row['transcript_id'],
                                   text=row['utterance_text'], codes=[code_ids[row['label']]])
                              for row in dev]
        _require(benchmark == expected_benchmark)
        _require(metadata['codebook_version_id'] == version['id'])
        workspace = dict(project={'slug': 'demo', 'name': 'AnnoMI demo'},
                         sources=[], segments=[], cases=[], attributes=[], source_cases=[],
                         codes=[{**row, 'examples_pos': [], 'examples_neg': []} for row in frozen],
                         codebook_versions=[version], coding_events=[], current_codings=[],
                         suggestions=[], memos=[], experiments=[], evaluation_runs=[], code_proposals=[],
                         routing=json.loads(canonical(ROUTING)), pipeline_version=pipeline)
        for identity in selected:
            utterances = sorted(groups[identity], key=lambda row: int(row['utterance_id']))
            mapping = marker['sources'][identity]
            source_id, case_id = mapping['id'], mapping['case_id']
            _require(type(source_id) is int and source_id > 0 and type(case_id) is int and case_id > 0)
            text = '\n'.join(row['utterance_text'] for row in utterances)
            digest = hashlib.sha256(text.encode()).hexdigest()
            source = dict(id=source_id, name='AnnoMI transcript '+identity, text=text,
                          content_hash=digest, version_of=None)
            actual = one('SELECT id,name,text,content_hash,version_of FROM sources WHERE id=?', (source_id,))
            _require(actual == source and mapping['content_hash'] == digest)
            provenance = one("SELECT value FROM attributes WHERE source_id=? AND key='source_sha256'", (source_id,))
            _require(provenance['value'] == demo.SOURCE_SHA256)
            case = dict(id=case_id, name=source['name'])
            _require(one('SELECT * FROM cases WHERE id=?', (case_id,)) == case)
            link = dict(source_id=source_id, case_id=case_id)
            _require(one('SELECT * FROM source_cases WHERE source_id=? AND case_id=?', (source_id, case_id)) == link)
            quality = one("SELECT * FROM attributes WHERE case_id=? AND key='mi_quality'", (case_id,))
            _require(quality == dict(id=quality['id'], case_id=case_id, source_id=None,
                                     key='mi_quality', value=utterances[0]['mi_quality']))
            _require(type(quality['id']) is int and quality['id'] > 0)
            workspace['sources'].append(source)
            workspace['cases'].append(case)
            workspace['source_cases'].append(link)
            workspace['attributes'].append(quality)
            position = 0
            for ordinal, row in enumerate(utterances):
                mapping = marker['segments'][row['segment_id']]
                segment_id, event_id = mapping['id'], mapping['event_id']
                _require(type(segment_id) is int and segment_id > 0 and type(event_id) is int and event_id > 0)
                end = position+len(row['utterance_text'])
                segment = dict(id=segment_id, source_id=source_id, start=position, end=end,
                               ordinal=ordinal, speaker=row['interlocutor'])
                _require(one('SELECT * FROM segments WHERE id=?', (segment_id,)) == segment)
                _require(mapping == dict(id=segment_id, event_id=event_id, source_id=source_id,
                                         code_id=code_ids[row['label']], start=position,
                                         end=end, speaker=row['interlocutor']))
                event = one('SELECT * FROM coding_events WHERE id=?', (event_id,))
                # Imported human labels have no model; later columns must be empty, not published.
                _require(event.pop('model_version', None) is None)
                _require(isinstance(event['pipeline_version'], str) and
                         re.fullmatch('[0-9a-f]{64}', event['pipeline_version']))
                expected_event = dict(id=event_id, segment_id=segment_id, code_id=code_ids[row['label']],
                    span_start=0, span_end=len(row['utterance_text']), actor_type='human',
                    actor=demo.ACTOR, action='assign', backend=None, model=None, cli_version=None,
                    score=None, rationale=f'Imported original expert label; transcript {identity}; '
                    f'utterance {row["utterance_id"]}; source {demo.SOURCE_COMMIT}.',
                    codebook_version_id=version['id'], pipeline_version=event['pipeline_version'],
                    prompt_hash='', experiment_id=None, suggestion_id=None, review_status='none',
                    review_trigger=None, reviewed_by=None, created_at=_timestamp(event['created_at']))
                _require(event == expected_event)
                workspace['segments'].append(segment)
                workspace['coding_events'].append(event)
                workspace['current_codings'].append(event.copy())
                position = end+1
        from qualia.core.analysis_models import AnalysisOptions
        from qualia.eval.analysis import analyze
        from qualia.io.analysis import export_analysis

        analysis = analyze(workspace, AnalysisOptions())
        return dict(format_version=1, project=workspace,
            analysis=analysis.model_dump(mode='json'),
            analysis_exports={kind: export_analysis(analysis, kind)
                              for kind in ('json', 'csv', 'python', 'r')}, attribution=dict(
            dataset='AnnoMI (simple): two complete dev transcripts',
            license='Public Domain License, as stated by the authors in the 2023 paper',
            sources=['https://www.mdpi.com/1999-5903/15/3/110',
                     'https://doi.org/10.1109/ICASSP43922.2022.9746035', demo.SOURCE_URL],
            note='Original expert annotations. Qualia selected the dev split; it is not an upstream '
                 'benchmark split. No AI predictions, evaluation results, or user edits are included. '
                 'No source video, audio, or images are redistributed.'))
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-path', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--csv-path', type=Path)
    args = parser.parse_args()
    snapshot = build_snapshot(args.project_path, args.csv_path)
    output = _path(args.output)
    project = _path(args.project_path)
    _require(output != project and project not in output.parents)
    _require(output.suffix == '.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(canonical(snapshot)+'\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
