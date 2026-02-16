from __future__ import annotations

from pathlib import Path

import pytest

np = pytest.importorskip("numpy")

from bioplatform.core.physics_engine import (
    bootstrap_error_cloud,
    cheng_prusoff_ki,
    global_joint_spr_itc_fit,
    global_kd_fit,
    infer_dg_from_kd,
    morrison_fraction_bound,
    quality_score_gate,
    simulate_itc_injections,
    simulate_spr_sensorgram,
    solver_convergence_path,
    to_molar,
    wang_ki,
)
from bioplatform.core.structure_engine import energetic_mapping, parse_pdb_atoms, residue_rmsf, sasa_rolling_ball


R = 8.31446261815324


def test_global_kd_fit_recovers_vanthoff_parameters() -> None:
    pytest.importorskip("scipy")

    temps = np.array([288.15, 298.15, 310.15], dtype=float)
    conc = np.logspace(-9, -5, 12)
    delta_h = -42000.0
    delta_s = -120.0

    kd_t = np.exp((delta_h - temps[:, None] * delta_s) / (R * temps[:, None]))
    response = conc[None, :] / (kd_t + conc[None, :])

    fit = global_kd_fit(conc.astype(np.float64), response.astype(np.float64), temps.astype(np.float64))
    assert abs((fit.delta_h_j_mol - delta_h) / delta_h) < 0.05
    assert abs((fit.delta_s_j_mol_k - delta_s) / delta_s) < 0.05
    assert fit.residual_rmse < 1e-4


def test_competition_and_depletion_equations() -> None:
    ki_cp = cheng_prusoff_ki(ic50_m=1e-6, tracer_conc_m=5e-8, tracer_kd_m=5e-8)
    assert ki_cp.ki_m == pytest.approx(5e-7)

    ki_wang = wang_ki(ic50_m=1e-6, receptor_total_m=5e-8, ligand_total_m=1e-7, kd_probe_m=5e-8)
    assert ki_wang.ki_m > 0

    fb = morrison_fraction_bound(np.array([1e-9, 1e-8, 1e-7], dtype=np.float64), enzyme_total_m=1e-8, ki_m=1e-9)
    assert fb.shape == (3,)
    assert np.all((fb >= 0) & (fb <= 1.0 + 1e-9))


def test_itc_spr_bootstrap_and_qc_gate() -> None:
    t = np.linspace(0, 300, 301, dtype=np.float64)
    spr = simulate_spr_sensorgram(t, analyte_conc_m=5e-7, kon_m_inv_s=2e5, koff_s_inv=5e-3, rmax=120.0, t_assoc_s=150.0)
    assert spr.response.shape == t.shape
    assert float(np.max(spr.response)) > 0

    itc = simulate_itc_injections(np.array([1e-11, 2e-11, 3e-11], dtype=np.float64), kd_m=1e-8, delta_h_j_mol=-35000.0)
    assert itc.shape == (3,)

    cloud = bootstrap_error_cloud(np.array([1e-9, 1e-8, 1e-7], dtype=np.float64), np.array([0.1, 0.5, 0.9], dtype=np.float64), 0.03)
    assert cloud.shape == (1000, 3)

    gate = quality_score_gate(ka_m_inv=1e7, protein_conc_m=5e-6, stoichiometry=1.0, mass_transport_ratio=0.4)
    assert gate.mass_transport_flag is True
    assert gate.c_value > 1.0


def test_units_and_dg() -> None:
    assert to_molar(500.0, "nM") == pytest.approx(5e-7)
    dg = infer_dg_from_kd(1e-7, 298.15)
    assert dg < 0


def test_structure_bridge_metrics(tmp_path: Path) -> None:
    pdb = tmp_path / "toy.pdb"
    pdb.write_text(
        "ATOM      1  CA  ALA A   1      11.000  12.000  13.000  1.00 20.00           C\n"
        "ATOM      2  CB  ALA A   1      12.000  13.000  14.000  1.00 22.00           C\n"
        "ATOM      3  CA  SER A   2      15.000  16.000  17.000  1.00 30.00           C\n",
        encoding="utf-8",
    )

    atoms = parse_pdb_atoms(pdb)
    assert len(atoms) == 3

    metrics = residue_rmsf(atoms)
    assert metrics.residue_ids.shape[0] == 2

    sasa = sasa_rolling_ball(atoms)
    assert sasa.total_sasa > 0

    kd_res = np.array([1e-7, 1e-6], dtype=np.float64)
    energy = energetic_mapping(metrics, kd_res)
    assert energy.delta_g_contrib_j_mol.shape[0] == 2


def test_global_joint_spr_itc_fit_and_convergence_path() -> None:
    pytest.importorskip("scipy")

    t = np.linspace(0.0, 240.0, 241, dtype=np.float64)
    true_spr = simulate_spr_sensorgram(
        t,
        analyte_conc_m=4e-7,
        kon_m_inv_s=2e5,
        koff_s_inv=4e-3,
        rmax=100.0,
        t_assoc_s=120.0,
    ).response

    inj = np.array([1e-11, 2e-11, 3e-11, 4e-11], dtype=np.float64)
    true_itc = simulate_itc_injections(inj, kd_m=2e-8, delta_h_j_mol=-38000.0)

    fit = global_joint_spr_itc_fit(
        spr_time_s=t,
        spr_response_ru=true_spr,
        spr_analyte_conc_m=4e-7,
        itc_injection_moles=inj,
        itc_heat_j=true_itc,
        temperature_k=298.15,
        t_assoc_s=120.0,
    )
    assert fit.kd_m > 0
    assert fit.spr_predicted.shape == true_spr.shape
    assert fit.itc_predicted.shape == true_itc.shape

    path = solver_convergence_path(10.0, 0.1, frames=20)
    assert path.shape == (20,)
    assert path[0] > path[-1]
