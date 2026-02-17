from pathlib import Path

from bioplatform.gui.performance_monitor import PerformanceMonitorModel


def test_performance_monitor_snapshot_has_message() -> None:
    snap = PerformanceMonitorModel().snapshot(focused=True)
    assert snap.mode in {"CPU", "GPU"}
    assert snap.message


def test_app_contains_performance_badge_hooks() -> None:
    source = Path("src/bioplatform/gui/app.py").read_text(encoding="utf-8")
    assert "PerformanceBadge" in source
    assert "_update_performance_badge" in source
