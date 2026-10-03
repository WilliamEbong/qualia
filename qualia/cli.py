"""Qualia command line."""

import os
import webbrowser

import typer
import uvicorn

from qualia.server.app import create_app
from qualia.workspace import init_project, list_projects

app = typer.Typer(no_args_is_help=True, help='Qualitative coding you can audit.')


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


@app.command('open')
def open_command(port: int = typer.Option(8765, min=1024, max=65535), browser: bool = True):
    """Open the local research interface."""
    port = int(os.environ.get('QUALIA_PORT') or port)
    if browser:
        webbrowser.open(f'http://127.0.0.1:{port}')
    uvicorn.run(create_app(), host='127.0.0.1', port=port, access_log=False)


if __name__ == '__main__':
    app()
