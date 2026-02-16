from __future__ import annotations

from pathlib import Path

import pytest

from bioplatform.core.antimicrobial_pro import solve_mic, validate_en_standard, zoi_analysis_placeholder
from bioplatform.core.microbiology_engine import (
    fit_growth_model,
    logistic_model,
    modified_gompertz,
    parse_virtual_plate,
)


def _rel_err(a: float, b: float) -> float:
    return abs(a - b) / max(abs(b), 1e-12)


@pytest.mark.parametrize("model_name", ["gompertz", "logistic"])
def test_growth_fit_recovers_parameters_to_0p1_percent(model_name: str) -> None:
    pytest.importorskip("scipy")
    time_hours = [i * 0.5 for i in range(1, 25)]

    if model_name == "gompertz":
        truth = {"a": 1.25, "mu": 0.72, "lag": 1.8}
        obs = [modified_gompertz(t, truth["a"], truth["mu"], truth["lag"]) for t in time_hours]
        fit = fit_growth_model(time_hours, obs, model_name="gompertz")
        assert _rel_err(fit.parameters["a"], truth["a"]) < 0.001
        assert _rel_err(fit.parameters["mu"], truth["mu"]) < 0.001
        assert _rel_err(fit.parameters["lag"], truth["lag"]) < 0.001
    else:
        truth = {"k": 1.4, "r": 0.61, "t0": 4.2}
        obs = [logistic_model(t, truth["k"], truth["r"], truth["t0"]) for t in time_hours]
        fit = fit_growth_model(time_hours, obs, model_name="logistic")
        assert _rel_err(fit.parameters["k"], truth["k"]) < 0.001
        assert _rel_err(fit.parameters["r"], truth["r"]) < 0.001
        assert _rel_err(fit.parameters["t0"], truth["t0"]) < 0.001

    assert fit.rmse < 1e-6
    assert fit.r_squared > 0.99999
    assert fit.mu_max > 0


def test_virtual_plate_parser_maps_metadata(tmp_path: Path) -> None:
    csv_file = tmp_path / "plate.csv"
    csv_file.write_text(
        "well,strain,replicate,treatment,t0,t1,t2\n"
        "A1,Ecoli,R1,Control,0.05,0.09,0.17\n"
        "A2,Ecoli,R2,DrugA,0.04,0.05,0.06\n",
        encoding="utf-8",
    )

    plate = parse_virtual_plate(csv_file, plate_format="96")
    assert plate.format_name == "96-well"
    assert len(plate.records) == 2
    assert plate.records[0].well == "A1"
    assert plate.records[1].treatment == "DrugA"
    assert plate.records[0].values == [0.05, 0.09, 0.17]


def test_en_validator_and_mic_solver() -> None:
    en = validate_en_standard(
        n0=1e8,
        na=1e2,
        n0_water=1.1e8,
        inoculum_reference=1e8,
        neutralization_recovery_fraction=0.8,
        is_fungal=False,
    )
    assert en.standard == "EN 1276"
    assert en.pass_fail is True
    assert en.log_reduction >= 5.0

    concentrations = [0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
    growth = [0.95, 0.90, 0.82, 0.55, 0.22, 0.08, 0.03]
    mic = solve_mic(concentrations, growth)
    assert 4.0 <= mic.mic <= 12.0
    assert mic.lower_ci_95 < mic.mic < mic.upper_ci_95


def test_zoi_placeholder() -> None:
    out = zoi_analysis_placeholder("plate.jpg")
    assert out.status == "planned"
    assert "OpenCV" in out.notes
