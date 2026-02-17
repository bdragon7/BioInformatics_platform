from bioplatform.integration.unified_system import UnifiedBioInformaticsSystem
from bioplatform.plotting.visual_plot_builder import PlotConfiguration, PlotType


def test_unified_system_verify_and_plot_request() -> None:
    system = UnifiedBioInformaticsSystem()
    status = system.verify_system()
    assert "pymol" in status
    assert "rdkit" in status

    code = system.on_plot_requested(PlotConfiguration(plot_type=PlotType.LINE, data_source="x.csv"))
    assert "matplotlib" in code
    assert "pd.read_csv('x.csv')" in code

    recent = system.logger.recent(limit=5)
    assert any("plot:" in entry.message for entry in recent)
