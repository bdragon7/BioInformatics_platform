from pathlib import Path


def test_app_has_analysis_library_ui_entry() -> None:
    src = Path('src/bioplatform/gui/app.py').read_text(encoding='utf-8')
    assert 'Analysis Library' in src
    assert 'open_analysis_library' in src
    assert 'analysis_library.catalog()' in src
