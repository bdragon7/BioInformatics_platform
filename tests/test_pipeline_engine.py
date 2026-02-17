from pathlib import Path

from bioplatform.core.pipeline_engine import PythonRPipelineEngine, infer_numeric_series


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


def test_plot_suggestions_include_advanced_view() -> None:
    engine = PythonRPipelineEngine()
    suggestions = engine.suggest_insightful_plot_types([0.1, 0.2, 0.15, 0.3])
    assert len(suggestions) == 3
    assert any(item.advanced for item in suggestions)


def test_interactive_payload_has_style_guide_and_suggestions() -> None:
    engine = PythonRPipelineEngine()
    payload = engine.interactive_plot_payload([1.0, 2.0, 1.5], [1])
    assert "suggestions" in payload
    assert "style_guide" in payload


def test_world_class_style_guide_has_palette() -> None:
    guide = PythonRPipelineEngine.world_class_plot_style_guide()
    assert "palette" in guide
    assert isinstance(guide["palette"], list)


def test_infer_numeric_series_from_records() -> None:
    series = infer_numeric_series([{"time": "1", "name": "a"}, {"time": "2", "name": "b"}])
    assert series == [1.0, 2.0]


def test_load_values_from_csv_without_manual_mapping(tmp_path: Path) -> None:
    csv_file = tmp_path / "values.csv"
    csv_file.write_text("sample,signal\nA,1.2\nB,2.5\n", encoding="utf-8")
    engine = PythonRPipelineEngine()
    values = engine.load_values_from_file(csv_file)
    assert values == [1.2, 2.5]


def test_load_values_from_json_without_manual_mapping(tmp_path: Path) -> None:
    json_file = tmp_path / "values.json"
    json_file.write_text('[{"x": 3}, {"x": 4.5}]', encoding="utf-8")
    engine = PythonRPipelineEngine()
    values = engine.load_values_from_file(json_file)
    assert values == [3.0, 4.5]
