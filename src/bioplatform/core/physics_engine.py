from __future__ import annotations

"""Thermodynamic and kinetic global fitting engine.

This module is vectorized with NumPy for high-throughput fitting workloads.
"""

from dataclasses import dataclass
from math import log
from typing import Literal

import numpy as np
from numpy.typing import NDArray

R_GAS_J_MOL_K = 8.31446261815324


class UnitError(ValueError):
    """Raised when unit handling is invalid or incompatible."""


@dataclass(frozen=True, slots=True)
class GlobalKdFitResult:
    kd_ref_m: float
    delta_h_j_mol: float
    delta_s_j_mol_k: float
    residual_rmse: float
    predicted: NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class CompetitionBindingResult:
    ki_m: float


@dataclass(frozen=True, slots=True)
class DigitalTwinResult:
    time_s: NDArray[np.float64]
    response: NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class PhysicsQualityGate:
    c_value: float
    c_warning: str
    mass_transport_flag: bool


@dataclass(frozen=True, slots=True)
class JointThermoKineticFitResult:
    kd_m: float
    kon_m_inv_s: float
    koff_s_inv: float
    rmax: float
    delta_h_j_mol: float
    delta_s_j_mol_k: float
    rmse: float
    spr_predicted: NDArray[np.float64]
    itc_predicted: NDArray[np.float64]


def global_joint_spr_itc_fit(
    spr_time_s: NDArray[np.float64],
    spr_response_ru: NDArray[np.float64],
    spr_analyte_conc_m: float,
    itc_injection_moles: NDArray[np.float64],
    itc_heat_j: NDArray[np.float64],
    temperature_k: float = 298.15,
    t_assoc_s: float | None = None,
) -> JointThermoKineticFitResult:
    """Globally fit SPR and ITC with shared thermodynamics/kinetics.

    Shared-state model:
      - Kd(T) is constrained by Van't Hoff relation (ΔH, ΔS).
      - Kinetic relation Kd = koff / kon links SPR rates to thermodynamics.
      - ITC heats follow single-site digital twin scaled by instrument factor.
    """
    if spr_time_s.ndim != 1 or spr_response_ru.ndim != 1:
        raise ValueError("SPR arrays must be 1D")
    if spr_time_s.shape[0] != spr_response_ru.shape[0]:
        raise ValueError("SPR time/response lengths must match")
    if itc_injection_moles.ndim != 1 or itc_heat_j.ndim != 1:
        raise ValueError("ITC arrays must be 1D")
    if itc_injection_moles.shape[0] != itc_heat_j.shape[0]:
        raise ValueError("ITC injection/heat lengths must match")

    try:
        from scipy.optimize import least_squares  # type: ignore
    except Exception as exc:
        raise RuntimeError("SciPy is required for global_joint_spr_itc_fit") from exc

    assoc_switch = float(t_assoc_s) if t_assoc_s is not None else float(np.median(spr_time_s))

    def residual(theta: NDArray[np.float64]) -> NDArray[np.float64]:
        log10_kon, log10_koff, log10_rmax, delta_h, delta_s, itc_scale = theta
        kon = 10.0**log10_kon
        koff = 10.0**log10_koff
        rmax = 10.0**log10_rmax

        spr_pred = simulate_spr_sensorgram(
            spr_time_s,
            analyte_conc_m=spr_analyte_conc_m,
            kon_m_inv_s=kon,
            koff_s_inv=koff,
            rmax=rmax,
            t_assoc_s=assoc_switch,
        ).response

        kd_vh = float(_vanthoff_kd(np.array([temperature_k], dtype=np.float64), delta_h, delta_s)[0])
        kd_kin = koff / max(kon, 1e-18)
        kd_shared = np.sqrt(max(kd_vh, 1e-18) * max(kd_kin, 1e-18))
        itc_pred = itc_scale * simulate_itc_injections(itc_injection_moles, kd_shared, delta_h)

        spr_scale = max(float(np.std(spr_response_ru)), 1e-9)
        itc_scale_norm = max(float(np.std(itc_heat_j)), 1e-12)
        return np.concatenate([(spr_pred - spr_response_ru) / spr_scale, (itc_pred - itc_heat_j) / itc_scale_norm])

    x0 = np.array([5.0, -2.0, 2.0, -30000.0, -80.0, 1.0], dtype=np.float64)
    fit = least_squares(residual, x0=x0, method="trf")
    log10_kon, log10_koff, log10_rmax, d_h, d_s, itc_scale = fit.x

    kon = float(10.0**log10_kon)
    koff = float(10.0**log10_koff)
    rmax = float(10.0**log10_rmax)
    kd_vh = float(_vanthoff_kd(np.array([temperature_k], dtype=np.float64), float(d_h), float(d_s))[0])
    kd_kin = koff / max(kon, 1e-18)
    kd = float(np.sqrt(max(kd_vh, 1e-18) * max(kd_kin, 1e-18)))

    spr_pred = simulate_spr_sensorgram(
        spr_time_s,
        analyte_conc_m=spr_analyte_conc_m,
        kon_m_inv_s=kon,
        koff_s_inv=koff,
        rmax=rmax,
        t_assoc_s=assoc_switch,
    ).response
    itc_pred = float(itc_scale) * simulate_itc_injections(itc_injection_moles, kd, float(d_h))

    rmse = float(np.sqrt(np.mean((spr_pred - spr_response_ru) ** 2)))
    return JointThermoKineticFitResult(
        kd_m=kd,
        kon_m_inv_s=kon,
        koff_s_inv=koff,
        rmax=rmax,
        delta_h_j_mol=float(d_h),
        delta_s_j_mol_k=float(d_s),
        rmse=rmse,
        spr_predicted=spr_pred.astype(np.float64),
        itc_predicted=itc_pred.astype(np.float64),
    )


