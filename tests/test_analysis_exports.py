"""Synthetic-only read snapshots and independently executable analysis exports."""

import csv
import io
import json
import shutil
import subprocess
import sys

import pytest

from qualia.core.analysis_models import AnalysisOptions
from qualia.eval.analysis import analyze
from qualia.io import analysis as analysis_io
from qualia.store.db import Store
from qualia.workspace import init_project


def data_fixture():
    data = dict(sources=[], segments=[], cases=[], source_cases=[], attributes=[],
                codes=[{'id': 1, 'name': '=Code label'}, {'id': 2, 'name': 'Other'}],
                codebook_versions=[{'id': 1, 'hash': 'synthetic-version'}],
                current_codings=[], pipeline_version='synthetic-pipeline')
    for i in range(1, 9):
        text = 'SECRET_TRANSCRIPT synthetic '+str(i)
        data['sources'].append(dict(id=i, name='SECRET_SOURCE', text=text))
        data['segments'].append(dict(id=i, source_id=i, start=0, end=len(text), speaker='SECRET_SPEAKER'))
        data['cases'].append(dict(id=i, name='=Sensitive case '+str(i)))
        data['source_cases'].append(dict(source_id=i, case_id=i))
    for case, field, value in [
        (1, 'x', '-5'), (2, 'x', '+2'), (3, 'x', '.5'), (5, 'x', "'-5"),
        (6, 'x', '1'), (6, 'x', '2'), (7, 'x', 'NaN'), (8, 'x', '1e151'),
        (1, 'y', '-10'), (2, 'y', '+4'), (3, 'y', '1'), (4, 'y', '2'),
        (5, 'y', '3'), (6, 'y', '4'), (7, 'y', '5'), (8, 'y', '6'),
        (1, "unselected'\n__import__('os')", '=Never execute data'),
        (2, 'multiline', 'a,"b"\r\nnext'), (3, 'tab', '\t=Never execute data'),
    ]:
        data['attributes'].append(dict(case_id=case, key=field, value=value))
    for identity, segment, code in [(1, 1, 1), (2, 1, 1), (3, 2, 1), (4, 2, 2)]:
        data['current_codings'].append(dict(id=identity, segment_id=segment, code_id=code,
            span_start=0, span_end=4, action='assign', codebook_version_id=1))
    return data


def report_fixture():
    return analyze(data_fixture(), AnalysisOptions(numeric_fields=['x', 'y']))


def execute_python(tmp_path, report):
    csv_path = tmp_path/'qualia-analysis.csv'
    script = tmp_path/'qualia-analysis.py'
    csv_path.write_text(analysis_io.export_analysis(report, 'csv')['content'], encoding='utf-8', newline='')
    script.write_text(analysis_io.export_analysis(report, 'python')['content'], encoding='utf-8', newline='')
    result = subprocess.run([sys.executable, '-I', str(script), str(csv_path)],
                            capture_output=True, text=True, encoding='utf-8', timeout=10)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_json_excludes_transcripts_and_words_but_marks_metadata_privacy():
    report = report_fixture()
    before = report.model_dump()
    exported = analysis_io.export_analysis(report, 'json')
    data = json.loads(exported['content'])
    assert data['text_excluded'] is True and data['attribute_values_included'] is True
    assert 'not anonymization' in data['privacy_note']
    assert all(secret not in exported['content'] for secret in
               ('SECRET_TRANSCRIPT', 'SECRET_SOURCE', 'SECRET_SPEAKER'))
    assert '=Sensitive case' in exported['content']  # Intentional research metadata.
    assert 'words' not in data['report']
    assert data['report']['excerpts'][0] == {'segment_id': 1, 'source_id': 1, 'coding_event_ids': [1, 2]}
    assert data['input_hash'] == report.input_hash
    assert data['report']['codebook_hashes'] == {'1': 'synthetic-version'}
    assert report.model_dump() == before
    assert exported == analysis_io.export_analysis(report, 'json')


def test_csv_stable_ids_dictionary_all_attributes_and_reversible_formula_escaping():
    report = report_fixture()
    metadata = json.loads(analysis_io.export_analysis(report, 'json')['content'])
    columns = metadata['column_dictionary']
    attrs = {entry['field']: (name, entry) for name, entry in columns.items() if entry['kind'] == 'attribute'}
    assert set(attrs) == {key for row in report.case_rows for key in row.attributes}
    x, info = attrs['x']
    rows = list(csv.DictReader(io.StringIO(analysis_io.export_analysis(report, 'csv')['content'])))
    assert rows[0][x] == "'-5" and rows[0][info['escaped_column']] == '1'
    assert rows[1][x] == "'+2" and rows[1][info['escaped_column']] == '1'
    assert rows[4][x] == "'-5" and rows[4][info['escaped_column']] == '0'
    assert rows[5][info['status_column']] == 'conflicting'
    assert rows[0]['case_name'].startswith("'=") and rows[0]['case_name_escaped'] == '1'
    assert rows[0]['code_1'] == '1' and rows[1]['code_1'] == '1'
    assert 'SECRET_TRANSCRIPT' not in str(rows)
    assert rows[1][attrs['multiline'][0]] == 'a,"b"\r\nnext'
    assert all(name.isascii() and '\n' not in name for name in columns)


