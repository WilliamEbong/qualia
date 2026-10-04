"""Qualia command line."""

import json
import subprocess
import threading
import time
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
benchmark_app = typer.Typer(no_args_is_help=True)
app.add_typer(benchmark_app, name='benchmark')
jev_app = typer.Typer(no_args_is_help=True)
app.add_typer(jev_app, name='jev')


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


@app.command('analyze')
def analyze_command(project: str = 'demo', source_id: int | None = None,
                    case_id: int | None = None, code: list[int] | None = typer.Option(None),
                    code_match: str = 'any', query: str = '', group_by: str | None = None,
                    cooccurrence: str = 'segment', numeric: list[str] | None = typer.Option(None),
                    min_word_length: int = 3, stopword: list[str] | None = typer.Option(None),
                    top_words: int = 30, format: str = 'json'):
    """Read-only mixed-methods analysis; exports omit transcript text and retain case attributes."""
    from qualia.core.analysis_models import AnalysisOptions
    from qualia.io.analysis import export_analysis, read_analysis

    try:
        options = AnalysisOptions(source_id=source_id, case_id=case_id, code_ids=code or [],
                                  code_match=code_match, query=query, group_by=group_by,
                                  cooccurrence=cooccurrence, numeric_fields=numeric or [],
                                  min_word_length=min_word_length, stopwords=stopword or [],
                                  top_words=top_words)
        if format not in ('json', 'csv', 'python', 'r'):
            raise ValueError('analysis export format must be json, csv, python or r')
        path = resolve_project(project)
        with Store(path / 'project.db') as db:
            report = read_analysis(db, path, options)
        typer.echo(export_analysis(report, format)['content'])
    except (ValueError, OSError) as exc:
        raise typer.BadParameter(str(exc)) from exc


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


@app.command('classify')
def classify_command(project: str = 'demo', backend: str | None = None, model: str | None = None,
                     segments: str = '', escalate: bool = False):
    """Generate reviewable suggestions under the project's egress and budget policy."""
    from qualia.ai.router import classify_project

    try:
        selected = [int(value.strip()) for value in segments.split(',') if value.strip()] or None
        path = resolve_project(project)
        with Store(path / 'project.db') as db:
            result = classify_project(db, path, backend=backend, model=model, segment_ids=selected,
                                      task='escalation' if escalate else 'classification')
        typer.echo(json.dumps(result, ensure_ascii=False))
        if result['status'] not in ('completed', 'partial'):
            raise typer.Exit(1)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc


@app.command('availability')
def availability_command(project: str = 'demo'):
    """Show usable classifiers and exact reasons disabled backends cannot run."""
    from qualia.ai.router import availability

    typer.echo(json.dumps(availability(resolve_project(project)), ensure_ascii=False))


@app.command('review')
def review_command(suggestion: int, decision: str, project: str = 'demo',
                   actor: str = 'researcher', note: str = ''):
    """Accept or reject a suggestion and append human feedback atomically."""
    path = resolve_project(project)
    try:
        with Store(path / 'project.db') as db:
            typer.echo(db.review(suggestion, decision, actor, pipeline_hash(path), note))
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc


@benchmark_app.command('import')
def benchmark_import(file: Path, project: str = 'demo', split: str = 'validation',
                     version: int | None = None):
    """Import a complete JSONL split once, bound to a frozen codebook."""
    from qualia.io.benchmarks import import_benchmark

    path = resolve_project(project)
    try:
        with Store(path / 'project.db') as db:
            frozen = (db.one('SELECT * FROM codebook_versions WHERE id=?', (version,)) if version else
                      db.one('SELECT * FROM codebook_versions ORDER BY id DESC LIMIT 1'))
            if frozen is None:
                raise ValueError('freeze the benchmark codebook first')
            codes = [code['id'] for code in json.loads(frozen['snapshot_json'])
                     if code.get('status', 'active') == 'active']
            result = import_benchmark(path, file.read_bytes(), split, frozen['id'], codes)
        typer.echo(json.dumps(result, ensure_ascii=False))
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc


@jev_app.command('check')
def jev_check(project: str = 'demo'):
    """Check local Jev readiness without sending a request or displaying the key."""
    from qualia.ai.backends.jev import INPUT_RATE, MODEL, RESERVED_INPUT_TOKENS, JevBackend
    from qualia.workspace import read_config

    provider = JevBackend()
    config = read_config(resolve_project(project))
    typer.echo(json.dumps({'key_configured': provider.available(), 'model': MODEL,
                           'allow_external': config.get('allow_external', False),
                           'jev_enabled': config.get('jev_enabled', False),
                           'daily_usd_limit': config.get('jev_daily_usd', 1.0),
                           'maximum_reserved_usd_per_request': RESERVED_INPUT_TOKENS * INPUT_RATE,
                           'network_requests': 0}))


@jev_app.command('enable')
def jev_enable(project: str = 'demo'):
    """Explicitly permit external AI and Jev in the selected project; leave budget limits intact."""
    _jev_policy(project, True)


