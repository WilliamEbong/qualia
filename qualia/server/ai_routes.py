"""Classification admission and explicit human review."""

from pathlib import Path

from fastapi import FastAPI

from qualia.server.api_models import (
    Availability,
    ClassifyInput,
    ClassifyResult,
    IdResult,
    ReviewInput,
)
from qualia.server.workspace_routes import existing_project
from qualia.store.db import Store
from qualia.workspace import pipeline_hash


def register_ai_routes(app: FastAPI, home: Path | None):
    @app.get('/api/projects/{slug}/ai/availability', response_model=Availability)
    def availability(slug: str):
        from qualia.ai.router import availability

        return availability(existing_project(slug, home))

    @app.post('/api/projects/{slug}/classify', response_model=ClassifyResult)
    def classify(slug: str, record: ClassifyInput):
        from qualia.ai.router import classify_project

        path = existing_project(slug, home)
        with Store(path / 'project.db') as db:
            return classify_project(db, path, **record.model_dump())

    @app.post('/api/projects/{slug}/review', response_model=IdResult)
    def review(slug: str, record: ReviewInput):
        path = existing_project(slug, home)
        with Store(path / 'project.db') as db:
            return {'id': db.review(record.suggestion_id, record.decision, record.actor,
                                    pipeline_hash(path), record.note)}