def solver_convergence_path(initial_residual_norm: float, final_residual_norm: float, frames: int = 60) -> NDArray[np.float64]:
    """Generate a smooth residual path for UI convergence animation."""
    start = max(initial_residual_norm, 1e-12)
    end = max(final_residual_norm, 1e-12)
    return np.geomspace(start, end, num=max(frames, 2)).astype(np.float64)


def _unit_factor_to_molar(unit: Literal["M", "mM", "uM", "nM"]) -> float:
    factors: dict[str, float] = {"M": 1.0, "mM": 1e-3, "uM": 1e-6, "nM": 1e-9}
    if unit not in factors:
        raise UnitError(f"Unsupported concentration unit: {unit}")
    return factors[unit]


def to_molar(value: float, unit: Literal["M", "mM", "uM", "nM"]) -> float:
    if value < 0:
        raise UnitError("Concentration cannot be negative")
    return value * _unit_factor_to_molar(unit)


def cheng_prusoff_ki(ic50_m: float, tracer_conc_m: float, tracer_kd_m: float) -> CompetitionBindingResult:
    """Cheng-Prusoff relation for competitive inhibition.

    Equation:
        Ki = IC50 / (1 + [L]/Kd_L)
    """
    if tracer_kd_m <= 0:
        raise ValueError("tracer_kd_m must be > 0")
    return CompetitionBindingResult(ki_m=ic50_m / (1.0 + (tracer_conc_m / tracer_kd_m)))


def wang_ki(ic50_m: float, receptor_total_m: float, ligand_total_m: float, kd_probe_m: float) -> CompetitionBindingResult:
    """Wang correction for tight-binding displacement style conditions.

    Uses a practical approximation suitable for production screening:
        Ki ~= IC50 / (1 + ([L]-[R]/2)/Kd_probe)
    """
    if kd_probe_m <= 0:
        raise ValueError("kd_probe_m must be > 0")
    correction = 1.0 + ((ligand_total_m - receptor_total_m / 2.0) / kd_probe_m)
    return CompetitionBindingResult(ki_m=ic50_m / max(correction, 1e-12))


def morrison_fraction_bound(inhibitor_total_m: NDArray[np.float64], enzyme_total_m: float, ki_m: float) -> NDArray[np.float64]:
    """Morrison equation for tight-binding depletion.

    Equation:
        f_b = ((E_t + I_t + Ki) - sqrt((E_t + I_t + Ki)^2 - 4E_tI_t)) / (2E_t)
    """
    et = max(enzyme_total_m, 1e-18)
    term = et + inhibitor_total_m + ki_m
    disc = np.maximum(term * term - 4.0 * et * inhibitor_total_m, 0.0)
    return (term - np.sqrt(disc)) / (2.0 * et)


def _vanthoff_kd(temperature_k: NDArray[np.float64], delta_h_j_mol: float, delta_s_j_mol_k: float) -> NDArray[np.float64]:
    return np.exp((delta_h_j_mol - temperature_k * delta_s_j_mol_k) / (R_GAS_J_MOL_K * temperature_k))


