"""Public API boundary models, deliberately rejecting unexpected fields."""

from pydantic import BaseModel, ConfigDict, Field


class Record(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ProjectInput(Record):
    name: str = Field(pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$', max_length=80)


class ProjectSummary(Record):
    slug: str
    name: str


class Health(Record):
    status: str = 'ok'
    version: str


class Workspace(Record):
    project: ProjectSummary
    sources: list[dict]
    segments: list[dict]
    cases: list[dict]
    attributes: list[dict]
    source_cases: list[dict]
    codes: list[dict]
    codebook_versions: list[dict]
    coding_events: list[dict]
    current_codings: list[dict]
    suggestions: list[dict]
    memos: list[dict]
    experiments: list[dict]
    evaluation_runs: list[dict]
    routing: dict
    pipeline_version: str
