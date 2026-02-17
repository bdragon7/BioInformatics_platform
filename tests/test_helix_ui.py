from pathlib import Path
from main import build_parser
from bioplatform.gui.helix_theme import HELIX_QSS, helix_palette
from bioplatform.gui.sequence_viewer import sequence_color_map


def test_helix_theme_contains_rounded_geometry_rules() -> None:
    assert 'border-radius: 24px' in HELIX_QSS
    assert 'border-radius: 12px' in HELIX_QSS


def test_helix_palette_keys() -> None:
    palette = helix_palette()
    assert {'surface', 'surface_elevated', 'accent_indigo', 'accent_slate', 'text'}.issubset(palette)


def test_sequence_color_map_has_dna_bases() -> None:
    cmap = sequence_color_map()
    for base in ['A', 'C', 'G', 'T', 'a', 'c', 'g', 't']:
        assert base in cmap


def test_cli_has_helix_ui_flag() -> None:
    parser = build_parser()
    args = parser.parse_args(['--helix-ui'])
    assert args.helix_ui is True


def test_helix_has_gemma_local_controls() -> None:
    source = Path("src/bioplatform/gui/helix_main_window.py").read_text(encoding="utf-8")
    assert "Gemma-Local" in source
    assert "Gemma Model Manager" in source
    assert "GemmaStreamWorker" in source


def test_helix_shelf_uses_svg_icons() -> None:
    source = Path("src/bioplatform/gui/helix_main_window.py").read_text(encoding="utf-8")
    assert '"assets" / "icons"' in source
    assert "ShelfToolButton" in source
