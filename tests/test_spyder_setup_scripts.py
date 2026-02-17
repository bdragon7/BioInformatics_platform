from pathlib import Path


def test_spyder_setup_scripts_exist() -> None:
    assert Path('scripts/setup_spyder_env.bat').exists()
    assert Path('scripts/setup_spyder_env.sh').exists()


def test_spyder_setup_docs_hint() -> None:
    text = Path('README.md').read_text(encoding='utf-8')
    assert 'Spyder setup helper (no Conda required)' in text
