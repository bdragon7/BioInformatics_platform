from pathlib import Path


def test_data_table_has_excel_like_table_view_hooks() -> None:
    source = Path("src/bioplatform/gui/data_table.py").read_text(encoding="utf-8")
    assert "class ExcelLikeTableView" in source
    assert "event.matches(qt.QKeySequence.Copy)" in source
    assert "event.matches(qt.QKeySequence.Paste)" in source
    assert "Insert Row Above" in source
    assert "Delete Selected Row(s)" in source


def test_data_table_uses_function_registry_for_formulas() -> None:
    source = Path("src/bioplatform/gui/data_table.py").read_text(encoding="utf-8")
    assert "EXCEL_FUNCTIONS" in source
    assert '"STDEV.P"' in source
    assert '__RANGE__("' in source
