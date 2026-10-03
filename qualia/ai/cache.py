"""Cache identities include record identity and every effective classification input."""

import hashlib

from qualia.ai.schemas import validate_result
from qualia.store.db import canonical


def cache_key(*, segment, prompt_hash, codebook_version_id, backend, model,
              pipeline_version, task='classification', context_hash='') -> str:
    value = {'segment': segment, 'prompt_hash': prompt_hash, 'codebook_version_id': codebook_version_id,
             'backend': backend, 'model': model, 'pipeline_version': pipeline_version, 'task': task,
             'context_hash': context_hash}
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def load_cached(db, key: str, segment: dict, codebook: list[dict]) -> dict | None:
    row = db.one('SELECT result_json FROM result_cache WHERE key=?', (key,))
    if row:
        try:
            return validate_result(row['result_json'], [segment], codebook)
        except ValueError:
            pass
    return None
