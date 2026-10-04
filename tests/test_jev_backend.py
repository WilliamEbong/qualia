"""Synthetic wire contracts and an explicitly recorded normalized live response."""

import asyncio
import json
import time
from pathlib import Path

import httpx
import pytest

from qualia.ai.backends import jev
from qualia.ai.backends.process import BackendError
from qualia.ai.router import classify_segments
from qualia.ai.schemas import response_schema, validate_result
from qualia.store.db import Store
from qualia.workspace import ROUTING

SEGMENTS = [{'id': 's-1', 'text': 'I feel hopeful 😀.'}]
CODEBOOK = [{'id': 9, 'name': 'Hope', 'definition': 'Explicit hope.', 'status': 'active'}]
CONTEXT = {'model': 'jev-1.13.0', 'prompt': 'Code explicit hope.', 'codebook': CODEBOOK,
           'max_output_tokens': 8192}


def test_recorded_live_normalized_response_matches_application_contract():
    fixture = json.loads((Path(__file__).parent / 'fixtures/jev/live-normalized.json').read_text())
    result = validate_result(fixture['response'], fixture['segments'], fixture['codebook'])
    assert result['predictions'][0]['segment_id'] == 'synthetic-1'
    assert result['input_tokens'] == fixture['usage']['input_tokens']
    assert fixture['usage']['cost_usd'] == pytest.approx(result['input_tokens'] * jev.INPUT_RATE)
    assert fixture['provenance']['kind'] == 'live_normalized_adapter_response'


@pytest.fixture(autouse=True)
def synthetic_key(monkeypatch, tmp_path):
    monkeypatch.setenv('TYPESAFE_API_KEY', 'synthetic-test-key-never-real')
    monkeypatch.setattr(jev, 'ENV_FILE', tmp_path / '.env')


def response_for(request, probability=.9):
    body = json.loads(request.content)
    return {'model': 'jev-1.13.0', 'answers': {
        key: {'type': 'noul', 'noul': probability} for key in body['questions']},
        'usage': {'input_tokens': 120, 'output_tokens': 10}}


def test_request_noul_translation_usage_and_cost():
    calls = []

    def handler(request):
        calls.append(request)
        assert str(request.url) == 'https://api.typesafe.ai/v1/systemone'
        assert request.method == 'POST'
        assert request.headers['authorization'] == 'Bearer synthetic-test-key-never-real'
        payload = json.loads(request.content)
        assert set(payload) == {'state', 'questions', 'model'}
        question = next(iter(payload['questions'].values()))
        assert question['type'] == 'noul' and 'Explicit hope.' in question['instructions']
        assert 's-1' in question['instructions']  # IDs alone are not visible to Jev.
        assert payload['state']['segments'] == SEGMENTS
        return httpx.Response(200, json=response_for(request))

    backend = jev.JevBackend(transport=httpx.MockTransport(handler))
    assert backend.available() and calls == []
    assert backend.estimate_cost(SEGMENTS, CONTEXT) >= 64000 * .042 / 1_000_000
    raw = backend.classify(SEGMENTS, response_schema(), CONTEXT)
    result = validate_result(raw, SEGMENTS, CODEBOOK)
    code = result['predictions'][0]['codes'][0]
    assert code['code_id'] == 9 and code['score'] == .9
    assert code['span_start'] == 0 and code['span_end'] == len(SEGMENTS[0]['text'])
    assert 'whole segment' in code['rationale'].lower()
    assert result['input_tokens'] == 120 and result['output_tokens'] == 10
    assert 'jev-1.13.0' in result['cli_version']
    assert backend.actual_cost(result, CONTEXT) == pytest.approx(120 * .042 / 1_000_000)
    assert len(calls) == 1


@pytest.mark.parametrize('key', ['', 'PASTE_YOUR_ACTUAL_KEY_HERE', 'replace-me', 'x\r\nInjected'])
def test_missing_placeholder_or_malformed_key_never_calls(monkeypatch, key):
    monkeypatch.setenv('TYPESAFE_API_KEY', key)
    calls = []
    backend = jev.JevBackend(transport=httpx.MockTransport(lambda req: calls.append(req)))
    assert not backend.available()
    with pytest.raises(BackendError):
        backend.classify(SEGMENTS, response_schema(), CONTEXT)
    assert calls == []


