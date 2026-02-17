from __future__ import annotations

from dataclasses import dataclass
from math import exp, log

R_GAS = 8.31446261815324  # J/(mol*K)


@dataclass(slots=True)
class BindingExperiment:
    technique: str
    protein: str
    ligand: str
    temperature_c: float
    concentrations: list[float]
    response: list[float]


@dataclass(slots=True)
class FitQuality:
    r_squared: float
    rmse: float


@dataclass(slots=True)
class IC50Result:
    top: float
    bottom: float
    log_ic50: float
    hill_slope: float

    @property
    def ic50(self) -> float:
        return 10 ** self.log_ic50


def four_pl(x: float, top: float, bottom: float, log_ic50: float, hill_slope: float) -> float:
    return bottom + (top - bottom) / (1 + 10 ** ((log_ic50 - x) * hill_slope))


def cheng_prusoff_ki(ic50: float, tracer_conc: float, tracer_kd: float) -> float:
    if tracer_kd <= 0:
        raise ValueError("tracer_kd must be > 0")
    return ic50 / (1 + (tracer_conc / tracer_kd))


def gibbs_from_kd(kd_molar: float, temperature_k: float) -> float:
    """ΔG = RT ln(Kd), J/mol."""
    if kd_molar <= 0:
        raise ValueError("Kd must be > 0")
    return R_GAS * temperature_k * log(kd_molar)


def kd_from_rates(kon: float, koff: float) -> float:
    if kon <= 0:
        raise ValueError("kon must be > 0")
    return koff / kon


def residence_time(koff: float) -> float:
    if koff <= 0:
        raise ValueError("koff must be > 0")
    return 1.0 / koff


def fa_anisotropy(i_parallel: float, i_perpendicular: float) -> float:
    denom = i_parallel + 2 * i_perpendicular
    if denom == 0:
        raise ValueError("invalid intensity values")
    return (i_parallel - i_perpendicular) / denom


def fit_quality(y_true: list[float], y_pred: list[float]) -> FitQuality:
    if len(y_true) != len(y_pred) or not y_true:
        raise ValueError("equal non-empty vectors required")
    mean = sum(y_true) / len(y_true)
    ss_tot = sum((y - mean) ** 2 for y in y_true)
    ss_res = sum((a - b) ** 2 for a, b in zip(y_true, y_pred))
    r2 = 1 - ss_res / ss_tot if ss_tot else 1.0
    rmse = (ss_res / len(y_true)) ** 0.5
    return FitQuality(r2, rmse)


def c_value(ka: float, protein_conc: float, stoichiometry: float) -> float:
    return ka * protein_conc * stoichiometry


def itc_c_value_warning(c: float) -> str:
    if c < 1:
        return "c-value < 1: binding likely too weak, Kd uncertainty high"
    if c > 1000:
        return "c-value > 1000: binding likely too tight, Kd lower-limit behavior"
    return "c-value in optimal range"


def association_response(t: float, r_eq: float, r0: float, k_obs: float) -> float:
    return r_eq - (r_eq - r0) * exp(-k_obs * t)


def dissociation_response(t: float, r0: float, r_inf: float, koff: float) -> float:
    return r_inf + (r0 - r_inf) * exp(-koff * t)
