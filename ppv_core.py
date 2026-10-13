"""Pulse pressure variation (PPV) from invasive arterial-waveform extrema.

The maximum and minimum pulse pressures must refer to beats observed in
the same respiratory cycle. Paired systolic/diastolic values must be taken
from the same beat; independent blood-pressure extrema are not valid pairs.
"""
import math


def _pressure(value, name, *, allow_zero=False):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(number) or number < 0 or (number == 0 and not allow_zero):
        raise ValueError(f"{name} must be {'nonnegative' if allow_zero else 'positive'} and finite")
    return number


def calculate_ppv(
    pp_max=None, pp_min=None, *,
    sbp_max=None, dbp_max=None, sbp_min=None, dbp_min=None,
):
    """Compute 100 * (PPmax - PPmin) / ((PPmax + PPmin) / 2).

    Provide either pp_max and pp_min (mmHg) or two pairs of simultaneous
    systolic/diastolic pressures: one at maximum and one at minimum PP.
    This is a measurement calculation, not a treatment recommendation.
    """
    direct = pp_max is not None or pp_min is not None
    pairs = (sbp_max, dbp_max, sbp_min, dbp_min)
    paired = any(value is not None for value in pairs)
    if direct and paired:
        raise ValueError("Use either pulse pressures or paired blood pressures, not both")
    if direct:
        if pp_max is None or pp_min is None:
            raise ValueError("Both pp_max and pp_min are required")
        maximum = _pressure(pp_max, "pp_max")
        minimum = _pressure(pp_min, "pp_min")
    elif paired:
        if any(value is None for value in pairs):
            raise ValueError("All four paired systolic/diastolic pressures are required")
        sys_hi = _pressure(sbp_max, "sbp_max")
        dia_hi = _pressure(dbp_max, "dbp_max", allow_zero=True)
        sys_lo = _pressure(sbp_min, "sbp_min")
        dia_lo = _pressure(dbp_min, "dbp_min", allow_zero=True)
        maximum = sys_hi - dia_hi
        minimum = sys_lo - dia_lo
        if maximum <= 0 or minimum <= 0:
            raise ValueError("Each systolic pressure must exceed its paired diastolic pressure")
    else:
        raise ValueError("Provide pp_max and pp_min or two paired blood pressures")
    if maximum < minimum:
        raise ValueError("Maximum pulse pressure must be greater than or equal to minimum")
    mean = maximum / 2 + minimum / 2
    if not math.isfinite(mean) or mean <= 0:
        raise ValueError("Pulse pressures are too large to calculate reliably")
    variation = 100 * ((maximum - minimum) / mean)
    if not math.isfinite(variation):
        raise ValueError("Pulse pressures are too large to calculate reliably")
    return {
        "pp_max": round(maximum, 2),
        "pp_min": round(minimum, 2),
        "pp_mean": round(mean, 2),
        "ppv_percent": round(variation, 2),
        "unit": "mmHg",
    }
