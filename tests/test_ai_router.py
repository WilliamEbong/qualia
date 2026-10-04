import json

import pytest

from qualia.ai.backends.fake import FakeBackend
from qualia.ai.router import classify_project, classify_segments
from qualia.io.imports import import_text
from qualia.store.db import Store
from qualia.workspace import ROUTING, init_project


class CountingBackend(FakeBackend):
    name = 'fixture'

    def __init__(self, *, external=False, failures=0):
        self.external = external
        self.calls = 0
        self.failures = failures

    def classify(self, segments, schema, context):
        self.calls += 1
        if self.calls <= self.failures:
            error = ValueError('RAW_SECRET_PROVIDER_BODY')
            error.code = 'timeout'
            raise error
        return super().classify(segments, schema, context)


def run(db, backend, *, text='Synthetic.', config=None, persist=False):
    return classify_segments(db, [{'id': 's1', 'text': text}],
                             [{'id': 1, 'name': 'Synthetic', 'status': 'active'}],
                             {**ROUTING, **(config or {})}, prompt='Classify synthetic content.',
                             codebook_version_id=1, pipeline_version='pipeline',
                             backend='fixture', model='fixture-v1', run_id='run', persist=persist,
                             registry={'fixture': backend})


@pytest.mark.parametrize('config,status', [({'daily_calls': 0}, 'budget_reached'),
                                            ({'run_segments': 0}, 'budget_reached'),
                                            ({'allow_external': False}, 'blocked')])
def test_pre_call_gates_make_zero_calls(config, status):
    backend = CountingBackend(external=status == 'blocked')
    with Store(':memory:') as db:
        result = run(db, backend, config=config)
        assert result['status'] == status
        assert backend.calls == result['calls'] == 0
        assert not db.rows('SELECT * FROM usage_ledger')
        assert not db.rows('SELECT * FROM egress_log')


def test_long_segment_rejected_without_truncation_or_call():
    backend = CountingBackend()
    with Store(':memory:') as db:
        result = run(db, backend, text='x'*10000)
        assert result['status'] == 'error' and 's1' in result['errors'][0]
        assert backend.calls == 0


def test_batches_shrink_to_what_the_provider_admits():
    class Bounded(CountingBackend):
        sizes = []

        def estimate_cost(self, segments, context):
            if len(segments) > 3:
                raise ValueError('request exceeds local size bound')
            return 0.0

        def classify(self, segments, schema, context):
            self.sizes.append(len(segments))
            return super().classify(segments, schema, context)

    backend = Bounded()
    segments = [{'id': f's{index}', 'text': 'Synthetic.'} for index in range(8)]
    with Store(':memory:') as db:
        result = classify_segments(db, segments, [{'id': 1, 'name': 'Synthetic', 'status': 'active'}],
                                   dict(ROUTING), prompt='Classify synthetic content.',
                                   codebook_version_id=1, pipeline_version='pipeline',
                                   backend='fixture', model='fixture-v1', registry={'fixture': backend})
    assert result['status'] == 'completed' and result['segments'] == 8
    assert backend.sizes == [3, 3, 2] and result['calls'] == 3


def test_retry_has_separate_reservation_egress_and_sanitized_error():
    backend = CountingBackend(external=True, failures=1)
    with Store(':memory:') as db:
        result = run(db, backend, config={'allow_external': True, 'max_retries': 1})
        assert result['status'] == 'completed'
        assert result['calls'] == backend.calls == 2
        assert len(db.rows('SELECT * FROM egress_log')) == 2
        assert [r['status'] for r in db.rows("SELECT status FROM usage_ledger WHERE reservation_id IS NOT NULL ORDER BY id")] == ['error', 'ok']
        assert 'RAW_SECRET' not in json.dumps(result)


