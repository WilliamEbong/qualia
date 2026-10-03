import csv
import io
import json

import pytest
from test_coding import seed_coding

from qualia.io.exporters import export_data
from qualia.store.db import Store
from qualia.workspace import init_project, vault_dir


@pytest.mark.parametrize('format', ['json', 'csv'])
def test_no_text_export_preserves_provenance_without_free_text_or_vault(tmp_path, format):
    project = init_project('study', tmp_path)
    secret = 'SYNTHETIC_PRIVATE_TRANSCRIPT'
    (vault_dir(project) / 'protected.jsonl').write_text('SYNTHETIC_VAULT')
    (project / 'config/prompts/classify.txt').write_text('SYNTHETIC_RAW_PROMPT')
    with Store(project / 'project.db') as db:
        _, _, event = seed_coding(db)
        db.assign({**event, 'rationale': secret})
        db.save_memo({'title': secret, 'text': secret})
        db.save_case({'name': 'Case', 'attributes': {'text': secret}, 'source_ids': []})
        db.save_code({'examples_pos': [secret], 'definition': secret}, event['code_id'])
        db.freeze_codebook()
        db.add('evaluation_runs', {'split': 'validation', 'backend': 'fake', 'model': 'fake',
                                   'pipeline_version': 'synthetic', 'metrics_json': '{}',
                                   'predictions_json': json.dumps([{'text': secret}])})
        output = export_data(db, project, format, bundle='reproducibility')
        assert secret not in output
        assert 'A😀BC' not in output
        assert 'SYNTHETIC_VAULT' not in output
        assert 'SYNTHETIC_RAW_PROMPT' not in output
        assert 'predictions_json' not in output
        if format == 'json':
            data = json.loads(output)
            assert data['attribute_values_redacted'] is True
            assert 'value' not in data['attributes'][0]
            exported = data['coding_events'][0]
            assert all(exported[k] == event[k] for k in (
                'segment_id', 'codebook_version_id', 'actor', 'pipeline_version'))
            assert data['codebook_versions']
            assert data['evaluation_runs']
            assert data['config_hashes']
        else:
            rows = list(csv.DictReader(io.StringIO(output)))
            exported = next(row for row in rows if row['record_type'] == 'coding_events')
            assert exported['actor'] == event['actor']
            assert exported['pipeline_version'] == event['pipeline_version']


def test_explicit_text_export_and_formula_safety(tmp_path):
    project = init_project('study', tmp_path)
    with Store(project / 'project.db') as db:
        _, _, event = seed_coding(db)
        db.assign(event)
        db.save_memo({'title': '=1+1', 'text': '@SUM(1,2)'})
        data = json.loads(export_data(db, project, no_text=False))
        assert data['sources'][0]['text'] == 'A😀BC'
        rows = list(csv.DictReader(io.StringIO(export_data(db, project, 'csv', no_text=False))))
        memo = next(row for row in rows if row['record_type'] == 'memos')
        assert memo['title'] == "'=1+1"
        assert memo['text'] == "'@SUM(1,2)"
        with pytest.raises(ValueError, match='format'):
            export_data(db, project, 'pdf')
