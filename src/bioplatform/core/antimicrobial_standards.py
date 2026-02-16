from __future__ import annotations

from dataclasses import dataclass
from math import log10, sqrt


@dataclass(slots=True)
class EN1276Input:
    n0: float
    na: float
    n0_water: float
    inoculum_reference: float
    neutralization_recovery_fraction: float
    contact_time_min: int
    temperature_c: float
    organism: str


@dataclass(slots=True)
class EN1276Result:
    log_reduction: float
    pass_criterion: bool
    water_control_valid: bool
    neutralization_valid: bool
    overall_valid: bool
    message: str


def en1276_log_reduction(n0: float, na: float) -> float:
    if n0 <= 0 or na <= 0:
        raise ValueError("Counts must be > 0 for log10 calculation")
    return log10(n0) - log10(na)


def en1276_evaluate(inp: EN1276Input) -> EN1276Result:
    lr = en1276_log_reduction(inp.n0, inp.na)
    water_delta = abs(log10(inp.n0_water) - log10(inp.inoculum_reference)) if inp.n0_water > 0 and inp.inoculum_reference > 0 else 9.0
    water_valid = water_delta <= 0.5
    neutral_valid = inp.neutralization_recovery_fraction >= 0.5
    pass_criterion = lr >= 5.0
    overall = pass_criterion and water_valid and neutral_valid
    parts = []
    parts.append("pass" if pass_criterion else "fail")
    if not water_valid:
        parts.append("invalid water control")
    if not neutral_valid:
        parts.append("neutralization ineffective")
    return EN1276Result(
        log_reduction=lr,
        pass_criterion=pass_criterion,
        water_control_valid=water_valid,
        neutralization_valid=neutral_valid,
        overall_valid=overall,
        message=", ".join(parts),
    )


@dataclass(slots=True)
class BiofilmKillResult:
    log_reduction: float
    mbec_reached: bool


def biofilm_log_reduction(cfu_before: float, cfu_after: float) -> float:
    if cfu_before <= 0 or cfu_after <= 0:
        raise ValueError("CFU counts must be > 0")
    return log10(cfu_before) - log10(cfu_after)


def compare_biofilm_vs_planktonic(biofilm_lr: float, planktonic_lr: float) -> str:
    delta = planktonic_lr - biofilm_lr
    if delta >= 2.0:
        return "Biofilm resistance suspected: planktonic kill greatly exceeds biofilm kill."
    return "Biofilm/planktonic susceptibility gap acceptable."


def mean_sd_ci95(values: list[float]) -> tuple[float, float, float]:
    if not values:
        raise ValueError("values required")
    mean = sum(values) / len(values)
    if len(values) == 1:
        return mean, 0.0, 0.0
    var = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    sd = sqrt(var)
    ci95 = 1.96 * sd / sqrt(len(values))
    return mean, sd, ci95
