"""Hand-derived metrics fix denominators, absent labels and calibration units."""

import math

import pytest

from qualia.eval.calibration import expected_calibration_error
from qualia.eval.metrics import evaluate_metrics


def reference(identity, codes, **extra):
    return {'segment_id': identity, 'text': 'Synthetic text', 'transcript_id': identity,
            'codes': codes, **extra}


def prediction(identity, codes):
    return {'segment_id': identity, 'codes': [{'code_id': code, 'score': score,
            'span_start': 0, 'span_end': 1, 'rationale': 'Synthetic'} for code, score in codes]}


def test_hand_computed_multilabel_full_codebook_and_resources():
    records = [reference('a', [1, 2]), reference('b', [2]), reference('c', [])]
    predictions = [prediction('c', []), prediction('a', [(1, .2), (1, .8)]),
                   prediction('b', [(1, .6), (2, 1.0)])]
    result = evaluate_metrics(records, predictions, [2, 1, 3], calls=2,
                              latency_ms=123, escalated_segments=1)
    assert result['per_code'] == [
        {'code_id': 2, 'precision': 1., 'recall': .5, 'f1': 2/3, 'support': 2},
        {'code_id': 1, 'precision': .5, 'recall': 1., 'f1': 2/3, 'support': 1},
        {'code_id': 3, 'precision': 0., 'recall': 0., 'f1': 0., 'support': 0},
    ]
    assert result['macro_f1'] == pytest.approx(4/9)
    assert result['micro_f1'] == pytest.approx(2/3)
    assert result['exact_match'] == pytest.approx(1/3)
    assert result['partial_match'] == pytest.approx(2/3)
    assert result['kappa'] == pytest.approx(1/7)
    assert result['alpha'] == pytest.approx(3/13)
    assert result['alpha_basis'] == 'reference_vs_prediction'
    assert result['ece'] == pytest.approx(4/15)
    assert result['scored_prediction_count'] == 3  # repeated spans count once, highest score wins
    assert result['escalation_rate'] == pytest.approx(1/3)
    assert result['calls_per_1000'] == pytest.approx(2000/3)
    assert result['latency_ms'] == 123


def test_empty_and_degenerate_agreement_are_not_reported_as_zero_accuracy():
    result = evaluate_metrics([], [], [1])
    for key in ('macro_f1', 'micro_f1', 'exact_match', 'partial_match', 'kappa', 'alpha',
                'ece', 'escalation_rate', 'calls_per_1000'):
        assert result[key] is None
    assert result['per_code'][0]['support'] == 0
    assert result['per_code'][0]['f1'] is None
    result = evaluate_metrics([reference('a', [])], [prediction('a', [])], [1])
    assert result['exact_match'] == result['partial_match'] == 1
    assert result['micro_f1'] == 0
    assert result['kappa'] is result['alpha'] is result['ece'] is None


def test_single_code_uses_positive_class_not_binary_accuracy():
    result = evaluate_metrics([reference('a', [7]), reference('b', [])],
                              [prediction('a', []), prediction('b', [])], [7])
    assert result['micro_f1'] == 0
    assert result['exact_match'] == .5


def test_calibration_boundaries_and_unscored_predictions():
    result = expected_calibration_error([0, .1, .999, 1], [False, True, True, True])
    assert [entry['count'] for entry in result['bins']] == [1, 1, 0, 0, 0, 0, 0, 0, 0, 2]
    assert result['ece'] == pytest.approx(.901/4)
    assert expected_calibration_error([], [])['ece'] is None
    result = evaluate_metrics([reference('a', [1])], [prediction('a', [(1, None)])], [1])
    assert result['micro_f1'] == 1 and result['ece'] is None


def test_human_coder_alpha_is_separate_from_model_comparison():
    records = [reference('a', [1], coders=[[1], [1]]), reference('b', [2], coders=[[2], [2]])]
    result = evaluate_metrics(records, [prediction('a', [(2, .8)]), prediction('b', [(1, .8)])], [1, 2])
    assert result['alpha_basis'] == 'human_coders'
    assert result['alpha'] == 1
    assert result['kappa'] == -1


@pytest.mark.parametrize('predictions', [[], [prediction('wrong', [])],
                                        [prediction('a', []), prediction('a', [])]])
def test_incomplete_or_duplicate_predictions_cannot_shrink_denominator(predictions):
    with pytest.raises(ValueError, match='exactly one prediction'):
        evaluate_metrics([reference('a', [1])], predictions, [1])


@pytest.mark.parametrize('score', [math.nan, math.inf, -.1, 1.1, True])
def test_invalid_scores_are_rejected(score):
    with pytest.raises(ValueError, match='score must be finite'):
        evaluate_metrics([reference('a', [1])], [prediction('a', [(1, score)])], [1])


def test_unknown_labels_and_invalid_totals_are_rejected():
    with pytest.raises(ValueError, match='known code'):
        evaluate_metrics([reference('a', [9])], [prediction('a', [])], [1])
    with pytest.raises(ValueError, match='unknown code'):
        evaluate_metrics([reference('a', [1])], [prediction('a', [(9, .4)])], [1])
    with pytest.raises(ValueError, match='resource totals'):
        evaluate_metrics([], [], [1], escalated_segments=1)
