import json
from pathlib import Path

import pytest

from qualia.core.segmentation import segment_text
from qualia.io.imports import import_text
from qualia.store.db import Store
from qualia.workspace import init_project

FIXTURES = Path(__file__).parent / 'fixtures/workspace'


@pytest.mark.parametrize('method,text,expected,speakers', [
    ('paragraph', '  One 😀.\r\n\r\nTwo.  ', ['One 😀.', 'Two.'], [None, None]),
    ('utterance', 'A: Hello 😀.\nB: Yes.\n\n', ['Hello 😀.', 'Yes.'], ['A', 'B']),
    ('sentence', 'First 😀! Second?\nThird.', ['First 😀!', 'Second?', 'Third.'], [None]*3),
])
def test_segmentation_exact_offsets(method, text, expected, speakers):
    spans = segment_text(text, method)
    assert [text[s['start']:s['end']] for s in spans] == expected
    assert [s['speaker'] for s in spans] == speakers
    assert [s['ordinal'] for s in spans] == list(range(len(expected)))


@pytest.mark.parametrize('filename,format,count', [
    ('transcript.txt', 'txt', 1), ('transcript.md', 'md', 1), ('records.csv', 'csv', 2),
])
def test_import_formats_and_idempotence(tmp_path, filename, format, count):
    project = init_project('study', tmp_path)
    content = (FIXTURES / filename).read_bytes()
    with Store(project / 'project.db') as db:
        first = import_text(db, project, filename, content, format)
        again = import_text(db, project, 'renamed', content, format)
        assert first['new_sources'] == count
        assert again['new_sources'] == again['new_segments'] == 0
        assert first['source_ids'] == again['source_ids']
        for row in db.rows('SELECT s.*, sources.text FROM segments s JOIN sources ON sources.id=s.source_id'):
            assert row['text'][row['start']:row['end']].strip()


def test_invalid_csv_and_utf8_name_record_without_partial_writes(tmp_path):
    project = init_project('study', tmp_path)
    with Store(project / 'project.db') as db:
        with pytest.raises(ValueError, match=r'invalid.csv.*row 3'):
            import_text(db, project, 'invalid.csv', (FIXTURES / 'invalid.csv').read_bytes(), 'csv')
        assert db.rows('SELECT * FROM sources') == []
        assert db.rows('SELECT * FROM cases') == []
        with pytest.raises(ValueError, match='bad.txt.*UTF-8'):
            import_text(db, project, 'bad.txt', b'\xff', 'txt')


def test_import_respects_segmentation_config_and_csv_mapping(tmp_path):
    project = init_project('study', tmp_path)
    (project / 'config/segmentation.yaml').write_text(json.dumps({'method': 'sentence'}))
    with Store(project / 'project.db') as db:
        result = import_text(db, project, 'records.csv', (FIXTURES / 'records.csv').read_bytes(),
                             'csv', attribute_columns=['group'])
        assert result['new_segments'] == 3
        assert {s['speaker'] for s in db.rows('SELECT speaker FROM segments')} == {
            'Interviewer', 'Participant'}
        assert {a['value'] for a in db.rows('SELECT * FROM attributes')} == {'A', 'B'}


@pytest.mark.parametrize('content', ['text,case\nhello,a,extra\n', 'text,text\na,b\n',
                                      'text,case\n"unterminated,a\n'])
def test_malformed_csv_is_rejected(tmp_path, content):
    project = init_project('study', tmp_path)
    with Store(project / 'project.db') as db:
        with pytest.raises(ValueError, match='broken.csv'):
            import_text(db, project, 'broken.csv', content, 'csv')
        assert db.rows('SELECT * FROM sources') == []
