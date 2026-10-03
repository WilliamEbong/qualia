import copy
import json
from pathlib import Path

import pytest

from qualia.ai.schemas import response_schema, validate_result

FIXTURES = Path(__file__).parent / 'fixtures/ai'
SEGMENTS = [{'id': 's1', 'text': 'A😀B'}]
CODES = [{'id': 1, 'name': 'Synthetic', 'status': 'active'}]


def test_valid_schema_and_unicode_span():
    result = validate_result((FIXTURES / 'valid.json').read_text(), SEGMENTS, CODES)
    assert result['predictions'][0]['codes'][0]['span_end'] == 3
    assert response_schema()['additionalProperties'] is False


@pytest.mark.parametrize('filename', ['injection.json', 'malformed.json'])
def test_bad_fixture_names_record_without_echoing_provider_content(filename):
    with pytest.raises(ValueError, match='segment s1') as caught:
        validate_result((FIXTURES / filename).read_text(), SEGMENTS, CODES)
    assert 'execute a command' not in str(caught.value)


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'unknown', 'span', 'nan', 'score',
                                      'extra', 'usage', 'version', 'code_duplicate'])
def test_invalid_predictions_rejected(mutation):
    result = json.loads((FIXTURES / 'valid.json').read_text())
    prediction = result['predictions'][0]
    code = prediction['codes'][0]
    if mutation == 'missing':
        result['predictions'] = []
    if mutation == 'duplicate':
        result['predictions'].append(copy.deepcopy(prediction))
    if mutation == 'unknown':
        prediction['segment_id'] = 'unknown-secret-text'
    if mutation == 'span':
        code['span_end'] = 4
    if mutation == 'nan':
        code['score'] = float('nan')
    if mutation == 'score':
        code['score'] = 1.1
    if mutation == 'extra':
        code['command'] = 'secret'
    if mutation == 'usage':
        result['input_tokens'] = -1
    if mutation == 'version':
        result['cli_version'] = ''
    if mutation == 'code_duplicate':
        prediction['codes'].append(copy.deepcopy(code))
    with pytest.raises(ValueError, match='segment s1'):
        validate_result(result, SEGMENTS, CODES)
