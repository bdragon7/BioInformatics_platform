from pathlib import Path

from bioplatform.core.workspace import WorkspaceManager


def test_create_project(tmp_path: Path) -> None:
    manager = WorkspaceManager(tmp_path)
    paths = manager.create_project("demo")
    assert paths.root.exists()
    assert paths.raw.exists()
    assert paths.results.exists()


def test_audit_entries_chain_hashes(tmp_path: Path) -> None:
    manager = WorkspaceManager(tmp_path)
    first = manager.append_audit_entry(event="spreadsheet_edit", payload={"row": 1})
    second = manager.append_audit_entry(event="spreadsheet_edit", payload={"row": 2})
    assert manager.audit_log_path.exists()
    assert second["prev_hash"] == first["hash"]
