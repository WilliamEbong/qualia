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
    code_proposals: list[dict] = Field(default_factory=list)  # absent from older demo snapshots
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


class ClassifyInput(Record):
    backend: str | None = None
    model: str | None = None
    segment_ids: list[int] | None = None
    task: Literal['classification', 'escalation'] = 'classification'


class ClassifyResult(Record):
    run_id: str
    backend: str
    model: str
    segments: int
    calls: int
    cache_hits: int
    escalated_segments: int
    suggestion_ids: list[int]
    predictions: list[dict]
    status: str
    errors: list[str]


class BackendAvailability(Record):
    name: str
    available: bool
    external: bool
    reason: str


class Availability(Record):
    allow_external: bool
    backends: list[BackendAvailability]


class ReviewInput(Record):
    suggestion_id: int = Field(gt=0)
    decision: Literal['accept', 'reject']
    actor: str = Field(default='researcher', min_length=1, max_length=200)
    note: str = Field(default='', max_length=10000)


class EvaluateInput(Record):
    backend: str | None = None
    model: str | None = None


class EvaluationResult(Record):
    id: int
    split: str
    backend: str
    model: str
    codebook_version_id: int
    pipeline_version: str
    metrics: dict
    created_at: str


class ExperimentResult(Record):
    id: int
    slug: str
    agent: str
    decision: Literal['KEEP', 'REVERT']
    reason: str
    hypothesis: str
    before_json: str
    after_json: str
    changed_files_json: str
    commit_hash: str | None
    tag: str | None
    created_at: str


class ProposalInput(Record):
    mode: Literal['draft', 'refine']
    backend: str | None = None
    model: str | None = None
    segment_ids: list[int] = Field(default_factory=list, max_length=20)
    code_ids: list[int] = Field(default_factory=list, max_length=2)
    focus: str = Field(default='', max_length=500)


class ProposalRun(Record):
    batch_id: str
    status: str
    backend: str
    model: str
    proposal_ids: list[int]
    errors: list[str]


class ProposalValues(Record):
    """Human edits applied on acceptance; omitted fields keep the proposed value."""
    name: str | None = Field(default=None, min_length=1, max_length=200)
    parent_id: int | None = None
    definition: str | None = Field(default=None, max_length=10000)
    include: str | None = Field(default=None, max_length=10000)
    exclude: str | None = Field(default=None, max_length=10000)
    examples_pos: list[str] | None = None
    examples_neg: list[str] | None = None
    status: Literal['active', 'archived'] | None = None


class ProposalDecisionInput(Record):
    decision: Literal['accept', 'reject']
    actor: str = Field(min_length=1, max_length=200)
    note: str = Field(default='', max_length=10000)
    values: ProposalValues | None = None


class ProposalDecisionResult(Record):
    id: int
    code_id: int | None
