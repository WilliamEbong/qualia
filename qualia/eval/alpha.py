"""Nominal Krippendorff alpha; units contain hashable category ratings or None."""

from collections import Counter


def nominal_alpha(units) -> float | None:
    """Exclude units with fewer than two ratings; undefined disagreement is None.

    Nominal code sets must be supplied as tuples/frozensets, not ordinal numbers.
    Coincidences weight each unit's ordered pairs by 1/(number of ratings - 1).
    """
    totals = Counter()
    observed = 0.0
    for unit in units:
        ratings = [rating for rating in unit if rating is not None]
        size = len(ratings)
        if size < 2:
            continue
        counts = Counter(ratings)
        totals.update(counts)
        observed += (size * size - sum(count * count for count in counts.values())) / (size - 1)
    count = sum(totals.values())
    if count < 2:
        return None
    expected = (count * count - sum(value * value for value in totals.values())) / (count - 1)
    return 1.0 - observed / expected if expected else None
