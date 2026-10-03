"""Validation-only API; protected evaluation is an explicit local CLI operation."""

from pathlib import Path

from fastapi import FastAPI

from qualia.server.api_models import EvaluateInput, EvaluationResult
from qualia.server.workspace_routes import existing_project
from qualia.store.db import Store


def register_evaluation_routes(app: FastAPI, home: Path | None):
    @app.post('/api/projects/{slug}/evaluate', response_model=EvaluationResult)
    def evaluate(slug: str, record: EvaluateInput):
        from qualia.evaluation import evaluate_project, write_reports

        path = existing_project(slug, home)
        with Store(path / 'project.db') as db:
            result = evaluate_project(db, path, **record.model_dump())
        write_reports(result, path / 'reports')
        return result
