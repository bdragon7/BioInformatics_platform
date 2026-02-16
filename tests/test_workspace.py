from pathlib import Path

from bioplatform.core.workspace import WorkspaceManager


def test_create_project(tmp_path: Path) -> None:
    manager = WorkspaceManager(tmp_path)
    paths = manager.create_project("demo")
    assert paths.root.exists()
    assert paths.raw.exists()
    assert paths.results.exists()
