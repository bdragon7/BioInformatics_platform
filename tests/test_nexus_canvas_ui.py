from pathlib import Path

from bioplatform.core.pipeline_engine import PythonRPipelineEngine


def test_helix_hud_hooks_present() -> None:
    source = Path("src/bioplatform/gui/helix_main_window.py").read_text(encoding="utf-8")
    assert "Nexus Control Center" in source
    assert "WA_NoMousePropagation" in source
    assert "compute_toggle" in source
    assert "nvidia-smi" in source
    assert "hud_timer.setInterval(500)" in source


def test_canvas_x_widget_and_data_bridge_hooks_present() -> None:
    interactive = Path("src/bioplatform/gui/interactive_plot.py").read_text(encoding="utf-8")
    table = Path("src/bioplatform/gui/data_table.py").read_text(encoding="utf-8")
    assert "Canvas-X" in interactive
    assert "LinearRegionItem" in interactive
    assert "pointEdited" in interactive
    assert "data_edited_point" in table
    assert "GraphEditorState" in table


def test_pipeline_engine_links_graph_editor_state() -> None:
    engine = PythonRPipelineEngine()
    result = engine.run_growth_pipeline([0.1, 0.12, 0.11, 1.0])
    payload = engine.interactive_plot_payload(result.cleaned, result.outliers)
    assert "style" in payload
    assert "editor_undo_depth" in payload


def test_compute_cost_tooltips_exist() -> None:
    source = Path("src/bioplatform/tooltips.py").read_text(encoding="utf-8")
    assert "compute.cost.qsar" in source
    assert "compute.cost.physics" in source
    assert "compute.cost.micro" in source
