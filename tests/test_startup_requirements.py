from pathlib import Path


def test_main_handles_runtime_installers_without_hard_fail() -> None:
    source = Path("main.py").read_text(encoding="utf-8")
    assert "ensure_r_installed" in source
    assert "ensure_pymol_installed" in source
    assert "R runtime not available" in source
