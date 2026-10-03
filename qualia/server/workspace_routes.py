"""Human research operations; SQL writes are delegated to the Store."""

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException

from qualia.server.api_models import (
    CaseInput,
    CodeInput,
    CodingInput,
    ExportResult,
    IdResult,
    ImportInput,
    ImportResult,
    MemoInput,
)
from qualia.store.db import Store
from qualia.workspace import pipeline_hash, project_dir


def existing_project(slug: str, home: Path | None = None) -> Path:
    path = project_dir(slug, home)
    if not (path / 'project.db').is_file():
        raise HTTPException(404, 'Project not found')
    return path


def register_workspace_routes(app: FastAPI, home: Path | None):
    @app.post('/api/projects/{slug}/import', response_model=ImportResult)
    def import_source(slug: str, record: ImportInput):
        from qualia.io.imports import import_text

        path = existing_project(slug, home)
        with Store(path / 'project.db') as db:
            return import_text(db, path, **record.model_dump())

    @app.post('/api/projects/{slug}/codes', response_model=IdResult)
    def create_code(slug: str, record: CodeInput):
        with Store(existing_project(slug, home) / 'project.db') as db:
            return {'id': db.save_code(record.model_dump())}

    @app.put('/api/projects/{slug}/codes/{code_id}', response_model=IdResult)
    def update_code(slug: str, code_id: int, record: CodeInput):
        with Store(existing_project(slug, home) / 'project.db') as db:
            return {'id': db.save_code(record.model_dump(), code_id=code_id)}

    @app.post('/api/projects/{slug}/codebook/freeze', response_model=IdResult)
    def freeze(slug: str):
        with Store(existing_project(slug, home) / 'project.db') as db:
            if not db.rows("SELECT id FROM codes WHERE status='active'"):
                raise ValueError('Add an active code before freezing the codebook')
            return {'id': db.freeze_codebook()['id']}

    @app.post('/api/projects/{slug}/coding', response_model=IdResult)
    def coding(slug: str, record: CodingInput):
        path = existing_project(slug, home)
        with Store(path / 'project.db') as db:
            segment = db.one('SELECT * FROM segments WHERE id=?', (record.segment_id,))
            if segment is None:
                raise ValueError(f'Segment {record.segment_id} not found')
            version = record.codebook_version_id
            if version is None:
                latest = db.one('SELECT id FROM codebook_versions ORDER BY id DESC LIMIT 1')
                if latest is None:
                    raise ValueError('Freeze a codebook version before coding')
                version = latest['id']
            values = record.model_dump()
            values.update(actor_type='human', codebook_version_id=version,
                          span_end=record.span_end if record.span_end is not None else segment['end']-segment['start'],
                          pipeline_version=pipeline_hash(path))
            return {'id': db.assign(values)}

    @app.post('/api/projects/{slug}/memos', response_model=IdResult)
    def create_memo(slug: str, record: MemoInput):
        with Store(existing_project(slug, home) / 'project.db') as db:
            return {'id': db.save_memo(record.model_dump())}

    @app.put('/api/projects/{slug}/memos/{memo_id}', response_model=IdResult)
    def update_memo(slug: str, memo_id: int, record: MemoInput):
        with Store(existing_project(slug, home) / 'project.db') as db:
            return {'id': db.save_memo(record.model_dump(), memo_id=memo_id)}

    @app.post('/api/projects/{slug}/cases', response_model=IdResult)
    def create_case(slug: str, record: CaseInput):
        with Store(existing_project(slug, home) / 'project.db') as db:
            return {'id': db.save_case(record.model_dump())}

    @app.put('/api/projects/{slug}/cases/{case_id}', response_model=IdResult)
    def update_case(slug: str, case_id: int, record: CaseInput):
        with Store(existing_project(slug, home) / 'project.db') as db:
            return {'id': db.save_case(record.model_dump(), case_id=case_id)}

    @app.get('/api/projects/{slug}/retrieval')
    def retrieval(slug: str, code_id: int | None = None, case_id: int | None = None):
        with Store(existing_project(slug, home) / 'project.db') as db:
            return db.retrieve(code_id=code_id, case_id=case_id)

    @app.get('/api/projects/{slug}/matrix')
    def matrix(slug: str):
        with Store(existing_project(slug, home) / 'project.db') as db:
            return db.matrix()

    @app.get('/api/projects/{slug}/export', response_model=ExportResult)
    def export(slug: str, format: Literal['json', 'csv'] = 'json', no_text: bool = True,
               bundle: Literal['reproducibility'] | None = None):
        from qualia.io.exporters import export_data

        path = existing_project(slug, home)
        with Store(path / 'project.db') as db:
            content = export_data(db, path, format=format, no_text=no_text, bundle=bundle)
        return {'filename': f'{slug}-{"reproducibility" if bundle else "coding"}.{format}',
                'media_type': 'application/json' if format == 'json' else 'text/csv', 'content': content}
