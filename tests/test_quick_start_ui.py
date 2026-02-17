from pathlib import Path


def test_quick_start_ui_hooks_present() -> None:
    source = Path("src/bioplatform/gui/app.py").read_text(encoding="utf-8")
    assert "Quick Start" in source
    assert "open_quick_start" in source
    assert "Quick Start (Office-style)" in source


def test_app_menu_and_runtime_hooks_present() -> None:
    source = Path("src/bioplatform/gui/app.py").read_text(encoding="utf-8")
    assert "Search GitHub Plugins" in source
    assert "Runtime Status" in source
    assert "plugin_install_mode" in source
