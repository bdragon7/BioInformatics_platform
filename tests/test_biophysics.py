from bioplatform.core.biophysics import (
    cheng_prusoff_ki,
    fa_anisotropy,
    gibbs_from_kd,
    itc_c_value_warning,
    kd_from_rates,
    residence_time,
)


def test_cheng_prusoff() -> None:
    ki = cheng_prusoff_ki(ic50=100.0, tracer_conc=10.0, tracer_kd=10.0)
    assert ki == 50.0


def test_fa_anisotropy() -> None:
    r = fa_anisotropy(100.0, 50.0)
    assert 0 < r < 1


def test_thermo_and_kinetics_helpers() -> None:
    kd = kd_from_rates(kon=1e5, koff=1e-2)
    assert kd == 1e-7
    tau = residence_time(1e-2)
    assert tau == 100.0
    dg = gibbs_from_kd(1e-7, 298.15)
    assert dg < 0


def test_itc_c_value_warning_ranges() -> None:
    assert "optimal" in itc_c_value_warning(100)
    assert "< 1" in itc_c_value_warning(0.5)
