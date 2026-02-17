from bioplatform.gui.schrodinger_md3_theme import (
    MaterialColorGenerator,
    SchrodingerMD3ColorScheme,
    build_schrodinger_md3_stylesheet,
)
from bioplatform.gui.themes import THEMES


def test_dark_pharmaceutical_theme_registered() -> None:
    assert "dark_pharmaceutical" in THEMES


def test_schrodinger_stylesheet_contains_md3_tokens() -> None:
    qss = build_schrodinger_md3_stylesheet()
    assert "QSplitter::handle:hover" in qss
    assert "QMenu::item:selected" in qss
    assert "QLabel#StatusSuccess" in qss


def test_tonal_palette_generation_shape() -> None:
    palette = MaterialColorGenerator.generate_tonal_palette("#0891B2")
    assert set([10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99]).issubset(palette)
    assert all(value.startswith("#") and len(value) == 7 for value in palette.values())


def test_color_scheme_defaults_are_dark_surface_first() -> None:
    colors = SchrodingerMD3ColorScheme()
    assert colors.neutral_10 == "#1A1C1E"
    assert colors.primary_50 == "#0891B2"
