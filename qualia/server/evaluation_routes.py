"""Validation and threshold-tuning API; protected evaluation is an explicit local CLI operation."""

from pathlib import Path

from fastapi import FastAPI

from qualia.server.api_models import EvaluateInput, EvaluationResult, ExperimentResult
from qualia.server.workspace_routes import existing_project
from qualia.store.db import Store


def register_evaluation_routes(app: FastAPI, home: Path | None):
    @app.get('/api/projects/{slug}/experiments', response_model=list[ExperimentResult])
    def history(slug: str):
        path = existing_project(slug, home)
        with Store(path / 'project.db') as db:
            return db.rows('SELECT * FROM experiments ORDER BY id')

    @app.post('/api/projects/{slug}/tune-thresholds', response_model=ExperimentResult)
    def tune_thresholds(slug: str, record: EvaluateInput):
        # Same measured experiment as `qualia improve --agent thresholds`; no AI operator runs.
        from qualia.improve.experiment import improve_project

        return improve_project(existing_project(slug, home), agent='thresholds', budget=1,
                               **record.model_dump())[0]

    @app.post('/api/projects/{slug}/evaluate', response_model=EvaluationResult)
    def evaluate(slug: str, record: EvaluateInput):
        from qualia.evaluation import evaluate_project, write_reports

        path = existing_project(slug, home)
        with Store(path / 'project.db') as db:
            result = evaluate_project(db, path, **record.model_dump())
        write_reports(result, path / 'reports')
        return result
