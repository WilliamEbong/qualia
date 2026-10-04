"""Token-gated read-only analysis requests; POST carries bounded query criteria."""

from pathlib import Path

from fastapi import FastAPI, HTTPException

from qualia.core.analysis_models import AnalysisExportRequest, AnalysisOptions, AnalysisReport
from qualia.server.api_models import ExportResult
from qualia.server.workspace_routes import existing_project
from qualia.store.db import Store


def register_analysis_routes(app: FastAPI, home: Path | None):
    @app.post('/api/projects/{slug}/analysis', response_model=AnalysisReport)
    def analysis(slug: str, options: AnalysisOptions):
        from qualia.io.analysis import read_analysis

        path = existing_project(slug, home)
        with Store(path / 'project.db') as db:
            return read_analysis(db, path, options)

    @app.post('/api/projects/{slug}/analysis/export', response_model=ExportResult)
    def export(slug: str, request: AnalysisExportRequest):
        from qualia.io.analysis import export_analysis, read_analysis

        path = existing_project(slug, home)
        with Store(path / 'project.db') as db:
            report = read_analysis(db, path, request.options)
        if request.expected_input_hash is not None and report.input_hash != request.expected_input_hash:
            raise HTTPException(409, 'Research data changed. Refresh analysis before downloading this report.')
        return export_analysis(report, request.format)
