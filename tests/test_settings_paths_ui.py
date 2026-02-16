from pathlib import Path


def test_settings_dialog_contains_path_preferences() -> None:
    src = Path('src/bioplatform/gui/app.py').read_text(encoding='utf-8')
    assert 'Project root' in src
    assert 'Output directory' in src
    assert 'config/user_preferences.json' in src