def global_kd_fit(
    concentrations_m: NDArray[np.float64],
    response_matrix: NDArray[np.float64],
    temperature_k: NDArray[np.float64],
) -> GlobalKdFitResult:
    """Global non-linear fitting across multi-temperature titration curves.

    Response model:
        y = c / (Kd(T) + c)
    with Van't Hoff coupled Kd(T):
        ln(Kd) = (ΔH / R)(1/T) - ΔS/R
    """
    if concentrations_m.ndim != 1:
        raise ValueError("concentrations_m must be 1D")
    if response_matrix.ndim != 2:
        raise ValueError("response_matrix must be 2D")
    if response_matrix.shape[0] != temperature_k.shape[0] or response_matrix.shape[1] != concentrations_m.shape[0]:
        raise ValueError("response_matrix shape must match [n_temp, n_conc]")

    try:
        from scipy.optimize import least_squares  # type: ignore
    except Exception as exc:
        raise RuntimeError("SciPy is required for global_kd_fit") from exc

    c = concentrations_m[None, :]
    t = temperature_k[:, None]
    y_obs = response_matrix

    def residual(theta: NDArray[np.float64]) -> NDArray[np.float64]:
        delta_h, delta_s = theta[0], theta[1]
        kd_t = _vanthoff_kd(t, delta_h, delta_s)
        y_hat = c / (kd_t + c)
        return (y_hat - y_obs).ravel()

    x0 = np.array([-30000.0, -80.0], dtype=np.float64)
    fit = least_squares(residual, x0=x0, method="trf")
    d_h = float(fit.x[0])
    d_s = float(fit.x[1])
    kd_ref = float(_vanthoff_kd(np.array([298.15], dtype=np.float64), d_h, d_s)[0])
    pred = (concentrations_m[None, :] / (_vanthoff_kd(temperature_k[:, None], d_h, d_s) + concentrations_m[None, :])).astype(np.float64)
    rmse = float(np.sqrt(np.mean((pred - y_obs) ** 2)))
    return GlobalKdFitResult(
        kd_ref_m=kd_ref,
        delta_h_j_mol=d_h,
        delta_s_j_mol_k=d_s,
        residual_rmse=rmse,
        predicted=pred,
    )


def simulate_spr_sensorgram(
    time_s: NDArray[np.float64],
    analyte_conc_m: float,
    kon_m_inv_s: float,
    koff_s_inv: float,
    rmax: float,
    t_assoc_s: float,
) -> DigitalTwinResult:
    """Generate synthetic SPR sensorgram from kinetic rates.

    Equation:
        R_assoc(t) = Rmax * (1 - exp(-(kon*C + koff)t)) * kon*C/(kon*C + koff)
        R_diss(t) = R(t_assoc) * exp(-koff*(t - t_assoc))
    """
    kobs = kon_m_inv_s * analyte_conc_m + koff_s_inv
    steady = rmax * (kon_m_inv_s * analyte_conc_m) / max(kobs, 1e-12)
    assoc = steady * (1.0 - np.exp(-kobs * np.minimum(time_s, t_assoc_s)))
    r_at_switch = steady * (1.0 - np.exp(-kobs * t_assoc_s))
    diss = r_at_switch * np.exp(-koff_s_inv * np.maximum(time_s - t_assoc_s, 0.0))
    response = np.where(time_s <= t_assoc_s, assoc, diss)
    return DigitalTwinResult(time_s=time_s.astype(np.float64), response=response.astype(np.float64))


def simulate_itc_injections(
    injection_moles: NDArray[np.float64],
    kd_m: float,
    delta_h_j_mol: float,
) -> NDArray[np.float64]:
    """Digital twin ITC heats from single-site binding approximation."""
    frac_bound = injection_moles / (kd_m + injection_moles)
    heat = delta_h_j_mol * np.diff(np.concatenate(([0.0], frac_bound)))
    return heat.astype(np.float64)


def bootstrap_error_cloud(
    concentrations_m: NDArray[np.float64],
    mean_curve: NDArray[np.float64],
    sigma: float,
    n_iter: int = 1000,
    random_seed: int = 7,
) -> NDArray[np.float64]:
    """Generate bootstrap Monte Carlo cloud around a fitted curve.

    Returns matrix [n_iter, n_points].
    """
    rng = np.random.default_rng(random_seed)
    return rng.normal(loc=mean_curve[None, :], scale=sigma, size=(n_iter, concentrations_m.shape[0])).astype(np.float64)


def quality_score_gate(ka_m_inv: float, protein_conc_m: float, stoichiometry: float, mass_transport_ratio: float) -> PhysicsQualityGate:
    """QC gate for ITC/SPR runs.

    c-value equation:
        c = Ka * [M]_t * n
    """
    c_val = ka_m_inv * protein_conc_m * stoichiometry
    if c_val < 1.0:
        warning = "Low c-value: parameter identifiability risk"
    elif c_val > 1000.0:
        warning = "High c-value: likely lower-bound Kd regime"
    else:
        warning = "c-value in reliable window"
    return PhysicsQualityGate(c_value=c_val, c_warning=warning, mass_transport_flag=mass_transport_ratio > 0.25)


def infer_dg_from_kd(kd_m: float, temperature_k: float) -> float:
    """Compute Gibbs free energy.

    Equation:
        ΔG = RT ln(Kd)
    """
    if kd_m <= 0 or temperature_k <= 0:
        raise ValueError("kd_m and temperature_k must be positive")
    return R_GAS_J_MOL_K * temperature_k * log(kd_m)
