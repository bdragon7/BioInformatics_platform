from __future__ import annotations

import pytest

from bioplatform.core.formulation_engine import (
    FormulationManager,
    IngredientSpec,
    IngredientTarget,
)


def _manager() -> FormulationManager:
    m = FormulationManager()
    m.register_ingredient(IngredientSpec("Citric Acid", molecular_weight=192.12, density_g_ml=1.66, pka=3.13, charge=-1, role="acid"))
    m.register_ingredient(IngredientSpec("Sodium Citrate", molecular_weight=258.06, density_g_ml=1.7, pka=3.13, charge=1, role="base"))
    m.register_ingredient(IngredientSpec("Sodium Chloride", molecular_weight=58.44, density_g_ml=2.16, charge=1, role="salt"))
    m.register_ingredient(IngredientSpec("Glycerol", molecular_weight=92.09, density_g_ml=1.261, role="solute"))
    return m


def test_basic_formulation_outputs() -> None:
    m = _manager()
    result = m.formulate(
        [
            IngredientTarget("Citric Acid", "molar", 0.05),
            IngredientTarget("Sodium Citrate", "molar", 0.05),
            IngredientTarget("Sodium Chloride", "mass_per_volume", 9.0),
        ],
        final_volume_ml=1000,
    )
    assert 2.5 <= result.theoretical_ph <= 8.5
    assert result.ionic_strength_m >= 0
    assert result.components


def test_density_correction_non_linear() -> None:
    v1 = FormulationManager.density_corrected_volume_ml(100, concentration_w_w=0.1)
    v2 = FormulationManager.density_corrected_volume_ml(100, concentration_w_w=0.7)
    assert v2 < v1


def test_henderson_hasselbalch_equimolar_near_pka() -> None:
    ph = FormulationManager.henderson_hasselbalch(0.1, 0.1, 4.75)
    assert abs(ph - 4.75) < 1e-9


def test_ionic_strength_formula() -> None:
    i = FormulationManager.ionic_strength({1: 0.1, -1: 0.1, 2: 0.02})
    assert i > 0.0


@pytest.mark.parametrize("bad_volume", [0, -1, -10])
def test_invalid_final_volume_errors(bad_volume: float) -> None:
    m = _manager()
    with pytest.raises(ValueError):
        m.formulate([], final_volume_ml=bad_volume)


@pytest.mark.parametrize("temp", [-20, 130, 1000])
def test_invalid_temperature_errors(temp: float) -> None:
    m = _manager()
    with pytest.raises(ValueError):
        m.formulate([], final_volume_ml=1000, temperature_c=temp)


@pytest.mark.parametrize("mass,molarity", [(-1, 0.1), (1, 0), (1, -0.1)])
def test_volume_solver_bad_inputs(mass: float, molarity: float) -> None:
    m = _manager()
    spec = m.ingredient_catalog["sodium chloride"]
    with pytest.raises(ValueError):
        m.solve_volume_from_mass_and_molarity(spec, mass, molarity)


# 56 edge-case scenarios for concentration sanity checks.
@pytest.mark.parametrize("value", [
    -100, -50, -10, -5, -1, -0.5, -0.1, -0.01,
    0, 1e-9, 1e-6, 1e-4, 1e-3, 0.005, 0.01, 0.02,
    0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1,
    0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9,
    1.0, 1.2, 1.5, 2.0, 3.0, 4.0, 5.0, 7.5,
    10.0, 12.5, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0,
    60.0, 75.0, 90.0, 100.0, 150.0, 200.0, 500.0, 1000.0,
])
def test_edge_case_component_values(value: float) -> None:
    m = _manager()
    if value < 0:
        with pytest.raises(ValueError):
            m.formulate([IngredientTarget("Sodium Chloride", "molar", value)], 1000)
        return

    result = m.formulate([IngredientTarget("Sodium Chloride", "molar", value)], 1000)
    assert result.final_volume_ml == 1000
    assert result.estimated_density_g_ml >= 0
    assert result.ionic_strength_m >= 0


def test_unknown_ingredient_warns_not_crash() -> None:
    m = _manager()
    result = m.formulate([IngredientTarget("Unknown X", "molar", 0.1)], 1000)
    assert any("Unknown ingredient" in w for w in result.warnings)