def test_env_file_read_preserves_file_and_never_executes(monkeypatch):
    monkeypatch.delenv('TYPESAFE_API_KEY')
    body = '# local\nOTHER=$(do not execute)\nTYPESAFE_API_KEY="synthetic-file-key"\n'
    jev.ENV_FILE.write_text(body)
    assert jev.JevBackend().available()
    assert jev.ENV_FILE.read_text() == body
    jev.ENV_FILE.write_text(body + 'TYPESAFE_API_KEY=duplicate\n')
    assert not jev.JevBackend().available()


@pytest.mark.parametrize('status,code', [(401, 'authentication'), (422, 'invalid_input'),
                                       (429, 'rate_limit'), (529, 'transient'),
                                       (302, 'provider_error')])
def test_error_no_internal_retry_no_key_leak(status, code):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, headers={'Location': 'https://untrusted.invalid'},
                              text='synthetic-test-key-never-real research-secret')

    with pytest.raises(BackendError) as caught:
        jev.JevBackend(transport=httpx.MockTransport(handler)).classify(
            SEGMENTS, response_schema(), CONTEXT)
    assert caught.value.code == code and caught.value.segment_id == 's-1'
    assert 'synthetic-test-key' not in str(caught.value) and 'research-secret' not in str(caught.value)
    assert len(calls) == 1


@pytest.mark.parametrize('mutation', ['missing', 'unknown', 'wrong_type', 'bool', 'nan',
                                    'negative_usage', 'wrong_model'])
def test_invalid_response_rejected_and_usage_retained(mutation):
    def handler(request):
        body = response_for(request)
        key = next(iter(body['answers']))
        if mutation == 'missing':
            body['answers'].clear()
        elif mutation == 'unknown':
            body['answers']['unknown'] = body['answers'].pop(key)
        elif mutation == 'wrong_type':
            body['answers'][key]['type'] = 'score'
        elif mutation in ('bool', 'nan'):
            body['answers'][key]['noul'] = True if mutation == 'bool' else float('nan')
        elif mutation == 'negative_usage':
            body['usage']['input_tokens'] = -1
        elif mutation == 'wrong_model':
            body['model'] = 'not-jev'
        return httpx.Response(200, content=json.dumps(body).encode())

    with pytest.raises(BackendError) as caught:
        jev.JevBackend(transport=httpx.MockTransport(handler)).classify(
            SEGMENTS, response_schema(), CONTEXT)
    assert caught.value.code == 'invalid_response'
    if mutation not in ('negative_usage', 'nan'):
        assert caught.value.input_tokens == 120


def test_all_primitives_and_question_mapping():
    questions = {'n': {'type': 'noul', 'instructions': 'Applies?', 'criteria': {'true': 'yes', 'false': 'no'}},
                 'c': {'type': 'choice', 'instructions': 'Choose.', 'criteria': {'yes': 'yes', 'no': 'no'}},
                 's': {'type': 'score', 'instructions': 'Rate.', 'criteria': ['none', 'some', 'much']}}
    answers = {'n': {'type': 'noul', 'noul': .8},
               'c': {'type': 'choice', 'choice': 'yes', 'confidence': .7,
                     'probabilities': {'yes': .9, 'no': .1}},
               's': {'type': 'score', 'score': 1.7, 'confidence': .8,
                     'probabilities': {'0': .1, '1': .1, '2': .8},
                     'legend': {'0': 'none', '1': 'some', '2': 'much'}}}
    assert jev.validate_answers(questions, answers) == answers
    answers['c']['choice'] = 'unknown'
    with pytest.raises(ValueError):
        jev.validate_answers(questions, answers)


@pytest.mark.parametrize('mutation', ['extra_id', 'wrong_level', 'wrong_legend', 'wrong_mean',
                                    'invalid_confidence', 'invalid_sum', 'infinite'])
def test_score_primitive_rejects_invalid_distribution(mutation):
    questions = {'s': {'type': 'score', 'instructions': 'Rate.', 'criteria': ['none', 'much']}}
    answer = {'type': 'score', 'score': .8, 'confidence': .9, 'legend': {'0': 'none', '1': 'much'},
              'probabilities': {'0': .2, '1': .8}}
    answers = {'s': answer}
    if mutation == 'extra_id':
        answers['unknown'] = answer
    elif mutation == 'wrong_level':
        answer['probabilities']['2'] = answer['probabilities'].pop('1')
    elif mutation == 'wrong_legend':
        answer['legend']['0'] = 'different'
    elif mutation == 'wrong_mean':
        answer['score'] = .2
    elif mutation == 'invalid_confidence':
        answer['confidence'] = True
    elif mutation == 'invalid_sum':
        answer['probabilities']['0'] = .9
    elif mutation == 'infinite':
        answer['score'] = float('inf')
    with pytest.raises(ValueError):
        jev.validate_answers(questions, answers)


