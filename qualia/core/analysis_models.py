"""Typed read-only analysis contract shared by pure calculations and the API."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

FieldName = Annotated[str, Field(min_length=1, max_length=100)]
CodeId = Annotated[int, Field(ge=1)]
Stopword = Annotated[str, Field(min_length=1, max_length=80)]


class AnalysisOptions(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    source_id: int | None = Field(default=None, ge=1)
    case_id: int | None = Field(default=None, ge=1)
    code_ids: list[CodeId] = Field(default_factory=list, max_length=50)
    code_match: Literal['any', 'all'] = 'any'
    query: str = Field(default='', max_length=200)
    group_by: str | None = Field(default=None, max_length=100)
    cooccurrence: Literal['segment', 'overlap'] = 'segment'
    numeric_fields: list[FieldName] = Field(default_factory=list, max_length=8)
    min_word_length: int = Field(default=3, ge=1, le=30)
    stopwords: list[Stopword] = Field(default_factory=list, max_length=200)
    top_words: int = Field(default=30, ge=1, le=100)
    excerpt_limit: int = Field(default=100, ge=1, le=500)

    @model_validator(mode='after')
    def unique_selections(self):
        if len(self.code_ids) != len(set(self.code_ids)) or len(self.numeric_fields) != len(set(self.numeric_fields)):
            raise ValueError('Select each code or numeric field only once')
        return self


class AnalysisFrequency(BaseModel):
    code_id: int
    name: str
    segment_count: int
    case_count: int
    segment_percent: float
    case_percent: float
    segment_ids: list[int]
    case_ids: list[int]
    codebook_version_ids: list[int]


class AnalysisGroup(BaseModel):
    value: str
    status: Literal['value', 'missing', 'conflicting']
    case_ids: list[int]
    segment_ids: list[int]
    frequencies: list[AnalysisFrequency]


class AnalysisPair(BaseModel):
    left_code_id: int
    right_code_id: int
    count: int
    union_count: int
    jaccard: float | None
    segment_ids: list[int]


class AnalysisWord(BaseModel):
    word: str
    count: int
    segment_count: int
    segment_ids: list[int]


class AnalysisValue(BaseModel):
    case_id: int
    value: float


class AnalysisNumeric(BaseModel):
    field: str
    valid: int
    missing: int
    invalid: int
    mean: float | None
    median: float | None
    sample_sd: float | None
    minimum: float | None
    maximum: float | None
    values: list[AnalysisValue]


class AnalysisPoint(BaseModel):
    case_id: int
    x: float
    y: float


class AnalysisCorrelation(BaseModel):
    x_field: str
    y_field: str
    n: int
    pearson_r: float | None
    points: list[AnalysisPoint]


class AnalysisExcerpt(BaseModel):
    segment_id: int
    source_id: int
    source_name: str
    speaker: str | None
    text: str
    coding_event_ids: list[int]


class AnalysisCase(BaseModel):
    case_id: int
    name: str
    attributes: dict[str, str | None]
    attribute_status: dict[str, Literal['value', 'missing', 'conflicting']]
    code_counts: dict[str, int]


class AnalysisReport(BaseModel):
    format_version: Literal[1] = 1
    options: AnalysisOptions
    methods: list[str]
    warnings: list[str]
    source_count: int
    segment_count: int
    case_count: int
    coded_segment_count: int
    selected_segment_ids: list[int]
    input_hash: str
    coding_event_ids: list[int]
    codebook_version_ids: list[int]
    codebook_hashes: dict[str, str]
    pipeline_version: str
    frequencies: list[AnalysisFrequency]
    groups: list[AnalysisGroup]
    pairs: list[AnalysisPair]
    words: list[AnalysisWord]
    numeric: list[AnalysisNumeric]
    correlations: list[AnalysisCorrelation]
    excerpts: list[AnalysisExcerpt]
    excerpt_total: int
    case_rows: list[AnalysisCase]


class AnalysisExportRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    options: AnalysisOptions = Field(default_factory=AnalysisOptions)
    format: Literal['json', 'csv', 'python', 'r'] = 'json'
    expected_input_hash: str | None = Field(default=None, pattern=r'^[0-9a-f]{64}$')
