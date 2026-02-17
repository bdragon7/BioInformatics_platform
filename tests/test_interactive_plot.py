from bioplatform.gui.interactive_plot import parse_custom_entry


def test_parse_custom_entry_pairs() -> None:
    parsed = parse_custom_entry("kind=scatter;color=#A93226;line_width=2.5")
    assert parsed["kind"] == "scatter"
    assert parsed["color"] == "#A93226"
    assert parsed["line_width"] == "2.5"


def test_parse_custom_entry_flags() -> None:
    parsed = parse_custom_entry("minimal")
    assert parsed["minimal"] == "true"
