"""Independent dev-only GPL oracle; production imports only our nominal routine."""

import krippendorff
import numpy as np
import pytest

from qualia.eval.alpha import nominal_alpha


@pytest.mark.parametrize('units', [
    [[0, 0], [0, 1], [1, 1], [2, 2], [2, 1]],
    [[0, 1, 2], [1, 2, 0], [2, 0, 1], [0, 1, 0]],
    [[0, None, 0, 1], [1, 1, None, None], [2, 2, 2, 2], [None, 0, 1, None], [1, None, None, None]],
])
def test_three_independent_nominal_fixtures_match_oracle(units):
    ratings = np.array([[np.nan if rating is None else rating for rating in unit] for unit in units]).T
    expected = krippendorff.alpha(reliability_data=ratings, level_of_measurement='nominal')
    assert nominal_alpha(units) == pytest.approx(expected, abs=1e-9)


def test_missing_or_constant_ratings_have_undefined_alpha():
    assert nominal_alpha([]) is None
    assert nominal_alpha([[None, 0], [1, None]]) is None
    assert nominal_alpha([[0, 0], [0, 0]]) is None


def test_code_sets_are_nominal_categories_not_ordered_numeric_scores():
    assert nominal_alpha([[(1, 2), (1, 2)], [(3,), (3,)]]) == 1
    assert nominal_alpha([[('x',), ('y',)], [('x',), ('y',)]]) == pytest.approx(-.5)
