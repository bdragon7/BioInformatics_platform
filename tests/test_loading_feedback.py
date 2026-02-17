from pathlib import Path


def test_app_contains_loading_feedback_components() -> None:
    app_source = Path('src/bioplatform/gui/app.py').read_text(encoding='utf-8')
    assert 'QSplashScreen' in app_source
    assert 'QProgressDialog' in app_source
    assert 'QProgressBar' in app_source
    assert '_execute_with_progress' in app_source


def test_readme_mentions_windows_exe_alternative() -> None:
    readme = Path('README.md').read_text(encoding='utf-8')
    assert 'Windows executable alternative (.exe)' in readme
