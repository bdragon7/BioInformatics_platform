from pathlib import Path


def test_app_has_toolkit_settings_ui_hooks() -> None:
    src = Path('src/bioplatform/gui/app.py').read_text(encoding='utf-8')
    assert 'open_toolkit_settings' in src
    assert 'Integrated Toolkit Settings' in src
    assert 'ToolSettingsManager' in src
