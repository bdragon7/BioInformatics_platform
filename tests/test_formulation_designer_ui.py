from pathlib import Path


def test_formulation_designer_hooks_present() -> None:
    source = Path("src/bioplatform/gui/formulation/formulation_designer.py").read_text(encoding="utf-8")
    assert "Formulation Engineering Suite" in source
    assert "Generate Lab Handling Sheet" in source
    assert "Helix-Pulse" in source
    assert "#2ECC71" in source
    assert "#E74C3C" in source


def test_app_wires_new_formulation_wizard() -> None:
    source = Path("src/bioplatform/gui/app.py").read_text(encoding="utf-8")
    assert "New Formulation" in source
    assert "open_formulation_designer_wizard" in source
