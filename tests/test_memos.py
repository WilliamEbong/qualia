import sqlite3

import pytest
from typer.testing import CliRunner

from qualia.cli import app
from qualia.store.db import Store


def test_memo_kinds_links_and_history_are_kept():
    with Store(':memory:') as db:
        source = db.add('sources', {'name': 's', 'text': 'Some text.', 'content_hash': 'h'})
        case = db.save_case({'name': 'P1', 'source_ids': [source]})
        memo = db.save_memo({'title': 'Position', 'text': 'I worked as a nurse.', 'kind': 'reflexive',
                             'case_id': case, 'source_id': source})
        db.save_memo({'text': 'I worked as a nurse for ten years.'}, memo)
        db.save_memo({'kind': 'method'}, memo)
        row = db.one('SELECT * FROM memos')
        assert (row['kind'], row['case_id'], row['source_id']) == ('method', case, source)
        history = db.rows('SELECT text, kind FROM memo_revisions WHERE memo_id=? ORDER BY id', (memo,))
        assert history == [{'text': 'I worked as a nurse.', 'kind': 'reflexive'},
                           {'text': 'I worked as a nurse for ten years.', 'kind': 'reflexive'}]
        with pytest.raises(sqlite3.IntegrityError, match='append-only'):
            db.connection.execute('DELETE FROM memo_revisions')
        db.connection.rollback()
        for values in ({'title': 't', 'text': 'x', 'kind': 'theory'}, {'title': 't', 'text': 'x', 'case_id': 9}):
            with pytest.raises(ValueError):
                db.save_memo(values)


def test_cli_memo_edit_keeps_links_it_was_not_given(tmp_path, monkeypatch):
    monkeypatch.setenv('QUALIA_HOME', str(tmp_path))
    runner = CliRunner()
    assert runner.invoke(app, ['init', 'study']).exit_code == 0
    with Store(tmp_path / 'projects/study/project.db') as db:
        code = db.save_code({'name': 'Waiting'})
    result = runner.invoke(app, ['memo', 'Theme', 'Waiting as neglect', '--project', 'study',
                                 '--kind', 'theme', '--code', str(code)])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ['memo', 'Theme', 'Waiting as being unseen', '--project', 'study',
                                 '--memo-id', '1'])
    assert result.exit_code == 0, result.output
    with Store(tmp_path / 'projects/study/project.db') as db:
        memo = db.one('SELECT * FROM memos')
    assert (memo['kind'], memo['code_id'], memo['text']) == ('theme', code, 'Waiting as being unseen')
    bad = runner.invoke(app, ['memo', 'x', 'y', '--project', 'study', '--kind', 'theory'])
    assert bad.exit_code != 0 and 'Traceback' not in bad.output


def test_saving_an_unchanged_memo_adds_no_revision():
    with Store(':memory:') as db:
        memo = db.save_memo({'title': 't', 'text': 'same'})
        db.save_memo({'title': 't', 'text': 'same'}, memo)
        assert db.rows('SELECT * FROM memo_revisions') == []
