from pathlib import Path


def test_structure_viewport_has_apex_hooks() -> None:
    source = Path("src/bioplatform/gui/structure_viewport.py").read_text(encoding="utf-8")
    assert "Apex Structural Intelligence" in source
    assert "PyMOLCommandWorker" in source
    assert "residueSelected" in source
    assert "focus_outlier" in source
    assert "#dc2626" in source or "color red" in source
    assert "GemmaInsightWorker" in source
    assert "HistorySlider" in source


def test_helix_model_action_wired_to_apex_viewport() -> None:
    source = Path("src/bioplatform/gui/helix_main_window.py").read_text(encoding="utf-8")
    assert "open_apex_structure_viewport" in source
    assert "open_structure_viewport" in source
    assert "_highlight_variant_row" in source
