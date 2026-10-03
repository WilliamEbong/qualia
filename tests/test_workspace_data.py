import pytest

from qualia.io.imports import import_text
from qualia.store.db import Store
from qualia.workspace import init_project


def test_csv_duplicate_text_has_multiple_cases_without_duplicate_attributes(tmp_path):
    project = init_project('study', tmp_path)
    content = 'text,case,group\nShared synthetic text,alpha,A\nShared synthetic text,beta,B\n'
    with Store(project / 'project.db') as db:
        result = import_text(db, project, 'cases.csv', content, 'csv', attribute_columns=['group'])
        assert result['new_sources'] == 1
        import_text(db, project, 'cases.csv', content, 'csv', attribute_columns=['group'])
        assert len(db.rows('SELECT * FROM source_cases')) == 2
        assert len(db.rows('SELECT * FROM attributes')) == 2


def test_explicit_lineage_and_failed_import_rollback(tmp_path):
    project = init_project('study', tmp_path)
    with Store(project / 'project.db') as db:
        first = import_text(db, project, 'note', 'First version.', 'txt')['source_ids'][0]
        second = import_text(db, project, 'note', 'Changed version.', 'txt', version_of=first)
        assert db.one('SELECT version_of FROM sources WHERE id=?', second['source_ids'])['version_of'] == first
        with pytest.raises(ValueError, match='source.*999'):
            import_text(db, project, 'bad', 'Never committed.', 'txt', version_of=999)
        assert len(db.rows('SELECT * FROM sources')) == 2


def test_case_attribute_edits_and_links(tmp_path):
    project = init_project('study', tmp_path)
    with Store(project / 'project.db') as db:
        source = import_text(db, project, 'test', 'Synthetic.', 'txt')['source_ids'][0]
        case = db.save_case({'name': 'case-a'})
        db.link_case(source, case)
        db.link_case(source, case)
        db.save_attribute({'case_id': case, 'key': 'group', 'value': 'A'})
        db.save_attribute({'case_id': case, 'key': 'group', 'value': 'B'})
        db.save_case({'name': 'renamed', 'source_ids': [source], 'attributes': {'group': 'C'}}, case)
        assert db.one('SELECT name FROM cases WHERE id=?', (case,))['name'] == 'renamed'
        assert db.rows('SELECT value FROM attributes') == [{'value': 'C'}]
        assert len(db.rows('SELECT * FROM source_cases')) == 1
        with pytest.raises(ValueError, match='sources record 999'):
            db.save_case({'name': 'never-committed', 'source_ids': [999]}, case)
        assert db.one('SELECT name FROM cases WHERE id=?', (case,))['name'] == 'renamed'


def test_failed_write_rolls_back_entire_import(tmp_path, monkeypatch):
    project = init_project('study', tmp_path)
    with Store(project / 'project.db') as db:
        add = db.add

        def fail_second_source(table, values):
            if table == 'sources' and values['text'] == 'Second synthetic row':
                raise ValueError('synthetic storage failure')
            return add(table, values)

        monkeypatch.setattr(db, 'add', fail_second_source)
        with pytest.raises(ValueError, match='storage failure'):
            import_text(db, project, 'atomic.csv',
                        'text,case\nFirst synthetic row,first\nSecond synthetic row,second\n', 'csv')
        for table in ('sources', 'segments', 'cases', 'source_cases', 'attributes'):
            assert db.rows(f'SELECT * FROM {table}') == []
