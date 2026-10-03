"""Qualia command line."""

import json
import webbrowser
from pathlib import Path

import typer
import uvicorn

from qualia.server.app import create_app
from qualia.store.db import Store
from qualia.workspace import init_project, list_projects, local_setting, pipeline_hash, project_dir

app = typer.Typer(no_args_is_help=True, help='Qualitative coding you can audit.')
codebook_app = typer.Typer(no_args_is_help=True)
app.add_typer(codebook_app, name='codebook')


def resolve_project(slug: str) -> Path:
    path = project_dir(slug)
    if not (path / 'project.db').is_file():
        raise typer.BadParameter(f'Project {slug} does not exist; run qualia init {slug}')
    return path


@app.command()
def init(name: str):
    """Initialize a local research workspace outside this repository."""
    try:
        typer.echo(str(init_project(name)))
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc


@app.command('list')
def list_command():
    """List local workspaces."""
    for project in list_projects():
        typer.echo(project['slug'])


@app.command('import')
def import_command(file: Path, project: str = 'demo', text_column: str = 'text',
                   case_column: str = 'case', speaker_column: str = 'speaker',
                   attribute_columns: str = '', version_of: int | None = None):
    """Import UTF-8 TXT, Markdown or CSV with explicit column mapping."""
    from qualia.io.imports import import_text

    path = resolve_project(project)
    try:
        content = file.read_bytes()
        with Store(path / 'project.db') as db:
            result = import_text(db, path, file.name, content, file.suffix.lstrip('.').lower(),
                                 text_column=text_column, case_column=case_column,
                                 speaker_column=speaker_column,
                                 attribute_columns=[x.strip() for x in attribute_columns.split(',') if x.strip()],
                                 version_of=version_of)
        typer.echo(f"{result['new_sources']} new sources; {result['new_segments']} new segments")
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc


@codebook_app.command('add')
def add_code(name: str, definition: str = '', parent: int | None = None, project: str = 'demo'):
    """Create a human-defined draft code."""
    with Store(resolve_project(project) / 'project.db') as db:
        typer.echo(db.save_code({'name': name, 'definition': definition, 'parent_id': parent}))


@codebook_app.command('freeze')
def freeze_codebook(project: str = 'demo'):
    """Freeze the human codebook into an immutable version."""
    with Store(resolve_project(project) / 'project.db') as db:
        if not db.rows("SELECT id FROM codes WHERE status='active'"):
            raise typer.BadParameter('Add an active code before freezing')
        frozen = db.freeze_codebook()
        typer.echo(f"cb_v{frozen['id']} · {frozen['hash']}")


@codebook_app.command('save')
def save_code(file: Path, code_id: int | None = None, project: str = 'demo'):
    """Create/edit/archive a draft code from a validated JSON record."""
    from qualia.server.api_models import CodeInput

    try:
        record = CodeInput.model_validate_json(file.read_text(encoding='utf-8'))
        with Store(resolve_project(project) / 'project.db') as db:
            typer.echo(db.save_code(record.model_dump(), code_id=code_id))
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(f'Invalid code record in {file.name}') from exc


@codebook_app.command('list')
def list_codes(project: str = 'demo'):
    """Inspect draft codes and their hierarchy."""
    with Store(resolve_project(project) / 'project.db') as db:
        typer.echo(json.dumps(db.rows('SELECT * FROM codes ORDER BY id'), ensure_ascii=False))


@app.command('code')
def code_command(segment: int, code: int, project: str = 'demo', start: int = 0,
                 end: int | None = None, version: int | None = None,
                 remove: bool = False, actor: str = 'researcher'):
    """Append a human span assignment or removal; offsets count Unicode code points."""
    from qualia.server.api_models import CodingInput

    path = resolve_project(project)
    record = CodingInput(segment_id=segment, code_id=code, span_start=start, span_end=end,
                         codebook_version_id=version, action='remove' if remove else 'assign', actor=actor)
    with Store(path / 'project.db') as db:
        selected = db.one('SELECT * FROM segments WHERE id=?', (segment,))
        frozen = db.one('SELECT id FROM codebook_versions ORDER BY id DESC LIMIT 1')
        if selected is None or frozen is None:
            raise typer.BadParameter('Select an existing segment and freeze a codebook first')
        values = record.model_dump()
        values.update(actor_type='human', pipeline_version=pipeline_hash(path),
                      codebook_version_id=version or frozen['id'],
                      span_end=end if end is not None else selected['end']-selected['start'])
        typer.echo(db.assign(values))


@app.command('memo')
def memo_command(title: str, text: str, project: str = 'demo', memo_id: int | None = None,
                 segment: int | None = None, code: int | None = None):
    """Create or edit a research memo linked to a segment or code."""
    from qualia.server.api_models import MemoInput

    record = MemoInput(title=title, text=text, segment_id=segment, code_id=code)
    with Store(resolve_project(project) / 'project.db') as db:
        typer.echo(db.save_memo(record.model_dump(), memo_id=memo_id))


@app.command('case')
def case_command(name: str, project: str = 'demo', case_id: int | None = None,
                 source: int | None = None, attributes: str = '{}'):
    """Create/update a case with optional source association and JSON attributes."""
    from qualia.server.api_models import CaseInput

    try:
        record = CaseInput(name=name, source_ids=[source] if source else [], attributes=json.loads(attributes))
    except ValueError as exc:
        raise typer.BadParameter('Attributes must be a JSON object of string values') from exc
    with Store(resolve_project(project) / 'project.db') as db:
        typer.echo(db.save_case(record.model_dump(), case_id=case_id))


@app.command('retrieve')
def retrieve_command(project: str = 'demo', code: int | None = None, case: int | None = None):
    """Retrieve current coded excerpts by code or case."""
    with Store(resolve_project(project) / 'project.db') as db:
        typer.echo(json.dumps(db.retrieve(code_id=code, case_id=case), ensure_ascii=False))


@app.command('matrix')
def matrix_command(project: str = 'demo'):
    """Count distinct currently coded segments per code and case."""
    with Store(resolve_project(project) / 'project.db') as db:
        typer.echo(json.dumps(db.matrix()))


@app.command('export')
def export_command(project: str = 'demo', format: str = 'json',
                   no_text: bool = typer.Option(True, '--no-text/--include-text'),
                   bundle: str | None = None, output: Path | None = None):
    """Export provenance, optionally as a reproducibility bundle. Text is excluded by default."""
    from qualia.io.exporters import export_data

    path = resolve_project(project)
    with Store(path / 'project.db') as db:
        content = export_data(db, path, format=format, no_text=no_text, bundle=bundle)
    if output:
        output.write_text(content, encoding='utf-8')
        typer.echo(str(output))
    else:
        typer.echo(content)


@app.command('open')
def open_command(port: int = typer.Option(8765, min=1024, max=65535), browser: bool = True):
    """Open the local research interface."""
    try:
        port = int(local_setting('QUALIA_PORT') or port)
    except ValueError as exc:
        raise typer.BadParameter('QUALIA_PORT must be an integer') from exc
    if not 1024 <= port <= 65535:
        raise typer.BadParameter('QUALIA_PORT must be between 1024 and 65535')
    if browser:
        webbrowser.open(f'http://127.0.0.1:{port}')
    uvicorn.run(create_app(), host='127.0.0.1', port=port, access_log=False)


if __name__ == '__main__':
    app()
