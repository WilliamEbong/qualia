"""Authenticated loopback API and bundled SPA."""

import secrets
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from qualia import __version__
from qualia.server.api_models import Health, ProjectInput, ProjectSummary, Workspace
from qualia.store.db import Store
from qualia.workspace import (
    REPO,
    init_project,
    list_projects,
    pipeline_hash,
    project_dir,
    read_config,
)


def create_app(home: Path | None = None, token: str | None = None, dist: Path | None = None) -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.token = token or secrets.token_urlsafe(32)
    app.state.home = home
    web = dist or REPO / 'web/dist'

    @app.middleware('http')
    async def secure(request: Request, call_next):
        host = request.headers.get('host', '')
        try:
            parsed = urlsplit('http://' + host)
            valid_host = parsed.hostname in ('localhost', '127.0.0.1') and not parsed.username
        except ValueError:
            valid_host = False
        origin = request.headers.get('origin')
        if not valid_host:
            response = JSONResponse({'detail': 'Host forbidden'}, status_code=403)
        elif origin and origin != f'http://{host}':
            response = JSONResponse({'detail': 'Origin forbidden'}, status_code=403)
        elif request.url.path.startswith('/api/') and not secrets.compare_digest(
                request.headers.get('x-qualia-token', ''), app.state.token):
            response = JSONResponse({'detail': 'Invalid launch token'}, status_code=401)
        else:
            response = await call_next(request)
        response.headers.update({
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                                       "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
                                       "base-uri 'none'; form-action 'self'",
            'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY',
            'Referrer-Policy': 'no-referrer', 'Cache-Control': 'no-store',
        })
        return response

    @app.exception_handler(ValueError)
    async def invalid_record(request, exc):
        return JSONResponse({'detail': str(exc)}, status_code=400)

    @app.get('/api/health', response_model=Health)
    def health():
        return Health(version=__version__)

    @app.get('/api/projects', response_model=list[ProjectSummary])
    def projects():
        return list_projects(home)

    @app.post('/api/projects', response_model=ProjectSummary, status_code=201)
    def create_project(record: ProjectInput):
        path = init_project(record.name, home)
        return {'slug': path.name, 'name': path.name.replace('-', ' ').title()}

    @app.get('/api/projects/{slug}', response_model=Workspace)
    def workspace(slug: str):
        path = project_dir(slug, home)
        if not (path / 'project.db').is_file():
            raise HTTPException(404, 'Project not found')
        with Store(path / 'project.db') as db:
            data = {table: db.rows(f'SELECT * FROM {table}') for table in (
                'sources', 'segments', 'cases', 'attributes', 'source_cases', 'codes',
                'codebook_versions', 'coding_events', 'current_codings', 'memos',
                'experiments', 'evaluation_runs')}
            data['suggestions'] = db.rows('SELECT * FROM pending_suggestions')
        return {**data, 'project': {'slug': slug, 'name': slug.replace('-', ' ').title()},
                'routing': read_config(path), 'pipeline_version': pipeline_hash(path)}

    @app.get('/{asset:path}', include_in_schema=False)
    def spa(asset: str):
        if asset.startswith('api/'):
            raise HTTPException(404)
        resolved = (web / asset).resolve()
        if asset and resolved.is_relative_to(web.resolve()) and resolved.is_file():
            if resolved.suffix != '.html':
                return FileResponse(resolved)
        index = web / 'index.html'
        html = index.read_text(encoding='utf-8') if index.exists() else (
            '<!doctype html><html><head><title>Qualia</title></head><body>'
            '<h1>Qualia</h1><p>Build the web application with npm run build in web.</p></body></html>')
        return HTMLResponse(html.replace('</head>',
                            f'<meta name="qualia-token" content="{app.state.token}"></head>'))

    return app
