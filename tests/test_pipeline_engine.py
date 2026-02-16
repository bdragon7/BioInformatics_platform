from pathlib import Path

from bioplatform.core.pipeline_engine import PythonRPipelineEngine


def test_growth_pipeline_produces_stats_and_outliers() -> None:
    engine = PythonRPipelineEngine()
    result = engine.run_growth_pipeline([0.1, 0.12, 0.11, 0.09, 1.1])
    assert "mean" in result.stats
    assert isinstance(result.outliers, list)


def test_r_pipeline_template_present() -> None:
    engine = PythonRPipelineEngine()
    tpl = engine.r_pipeline_template()
    assert "ggplot2" in tpl


def test_export_figure_api_handles_none(tmp_path: Path) -> None:
    engine = PythonRPipelineEngine()
    exported = engine.export_figure_high_quality(None, tmp_path / "plot")
    assert exported == {}
