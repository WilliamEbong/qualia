"""Pinned AnnoMI demo ingestion; protected utterances never enter the project database."""

import csv
import hashlib
import io
import json
from collections import defaultdict

from qualia.io.benchmarks import import_benchmark, split_transcripts
from qualia.store.db import canonical
from qualia.workspace import check_manifest, pipeline_hash

SOURCE_COMMIT = '42936645ec3857a9c84ab296a36a3c34b779ef49'
SOURCE_SHA256 = 'b178db3b0b9858a0fa4ed670dabeccd63e975ba67e141d7ae16f2e8214f78e61'
SOURCE_URL = f'https://raw.githubusercontent.com/uccollab/AnnoMI/{SOURCE_COMMIT}/AnnoMI-simple.csv'
COLUMNS = ['transcript_id', 'mi_quality', 'video_title', 'video_url', 'topic', 'utterance_id',
           'interlocutor', 'timestamp', 'utterance_text', 'main_therapist_behaviour', 'client_talk_type']
DEFINITIONS = {
    'reflection': 'Therapist expresses understanding of what the client has said.',
    'question': "Therapist asks an inquiry to obtain information or explore the client's perspective.",
    'therapist_input': 'Therapist offers information, advice, or other input.',
    'other': 'Therapist utterance outside the listed main behaviors.',
    'change': 'Client language favoring positive behavior change.',
    'sustain': 'Client language favoring continuation of the status quo.',
    'neutral': 'Client language expressing neither change nor sustain.',
}
ATTRIBUTION = ('Demo paraphrase of AnnoMI high-level labels; Wu et al. (2022), '
               'doi:10.1109/ICASSP43922.2022.9746035; Wu et al. (2023), doi:10.3390/fi15030110. '
               'The source does not supply a complete inclusion/exclusion/examples codebook.')
ACTOR = 'AnnoMI expert annotation (simple dataset; individual coder unspecified)'


def _parse(raw):
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise ValueError('AnnoMI-simple.csv: invalid UTF-8') from None
    reader = csv.DictReader(io.StringIO(text, newline=''), strict=True)
    records, seen = [], set()
    try:
        if reader.fieldnames != COLUMNS:
            raise ValueError('AnnoMI-simple.csv: row 1: unexpected columns')
        for row in reader:
            try:
                if set(row) != set(COLUMNS) or any(not isinstance(value, str) for value in row.values()):
                    raise ValueError('columns')
                if any('\x00' in value for value in row.values()) or not row['utterance_text'].strip():
                    raise ValueError('invalid text')
                if not row['transcript_id'].isdecimal() or not row['utterance_id'].isdecimal():
                    raise ValueError('identity')
                row['transcript_id'] = str(int(row['transcript_id']))
                row['utterance_id'] = str(int(row['utterance_id']))
                identity = (row['transcript_id'], row['utterance_id'])
                if identity in seen or row['mi_quality'] not in ('high', 'low'):
                    raise ValueError('duplicate or quality')
                speaker = row['interlocutor']
                label = row['main_therapist_behaviour'] if speaker == 'therapist' else row['client_talk_type']
                allowed = ('reflection', 'question', 'therapist_input', 'other') if speaker == 'therapist' else ('change', 'sustain', 'neutral')
                irrelevant = row['client_talk_type'] if speaker == 'therapist' else row['main_therapist_behaviour']
                if speaker not in ('therapist', 'client') or label not in allowed or irrelevant != 'n/a':
                    raise ValueError('label')
                seen.add(identity)
                records.append({**row, 'label': label,
                                'segment_id': f'annomi:{SOURCE_COMMIT}:{identity[0]}:{identity[1]}'})
            except (ValueError, TypeError):
                raise ValueError(f'AnnoMI-simple.csv: row {reader.line_num}: invalid identity, text or annotation') from None
    except csv.Error:
        raise ValueError(f'AnnoMI-simple.csv: row {reader.line_num}: malformed CSV') from None
    if not records:
        raise ValueError('AnnoMI-simple.csv: row 1: empty dataset')
    return records


def _repeat(db, project, marker):
    try:
        if marker['source_sha256'] != SOURCE_SHA256 or marker['source_commit'] != SOURCE_COMMIT:
            raise ValueError('source identity')
        frozen = db.one('SELECT hash FROM codebook_versions WHERE id=?', (marker['codebook_version_id'],))
        if not frozen or frozen['hash'] != marker['codebook_hash']:
            raise ValueError('codebook identity')
        sources = {row['id']: row for row in db.rows('SELECT id,content_hash FROM sources')}
        segments = {row['id']: row for row in db.rows('SELECT * FROM segments')}
        events = {row['id']: row for row in db.rows('SELECT * FROM coding_events WHERE actor=?', (ACTOR,))}
        for source in marker['sources'].values():
            if sources.get(source['id'], {}).get('content_hash') != source['content_hash']:
                raise ValueError('source mapping')
        for segment in marker['segments'].values():
            row = segments.get(segment['id'])
            event = events.get(segment['event_id'])
            if (not row or any(row[key] != segment[key] for key in ('source_id', 'start', 'end', 'speaker'))
                    or not event or event['segment_id'] != row['id'] or event['code_id'] != segment['code_id']):
                raise ValueError('segment mapping')
        index = json.loads((project/'benchmarks/index.json').read_bytes())
        if {key: value['metadata'] for key, value in index['splits'].items()} != marker['splits']:
            raise ValueError('benchmark index')
        if not check_manifest(project):
            raise ValueError('manifest mismatch')
    except (OSError, ValueError, KeyError, TypeError):
        raise ValueError('demo completion marker or immutable dataset evidence does not match') from None
    return {'new_sources': 0, 'new_segments': 0, 'new_events': 0,
            'codebook_version_id': marker['codebook_version_id'], 'splits': marker['splits']}


