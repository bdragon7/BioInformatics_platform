from pathlib import Path


def test_conda_launchers_exist() -> None:
    assert Path('launch_conda.bat').exists()
    assert Path('launch_conda.sh').exists()
    assert Path('scripts/setup_conda_env.bat').exists()
    assert Path('scripts/setup_conda_env.sh').exists()


def test_conda_launcher_docs_hint() -> None:
    readme = Path('README.md').read_text(encoding='utf-8')
    assert 'Launch with Anaconda / Miniconda' in readme
