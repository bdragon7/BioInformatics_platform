from pathlib import Path


def test_physics_studio_has_deep_space_palette_and_controls() -> None:
    src = Path("src/bioplatform/gui/physics/physics_studio.py").read_text(encoding="utf-8")
    assert "#0F172A" in src
    assert "#38BDF8" in src
    assert "#F472B6" in src
    assert "Kinetic Scrubbing" in src
    assert "Global Fit (TRF)" in src
