from bioplatform.tooltips import TOOLTIPS


def test_master_plotting_tooltips_present() -> None:
    assert "plot.master_architect" in TOOLTIPS
    assert "plot.style_guide" in TOOLTIPS
