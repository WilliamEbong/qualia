"""Sealed metric calculations: data in, JSON-compatible deterministic metrics out."""

import math

from scipy.stats import binomtest
from sklearn.metrics import (
    cohen_kappa_score,
    f1_score,
    precision_recall_curve,
    precision_recall_fscore_support,
)

from qualia.eval.alpha import nominal_alpha
from qualia.eval.calibration import expected_calibration_error

REVIEW_PRECISION = .9
THRESHOLD_GRID = [step / 20 for step in range(1, 20)]


def _wilson(successes, total):
    if not total:
        return None
    interval = binomtest(successes, total).proportion_ci(confidence_level=.95, method='wilson')
    return [float(interval.low), float(interval.high)]


def _review(scores, correct):
    """Share of scored assignments to review so those at or above the cutoff reach the target."""
    if not scores:
        return None, None
    if not any(correct):
        return 1.0, None
    precision, _, thresholds = precision_recall_curve(correct, scores)
    # precision[i] covers scores >= thresholds[i]; its extra final entry has no threshold.
    eligible = [float(threshold) for value, threshold in zip(precision, thresholds) if value >= REVIEW_PRECISION]
    if not eligible:
        return 1.0, None
    cutoff = min(eligible)
    return sum(score < cutoff for score in scores) / len(scores), cutoff


def _codes(values, allowed):
    if (not isinstance(values, list) or any(type(code) is not int or code not in allowed for code in values)
            or len(set(values)) != len(values)):
        raise ValueError('labels must be distinct known code IDs')
    return set(values)


