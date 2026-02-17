from bioplatform.core.microbiology import (
    analyze_growth_curve,
    contamination_flags,
    detect_outliers_zscore,
    fit_standard_curve,
    standards_alignment_notes,
)


def test_detect_outliers_zscore() -> None:
    values = [0.1, 0.12, 0.11, 0.09, 1.1]
    outliers = detect_outliers_zscore(values, threshold=1.8)
    assert outliers == [4]


def test_fit_standard_curve() -> None:
    fit = fit_standard_curve([1, 2, 3, 4], [2, 4, 6, 8])
    assert round(fit.slope, 2) == 2.0
    assert round(fit.intercept, 2) == 0.0
    assert fit.r_squared > 0.99


def test_growth_metrics_and_contamination_flags() -> None:
    metrics = analyze_growth_curve([0, 1, 2, 3], [0.05, 0.07, 0.2, 0.45])
    assert metrics.mu_max > 0
    assert metrics.carrying_capacity == 0.45
    assert metrics.generation_time is not None

    flags = contamination_flags([0.01, 0.012, 0.014, 0.05], spike_multiplier=2.5)
    assert flags


def test_standards_alignment_notes_contains_en_and_astm() -> None:
    notes = standards_alignment_notes()
    assert "EN 1276" in notes
    assert any(k.startswith("ASTM") for k in notes)
