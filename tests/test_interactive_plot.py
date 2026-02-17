from bioplatform.gui.interactive_plot import parse_custom_entry


def test_parse_custom_entry_pairs() -> None:
    parsed = parse_custom_entry("kind=scatter;color=#A93226;line_width=2.5")
    assert parsed["kind"] == "scatter"
    assert parsed["color"] == "#A93226"
    assert parsed["line_width"] == "2.5"


def test_parse_custom_entry_flags() -> None:
    parsed = parse_custom_entry("minimal")
    assert parsed["minimal"] == "true"


def test_interactive_plot_has_highlight_point_hook() -> None:
    from pathlib import Path

    source = Path("src/bioplatform/gui/interactive_plot.py").read_text(encoding="utf-8")
    assert "def highlight_point" in source


def test_data_table_links_selection_to_plot_highlight() -> None:
    from pathlib import Path

    source = Path("src/bioplatform/gui/data_table.py").read_text(encoding="utf-8")
    assert "pointSelected.connect(self._select_from_plot)" in source
    assert "self.plot_widget.highlight_point" in source
