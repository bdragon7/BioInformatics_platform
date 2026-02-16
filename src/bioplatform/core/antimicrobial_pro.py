from __future__ import annotations

"""Regulatory and antimicrobial intelligence toolkit."""

from dataclasses import dataclass
from math import exp, log, log10, sqrt


@dataclass(slots=True)
class ENStandardResult:
    log_reduction: float
    water_control_valid: bool
    neutralizer_valid: bool
    pass_fail: bool
    standard: str


@dataclass(slots=True)
class MICResult:
    mic: float
    lower_ci_95: float
    upper_ci_95: float
    slope: float


@dataclass(slots=True)
class ZoneInhibitionPlaceholder:
    status: str
    notes: str


def validate_en_standard(
    n0: float,
    na: float,
    n0_water: float,
    inoculum_reference: float,
    neutralization_recovery_fraction: float,
    is_fungal: bool = False,
) -> ENStandardResult:
    if n0 <= 0 or na <= 0:
        raise ValueError("n0 and na must be > 0")

    log_reduction = log10(n0) - log10(na)
    water_delta = abs(log10(max(n0_water, 1e-12)) - log10(max(inoculum_reference, 1e-12)))
    water_ok = water_delta <= 0.5
    neutral_ok = neutralization_recovery_fraction >= 0.5
    target = 4.0 if is_fungal else 5.0
    pass_fail = log_reduction >= target and water_ok and neutral_ok

    return ENStandardResult(
        log_reduction=log_reduction,
        water_control_valid=water_ok,
        neutralizer_valid=neutral_ok,
        pass_fail=pass_fail,
        standard="EN 1650" if is_fungal else "EN 1276",
    )


def solve_mic(
    concentrations: list[float],
    relative_growth: list[float],
    growth_threshold: float = 0.1,
    iterations: int = 2500,
    learning_rate: float = 0.01,
) -> MICResult:
    """Solve MIC with gradient descent on a logistic inhibition curve.

    Equation:
        y = 1 / (1 + exp(s * (log10(c) - log10(MIC))))
    """
    if len(concentrations) != len(relative_growth) or len(concentrations) < 4:
        raise ValueError("Need >=4 paired concentration/growth values")
    if any(c <= 0 for c in concentrations):
        raise ValueError("Concentrations must be > 0")

    x = [log10(c) for c in concentrations]
    y = [min(1.0, max(0.0, v)) for v in relative_growth]

    theta_mic = sum(x) / len(x)
    theta_slope = 2.0

    for _ in range(iterations):
        grad_m = 0.0
        grad_s = 0.0
        for xi, yi in zip(x, y):
            z = theta_slope * (xi - theta_mic)
            pred = 1.0 / (1.0 + exp(z))
            err = pred - yi
            common = pred * (1.0 - pred)
            d_pred_d_m = theta_slope * common
            d_pred_d_s = -(xi - theta_mic) * common
            grad_m += 2.0 * err * d_pred_d_m
            grad_s += 2.0 * err * d_pred_d_s

        n = float(len(x))
        theta_mic -= learning_rate * grad_m / n
        theta_slope -= learning_rate * grad_s / n
        theta_slope = max(theta_slope, 0.2)

    # report MIC at configurable growth threshold, not 50% inhibition midpoint.
    log_mic_threshold = theta_mic + (log((1.0 / max(growth_threshold, 1e-6)) - 1.0) / max(theta_slope, 1e-6))
    mic = 10 ** log_mic_threshold

    preds: list[float] = []
    for xi in x:
        z = theta_slope * (xi - theta_mic)
        preds.append(1.0 / (1.0 + exp(z)))

    residuals = [a - b for a, b in zip(y, preds)]
    rmse = sqrt(sum(r * r for r in residuals) / max(1, len(residuals) - 2))
    # approximate CI in log-domain using local slope around threshold crossing.
    local_sensitivity = max(theta_slope * growth_threshold * (1.0 - growth_threshold), 1e-6)
    se_log_mic = rmse / local_sensitivity
    delta = 1.96 * se_log_mic
    return MICResult(
        mic=mic,
        lower_ci_95=10 ** (log_mic_threshold - delta),
        upper_ci_95=10 ** (log_mic_threshold + delta),
        slope=theta_slope,
    )


def zoi_analysis_placeholder(image_path: str) -> ZoneInhibitionPlaceholder:
    """Placeholder for OpenCV-based Zone of Inhibition pipeline."""
    return ZoneInhibitionPlaceholder(
        status="planned",
        notes=f"OpenCV ZoI module reserved for future image pipeline: {image_path}",
    )
