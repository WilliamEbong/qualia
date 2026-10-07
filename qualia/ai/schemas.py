"""Strict provider adapters; failures identify input records without printing responses."""

import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Record(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class CodePrediction(Record):
    code_id: int
    score: float = Field(ge=0, le=1)
    rationale: str = Field(max_length=4000)
    span_start: int = Field(ge=0)
    span_end: int = Field(gt=0)


class Prediction(Record):
    segment_id: str
    codes: list[CodePrediction]


class Predictions(Record):
    predictions: list[Prediction]


class Result(Predictions):
    input_tokens: int = Field(ge=0, le=2**63-1)
    output_tokens: int = Field(ge=0, le=2**63-1)
    cli_version: str = Field(min_length=1, max_length=200)


class OperatorEdit(Record):
    path: str = Field(min_length=1, max_length=240)
    original_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    content: str = Field(max_length=65536)


class OperatorProposal(Record):
    hypothesis: str = Field(min_length=1, max_length=2000)
    edits: list[OperatorEdit] = Field(max_length=16)


class OperatorResult(OperatorProposal):
    input_tokens: int = Field(ge=0, le=2**63-1)
    output_tokens: int = Field(ge=0, le=2**63-1)
    cli_version: str = Field(min_length=1, max_length=200)


Excerpt = Annotated[str, Field(min_length=1, max_length=1000)]


class ProposedCode(Record):
    # Every field is required: strict structured-output providers reject optional properties.
    kind: Literal['new_code', 'revise_code']
    target_code_id: int | None
    name: str = Field(min_length=1, max_length=200)
    definition: str = Field(max_length=2000)
    include: str = Field(max_length=2000)
    exclude: str = Field(max_length=2000)
    examples_pos: list[Excerpt] = Field(max_length=5)
    examples_neg: list[Excerpt] = Field(max_length=5)
    rationale: str = Field(min_length=1, max_length=2000)
    evidence_segment_ids: list[str] = Field(min_length=1, max_length=20)


class CodeProposalSet(Record):
    proposals: list[ProposedCode] = Field(max_length=12)


class CodeProposalResult(CodeProposalSet):
    input_tokens: int = Field(ge=0, le=2**63-1)
    output_tokens: int = Field(ge=0, le=2**63-1)
    cli_version: str = Field(min_length=1, max_length=200)


class Tier(Record):
    backend: str = Field(min_length=1)
    model: str = Field(min_length=1)


class Routing(Record):
    allow_external: bool = False
    backend: str = 'rules'
    model: str = 'rules-v1'
    jev_enabled: bool = False
    segments_per_call: int = Field(default=20, ge=1, le=20)
    max_segment_chars: int = Field(default=4000, ge=1, le=4000)
    daily_calls: int = Field(default=300, ge=0)
    run_segments: int = Field(default=2000, ge=0)
    jev_daily_usd: float = Field(default=1.0, ge=0, allow_inf_nan=False)
    human_review_below: float = Field(default=0.70, ge=0, le=1)
    qc_sample_rate: float = Field(default=0.05, ge=0, le=1)
    max_output_tokens: int = Field(default=8192, ge=1, le=8192)
    max_retries: int = Field(default=0, ge=0, le=2)
    escalate_below: float | None = Field(default=None, ge=0, le=1)
    fake_mode: Literal['first', 'all', 'none'] = 'first'
    tiers: dict[str, Tier] = Field(default_factory=dict)
    tasks: dict[str, Tier] = Field(default_factory=dict)
    # Minimum model-reported score per frozen code ID for a code to become a suggestion.
    code_thresholds: dict[Annotated[str, Field(pattern=r'^[1-9][0-9]*$')],
                          Annotated[float, Field(gt=0, le=1)]] = Field(default_factory=dict)


def routing_config(value: dict) -> dict:
    try:
        return Routing.model_validate(value).model_dump()
    except ValidationError:
        raise ValueError('invalid routing configuration') from None


def response_schema() -> dict:
    return Predictions.model_json_schema()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON property')
        result[key] = value
    return result


class ResponseValidationError(ValueError):
    """Safe diagnostic whose record identity comes from the trusted input batch."""

    def __init__(self, segment_id, reason):
        self.segment_id = segment_id
        super().__init__(f'segment {segment_id}: {reason}')


def validate_result(raw, segments: list[dict], codebook: list[dict]) -> dict:
    first = str(segments[0]['id']) if segments else 'unknown'
    expected = {str(segment['id']): segment['text'] for segment in segments}
    value = None
    def identity_at(index):
        predictions = value.get('predictions') if isinstance(value, dict) else None
        if isinstance(predictions, list) and 0 <= index < len(predictions):
            prediction = predictions[index]
            identity = prediction.get('segment_id') if isinstance(prediction, dict) else None
            if isinstance(identity, str) and identity in expected:
                return identity
        return str(segments[index]['id']) if 0 <= index < len(segments) else first

    try:
        value = json.loads(raw, object_pairs_hook=_unique_object) if isinstance(raw, str) else raw
        result = Result.model_validate(value).model_dump()
    except ValidationError as exc:
        location = exc.errors(include_input=False)[0]['loc']
        identity = identity_at(location[1]) if (len(location) > 1 and
                   location[0] == 'predictions' and type(location[1]) is int) else first
        raise ResponseValidationError(identity, 'invalid provider response') from None
    except (ValueError, TypeError):
        raise ResponseValidationError(first, 'invalid provider response') from None
    if not result['cli_version'].strip():
        raise ResponseValidationError(first, 'missing CLI version')
    codes = {code['id'] for code in codebook if code.get('status', 'active') == 'active'}
    seen = set()
    for index, prediction in enumerate(result['predictions']):
        segment_id = prediction['segment_id']
        if segment_id not in expected:
            raise ResponseValidationError(identity_at(index), 'unexpected provider segment identifier')
        if segment_id in seen:
            raise ResponseValidationError(segment_id, 'duplicate prediction')
        seen.add(segment_id)
        spans = set()
        for code in prediction['codes']:
            if code['code_id'] not in codes:
                raise ResponseValidationError(segment_id, 'unknown or archived code')
            if not 0 <= code['span_start'] < code['span_end'] <= len(expected[segment_id]):
                raise ResponseValidationError(segment_id, 'span outside source text')
            identity = (code['code_id'], code['span_start'], code['span_end'])
            if identity in spans:
                raise ResponseValidationError(segment_id, 'duplicate code span')
            spans.add(identity)
    missing = expected.keys() - seen
    if missing:
        raise ResponseValidationError(next(key for key in expected if key in missing), 'missing prediction')
    return result


class ProposalValidationError(ValueError):
    """Safe diagnostic naming the proposal position, never echoing provider text."""


def validate_proposals(raw, mode: str, segments: list[dict], codes: list[dict],
                       targets: set[int] = frozenset()) -> dict:
    """Reject the whole response unless every proposal is grounded in the supplied text."""
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object) if isinstance(raw, str) else raw
        result = CodeProposalResult.model_validate(value).model_dump()
    except (ValidationError, ValueError, TypeError):
        raise ProposalValidationError('invalid provider response') from None
    texts = {str(segment['id']): segment['text'] for segment in segments}
    names = {code['name'].strip().casefold(): code['id'] for code in codes}
    kind = 'new_code' if mode == 'draft' else 'revise_code'
    for index, proposal in enumerate(result['proposals'], start=1):
        def fail(reason):
            raise ProposalValidationError(f'proposal {index}: {reason}')
        if proposal['kind'] != kind:
            fail(f'{mode} mode accepts only {kind} proposals')
        target = proposal['target_code_id']
        if kind == 'new_code' and target is not None:
            fail('a new code cannot name a target')
        if kind == 'revise_code' and target not in targets:
            fail('revision targets a code that was not supplied')
        if not proposal['name'].strip():
            fail('empty code name')
        owner = names.get(proposal['name'].strip().casefold())
        if owner is not None and owner != target:
            fail('name collides with another code')
        names[proposal['name'].strip().casefold()] = target if target is not None else -index
        if any(identity not in texts for identity in proposal['evidence_segment_ids']):
            fail('evidence names a segment that was not supplied')
        # A revision may keep the researcher's existing examples; anything new must be quoted.
        kept = set()
        for code in codes:
            if code['id'] == target:
                kept = {*json.loads(code['examples_pos']), *json.loads(code['examples_neg'])}
        for example in proposal['examples_pos'] + proposal['examples_neg']:
            if example not in kept and not any(example in text for text in texts.values()):
                fail('example is not a verbatim quotation of a supplied segment')
    return result
