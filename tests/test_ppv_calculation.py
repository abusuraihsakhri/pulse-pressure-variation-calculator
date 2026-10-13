import math
import pytest
from ppv_core import calculate_ppv
from ppv import assess_row


@pytest.mark.parametrize(("high", "low", "expected"), [
    (42, 38, 10.0), (50, 50, 0.0), (60, 40, 40.0), (12.5, 10, 22.22),
])
def test_known_values(high, low, expected):
    assert calculate_ppv(high, low)["ppv_percent"] == expected


def test_corresponding_bp_beats():
    direct = calculate_ppv(42, 38)
    paired = calculate_ppv(sbp_max=122, dbp_max=80, sbp_min=118, dbp_min=80)
    assert direct == paired
    assert assess_row({"sbp_max": 122, "dbp_max": 80, "sbp_min": 118, "dbp_min": 80}) == paired


def test_assess_row_ppv_routing():
    assert assess_row({"pp_max": "42", "pp_min": "38"})["ppv_percent"] == 10


@pytest.mark.parametrize("values", [
    {}, {"pp_max": 42}, {"pp_max": 40, "pp_min": 42},
    {"pp_max": 0, "pp_min": 0}, {"pp_max": 42, "pp_min": -1},
    {"pp_max": "NaN", "pp_min": 10}, {"pp_max": math.inf, "pp_min": 10},
    {"pp_max": True, "pp_min": 10}, {"pp_max": "", "pp_min": 10},
    {"pp_max": 42, "pp_min": 38, "sbp_max": 120},
    {"sbp_max": 120, "dbp_max": 120, "sbp_min": 118, "dbp_min": 80},
    {"sbp_max": 120, "dbp_max": 80, "sbp_min": 119},
])
def test_invalid_input(values):
    with pytest.raises(ValueError):
        calculate_ppv(**values)


def test_invalid_row_is_explicit_error():
    assert "error" in assess_row({"pp_max": "NaN", "pp_min": "25"})
