from pathlib import Path


def test_default_theme_is_dark_pharmaceutical() -> None:
    app_source = Path('src/bioplatform/gui/app.py').read_text(encoding='utf-8')
    assert 'win.apply_theme("dark_pharmaceutical")' in app_source


def test_light_theme_uses_chromeos_like_beige_palette() -> None:
    theme_source = Path('src/bioplatform/gui/themes.py').read_text(encoding='utf-8')
    assert '#f6f2e8' in theme_source
    assert '#efe7d8' in theme_source
    assert '#fffaf1' in theme_source
