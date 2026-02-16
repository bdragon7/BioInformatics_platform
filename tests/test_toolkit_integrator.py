from pathlib import Path

from bioplatform.plugins.toolkit_integrator import ToolSettingsManager, ToolkitIntegratorPlugin


def test_tool_settings_manager_roundtrip(tmp_path: Path) -> None:
    manager = ToolSettingsManager(tmp_path / "config" / "integrated_tools.json")
    settings = manager.load()
    assert "gseapy" in settings

    settings["gseapy"] = False
    manager.save(settings)
    assert manager.load()["gseapy"] is False


def test_toolkit_integrator_sanitize_modes() -> None:
    plugin = ToolkitIntegratorPlugin()
    seq_res = plugin.execute_logic({"mode": "sanitize_sequence", "sequence": "ACGTXYZ"})
    assert seq_res["data"] == "ACGTNNN"

    growth_res = plugin.execute_logic({"mode": "sanitize_growth", "values": [0.1, None, 0.2]})
    assert growth_res["data"][1] == 0.1
    assert isinstance(growth_res["outliers"], list)