@jev_app.command('disable')
def jev_disable(project: str = 'demo'):
    """Disable external AI and Jev in the selected project."""
    _jev_policy(project, False)


def _jev_policy(slug: str, enabled: bool):
    from qualia.ai.schemas import routing_config
    from qualia.store.db import canonical
    from qualia.workspace import read_config

    path = resolve_project(slug)
    with Store(path / 'project.db') as db:
        with db.immediate():
            config = read_config(path)
            config.update(allow_external=enabled, jev_enabled=enabled)
            routing_config(config)
            (path / 'config/routing.yaml').write_text(canonical(config), encoding='utf-8')
    typer.echo('External AI and Jev ' + ('enabled' if enabled else 'disabled') + f' for {slug}.')


@app.command('evaluate')
def evaluate_command(project: str = 'demo', split: str = 'validation', protected: bool = False,
                     backend: str | None = None, model: str | None = None,
                     output: Path | None = None):
    """Evaluate a complete split and write JSON/Markdown reports; protected access is explicit."""
    from qualia.evaluation import evaluate_project, write_reports

    path = resolve_project(project)
    try:
        if protected and split != 'validation':
            raise ValueError('use --protected without --split')
        with Store(path / 'project.db') as db:
            result = evaluate_project(db, path, split='protected' if protected else split,
                                      protected=protected, backend=backend, model=model)
        paths = write_reports(result, output or path / 'reports')
        typer.echo(json.dumps(result, ensure_ascii=False))
        for report in paths:
            typer.echo(str(report))
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc


@app.command('improve')
def improve_command(project: str = 'demo', agent: str = 'claude',
                    budget: int = typer.Option(1, min=0),
                    backend: str | None = None, model: str | None = None):
    """Run bounded implementation experiments; trusted measurements decide KEEP or REVERT."""
    from qualia.improve.experiment import improve_project

    try:
        rows = improve_project(resolve_project(project), agent=agent, budget=budget,
                               backend=backend, model=model)
        typer.echo(json.dumps(rows, ensure_ascii=False))
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc


@app.command('history')
def history_command(project: str = 'demo'):
    """Read recorded experiment decisions and reproduction identities."""
    with Store(resolve_project(project) / 'project.db') as db:
        typer.echo(json.dumps(db.rows('SELECT * FROM experiments ORDER BY id'), ensure_ascii=False))


@app.command('demo')
def demo_command(project: str = 'demo', file: Path | None = None):
    """Create the licensed, pinned AnnoMI demo. Fetch its raw CSV first with scripts/fetch_demo.py."""
    from qualia.io.demo import import_demo
    from qualia.workspace import REPO

    try:
        content = (file or REPO / 'demo/data/AnnoMI-simple.csv').read_bytes()
        path = init_project(project)
        with Store(path / 'project.db') as db:
            result = import_demo(db, path, content)
        staged = subprocess.run(['git', '-C', str(path), 'diff', '--cached', '--quiet'], capture_output=True)
        if staged.returncode != 0:
            raise ValueError('demo imported; commit or unstage existing staged changes before preparing its baseline')
        subprocess.run(['git', '-C', str(path), 'add', '--', '.annomi-demo.json', 'benchmarks'],
                       check=True, capture_output=True)
        changed = subprocess.run(['git', '-C', str(path), 'diff', '--cached', '--quiet'], capture_output=True)
        if changed.returncode == 1:
            subprocess.run(['git', '-C', str(path), '-c', 'user.name=Qualia', '-c',
                            'user.email=qualia@localhost', 'commit', '-qm', 'Import pinned AnnoMI demo benchmarks'],
                           check=True, capture_output=True)
        elif changed.returncode != 0:
            raise ValueError('demo imported but its baseline could not be checked')
        typer.echo(json.dumps(result, ensure_ascii=False))
    except subprocess.CalledProcessError:
        raise typer.BadParameter('demo imported but its Git baseline could not be committed') from None
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc


@app.command('open')
def open_command(port: int = typer.Option(8765, min=1024, max=65535), browser: bool = True):
    """Open the local research interface."""
    try:
        port = int(local_setting('QUALIA_PORT') or port)
    except ValueError as exc:
        raise typer.BadParameter('QUALIA_PORT must be an integer') from exc
    if not 1024 <= port <= 65535:
        raise typer.BadParameter('QUALIA_PORT must be between 1024 and 65535')
    server = uvicorn.Server(uvicorn.Config(create_app(), host='127.0.0.1', port=port, access_log=False))
    stopped = threading.Event()
    if browser:
        threading.Thread(target=_open_when_ready, args=(server, port, stopped), daemon=True).start()
    try:
        server.run()
    finally:
        stopped.set()


def _open_when_ready(server, port: int, stopped: threading.Event):
    deadline = time.monotonic() + 30
    while not stopped.wait(0.05) and time.monotonic() < deadline:
        if server.started:
            webbrowser.open(f'http://127.0.0.1:{port}')
            return


if __name__ == '__main__':
    app()