@pytest.mark.parametrize('name', ['claude', 'codex'])
def test_native_invocations_are_small_pre_reserved_and_not_retried(name):
    class NativeFixture(CountingBackend):
        def classify(self, segments, schema, context):
            assert len(segments) <= 5
            assert len(db.rows("SELECT * FROM usage_ledger WHERE status='reserved'")) == self.calls + 1
            assert len(db.rows('SELECT * FROM egress_log')) == self.calls + 1
            return super().classify(segments, schema, context)

    provider = NativeFixture(external=True)
    provider.name = name
    segments = [{'id': str(i), 'text': f'Synthetic {i}.'} for i in range(6)]
    with Store(':memory:') as db:
        result = classify_segments(db, segments, [{'id': 1, 'name': 'Synthetic'}],
            {**ROUTING, 'allow_external': True, 'segments_per_call': 20, 'max_retries': 2},
            prompt='Synthetic.', codebook_version_id=1, pipeline_version='native-policy',
            backend=name, model='synthetic', registry={name: provider})
        assert result['status'] == 'completed'
        assert result['calls'] == provider.calls == 2
        assert [row['purpose'] for row in db.rows('SELECT * FROM egress_log')] == [
            'classification:cli_invocation', 'classification:cli_invocation']

    provider = NativeFixture(external=True, failures=1)
    provider.name = name
    with Store(':memory:') as db:
        result = classify_segments(db, segments[:1], [{'id': 1, 'name': 'Synthetic'}],
            {**ROUTING, 'allow_external': True, 'max_retries': 2},
            prompt='Synthetic.', codebook_version_id=1, pipeline_version='native-policy',
            backend=name, model='synthetic', registry={name: provider})
        assert result['status'] == 'error'
        assert result['calls'] == provider.calls == 1
        assert db.rows("SELECT * FROM usage_ledger WHERE status='error'")


def test_subscription_signin_failure_is_actionable_without_account_details():
    from qualia.ai.backends.process import BackendError

    class WrongLogin(CountingBackend):
        def classify(self, segments, schema, context):
            raise BackendError('subscription_auth_required', segments[0]['id'],
                               cli_version='2.1.284')

    with Store(':memory:') as db:
        result = run(db, WrongLogin(external=True), config={'allow_external': True})
        assert result['status'] == 'error'
        assert result['errors'] == ['segment s1: classification failed (subscription_auth_required)']
        assert db.one("SELECT cli_version FROM usage_ledger WHERE status='error'")['cli_version'] == '2.1.284'


def test_retry_respects_budget_and_evaluation_never_writes_coding():
    backend = CountingBackend(external=True, failures=1)
    with Store(':memory:') as db:
        result = run(db, backend, config={'allow_external': True, 'max_retries': 2, 'daily_calls': 1})
        assert result['status'] == 'budget_reached'
        assert result['calls'] == backend.calls == 1
        assert db.rows('SELECT * FROM coding_events') == []


def test_project_suggestions_cache_and_review_triggers(tmp_path):
    project = init_project('study', tmp_path)
    config = {**ROUTING, 'qc_sample_rate': 1.0}
    (project/'config/routing.yaml').write_text(json.dumps(config))
    with Store(project/'project.db') as db:
        import_text(db, project, 'synthetic', 'First.\n\nSecond.', 'txt')
        db.save_code({'name': 'Synthetic'})
        db.freeze_codebook()
        first = classify_project(db, project, backend='fake', run_id='stable-run')
        assert first['model'] == 'fake-v1'
        assert first['segments'] == 2 and first['calls'] == 1
        rows = db.rows('SELECT * FROM pending_suggestions')
        assert len(rows) == 2
        assert all(json.loads(r['review_trigger']) == ['below_threshold', 'qc_sample'] for r in rows)
        second = classify_project(db, project, backend='fake', run_id='stable-run')
        assert second['calls'] == 0 and second['cache_hits'] == 2
        assert len(db.rows("SELECT * FROM usage_ledger WHERE status='reserved'")) == 1


def test_explicit_escalation_uses_actual_disagreement_only():
    primary = CountingBackend()
    secondary = CountingBackend()
    with Store(':memory:') as db:
        config = {**ROUTING, 'escalate_below': 0.7,
                  'tiers': {'strong': {'backend': 'strong', 'model': 'strong-v1'}}}
        result = classify_segments(db, [{'id': 's1', 'text': 'Synthetic.'}],
                                   [{'id': 1, 'status': 'active'}, {'id': 2, 'status': 'active'}],
                                   config, prompt='Classify', codebook_version_id=1,
                                   pipeline_version='pipeline', backend='fixture', model='fixture-v1',
                                   registry={'fixture': primary, 'strong': secondary})
        assert result['calls'] == 2 and result['status'] == 'completed'
        assert db.rows('SELECT * FROM coding_events') == []


