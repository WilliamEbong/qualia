"""Public API boundary models, deliberately rejecting unexpected fields."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Record(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


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


class ImportInput(Record):
    name: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=10_000_000)
    format: Literal['txt', 'md', 'csv']
    text_column: str = 'text'
    case_column: str = 'case'
    speaker_column: str = 'speaker'
    attribute_columns: list[str] = Field(default_factory=list)
    version_of: int | None = None


class ImportResult(Record):
    new_sources: int
    source_ids: list[int]
    new_segments: int


class CodeInput(Record):
    name: str = Field(min_length=1, max_length=200)
    parent_id: int | None = None
    definition: str = Field(default='', max_length=10000)
    include: str = Field(default='', max_length=10000)
    exclude: str = Field(default='', max_length=10000)
    examples_pos: list[str] = Field(default_factory=list)
    examples_neg: list[str] = Field(default_factory=list)
    status: Literal['active', 'archived'] = 'active'


class CodingInput(Record):
    segment_id: int = Field(gt=0)
    code_id: int = Field(gt=0)
    span_start: int = Field(default=0, ge=0)
    span_end: int | None = Field(default=None, gt=0)
    codebook_version_id: int | None = Field(default=None, gt=0)
    action: Literal['assign', 'remove'] = 'assign'
    actor: str = Field(default='researcher', min_length=1, max_length=200)


class MemoInput(Record):
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(max_length=100000)
    segment_id: int | None = None
    code_id: int | None = None


class CaseInput(Record):
    name: str = Field(min_length=1, max_length=200)
    source_ids: list[int] = Field(default_factory=list)
    attributes: dict[str, str] = Field(default_factory=dict)


class IdResult(Record):
    id: int


class ExportResult(Record):
    filename: str
    media_type: str
    content: str
