from bioplatform.core.antimicrobial_standards import (
    EN1276Input,
    biofilm_log_reduction,
    compare_biofilm_vs_planktonic,
    en1276_evaluate,
    mean_sd_ci95,
)


def test_en1276_pass_case() -> None:
    result = en1276_evaluate(
        EN1276Input(
            n0=1_000_000,
            na=1,
            n0_water=950_000,
            inoculum_reference=1_000_000,
            neutralization_recovery_fraction=0.8,
            contact_time_min=5,
            temperature_c=20.0,
            organism="E. coli ATCC 10536",
        )
    )
    assert result.pass_criterion
    assert result.overall_valid


def test_biofilm_gap_interpretation() -> None:
    bio = biofilm_log_reduction(1_000_000, 100_000)
    msg = compare_biofilm_vs_planktonic(bio, 4.0)
    assert "resistance" in msg.lower()


def test_mean_sd_ci() -> None:
    mean, sd, ci = mean_sd_ci95([1.0, 2.0, 3.0])
    assert mean == 2.0
    assert sd > 0
    assert ci > 0
