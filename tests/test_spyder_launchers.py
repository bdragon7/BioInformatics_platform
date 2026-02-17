from pathlib import Path


def test_spyder_launchers_exist() -> None:
    assert Path('launch_spyder.bat').exists()
    assert Path('launch_spyder.sh').exists()


def test_spyder_docs_hint() -> None:
    readme = Path('README.md').read_text(encoding='utf-8')
    assert 'Launch with Spyder' in readme