def test_cache_requires_same_complete_batch_context():
    class ContextBackend(CountingBackend):
        def classify(self, segments, schema, context):
            result = super().classify(segments, schema, context)
            for prediction in result['predictions']:
                prediction['codes'][0]['rationale'] = f'Batch size {len(segments)}'
            return result

    provider = ContextBackend()
    def invoke(db, segments):
        return classify_segments(db, segments, [{'id': 1}], ROUTING, prompt='Classify',
                                 codebook_version_id=1, pipeline_version='pipeline',
                                 backend='fixture', registry={'fixture': provider})
    with Store(':memory:') as db:
        pair = [{'id': 's1', 'text': 'First'}, {'id': 's2', 'text': 'Second'}]
        assert invoke(db, pair)['calls'] == 1
        single = invoke(db, pair[:1])
        assert single['calls'] == 1 and single['cache_hits'] == 0
        assert single['predictions'][0]['codes'][0]['rationale'] == 'Batch size 1'
        assert invoke(db, pair)['cache_hits'] == 2


@pytest.mark.parametrize('failure', ['unknown_code', 'bad_score', 'unknown_segment'])
def test_second_invalid_record_identifies_trusted_second_input(failure):
    class InvalidBackend(CountingBackend):
        def classify(self, segments, schema, context):
            result = super().classify(segments, schema, context)
            prediction = result['predictions'][1]
            if failure == 'unknown_code':
                prediction['codes'][0]['code_id'] = 999
            elif failure == 'bad_score':
                prediction['codes'][0]['score'] = 'RAW_SECRET'
            else:
                prediction['segment_id'] = 'RAW_SECRET'
            result['input_tokens'] = 19
            return result

    with Store(':memory:') as db:
        result = classify_segments(db, [{'id': 's1', 'text': 'First'}, {'id': 's2', 'text': 'Second'}],
                                   [{'id': 1}], ROUTING, prompt='Classify', codebook_version_id=1,
                                   pipeline_version='pipeline', backend='fixture',
                                   registry={'fixture': InvalidBackend()})
        assert result['status'] == 'error' and 'segment s2:' in result['errors'][0]
        assert 'RAW_SECRET' not in json.dumps(result)
        assert not db.rows('SELECT * FROM coding_events')
        assert db.one("SELECT input_tokens FROM usage_ledger WHERE status='error'")['input_tokens'] == 19


@pytest.mark.parametrize('config', [{'segments_per_call': 21}, {'max_segment_chars': 4001},
                                   {'max_output_tokens': 8193}])
def test_unsupported_limits_fail_before_reservation(config):
    with Store(':memory:') as db:
        provider = CountingBackend()
        with pytest.raises(ValueError, match='routing configuration'):
            run(db, provider, config=config)
        assert provider.calls == 0 and not db.rows('SELECT * FROM usage_ledger')


def test_unavailable_route_and_complete_input_budget_make_no_new_calls():
    provider = CountingBackend()
    with Store(':memory:') as db:
        provider.available = lambda: False
        assert run(db, provider)['status'] == 'unavailable'
        assert not db.rows('SELECT * FROM usage_ledger')
        provider.available = lambda: True
        assert run(db, provider, config={'run_segments': 1})['calls'] == 1
        result = run(db, provider, config={'run_segments': 1})
        assert result['status'] == 'budget_reached'
        assert result['cache_hits'] == result['calls'] == 0


def test_observed_over_limit_tokens_are_recorded_but_predictions_rejected():
    class TokenBackend(CountingBackend):
        def classify(self, segments, schema, context):
            result = super().classify(segments, schema, context)
            result['output_tokens'] = 8193
            return result
    with Store(':memory:') as db:
        result = run(db, TokenBackend())
        assert result['status'] == 'error' and result['predictions'] == []
        assert db.one("SELECT output_tokens FROM usage_ledger WHERE status='error'")['output_tokens'] == 8193
        assert not db.rows('SELECT * FROM result_cache')


