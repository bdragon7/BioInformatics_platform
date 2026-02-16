from pathlib import Path


def test_formulation_toolbox_hook_present() -> None:
    source = Path("src/bioplatform/gui/app.py").read_text(encoding="utf-8")
    assert "Formulation Toolbox" in source
    assert "open_formulation_toolbox" in source
    assert "Analyze Formulation" in source
    assert "Include soiling (organic load) as DoE variable" in source
    assert "Include hard water as DoE variable" in source
    assert "E. coli" in source
    assert "S. aureus" in source
    assert "DoE interaction map" in source