def evaluate_metrics(records, predictions, code_ids, *, calls=0, latency_ms=0, escalated_segments=0):
    """Evaluate complete paired predictions; never omit a failed/missing segment.

    Reference/prediction agreement treats whole code sets as nominal categories.
    If records supply human coders, alpha instead uses their nominal code sets.
    """
    if any(type(code) is not int for code in code_ids) or len(set(code_ids)) != len(code_ids):
        raise ValueError('code ordering requires distinct integer IDs')
    if (type(calls) is not int or calls < 0 or type(escalated_segments) is not int
            or not 0 <= escalated_segments <= len(records)
            or type(latency_ms) not in (int, float) or not math.isfinite(latency_ms) or latency_ms < 0):
        raise ValueError('invalid evaluation resource totals')
    allowed = set(code_ids)
    ids = [record['segment_id'] for record in records]
    predicted_ids = [prediction['segment_id'] for prediction in predictions]
    if (any(not isinstance(identity, str) or not identity for identity in ids + predicted_ids)
            or len(set(ids)) != len(ids) or len(set(predicted_ids)) != len(predicted_ids)
            or set(ids) != set(predicted_ids)):
        raise ValueError('evaluation requires exactly one prediction for every reference segment')
    by_id = {prediction['segment_id']: prediction for prediction in predictions}
    gold, predicted, scores, correct, human_units = [], [], [], [], []
    has_coders = any('coders' in record for record in records)
    for record in records:
        reference = _codes(record['codes'], allowed)
        confidences = {}
        selected = set()
        for code in by_id[record['segment_id']]['codes']:
            code_id = code['code_id']
            if type(code_id) is not int or code_id not in allowed:
                raise ValueError('prediction contains unknown code ID')
            selected.add(code_id)
            score = code.get('score')
            if score is not None:
                if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
                    raise ValueError('prediction score must be finite and between zero and one')
                confidences[code_id] = max(confidences.get(code_id, 0), score)
        gold.append(reference)
        predicted.append(selected)
        for code_id, score in confidences.items():
            scores.append(score)
            correct.append(code_id in reference)
        coders = record.get('coders', [])
        if not isinstance(coders, list):
            raise ValueError('coders must be a list of code lists or missing ratings')
        human_units.append([tuple(sorted(_codes(coder, allowed))) if coder is not None else None
                            for coder in coders])
    count = len(records)
    per_code = []
    for code_id in code_ids:
        truth = [int(code_id in item) for item in gold]
        guesses = [int(code_id in item) for item in predicted]
        precision, recall, f1 = (None, None, None)
        if count:
            precision, recall, f1, _ = precision_recall_fscore_support(
                truth, guesses, average='binary', zero_division=0)
            precision, recall, f1 = float(precision), float(recall), float(f1)
        hits = sum(left and right for left, right in zip(truth, guesses, strict=True))
        per_code.append({'code_id': code_id, 'precision': precision, 'recall': recall,
                         'f1': f1, 'support': sum(truth), 'precision_ci95': _wilson(hits, sum(guesses)),
                         'recall_ci95': _wilson(hits, sum(truth))})
    micro = None
    if count and code_ids:
        truth = [int(code in row) for row in gold for code in code_ids]
        guesses = [int(code in row) for row in predicted for code in code_ids]
        micro = float(precision_recall_fscore_support(truth, guesses, average='binary', zero_division=0)[2])
    gold_categories = [tuple(sorted(row)) for row in gold]
    predicted_categories = [tuple(sorted(row)) for row in predicted]
    categories = {category: index for index, category in enumerate(sorted(set(gold_categories + predicted_categories)))}
    kappa = None
    if count and len(categories) > 1:
        value = float(cohen_kappa_score([categories[row] for row in gold_categories],
                                       [categories[row] for row in predicted_categories]))
        kappa = value if math.isfinite(value) else None
    units = human_units if has_coders else list(zip(gold_categories, predicted_categories, strict=True))
    calibration = expected_calibration_error(scores, correct)
    review_share, review_cutoff = _review(scores, correct)
    return {
        'per_code': per_code,
        'macro_f1': sum(row['f1'] for row in per_code) / len(per_code) if count and per_code else None,
        'micro_f1': micro,
        'exact_match': sum(left == right for left, right in zip(gold, predicted, strict=True)) / count if count else None,
        'partial_match': sum(len(left & right) / len(left | right) if left | right else 1.0
                             for left, right in zip(gold, predicted, strict=True)) / count if count else None,
        'kappa': kappa, 'alpha': nominal_alpha(units), 'ece': calibration['ece'],
        'escalation_rate': escalated_segments / count if count else None,
        'calls_per_1000': calls * 1000 / count if count else None, 'latency_ms': float(latency_ms),
        'segment_count': count, 'scored_prediction_count': len(scores), 'calls': calls,
        'escalated_segments': escalated_segments, 'calibration_bins': calibration['bins'],
        'review_share': review_share, 'review_cutoff': review_cutoff,
        'alpha_basis': 'human_coders' if has_coders else 'reference_vs_prediction',
        'definitions': {
            'zero_division': 'Per-code and micro precision/recall/F1 use zero when no positives; empty corpus uses null.',
            'macro_f1': 'Unweighted mean over the full frozen codebook, including absent labels.',
            'partial_match': 'Mean per-segment code-set Jaccard; two empty sets score one.',
            'kappa': 'Cohen kappa on nominal reference and predicted code-set categories; undefined is null.',
            'alpha': 'Nominal code-set categories; missing ratings and units with fewer than two ratings excluded; undefined is null.',
            'ece': 'Predicted (segment, code) assignments; repeated spans use maximum model-reported score. Correct means code is in reference. Ten equal-width bins; final bin includes 1. No scored assignments gives null. This does not measure missed-label calibration.',
            'escalation_rate': 'Distinct escalated segments divided by evaluated segments; empty denominator is null.',
            'calls_per_1000': 'Attempted backend dispatches divided by evaluated segments times 1000. Native Claude/Codex dispatches are CLI invocations, potentially containing multiple provider requests; Jev dispatches are HTTP requests including retries. Empty denominator is null.',
            'latency_ms': 'Total supplied wall-clock evaluation latency in milliseconds.',
            'ci95': 'Per-code precision_ci95/recall_ci95 are 95% Wilson score intervals over predicted/reference segment counts; a zero denominator is null. Wide intervals mean few examples.',
            'review_share': 'Share of scored predicted assignments scoring below review_cutoff: reviewing them leaves the rest at 90% precision or better on this evaluation set. 1.0 when no cutoff reaches 90%; null without scored assignments. Describes this set, not future accuracy.',
            'review_cutoff': 'Lowest model-reported score at which assignments scoring at or above it reach 90% precision on this evaluation set; null when unreachable or unscored.',
        },
    }


def tune_thresholds(records, candidates, code_ids, current):
    """Per-code score cutoff maximising that code's F1 on tuning data (ties toward 0.5).

    Codes without reference positives, or that no cutoff can find, keep their current value.
    ponytail: a small dev split can overfit; validation KEEP/REVERT is the guard.
    """
    ids = [record['segment_id'] for record in records]
    by_id = {candidate['segment_id']: candidate for candidate in candidates}
    if len(set(ids)) != len(ids) or len(by_id) != len(candidates) or set(ids) != set(by_id):
        raise ValueError('tuning requires exactly one prediction for every reference segment')
    tuned = dict(current)
    for code_id in code_ids:
        truth = [int(code_id in record['codes']) for record in records]
        if not any(truth):
            continue
        scores = [max((code['score'] for code in by_id[identity]['codes'] if code['code_id'] == code_id),
                      default=0.0) for identity in ids]

        def f1_at(threshold):
            return f1_score(truth, [int(score >= threshold) for score in scores], zero_division=0)

        best = max(THRESHOLD_GRID, key=lambda threshold: (f1_at(threshold), -abs(threshold - .5)))
        if f1_at(best) > 0:
            tuned[str(code_id)] = best
    return tuned
