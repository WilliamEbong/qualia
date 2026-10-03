"""Validated, write-once benchmark publication with explicit protected access."""

import hashlib
import json
import os
from contextlib import contextmanager

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from qualia.store.db import canonical
from qualia.workspace import (
    check_manifest,
    extend_manifest,
    manifest_snapshot,
    protected_artifact_path,
    vault_dir,
)

SPLITS = ('dev', 'validation', 'protected')


class BenchmarkRecord(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    segment_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    codes: list[int]
    transcript_id: str = Field(min_length=1)
    coders: list[list[int] | None] | None = None

    @field_validator('segment_id', 'transcript_id', 'text')
    @classmethod
    def nonblank(cls, value):
        if not value.strip() or '\x00' in value:
            raise ValueError('blank or NUL text')
        return value


def _hash(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode('utf-8')).hexdigest()


def _json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def _validate(records_or_bytes, split, code_ids):
    if isinstance(records_or_bytes, bytes):
        raw = records_or_bytes
        try:
            lines = raw.decode('utf-8').splitlines()
        except UnicodeDecodeError:
            raise ValueError(f'{split}.jsonl: line 1: invalid UTF-8') from None
    elif isinstance(records_or_bytes, list):
        try:
            lines = [canonical(record) for record in records_or_bytes]
            raw = ('\n'.join(lines) + '\n').encode('utf-8')
        except (TypeError, ValueError, UnicodeEncodeError):
            raise ValueError(f'{split}.jsonl: line 1: invalid record') from None
    else:
        raise ValueError(f'{split}.jsonl: line 1: expected JSONL bytes or records')
    records, seen = [], set()
    for number, line in enumerate(lines, 1):
        try:
            record = BenchmarkRecord.model_validate(_json(line)).model_dump(exclude_none=True)
            identity = record['segment_id']
            labels = [record['codes'], *(coder for coder in record.get('coders', []) if coder is not None)]
            if identity in seen or any(len(set(values)) != len(values) or not set(values) <= code_ids for values in labels):
                raise ValueError('duplicate record or invalid labels')
            seen.add(identity)
            records.append(record)
        except (ValueError, TypeError, ValidationError):
            raise ValueError(f'{split}.jsonl: line {number}: invalid record, duplicate identity or unknown code') from None
    if not records:
        raise ValueError(f'{split}.jsonl: line 1: benchmark is empty')
    return records, raw


def _read_index(project):
    path = project/'benchmarks/index.json'
    if path.is_symlink() or path.resolve().parent != project.resolve()/'benchmarks':
        raise ValueError('benchmark index path escapes project')
    if not path.exists():
        if (project/'benchmarks/.published').exists():
            raise ValueError('benchmark split index is missing')
        return {'version': 1, 'splits': {}}
    try:
        index = _json(path.read_bytes())
        if index['version'] != 1 or not isinstance(index['splits'], dict) or set(index['splits']) - set(SPLITS):
            raise ValueError('invalid index')
        for value in index['splits'].values():
            if (not isinstance(value['metadata'], dict) or not isinstance(value['segment_hashes'], list)
                    or not isinstance(value['transcript_hashes'], list)):
                raise ValueError('invalid entry')
        return index
    except (OSError, ValueError, KeyError, TypeError):
        raise ValueError('invalid benchmark split index') from None


def _directory(project, split):
    if split == 'protected':
        protected_artifact_path(project, 'benchmarks/protected/metadata.json')
        return protected_artifact_path(project, 'benchmarks/protected/records.jsonl').parent
    root = vault_dir(project)/'benchmarks' if split == 'protected' else project/'benchmarks'
    path = root/split
    expected = vault_dir(project)/'benchmarks' if split == 'protected' else project.resolve()/'benchmarks'
    if (root.resolve() != expected or path.resolve().parent != root.resolve() or path.is_symlink()
            or any((path/name).is_symlink() for name in ('records.jsonl', 'metadata.json'))):
        raise ValueError('benchmark path escapes split root')
    return path


@contextmanager
def _publication_lock(project):
    lock = project/'benchmarks/.import.lock'
    if lock.parent.resolve() != project.resolve()/'benchmarks':
        raise ValueError('benchmark publication path escapes project')
    try:
        handle = lock.open('xb')
    except FileExistsError:
        raise ValueError('benchmark publication is already in progress') from None
    try:
        handle.close()
        yield
    finally:
        lock.unlink()


def import_benchmark(project, records_or_bytes, split, codebook_version_id, code_ids):
    """Validate before publication; an identical import is a no-op, never an overwrite."""
    if split not in SPLITS:
        raise ValueError('unknown benchmark split')
    if type(codebook_version_id) is not int or codebook_version_id < 1:
        raise ValueError('benchmark requires a frozen codebook version')
    if (not isinstance(code_ids, (list, tuple, set)) or not code_ids or
            any(type(code) is not int or code < 1 for code in code_ids)):
        raise ValueError('benchmark requires known code IDs')
    records, raw = _validate(records_or_bytes, split, set(code_ids))
    metadata = {'format_version': 1, 'split': split, 'codebook_version_id': codebook_version_id,
                'code_ids': sorted(set(code_ids)), 'sha256': _hash(raw),
                'counts': {'records': len(records), 'transcripts': len({r['transcript_id'] for r in records})}}
    hashes = {'segment_hashes': sorted({_hash(r['segment_id']) for r in records}),
              'transcript_hashes': sorted({_hash(r['transcript_id']) for r in records})}
    with _publication_lock(project):
        expected_manifest = manifest_snapshot(project) if split == 'protected' else None
        index = _read_index(project)
        if split in index['splits']:
            if index['splits'][split]['metadata'] != metadata:
                raise ValueError(f'{split} benchmark already published with different content')
            if split == 'protected':
                directory = _directory(project, split)
                if (_hash((directory/'records.jsonl').read_bytes()) != metadata['sha256'] or
                        _json((directory/'metadata.json').read_bytes()) != metadata):
                    raise ValueError('protected benchmark metadata or checksum mismatch')
            else:
                load_benchmark(project, split)
            return metadata
        for other in index['splits'].values():
            if set(hashes['transcript_hashes']) & set(other['transcript_hashes']):
                raise ValueError('benchmark transcript overlap across splits')
            if set(hashes['segment_hashes']) & set(other['segment_hashes']):
                raise ValueError('benchmark segment identity overlap across splits')
        directory = _directory(project, split)
        if directory.exists() and any(directory.iterdir()):
            raise ValueError('incomplete benchmark publication; existing files preserved')
        directory.mkdir(parents=True, exist_ok=True)
        # Exclusive writes leave a failed partial publication visible and never replace prior evidence.
        with (directory/'records.jsonl').open('xb') as stream:
            stream.write(raw)
        metadata_bytes = canonical(metadata).encode('utf-8')
        with (directory/'metadata.json').open('xb') as stream:
            stream.write(metadata_bytes)
        if split == 'protected':
            extend_manifest(project, expected_manifest, {
                'vault/benchmarks/protected/records.jsonl': _hash(raw),
                'vault/benchmarks/protected/metadata.json': _hash(metadata_bytes),
            })
        index['splits'][split] = {'metadata': metadata, **hashes}
        temporary = project/'benchmarks/.index-next.json'
        with temporary.open('xb') as stream:
            stream.write(canonical(index).encode('utf-8'))
        os.replace(temporary, project/'benchmarks/index.json')
        (project/'benchmarks/.published').touch(exist_ok=True)
    return metadata


def load_benchmark(project, split='validation', protected=False):
    if split not in SPLITS:
        raise ValueError('unknown benchmark split')
    if split == 'protected':
        if not protected:
            raise ValueError('explicit protected access is required')
        if not check_manifest(project):
            raise ValueError('protected manifest mismatch')
    index = _read_index(project)
    if split not in index['splits']:
        raise ValueError(f'{split} benchmark has not been imported')
    expected = index['splits'][split]
    directory = _directory(project, split)
    try:
        metadata = _json((directory/'metadata.json').read_bytes())
        raw = (directory/'records.jsonl').read_bytes()
    except (OSError, ValueError):
        raise ValueError(f'{split} benchmark files are invalid') from None
    if metadata != expected['metadata']:
        raise ValueError(f'{split} benchmark metadata mismatch')
    if _hash(raw) != metadata['sha256']:
        raise ValueError(f'{split} benchmark checksum mismatch')
    records, _ = _validate(raw, split, set(metadata['code_ids']))
    counts = {'records': len(records), 'transcripts': len({r['transcript_id'] for r in records})}
    if counts != metadata['counts']:
        raise ValueError(f'{split} benchmark counts mismatch')
    if (sorted({_hash(row['segment_id']) for row in records}) != expected['segment_hashes'] or
            sorted({_hash(row['transcript_id']) for row in records}) != expected['transcript_hashes']):
        raise ValueError(f'{split} benchmark identity index mismatch')
    return records, metadata


def split_transcripts(records, seed='qualia-annomi-v1'):
    """Stratified deterministic 60/20/20 allocation, preserving whole transcripts."""
    qualities = {}
    for record in records:
        identity = record['transcript_id']
        quality = record.get('mi_quality', 'all')
        if identity in qualities and qualities[identity] != quality:
            raise ValueError('inconsistent transcript quality')
        qualities[identity] = quality
    assignment = {}
    for quality in sorted(set(qualities.values())):
        identities = sorted((identity for identity in qualities if qualities[identity] == quality),
                            key=lambda identity: (_hash(f'{seed}:{identity}'), identity))
        dev = round(len(identities)*0.6)
        validation = int(len(identities)*0.2)
        for position, identity in enumerate(identities):
            assignment[identity] = 'dev' if position < dev else 'validation' if position < dev+validation else 'protected'
    result = {split: [] for split in SPLITS}
    for record in sorted(records, key=lambda row: (row['transcript_id'], row['segment_id'])):
        result[assignment[record['transcript_id']]].append(record)
    return result
