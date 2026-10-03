"""UTF-8 text and explicit CSV mapping, validated before any database writes."""

import csv
import io

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from qualia.core.segmentation import segment_text
from qualia.workspace import read_config


class SourceRecord(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    name: str = Field(min_length=1)
    text: str = Field(min_length=1)
    case: str | None = None
    speaker: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)

    @field_validator('name', 'text')
    @classmethod
    def nonempty(cls, value: str) -> str:
        if not value.strip() or '\x00' in value:
            raise ValueError('must contain nonblank text without NUL characters')
        return value


def _record(context: str, values: dict, method: str) -> dict:
    try:
        record = SourceRecord.model_validate(values).model_dump()
    except ValidationError as exc:
        fields = ', '.join('.'.join(map(str, error['loc'])) for error in exc.errors())
        raise ValueError(f'{context}: invalid {fields}') from None
    record['segments'] = segment_text(record['text'], method, record['speaker'])
    if not record['segments']:
        raise ValueError(f'{context}: no nonempty segments')
    return record


def import_text(db, project, name, content, format, text_column='text', case_column='case',
                speaker_column='speaker', attribute_columns=None, version_of=None) -> dict:
    """Validate the entire file, then atomically insert or deduplicate its source records."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError('import filename is required')
    if format not in ('txt', 'md', 'csv'):
        raise ValueError(f'{name}: unsupported import format')
    if isinstance(content, bytes):
        try:
            content = content.decode('utf-8-sig')
        except UnicodeDecodeError:
            raise ValueError(f'{name}: invalid UTF-8') from None
    if not isinstance(content, str):
        raise ValueError(f'{name}: content must be UTF-8 text')
    try:
        content.encode('utf-8')
    except UnicodeEncodeError:
        raise ValueError(f'{name}: invalid UTF-8') from None
    method = read_config(project, 'segmentation.yaml').get('method', 'paragraph')
    records = []
    if format != 'csv':
        records.append(_record(name, {'name': name, 'text': content}, method))
    else:
        attributes = attribute_columns or []
        if not isinstance(attributes, list) or any(not isinstance(v, str) for v in attributes):
            raise ValueError(f'{name}: attribute columns must be a list of names')
        reader = csv.DictReader(io.StringIO(content, newline=''), strict=True)
        try:
            columns = reader.fieldnames or []
            if (not columns or len(set(columns)) != len(columns) or any(not c for c in columns)
                    or text_column not in columns or any(c not in columns for c in attributes)):
                raise ValueError(f'{name}: row 1: invalid or missing mapped CSV columns')
            for row in reader:
                context = f'{name}: row {reader.line_num}'
                if None in row or any(value is None for value in row.values()):
                    raise ValueError(f'{context}: malformed CSV column count')
                records.append(_record(context, {
                    'name': context, 'text': row[text_column],
                    'case': (row.get(case_column) or '').strip() or None,
                    'speaker': (row.get(speaker_column) or '').strip() or None,
                    'attributes': {key: row[key] for key in attributes},
                }, method))
        except csv.Error:
            raise ValueError(f'{name}: row {reader.line_num}: malformed CSV') from None
        if not records:
            raise ValueError(f'{name}: CSV contains no records')
    return db.import_sources(records, version_of=version_of)
