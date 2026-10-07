"""Codebook proposals: created by AI or evidence, decided only by a named person."""

from pathlib import Path

from fastapi import FastAPI

from qualia.server.api_models import (
    ProposalDecisionInput,
    ProposalDecisionResult,
    ProposalInput,
    ProposalRun,
)
from qualia.server.workspace_routes import existing_project
from qualia.store.db import Store


def register_proposal_routes(app: FastAPI, home: Path | None):
    @app.post('/api/projects/{slug}/codebook/proposals/evidence', response_model=ProposalRun)
    def evidence(slug: str):
        from qualia.ai.proposals import propose_from_evidence

        with Store(existing_project(slug, home) / 'project.db') as db:
            return propose_from_evidence(db)

    @app.post('/api/projects/{slug}/codebook/proposals/ai', response_model=ProposalRun)
    def ai(slug: str, record: ProposalInput):
        from qualia.ai.proposals import propose_with_ai

        path = existing_project(slug, home)
        with Store(path / 'project.db') as db:
            return propose_with_ai(db, path, **record.model_dump())

    @app.post('/api/projects/{slug}/codebook/proposals/{proposal_id}/decision',
              response_model=ProposalDecisionResult)
    def decide(slug: str, proposal_id: int, record: ProposalDecisionInput):
        values = None
        if record.values is not None:
            # Only fields the person sent; an explicit null clears just the parent link.
            values = {key: value for key, value in record.values.model_dump(exclude_unset=True).items()
                      if value is not None or key == 'parent_id'}
        with Store(existing_project(slug, home) / 'project.db') as db:
            return db.decide_code_proposal(proposal_id, record.decision, record.actor, record.note, values)