def test_python_starter_reproduces_report_statistics_and_prevalence(tmp_path):
    report = report_fixture()
    result = execute_python(tmp_path, report)
    assert result['case_count'] == report.case_count
    for actual, expected in zip(result['numeric'], report.numeric, strict=True):
        assert actual == expected.model_dump(exclude={'values'})
    for actual, expected in zip(result['correlations'], report.correlations, strict=True):
        assert actual == expected.model_dump(exclude={'points'})
    assert result['numeric'][0]['valid'] == 3
    assert result['numeric'][0]['missing'] == 1
    assert result['numeric'][0]['invalid'] == 4
    assert result['correlations'][0]['n'] == 3
    assert result['correlations'][0]['pearson_r'] == pytest.approx(1)
    assert result['code_prevalence'][0] == {'code_id': 1, 'case_count': 2, 'case_percent': 25}


@pytest.mark.parametrize('mode', ['empty', 'two_pairs', 'constant', 'no_numeric'])
def test_starters_insufficient_and_constant_samples(tmp_path, mode):
    data = data_fixture()
    if mode == 'empty':
        options = AnalysisOptions(query='no match', numeric_fields=['x', 'y'])
    elif mode == 'no_numeric':
        options = AnalysisOptions()
    else:
        if mode == 'two_pairs':
            data['attributes'] = [row for row in data['attributes'] if not (row['key'] == 'x' and row['case_id'] == 3)]
        else:
            for row in data['attributes']:
                if row['key'] == 'x':
                    row['value'] = '4'
        options = AnalysisOptions(numeric_fields=['x', 'y'])
    report = analyze(data, options)
    result = execute_python(tmp_path, report)
    for actual, expected in zip(result['numeric'], report.numeric, strict=True):
        assert actual == expected.model_dump(exclude={'values'})
    assert all(row['pearson_r'] is None for row in result['correlations'])


def test_r_starter_embeds_only_safe_column_ids_in_executable_code(tmp_path):
    report = report_fixture()
    text = analysis_io.export_analysis(report, 'r')['content']
    executable = '\n'.join(line for line in text.splitlines() if not line.startswith('#'))
    assert '__import__' not in executable and 'Never execute' not in executable
    assert 'SECRET_' not in text and 'library(' not in executable and 'eval(' not in executable
    assert 'length(x) >= 3' in text and 'abs(value) <= 1e150' in text
    assert '"[\\h\\v]"' not in text  # R source requires doubled backslashes.
    rscript = shutil.which('Rscript')
    if rscript is None:
        pytest.skip('Rscript unavailable; generated base-R source reviewed, not executed')
    script = tmp_path/'qualia-analysis.R'
    csv_path = tmp_path/'qualia-analysis.csv'
    script.write_text(text, encoding='utf-8')
    csv_path.write_text(analysis_io.export_analysis(report, 'csv')['content'], encoding='utf-8', newline='')
    result = subprocess.run([rscript, str(script), str(csv_path)], capture_output=True,
                            text=True, encoding='utf-8', timeout=15)
    assert result.returncode == 0, result.stderr
    assert 'pearson_r' in result.stdout and '$valid' in result.stdout


def test_read_analysis_uses_one_transaction_and_does_not_write_or_read_vault(tmp_path, monkeypatch):
    project = init_project('analysis', tmp_path)
    with Store(project/'project.db') as db:
        source = db.add('sources', dict(name='Synthetic', text='abc', content_hash='test'))
        db.add('segments', dict(source_id=source, start=0, end=3, ordinal=0))
        db.save_case(dict(name='Case', source_ids=[source], attributes={'x': '1'}))
        before, changes = db.fingerprint(), db.connection.total_changes
        original = db.rows
        def rows(query, parameters=()):
            assert db.connection.in_transaction
            return original(query, parameters)
        monkeypatch.setattr(db, 'rows', rows)
        from qualia import workspace
        monkeypatch.setattr(workspace, 'vault_dir', lambda *args: pytest.fail('vault read'))
        report = analysis_io.read_analysis(db, project, AnalysisOptions(numeric_fields=['x']))
        assert report.numeric[0].mean == 1 and report.segment_count == 1
        monkeypatch.setattr(db, 'rows', original)
        assert db.fingerprint() == before and db.connection.total_changes == changes


def test_read_analysis_refuses_config_race(tmp_path, monkeypatch):
    project = init_project('analysis', tmp_path)
    hashes = iter(['first', 'second'])
    monkeypatch.setattr(analysis_io, 'pipeline_hash', lambda path: next(hashes))
    with Store(project/'project.db') as db, pytest.raises(ValueError, match='changed during'):
        analysis_io.read_analysis(db, project, AnalysisOptions())


def test_invalid_export_format_fails_before_generating_content():
    with pytest.raises(ValueError, match='unsupported'):
        analysis_io.export_analysis(report_fixture(), 'exe')