def test_changed_fake_mode_invalidates_cache_even_with_same_pipeline_label():
    provider = CountingBackend()
    with Store(':memory:') as db:
        assert run(db, provider)['predictions'][0]['codes']
        result = run(db, provider, config={'fake_mode': 'none'})
        assert result['calls'] == 1 and not result['predictions'][0]['codes']


def test_task_and_tier_selectors_keep_actual_model_identity():
    provider = CountingBackend()
    with Store(':memory:') as db:
        config = {**ROUTING, 'tasks': {'evaluation': {'backend': 'fixture', 'model': 'task-model'}},
                  'tiers': {'cheap': {'backend': 'fixture', 'model': 'tier-model'}}}
        def invoke(**changes):
            return classify_segments(db, [{'id': 's1', 'text': 'Synthetic'}], [{'id': 1}], config,
                                     prompt='Classify', codebook_version_id=1, pipeline_version='pipeline',
                                     registry={'fixture': provider}, **changes)
        assert invoke(task='evaluation')['model'] == 'task-model'
        assert invoke(backend='cheap')['model'] == 'tier-model'
        assert invoke(backend='cheap', model='explicit')['model'] == 'explicit'


@pytest.mark.parametrize('disagree', [True, False])
def test_review_reasons_use_actual_disagreement_and_zero_qc(tmp_path, disagree):
    class StrongBackend(CountingBackend):
        name = 'strong'
        def classify(self, segments, schema, context):
            result = super().classify(segments, schema, context)
            for prediction in result['predictions']:
                prediction['codes'][0]['score'] = 0.95
                if disagree:
                    prediction['codes'][0]['code_id'] = context['codebook'][1]['id']
            return result

    project = init_project('study', tmp_path)
    config = {**ROUTING, 'qc_sample_rate': 0.0, 'escalate_below': 0.7,
              'tiers': {'strong': {'backend': 'strong', 'model': 'strong-v1'}}}
    (project/'config/routing.yaml').write_text(json.dumps(config))
    with Store(project/'project.db') as db:
        import_text(db, project, 'synthetic', 'Synthetic text', 'txt')
        db.save_code({'name': 'First'})
        db.save_code({'name': 'Second'})
        db.freeze_codebook()
        result = classify_project(db, project, backend='fixture',
                                  registry={'fixture': CountingBackend(), 'strong': StrongBackend()})
        assert result['calls'] == 2
        suggestion = db.one('SELECT * FROM pending_suggestions')
        assert json.loads(suggestion['review_trigger']) == (['disagreement'] if disagree else [])
        assert suggestion['backend'] == 'strong' and suggestion['model'] == 'strong-v1'
        assert suggestion['score'] == 0.95


def test_partial_batch_failure_preserves_only_validated_outputs():
    class LaterFailure(CountingBackend):
        def classify(self, segments, schema, context):
            result = super().classify(segments, schema, context)
            if self.calls == 2:
                result['predictions'][0]['codes'][0]['span_end'] = 999
            return result
    provider = LaterFailure()
    with Store(':memory:') as db:
        result = classify_segments(db, [{'id': 's1', 'text': 'First'}, {'id': 's2', 'text': 'Second'}],
                                   [{'id': 1}], {**ROUTING, 'segments_per_call': 1}, prompt='Classify',
                                   codebook_version_id=1, pipeline_version='pipeline', backend='fixture',
                                   registry={'fixture': provider})
        assert result['status'] == 'partial' and result['calls'] == 2
        assert [prediction['segment_id'] for prediction in result['predictions']] == ['s1']
        assert 'segment s2:' in result['errors'][0] and 'invalid_response' in result['errors'][0]
        assert len(db.rows('SELECT * FROM result_cache')) == 1