@pytest.mark.parametrize('config', [{'allow_external': False}, {'jev_enabled': False},
                                   {'daily_calls': 0}, {'jev_daily_usd': 0}])
def test_router_gates_before_jev_http(config):
    calls = []
    backend = jev.JevBackend(transport=httpx.MockTransport(lambda req: calls.append(req)))
    with Store(':memory:') as db:
        result = classify_segments(db, SEGMENTS, CODEBOOK,
            {**ROUTING, 'allow_external': True, 'jev_enabled': True, **config},
            prompt='Synthetic.', codebook_version_id=1, pipeline_version='fixture',
            backend='jev', model='jev-1.13.0', registry={'jev': backend})
        assert result['calls'] == 0 and not calls
        assert not db.rows('SELECT * FROM egress_log')


def test_router_records_actual_cost_and_each_retry():
    calls = []

    def handler(request):
        calls.append(request)
        return (httpx.Response(529) if len(calls) == 1
                else httpx.Response(200, json=response_for(request)))

    backend = jev.JevBackend(transport=httpx.MockTransport(handler))
    with Store(':memory:') as db:
        result = classify_segments(db, SEGMENTS, CODEBOOK,
            {**ROUTING, 'allow_external': True, 'jev_enabled': True, 'max_retries': 1},
            prompt='Synthetic.', codebook_version_id=1, pipeline_version='fixture',
            backend='jev', model='jev-1.13.0', registry={'jev': backend})
        assert result['status'] == 'completed' and result['calls'] == len(calls) == 2
        assert len(db.rows('SELECT * FROM egress_log')) == 2
        rows = db.rows('SELECT * FROM usage_ledger WHERE reservation_id IS NOT NULL ORDER BY id')
        assert [row['status'] for row in rows] == ['error', 'ok']
        assert rows[0]['cost_usd'] == pytest.approx(jev.RESERVED_INPUT_TOKENS * jev.INPUT_RATE)
        assert rows[1]['cost_usd'] == pytest.approx(120 * jev.INPUT_RATE)
        assert not db.rows('SELECT * FROM coding_events')


@pytest.mark.parametrize('mode', ['flood', 'drip', 'delayed_headers'])
def test_stream_deadline_and_byte_ceiling_close_response(mode):
    closed = []

    class Stream(httpx.AsyncByteStream):
        async def __aiter__(self):
            if mode == 'flood':
                yield b'x' * 2048
            else:
                while True:
                    await asyncio.sleep(.02)
                    yield b' '

        async def aclose(self):
            closed.append(True)

    async def handler(request):
        if mode == 'delayed_headers':
            try:
                await asyncio.sleep(20)
            finally:
                closed.append(True)
        return httpx.Response(200, stream=Stream())

    backend = jev.JevBackend(transport=httpx.MockTransport(handler), timeout_seconds=.12,
                             max_response_bytes=1024)
    started = time.monotonic()
    with pytest.raises(BackendError) as caught:
        backend.classify(SEGMENTS, response_schema(), CONTEXT)
    assert caught.value.code == ('output_limit' if mode == 'flood' else 'timeout')
    assert time.monotonic() - started < 2 and closed


@pytest.mark.parametrize('payload', [b'not json secret', b'{"usage":{},"usage":{}}',
                                   b'{"answers":{"x":{"type":"noul","noul":0,"noul":1}}}'])
def test_malformed_and_duplicate_json(payload):
    backend = jev.JevBackend(transport=httpx.MockTransport(
        lambda req: httpx.Response(200, content=payload)))
    with pytest.raises(BackendError, match='invalid_response') as caught:
        backend.classify(SEGMENTS, response_schema(), CONTEXT)
    assert 'secret' not in str(caught.value)


def test_request_limit_rejected_before_reservation():
    codes = [{**CODEBOOK[0], 'id': index + 1} for index in range(257)]
    backend = jev.JevBackend(transport=httpx.MockTransport(lambda req: pytest.fail('unexpected HTTP')))
    with Store(':memory:') as db:
        result = classify_segments(db, SEGMENTS, codes,
            {**ROUTING, 'allow_external': True, 'jev_enabled': True}, prompt='Synthetic.',
            codebook_version_id=1, pipeline_version='fixture', backend='jev', model='jev-1.13.0',
            registry={'jev': backend})
        assert result['calls'] == 0 and not db.rows('SELECT * FROM egress_log')