def import_demo(db, project, csv_bytes):
    if not isinstance(csv_bytes, bytes) or hashlib.sha256(csv_bytes).hexdigest() != SOURCE_SHA256:
        raise ValueError('AnnoMI source checksum mismatch; original bytes required')
    marker_path = project/'.annomi-demo.json'
    if marker_path.is_symlink():
        raise ValueError('demo completion marker must not be a symlink')
    if marker_path.exists():
        try:
            marker = json.loads(marker_path.read_bytes())
        except (OSError, ValueError):
            raise ValueError('invalid demo completion marker') from None
        return _repeat(db, project, marker)
    if any(db.one(f'SELECT count(*) AS n FROM {table}')['n'] for table in
           ('sources', 'segments', 'cases', 'codes', 'codebook_versions', 'coding_events')):
        raise ValueError('demo requires an empty project or its verified completion marker')
    if not check_manifest(project):
        raise ValueError('protected manifest mismatch; demo import refused')
    records = _parse(csv_bytes)
    splits = split_transcripts(records)
    if any(not records for records in splits.values()):
        raise ValueError('demo needs nonempty dev, validation and protected transcript splits')
    visible = defaultdict(list)
    for row in splits['dev'] + splits['validation']:
        visible[row['transcript_id']].append(row)
    marker = {'format_version': 1, 'source_commit': SOURCE_COMMIT, 'source_sha256': SOURCE_SHA256,
              'source_url': SOURCE_URL, 'split_seed': 'qualia-annomi-v1', 'sources': {}, 'segments': {}}
    pipeline = pipeline_hash(project)
    with db.transaction():
        code_ids = {name: db.save_code({'name': name, 'definition': definition+' '+ATTRIBUTION})
                    for name, definition in DEFINITIONS.items()}
        frozen = db.freeze_codebook()
        marker.update(codebook_version_id=frozen['id'], codebook_hash=frozen['hash'])
        for identity in sorted(visible, key=int):
            utterances = sorted(visible[identity], key=lambda row: int(row['utterance_id']))
            first = utterances[0]
            if any(any(row[key] != first[key] for key in ('mi_quality', 'video_url', 'video_title', 'topic')) for row in utterances):
                raise ValueError(f'AnnoMI transcript {identity}: inconsistent metadata')
            text = '\n'.join(row['utterance_text'] for row in utterances)
            digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
            if db.one('SELECT id FROM sources WHERE content_hash=?', (digest,)):
                raise ValueError(f'AnnoMI transcript {identity}: identical source content needs explicit identity resolution')
            source = db.add('sources', {'name': f'AnnoMI transcript {identity}', 'text': text, 'content_hash': digest})
            case = db.save_case({'name': f'AnnoMI transcript {identity}', 'source_ids': [source],
                                'attributes': {key: first[key] for key in ('mi_quality', 'video_title', 'video_url', 'topic')}})
            provenance = {'dataset': 'AnnoMI-simple', 'source_commit': SOURCE_COMMIT,
                          'source_sha256': SOURCE_SHA256, 'source_url': SOURCE_URL, 'transcript_id': identity}
            for key, value in provenance.items():
                db.save_attribute({'source_id': source, 'key': key, 'value': value})
            marker['sources'][identity] = {'id': source, 'case_id': case, 'content_hash': digest}
            position, utterance_map = 0, []
            for ordinal, row in enumerate(utterances):
                end = position + len(row['utterance_text'])
                segment = db.add('segments', {'source_id': source, 'start': position, 'end': end,
                                              'ordinal': ordinal, 'speaker': row['interlocutor']})
                event = db.assign({'segment_id': segment, 'code_id': code_ids[row['label']],
                                   'span_start': 0, 'span_end': len(row['utterance_text']),
                                   'actor': ACTOR, 'action': 'assign', 'codebook_version_id': frozen['id'],
                                   'pipeline_version': pipeline,
                                   'rationale': f'Imported original expert label; transcript {identity}; utterance {row["utterance_id"]}; source {SOURCE_COMMIT}.'})
                marker['segments'][row['segment_id']] = {'id': segment, 'event_id': event,
                    'source_id': source, 'code_id': code_ids[row['label']], 'start': position,
                    'end': end, 'speaker': row['interlocutor']}
                utterance_map.append({'segment_id': segment, 'utterance_id': row['utterance_id'],
                                      'timestamp': row['timestamp']})
                position = end + 1
            db.save_attribute({'source_id': source, 'key': 'utterance_map', 'value': canonical(utterance_map)})
    marker['splits'] = {}
    for split, rows in splits.items():
        benchmark = [{'segment_id': row['segment_id'], 'transcript_id': f'annomi:{row["transcript_id"]}',
                      'text': row['utterance_text'], 'codes': [code_ids[row['label']]]} for row in rows]
        marker['splits'][split] = import_benchmark(project, benchmark, split, frozen['id'], list(code_ids.values()))
    # A failed publication leaves existing evidence intact and refuses an unmarked re-import.
    with marker_path.open('x', encoding='utf-8') as stream:
        stream.write(canonical(marker))
    return {'new_sources': len(marker['sources']), 'new_segments': len(marker['segments']),
            'new_events': len(marker['segments']), 'codebook_version_id': frozen['id'], 'splits': marker['splits']}
