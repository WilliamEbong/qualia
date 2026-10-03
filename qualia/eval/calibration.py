"""Deterministic ECE for scored predicted code assignments, not accuracy claims."""

import math


def expected_calibration_error(scores, correct, *, bins=10) -> dict:
    """Equal-width bins, right edge excluded except score 1 in the final bin."""
    if type(bins) is not int or bins <= 0 or len(scores) != len(correct):
        raise ValueError('invalid calibration dimensions')
    counts = [0] * bins
    confidence = [0.0] * bins
    accuracy = [0] * bins
    for score, outcome in zip(scores, correct, strict=True):
        if (type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1
                or type(outcome) is not bool):
            raise ValueError('calibration requires finite scores and boolean correctness')
        index = min(int(score * bins), bins - 1)
        counts[index] += 1
        confidence[index] += score
        accuracy[index] += outcome
    details = [{'lower': index / bins, 'upper': (index + 1) / bins, 'count': counts[index],
                'mean_confidence': confidence[index] / counts[index] if counts[index] else None,
                'accuracy': accuracy[index] / counts[index] if counts[index] else None}
               for index in range(bins)]
    total = len(scores)
    ece = sum(abs(confidence[i] - accuracy[i]) for i in range(bins)) / total if total else None
    return {'ece': ece, 'scored_prediction_count': total, 'bins': details}
