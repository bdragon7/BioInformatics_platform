from pathlib import Path


def test_main_enforces_runtime_installers() -> None:
    source = Path("main.py").read_text(encoding="utf-8")
    assert "ensure_r_installed" in source
    assert "ensure_pymol_installed" in source
    assert "if not ensure_r_installed()" in source
