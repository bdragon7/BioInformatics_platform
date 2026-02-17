from __future__ import annotations

from dataclasses import dataclass
from math import log


@dataclass(slots=True)
class StandardCurveResult:
    slope: float
    intercept: float
    r_squared: float


@dataclass(slots=True)
class GrowthMetrics:
    mu_max: float
    generation_time: float | None
    carrying_capacity: float
    lag_phase_hours: float


def detect_outliers_zscore(values: list[float], threshold: float = 2.5) -> list[int]:
    if len(values) < 3:
        return []
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    if variance == 0:
        return []
    std_dev = variance**0.5
    return [i for i, value in enumerate(values) if abs((value - mean) / std_dev) > threshold]


def fit_standard_curve(concentrations: list[float], signals: list[float]) -> StandardCurveResult:
    if len(concentrations) != len(signals) or len(concentrations) < 2:
        raise ValueError("At least two paired standard points are required")

    n = len(concentrations)
    x_mean = sum(concentrations) / n
    y_mean = sum(signals) / n

    sxx = sum((x - x_mean) ** 2 for x in concentrations)
    if sxx == 0:
        raise ValueError("Concentrations must vary to fit a regression line")
    sxy = sum((x - x_mean) * (y - y_mean) for x, y in zip(concentrations, signals))

    slope = sxy / sxx
    intercept = y_mean - slope * x_mean
    ss_tot = sum((y - y_mean) ** 2 for y in signals)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(concentrations, signals))
    r2 = 1.0 if ss_tot == 0 else 1 - (ss_res / ss_tot)

    return StandardCurveResult(slope=slope, intercept=intercept, r_squared=max(0.0, min(1.0, r2)))


def analyze_growth_curve(time_hours: list[float], od600_values: list[float]) -> GrowthMetrics:
    if len(time_hours) != len(od600_values) or len(time_hours) < 3:
        raise ValueError("Growth analysis requires at least 3 paired time/OD600 points")

    carrying_capacity = max(od600_values)

    mu_max = 0.0
    for i in range(1, len(time_hours)):
        t0, t1 = time_hours[i - 1], time_hours[i]
        y0, y1 = max(od600_values[i - 1], 1e-6), max(od600_values[i], 1e-6)
        dt = t1 - t0
        if dt <= 0:
            continue
        mu = (log(y1) - log(y0)) / dt
        mu_max = max(mu_max, mu)

    generation_time = (log(2) / mu_max) if mu_max > 0 else None

    baseline = od600_values[0]
    activation_threshold = baseline + 0.1 * max(carrying_capacity - baseline, 0.0)
    lag_phase_hours = time_hours[0]
    for t, od in zip(time_hours, od600_values):
        if od >= activation_threshold:
            lag_phase_hours = t
            break

    return GrowthMetrics(
        mu_max=mu_max,
        generation_time=generation_time,
        carrying_capacity=carrying_capacity,
        lag_phase_hours=lag_phase_hours,
    )


def contamination_flags(control_trace: list[float], spike_multiplier: float = 2.0) -> list[str]:
    if len(control_trace) < 2:
        return []

    flags: list[str] = []
    baseline = max(control_trace[0], 1e-6)
    if max(control_trace) > baseline * spike_multiplier:
        flags.append("Negative control spike detected; potential contamination.")

    for i in range(1, len(control_trace)):
        prev = max(control_trace[i - 1], 1e-6)
        if control_trace[i] > prev * spike_multiplier:
            flags.append(f"Abrupt control increase at index {i} (possible contamination event).")
            break

    return flags



def standards_alignment_notes() -> dict[str, str]:
    """Reference notes for common microbiology efficacy standards."""
    return {
        "EN 1276": "Quantitative suspension test for bactericidal activity in food/industrial/domestic areas.",
        "ASTM E2315": "Time-kill procedure for assessing antimicrobial activity using suspension methods.",
        "ASTM E1054": "Evaluation framework for inactivators/neutralizers in antimicrobial efficacy testing.",
    }