def test_default_batch_over_request_bound_is_split_not_failed():
    # Demo-shaped load: a 7-code codebook makes 20 segments exceed the 64 KB adapter bound.
    codes = [{**CODEBOOK[0], 'id': index, 'name': f'Code {index}',
              'definition': 'Synthetic definition of a recurring theme. ' * 12} for index in range(1, 8)]
    segments = [{'id': f's-{index}', 'text': 'Synthetic participant sentence. ' * 20}
                for index in range(20)]
    calls = []

    def handler(request):
        calls.append(len(json.loads(request.content)['state']['segments']))
        return httpx.Response(200, json=response_for(request))

    backend = jev.JevBackend(transport=httpx.MockTransport(handler))
    with pytest.raises(ValueError):
        backend.estimate_cost(segments, {**CONTEXT, 'codebook': codes})
    with Store(':memory:') as db:
        result = classify_segments(db, segments, codes,
            {**ROUTING, 'allow_external': True, 'jev_enabled': True}, prompt='Synthetic.',
            codebook_version_id=1, pipeline_version='fixture', backend='jev', model='jev-1.13.0',
            registry={'jev': backend})
        assert result['status'] == 'completed' and result['segments'] == 20
        assert len(calls) >= 2 and sum(calls) == 20 and result['calls'] == len(calls)
        assert len(db.rows('SELECT * FROM egress_log')) == len(calls)


def test_rejected_http_response_does_not_log_key_or_body(caplog):
    caplog.set_level('DEBUG')
    backend = jev.JevBackend(transport=httpx.MockTransport(lambda request: httpx.Response(
        401, text='synthetic-test-key-never-real private research content')))
    with pytest.raises(BackendError):
        backend.classify(SEGMENTS, response_schema(), CONTEXT)
    assert 'synthetic-test-key-never-real' not in caplog.text
    assert 'private research content' not in caplog.text


@pytest.mark.parametrize('scenario,expected', [('allowed', 'completed'), ('disabled', 'blocked'),
    ('external_off', 'blocked'), ('zero_calls', 'budget_reached'), ('zero_usd', 'budget_reached'),
    ('missing_key', 'unavailable')])
def test_default_registry_jev_policy_integration(monkeypatch, scenario, expected):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=response_for(request))

    backend = jev.JevBackend(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(jev, 'JevBackend', lambda: backend)
    if scenario == 'missing_key':
        monkeypatch.delenv('TYPESAFE_API_KEY')
    overrides = {'disabled': {'jev_enabled': False}, 'external_off': {'allow_external': False},
                 'zero_calls': {'daily_calls': 0}, 'zero_usd': {'jev_daily_usd': 0}}
    with Store(':memory:') as db:
        result = classify_segments(db, SEGMENTS, CODEBOOK,
            {**ROUTING, 'allow_external': True, 'jev_enabled': True, **overrides.get(scenario, {})},
            prompt='Synthetic.', codebook_version_id=1, pipeline_version='fixture', backend='jev')
        assert result['status'] == expected and result['model'] == jev.MODEL
        count = int(scenario == 'allowed')
        assert result['calls'] == len(calls) == count
        assert len(db.rows('SELECT * FROM egress_log')) == count
        assert not db.rows('SELECT * FROM coding_events')


def test_default_registry_retry_accounting_and_error_sanitization(monkeypatch):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(529, text='synthetic-test-key-never-real private-response')

    backend = jev.JevBackend(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(jev, 'JevBackend', lambda: backend)
    with Store(':memory:') as db:
        result = classify_segments(db, SEGMENTS, CODEBOOK,
            {**ROUTING, 'allow_external': True, 'jev_enabled': True, 'max_retries': 1},
            prompt='Synthetic.', codebook_version_id=1, pipeline_version='fixture', backend='jev')
        assert result['status'] == 'error' and result['calls'] == len(calls) == 2
        assert len(db.rows('SELECT * FROM egress_log')) == 2
        rows = db.rows('SELECT * FROM usage_ledger WHERE reservation_id IS NOT NULL')
        assert len(rows) == 2 and all(row['status'] == 'error' for row in rows)
        serialized = json.dumps({'result': result, 'rows': rows})
        assert 'synthetic-test-key-never-real' not in serialized
        assert 'private-response' not in serialized
