"""Pure fail-closed decisions from measured validation metrics and fixed policy."""

import math
from decimal import Decimal


def _number(value, *, maximum=None, integer=False):
    try:
        return (type(value) in (int, float) and math.isfinite(value) and value >= 0
                and (maximum is None or value <= maximum) and (not integer or value == int(value)))
    except OverflowError:
        return False


def _decimal(value):
    # Decimal representations preserve inclusive human-authored policy boundaries.
    return Decimal(str(value))


def _priority(metrics, code_id):
    rows = metrics.get('per_code')
    if not isinstance(rows, list):
        return None
    matching = [row.get('f1') for row in rows if isinstance(row, dict)
                and type(row.get('code_id')) is int and row['code_id'] == code_id]
    return matching[0] if len(matching) == 1 and _number(matching[0], maximum=1) else None


def decide(baseline: dict, candidate: dict, policy: dict, *, tests_passed: bool,
           challenge_regressions: int = 0) -> dict:
    """Return KEEP eligibility; caller must separately confirm and enforce scope.

    Calls are measured attempted calls (including retries), not token estimates.
    A successful first decision never substitutes for the required confirmation.
    """
    if not all(isinstance(value, dict) for value in (baseline, candidate, policy)):
        return {'keep': False, 'reasons': ['invalid metrics or policy']}
    priorities = policy.get('priority_codes')
    if (policy.get('primary') != 'macro_f1'
            or not _number(policy.get('min_delta'), maximum=1)
            or not _number(policy.get('priority_tolerance'), maximum=1)
            or not _number(policy.get('max_call_ratio'))
            or type(policy.get('challenge_regressions')) is not int or policy['challenge_regressions'] != 0
            or not isinstance(priorities, list) or any(type(code) is not int for code in priorities)
            or len(set(priorities)) != len(priorities)):
        return {'keep': False, 'reasons': ['invalid protected policy']}
    reasons = []
    if tests_passed is not True:
        reasons.append('tests did not pass')
    if type(challenge_regressions) is not int or challenge_regressions != 0:
        reasons.append('challenge regressions must be zero')
    old, new = baseline.get('macro_f1'), candidate.get('macro_f1')
    if not _number(old, maximum=1) or not _number(new, maximum=1):
        reasons.append('macro_f1 is missing, nonfinite or outside [0,1]')
    elif _decimal(new) - _decimal(old) < _decimal(policy['min_delta']):
        reasons.append('validation macro_f1 gain is below min_delta')
    for code_id in priorities:
        before, after = _priority(baseline, code_id), _priority(candidate, code_id)
        if before is None or after is None:
            reasons.append(f'priority code {code_id} F1 is missing, invalid or ambiguous')
        elif _decimal(before) - _decimal(after) > _decimal(policy['priority_tolerance']):
            reasons.append(f'priority code {code_id} regression exceeds tolerance')
    before_calls, after_calls = baseline.get('calls'), candidate.get('calls')
    if not _number(before_calls, integer=True) or not _number(after_calls, integer=True):
        reasons.append('calls must be finite nonnegative integer counts')
    elif _decimal(after_calls) > _decimal(before_calls) * _decimal(policy['max_call_ratio']):
        reasons.append('candidate calls exceed baseline call ratio')
    return {'keep': not reasons, 'reasons': reasons or ['measured validation gain and all policy checks passed']}
