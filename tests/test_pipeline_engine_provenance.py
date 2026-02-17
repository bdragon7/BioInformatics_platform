from pathlib import Path

from bioplatform.core.pipeline_engine import PythonRPipelineEngine


def test_pipeline_result_contains_provenance(tmp_path: Path) -> None:
    engine = PythonRPipelineEngine()
    result = engine.run_growth_pipeline([0.1, 0.2, 0.3])
    assert result.provenance.dataset_sha256
    out = tmp_path / "bundle.json"
    engine.export_result_bundle(result, out)
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "provenance" in text