def test_one_poisoned_cache_entry_refreshes_whole_batch():
    provider = CountingBackend()
    with Store(':memory:') as db:
        def invoke():
            return classify_segments(db, [{'id': 's1', 'text': 'First'}, {'id': 's2', 'text': 'Second'}],
                                     [{'id': 1}], ROUTING, prompt='Classify', codebook_version_id=1,
                                     pipeline_version='pipeline', backend='fixture',
                                     registry={'fixture': provider})
        assert invoke()['calls'] == 1
        key = db.one('SELECT key FROM result_cache ORDER BY key LIMIT 1')['key']
        db.cache_put(key, {'injected': 'RAW_SECRET'})
        refreshed = invoke()
        assert refreshed['calls'] == 1 and refreshed['cache_hits'] == 0
        assert refreshed['segments'] == 2
        assert invoke()['cache_hits'] == 2


class Scored(CountingBackend):
    """Emits every code with a fixed score, like a probability backend."""
    scores = {1: .9, 2: .4, 3: .6}

    def classify(self, segments, schema, context):
        self.calls += 1
        return {'predictions': [{'segment_id': segment['id'], 'codes': [
            {'code_id': code, 'score': score, 'rationale': 'Synthetic.', 'span_start': 0,
             'span_end': len(segment['text'])} for code, score in self.scores.items()]}
            for segment in segments], 'input_tokens': 0, 'output_tokens': 0, 'cli_version': 'scored-v1'}


THREE = [{'id': code, 'name': f'Code {code}', 'status': 'active'} for code in (1, 2, 3)]


def scored_run(db, registry, config=None, **options):
    return classify_segments(db, [{'id': 's1', 'text': 'Synthetic.'}], THREE, {**ROUTING, **(config or {})},
                             prompt='Classify', codebook_version_id=1, pipeline_version='pipeline',
                             backend='fixture', model='fixture-v1', registry=registry, **options)


def assigned(result):
    return [code['code_id'] for code in result['predictions'][0]['codes']]


def test_code_thresholds_apply_to_fresh_and_cached_results():
    backend = Scored()
    with Store(':memory:') as db:
        plain = scored_run(db, {'fixture': backend})
        assert assigned(plain) == [1, 2, 3] and 'candidates' not in plain  # no threshold: keep all
        cached = scored_run(db, {'fixture': backend}, {'code_thresholds': {'2': .3, '3': .7}})
        assert cached['cache_hits'] == 1 and backend.calls == 1
        assert assigned(cached) == [1, 2]
        raw = scored_run(db, {'fixture': backend}, {'code_thresholds': {'3': .7}}, with_candidates=True)
        assert assigned(raw) == [1, 2]
        assert [code['code_id'] for code in raw['candidates'][0]['codes']] == [1, 2, 3]


def test_backend_default_threshold_applies_until_a_code_overrides_it():
    class Probabilistic(Scored):
        default_threshold = .5

    with Store(':memory:') as db:
        assert assigned(scored_run(db, {'fixture': Probabilistic()})) == [1, 3]
        assert assigned(scored_run(db, {'fixture': Probabilistic()}, {'code_thresholds': {'2': .3}})) == [1, 2, 3]


def test_escalation_reads_thresholded_codes():
    class Probabilistic(Scored):
        default_threshold = .5

    tiers = {'escalate_below': .7, 'tiers': {'strong': {'backend': 'strong', 'model': 'strong-v1'}}}
    for thresholds, escalated in (({}, 1), ({'3': .65}, 0)):
        strong = CountingBackend()
        with Store(':memory:') as db:
            result = scored_run(db, {'fixture': Probabilistic(), 'strong': strong},
                                {**tiers, 'code_thresholds': thresholds})
        assert result['escalated_segments'] == strong.calls == escalated


def test_thresholds_filter_persisted_suggestions(tmp_path):
    project = init_project('thresholds', tmp_path)
    with Store(project/'project.db') as db:
        import_text(db, project, 'synthetic', 'First.', 'txt')
        first = db.save_code({'name': 'First'})
        second = db.save_code({'name': 'Second'})
        db.freeze_codebook()
        (project/'config/routing.yaml').write_text(json.dumps(
            {**ROUTING, 'fake_mode': 'all', 'code_thresholds': {str(second): .7}}))
        classify_project(db, project, backend='fake')
        assert [row['code_id'] for row in db.rows('SELECT code_id FROM pending_suggestions')] == [first]
