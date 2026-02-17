from pathlib import Path


def test_windows_exe_packaging_assets_exist() -> None:
    assert Path('scripts/build_windows_portable.ps1').exists()


def test_windows_exe_docs_and_workflow() -> None:
    readme = Path('README.md').read_text(encoding='utf-8')
    workflow = Path('.github/workflows/build-portable.yml').read_text(encoding='utf-8')

    assert 'Windows executable alternative (.exe)' in readme
    assert 'build-windows-exe' in workflow
    assert 'BioinformaticsStudio-windows-exe' in workflow
