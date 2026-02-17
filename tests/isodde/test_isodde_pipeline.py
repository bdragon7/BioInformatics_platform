from pathlib import Path

from bioplatform.isodde import DataManager, IsoDDEPipeline


def test_isodde_pipeline_predicts_workflow() -> None:
    pipe = IsoDDEPipeline()
    res = pipe.predict_full_workflow("MKTLLILAV", "CCO")
    assert res.structures
    assert res.affinity is not None
    assert res.pockets


def test_isodde_data_manager_writes_manifest(tmp_path: Path) -> None:
    manager = DataManager(tmp_path)
    manifest = manager.download_benchmarks()
    assert manifest.exists()
    assert "runs_n_poses" in manifest.read_text(encoding="utf-8")
