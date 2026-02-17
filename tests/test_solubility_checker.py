from bioplatform.core.solubility_checker import SolubilityChecker


def test_solubility_warning_trigger() -> None:
    checker = SolubilityChecker()
    warn = checker.check_solubility("chlorhexidine", concentration_g_l=70.0, temperature_c=25.0)
    assert warn is not None
    assert "High crystallization risk" in warn.warning


def test_incompatibility_matrix_flags_pairs() -> None:
    checker = SolubilityChecker()
    warnings = checker.check_incompatibilities(["Sodium Hypochlorite", "Citric Acid", "Water"])
    assert warnings
    assert "hazardous" in warnings[0].lower()


def test_arrhenius_retest_estimation() -> None:
    checker = SolubilityChecker()
    est = checker.estimate_retest_date(activation_energy_kj_mol=55.0, storage_temp_c=40.0, baseline_half_life_days=180)
    assert est.estimated_half_life_days > 0
    assert len(est.retest_date) == 10
