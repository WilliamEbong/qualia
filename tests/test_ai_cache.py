import copy

from qualia.ai.cache import cache_key, load_cached
from qualia.ai.schemas import validate_result
from qualia.store.db import Store


def test_every_semantic_cache_component_changes_key():
    arguments = dict(segment={'id': 's1', 'text': 'Synthetic'}, prompt_hash='prompt',
                     codebook_version_id=1, backend='fake', model='fake-v1',
                     pipeline_version='pipeline', task='classification')
    original = cache_key(**arguments)
    for field, value in [('segment', {'id': 's1', 'text': 'Changed'}),
                         ('segment', {'id': 's2', 'text': 'Synthetic'}), ('prompt_hash', 'other'),
                         ('codebook_version_id', 2), ('backend', 'rules'), ('model', 'other'),
                         ('pipeline_version', 'candidate'), ('task', 'evaluation'),
                         ('context_hash', 'different-batch')]:
        assert cache_key(**{**arguments, field: value}) != original


def test_poisoned_cache_is_ignored_and_replaceable():
    segment = {'id': 's1', 'text': 'Synthetic'}
    codes = [{'id': 1, 'status': 'active'}]
    result = {'predictions': [{'segment_id': 's1', 'codes': []}], 'input_tokens': 0,
              'output_tokens': 0, 'cli_version': 'fixture'}
    with Store(':memory:') as db:
        poisoned = copy.deepcopy(result)
        poisoned['predictions'][0]['segment_id'] = 'wrong'
        db.cache_put('key', poisoned)
        assert load_cached(db, 'key', segment, codes) is None
        db.cache_put('key', validate_result(result, [segment], codes))
        assert load_cached(db, 'key', segment, codes) == {**result, 'model_version': None}
