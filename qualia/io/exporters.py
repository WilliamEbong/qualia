"""Auditable exports with explicit text inclusion and no protected-vault traversal."""

import csv
import hashlib
import io
import json

from qualia.store.db import canonical
from qualia.workspace import pipeline_hash

TEXT_FIELDS = {'text', 'source_text', 'segment_text', 'excerpt', 'excerpts', 'rationale',
               'note', 'notes', 'title', 'hypothesis', 'reason', 'definition', 'include',
               'exclude', 'examples_pos', 'examples_neg', 'prompt', 'content', 'response'}


def _without_text(value):
    if isinstance(value, list):
        return [_without_text(item) for item in value]
    if not isinstance(value, dict):
        return value
    cleaned = {}
    for key, item in value.items():
        if key in TEXT_FIELDS or key in ('predictions', 'predictions_json'):
            continue
        if key.endswith('_json') and isinstance(item, str):
            cleaned[key] = canonical(_without_text(json.loads(item)))
        else:
            cleaned[key] = _without_text(item)
    if 'snapshot_json' in value:
        # Hash remains the original frozen version's identity, not a hash of this redacted copy.
        cleaned['snapshot_redacted'] = True
    return cleaned


def _csv_cell(value):
    if value is None:
        return ''
    if isinstance(value, (dict, list)):
        value = canonical(value)
    if isinstance(value, str) and (value.startswith(('\t', '\r', '\n'))
                                  or value.lstrip().startswith(('=', '+', '-', '@'))):
        return "'" + value
    return value


def export_data(db, project, format='json', no_text=True, bundle=None) -> str:
    """Export evidence; free-text fields require no_text=False, predictions stay excluded.

    No-text copies of frozen versions retain their original hashes and mark their snapshots
    redacted. An explicit text-inclusive bundle is required to reproduce textual code definitions.
    """
    if format not in ('json', 'csv'):
        raise ValueError('export format must be json or csv')
    if bundle not in (None, 'reproducibility'):
        raise ValueError('unsupported export bundle')
    tables = ['sources', 'segments', 'cases', 'source_cases', 'attributes', 'codes',
              'codebook_versions', 'coding_events', 'current_codings', 'memos', 'feedback_events']
    if bundle:
        tables += ['experiments', 'evaluation_runs', 'usage_ledger', 'egress_log']
    data = {'format_version': 1, 'text_excluded': no_text, 'bundle': bundle}
    with db.transaction():
        for table in tables:
            rows = db.rows(f'SELECT * FROM {table}')
            if table == 'evaluation_runs':
                rows = [{key: value for key, value in row.items() if key != 'predictions_json'}
                        for row in rows]
            data[table] = _without_text(rows) if no_text else rows
        if bundle:
            data['cli_versions'] = sorted({row['cli_version'] for row in data['coding_events']
                                           if row.get('cli_version')})
    if bundle:
        data['pipeline_version'] = pipeline_hash(project)
        data['config_hashes'] = {
            path.relative_to(project).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((project / 'config').rglob('*')) if path.is_file()
        }
    if format == 'json':
        return canonical(data)
    rows = []
    metadata = {}
    for table, records in data.items():
        if isinstance(records, list):
            rows.extend({'record_type': table, **(record if isinstance(record, dict) else {'value': record})}
                        for record in records)
        else:
            metadata[table] = records
    rows.insert(0, {'record_type': 'metadata', **metadata})
    columns = ['record_type', *sorted({key for row in rows for key in row} - {'record_type'})]
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(columns)
    for row in rows:
        writer.writerow([_csv_cell(row.get(column)) for column in columns])
    return output.getvalue()
