from pathlib import Path


def test_micro_dashboard_has_required_visual_language() -> None:
    source = Path("src/bioplatform/gui/microbiology/micro_dashboard.py").read_text(encoding="utf-8")
    assert "Microbiology Intelligence Dashboard" in source
    assert "#3498DB" in source
    assert "#9B59B6" in source
    assert "EN 1276 Wizard" in source
    assert "300 DPI TIFF" in source
