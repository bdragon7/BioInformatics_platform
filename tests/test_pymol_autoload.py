from pathlib import Path


def test_windows_build_scripts_include_pymol_autoload() -> None:
    exe_script = Path('scripts/build_windows_portable.ps1').read_text(encoding='utf-8')
    noexe_script = Path('scripts/build_windows_portable_noexe.ps1').read_text(encoding='utf-8')

    assert 'BIOPLATFORM_AUTOLOAD_PYMOL' in exe_script
    assert 'github.com/schrodinger/pymol-open-source.git' in exe_script

    assert 'BIOPLATFORM_AUTOLOAD_PYMOL' in noexe_script
    assert 'github.com/schrodinger/pymol-open-source.git' in noexe_script


def test_readme_mentions_pymol_autoload_override() -> None:
    readme = Path('README.md').read_text(encoding='utf-8')
    assert 'PyMOL auto-load from GitHub during Windows builds' in readme
    assert 'BIOPLATFORM_AUTOLOAD_PYMOL' in readme
