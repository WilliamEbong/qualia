"""Pure policy boundaries use measured metrics, never operator narrative."""

import math

import pytest

from qualia.improve.policy import decide

POLICY = {'primary': 'macro_f1', 'min_delta': .01, 'priority_tolerance': .02,
          'priority_codes': [7], 'challenge_regressions': 0, 'max_call_ratio': 1.2,
          'confirmation_required': True}


def metrics(f1=.60, priority=.70, calls=10):
    return {'macro_f1': f1, 'per_code': [{'code_id': 7, 'f1': priority}], 'calls': calls}


def test_inclusive_boundaries_pass_without_binary_float_rounding_rejections():
    result = decide(metrics(), metrics(.61, .68, 12), POLICY, tests_passed=True)
    assert result['keep'] is True
    assert result['reasons']


@pytest.mark.parametrize('candidate,phrase', [
    (metrics(.609999999, .70, 10), 'gain'),
    (metrics(.70, .679999999, 10), 'priority'),
    (metrics(.70, .70, 13), 'calls'),
])
def test_just_outside_each_boundary_reverts(candidate, phrase):
    result = decide(metrics(), candidate, POLICY, tests_passed=True)
    assert not result['keep']
    assert any(phrase in reason.lower() for reason in result['reasons'])


def test_tests_and_challenge_regressions_cannot_be_overridden_by_gain():
    result = decide(metrics(), metrics(.99), POLICY, tests_passed=False, challenge_regressions=1)
    assert not result['keep']
    assert any('tests' in reason for reason in result['reasons'])
    assert any('challenge' in reason for reason in result['reasons'])


def test_zero_baseline_calls_requires_zero_candidate_calls():
    assert decide(metrics(calls=0), metrics(.7, calls=0), POLICY, tests_passed=True)['keep']
    assert not decide(metrics(calls=0), metrics(.7, calls=1), POLICY, tests_passed=True)['keep']


@pytest.mark.parametrize('value', [None, math.nan, math.inf, -math.inf, True, '0.9', -1, 1.1])
def test_nonfinite_or_invalid_primary_never_keeps(value):
    assert not decide(metrics(), metrics(value), POLICY, tests_passed=True)['keep']
    assert not decide(metrics(value), metrics(.99), POLICY, tests_passed=True)['keep']


@pytest.mark.parametrize('value', [None, math.nan, math.inf, -1, True, 1.5])
def test_invalid_call_counts_never_keep(value):
    assert not decide(metrics(calls=value), metrics(.99), POLICY, tests_passed=True)['keep']
    assert not decide(metrics(), metrics(.99, calls=value), POLICY, tests_passed=True)['keep']


def test_missing_or_ambiguous_priority_metrics_fail_closed():
    for rows in [[], [{'code_id': 7, 'f1': None}], [{'code_id': 7, 'f1': .8}] * 2]:
        assert not decide(metrics(), {**metrics(.9), 'per_code': rows}, POLICY, tests_passed=True)['keep']


@pytest.mark.parametrize('change', [{'min_delta': math.nan}, {'priority_tolerance': -.1},
                                    {'max_call_ratio': math.inf}, {'priority_codes': ['7']},
                                    {'primary': 'operator_claim'}, {'challenge_regressions': 1}])
def test_invalid_or_weakened_policy_is_rejected(change):
    assert not decide(metrics(), metrics(.99), {**POLICY, **change}, tests_passed=True)['keep']


def test_confirmation_is_an_independent_policy_decision():
    assert decide(metrics(), metrics(.7), POLICY, tests_passed=True)['keep']
    assert not decide(metrics(), metrics(.59), POLICY, tests_passed=True)['keep']


def test_unrepresentable_numeric_input_reverts_without_crashing():
    assert not decide(metrics(), metrics(.99, calls=10**1000), POLICY, tests_passed=True)['keep']
