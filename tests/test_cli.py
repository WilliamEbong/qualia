import json

from typer.testing import CliRunner

from qualia.cli import app
from qualia.io.imports import import_text
from qualia.store.db import Store


def test_cli_import_codebook_coding_export(tmp_path, monkeypatch):
    monkeypatch.setenv('QUALIA_HOME', str(tmp_path / 'home'))
    runner = CliRunner()
    assert runner.invoke(app, ['init', 'study']).exit_code == 0
    transcript = tmp_path / 'transcript.txt'
    transcript.write_text('A new possibility.\n\nA careful decision.', encoding='utf-8')
    args = ['import', str(transcript), '--project', 'study']
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    assert '1 new sources' in result.output
    assert '0 new sources' in runner.invoke(app, args).output
    assert runner.invoke(app, ['codebook', 'add', 'Possibility', '--project', 'study']).exit_code == 0
    assert runner.invoke(app, ['codebook', 'freeze', '--project', 'study']).exit_code == 0
    result = runner.invoke(app, ['code', '1', '1', '--project', 'study'])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ['export', '--project', 'study', '--bundle', 'reproducibility'])
    assert result.exit_code == 0, result.output
    bundle = json.loads(result.output)
    assert bundle['coding_events'][0]['actor_type'] == 'human'
    assert 'A new possibility' not in result.output


def test_cli_preserves_newlines_and_supports_source_versions(tmp_path, monkeypatch):
    monkeypatch.setenv('QUALIA_HOME', str(tmp_path / 'home'))
    runner = CliRunner()
    assert runner.invoke(app, ['init', 'study']).exit_code == 0
    project = tmp_path / 'home' / 'projects' / 'study'
    transcript = tmp_path / 'transcript.txt'
    content = b'First paragraph.\r\n\r\nSecond paragraph.'
    transcript.write_bytes(content)
    with Store(project / 'project.db') as db:
        imported = import_text(db, project, transcript.name, content.decode('utf-8'), 'txt')
    result = runner.invoke(app, ['import', str(transcript), '--project', 'study'])
    assert result.exit_code == 0, result.output
    assert '0 new sources' in result.output
    original = imported['source_ids'][0]
    transcript.write_bytes(b'Edited paragraph.\r\n')
    result = runner.invoke(app, ['import', str(transcript), '--project', 'study', '--version-of', str(original)])
    assert result.exit_code == 0, result.output
    with Store(project / 'project.db') as db:
        assert db.one('SELECT version_of FROM sources ORDER BY id DESC LIMIT 1')['version_of'] == original


def test_cli_partial_code_edit_keeps_unsent_fields_and_errors_are_clean(tmp_path, monkeypatch):
    monkeypatch.setenv('QUALIA_HOME', str(tmp_path / 'home'))
    runner = CliRunner()
    assert runner.invoke(app, ['init', 'study']).exit_code == 0
    db_path = tmp_path / 'home/projects/study/project.db'
    with Store(db_path) as db:
        parent = db.save_code({'name': 'Parent'})
        child = db.save_code({'name': 'Child', 'parent_id': parent, 'status': 'archived'})
    edit = tmp_path / 'edit.json'
    edit.write_text(json.dumps({'name': 'Child', 'definition': 'Now defined.'}), encoding='utf-8')
    result = runner.invoke(app, ['codebook', 'save', str(edit), '--code-id', str(child), '--project', 'study'])
    assert result.exit_code == 0, result.output
    with Store(db_path) as db:
        row = db.one('SELECT * FROM codes WHERE id=?', (child,))
    assert (row['status'], row['parent_id'], row['definition']) == ('archived', parent, 'Now defined.')
    for args in (['codebook', 'add', 'Loop', '--parent', '99'], ['case', 'P1', '--source', '99']):
        result = runner.invoke(app, [*args, '--project', 'study'])
        assert result.exit_code == 2 and isinstance(result.exception, SystemExit), result.output


def test_read_snapshot_does_not_block_a_writer(tmp_path):
    path = tmp_path / 'project.db'
    with Store(path) as reader, Store(path) as writer:
        with reader.reading():
            reader.rows('SELECT * FROM codes')
            writer.save_code({'name': 'Written during a read'})
        assert reader.one('SELECT count(*) AS n FROM codes')['n'] == 1
