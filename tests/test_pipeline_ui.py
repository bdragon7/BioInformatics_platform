from pathlib import Path


def test_app_has_pipeline_runner_ui_hooks() -> None:
    src = Path('src/bioplatform/gui/app.py').read_text(encoding='utf-8')
    assert 'open_pipeline_runner' in src
    assert 'Pipeline: clean → stats → figure' in src
    assert 'PythonRPipelineEngine' in src
