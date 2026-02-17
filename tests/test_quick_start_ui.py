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


def test_app_enables_builtin_plugin_seeding() -> None:
    source = Path("src/bioplatform/gui/app.py").read_text(encoding="utf-8")
    assert "seed_builtins=True" in source


def test_app_defaults_to_dark_pharmaceutical_theme() -> None:
    source = Path("src/bioplatform/gui/app.py").read_text(encoding="utf-8")
    assert 'win.apply_theme("dark_pharmaceutical")' in source
    assert 'self.theme_combo.setCurrentText("dark_pharmaceutical")' in source


def test_app_has_plot_console_log_hooks() -> None:
    source = Path("src/bioplatform/gui/app.py").read_text(encoding="utf-8")
    assert "Visual Plot Builder" in source
    assert "open_dual_console" in source
    assert "open_system_log_viewer" in source


def test_app_toolbar_groups_and_terminal_tabs_present() -> None:
    source = Path("src/bioplatform/gui/app.py").read_text(encoding="utf-8")
    assert "add_group_label(\"Project\")" in source
    assert "add_group_label(\"Views\")" in source
    assert "add_group_label(\"Tools\")" in source
    assert "add_group_label(\"Actions\")" in source
    assert "add_group_label(\"System\")" in source
    assert "🐍 Python" in source
    assert "📊 R" in source
    assert "💻 System" in source
    assert "📄 Log" in source
    assert "📤 Output" in source
    assert "Ctrl+`" in source
