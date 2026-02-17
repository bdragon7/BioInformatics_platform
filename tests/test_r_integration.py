from pathlib import Path

from bioplatform.core.r_integration import RIntegrationManager


def test_r_installer_plan_shape(tmp_path: Path) -> None:
    manager = RIntegrationManager(app_dir=tmp_path)
    plan = manager.installer_plan()
    assert plan["estimated_size_mb"] == 250
    assert "DESeq2" in plan["recommended_packages"]


def test_feature_availability_without_r(tmp_path: Path) -> None:
    manager = RIntegrationManager(preferred_executable="__missing_r__", app_dir=tmp_path)
    status = manager.detect_r()
    availability = manager.feature_availability()
    assert status.available is False
    assert "R Required" in availability["de_deseq2"]
