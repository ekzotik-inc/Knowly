import pytest

from app.services.progression import level_for_xp


@pytest.mark.parametrize("xp, level", [(0, 1), (99, 1), (100, 2), (199, 2), (200, 3), (999, 10)])
def test_level_for_xp(xp, level):
    assert level_for_xp(xp) == level
